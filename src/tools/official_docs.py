"""Official documentation synchronization and search service."""
# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from importlib import import_module
from urllib.parse import urlparse

requests = import_module("requests")
yaml = import_module("yaml")

DOCUMENT_EXTENSIONS = {".md", ".mdx", ".rst", ".txt", ".html", ".htm"}


@dataclass
class DocEntry:
    name: str
    type: str
    version: str
    target: str
    repo: Optional[str] = None
    ref: Optional[str] = None
    doc_path: Optional[str] = None
    url: Optional[str] = None
    archive_format: Optional[str] = None
    strip_components: int = 0
    http_pages: Optional[List[Dict[str, Any]]] = None
    http_pages_file: Optional[str] = None
    http_headers: Optional[Dict[str, str]] = None
    http_timeout: int = 30


@dataclass
class HttpPage:
    """단일 HTTP 문서 페이지 정의."""

    url: str
    path: Optional[str] = None


class OfficialDocsService:
    """Handles mirroring and searching of official documentation."""

    def __init__(self, base_dir: Optional[str | Path] = None) -> None:
        self.base_dir = Path(base_dir or Path(__file__).resolve().parents[2])
        self.docs_dir = self.base_dir / "docs"
        self.manifest_path = self.docs_dir / "manifest.yaml"
        self.sources_dir = self.docs_dir / "sources"
        self.mirror_dir = self.docs_dir / "mirror"
        self.metadata_name = "metadata.json"
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.mirror_dir.mkdir(parents=True, exist_ok=True)

    def load_manifest(self) -> List[DocEntry]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        with self.manifest_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        entries: List[DocEntry] = []
        for item in data.get("docs", []):
            entries.append(
                DocEntry(
                    name=item["name"],
                    type=item["type"],
                    version=item.get("version", "latest"),
                    target=item["target"],
                    repo=item.get("repo"),
                    ref=item.get("ref"),
                    doc_path=item.get("doc_path"),
                    url=item.get("url"),
                    archive_format=item.get("archive_format"),
                    strip_components=item.get("strip_components", 0),
                    http_pages=item.get("pages"),
                    http_pages_file=item.get("pages_file"),
                    http_headers=item.get("http_headers"),
                    http_timeout=item.get("http_timeout", 30),
                )
            )
        return entries

    def sync_docs(self, names: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
        entries = self.load_manifest()
        results = []
        overall_success = True

        for entry in entries:
            if names and entry.name not in names:
                continue
            try:
                if entry.type == "git":
                    self._sync_git_entry(entry, force)
                elif entry.type == "archive":
                    self._sync_archive_entry(entry, force)
                elif entry.type == "http":
                    self._sync_http_entry(entry, force)
                else:
                    raise ValueError(f"Unsupported entry type: {entry.type}")
                results.append({"name": entry.name, "success": True})
            except Exception as exc:  # pragma: no cover - runtime issues logged to caller
                overall_success = False
                results.append({"name": entry.name, "success": False, "error": str(exc)})
        return {"success": overall_success, "results": results}

    def list_docs(self) -> Dict[str, Any]:
        docs = []
        for meta_path in self.mirror_dir.glob(f"**/{self.metadata_name}"):
            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    metadata = json.load(f)
                docs.append(metadata)
            except Exception:
                continue
        return {"count": len(docs), "docs": docs}

    def search_docs(self, keyword: str, name: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        keyword_lower = keyword.lower()
        matches = []
        targets = self._iter_doc_targets(name)
        for doc_dir in targets:
            files = list(doc_dir.rglob("*"))
            for file_path in files:
                if file_path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if keyword_lower in text.lower():
                    snippet = self._make_snippet(text, keyword_lower)
                    matches.append({
                        "file": str(file_path),
                        "snippet": snippet,
                        "doc": doc_dir.name
                    })
                if len(matches) >= limit:
                    return {"matches": matches, "count": len(matches)}
        return {"matches": matches, "count": len(matches)}

    # Internal helpers

    def _sync_git_entry(self, entry: DocEntry, force: bool) -> None:
        if not entry.repo or not entry.ref:
            raise ValueError(f"Git entry {entry.name} missing repo/ref")
        repo_dir = self.sources_dir / entry.name
        if repo_dir.exists():
            subprocess.run(["git", "fetch", "origin", entry.ref], cwd=repo_dir, check=True)
            subprocess.run(["git", "reset", "--hard", f"origin/{entry.ref}"], cwd=repo_dir, check=True)
        else:
            subprocess.run([
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                entry.ref,
                entry.repo,
                str(repo_dir),
            ], check=True)
        doc_source = repo_dir / (entry.doc_path or "")
        if not doc_source.exists():
            raise FileNotFoundError(f"Doc path not found for {entry.name}: {doc_source}")
        target_dir = self.mirror_dir / entry.target
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(doc_source, target_dir)
        self._write_metadata(entry, target_dir)

    def _sync_archive_entry(self, entry: DocEntry, force: bool) -> None:
        if not entry.url or not entry.archive_format:
            raise ValueError(f"Archive entry {entry.name} missing url/archive_format")
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "archive"
            self._download_file(entry.url, archive_path)
            extract_dir = Path(tmpdir) / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)
            if entry.archive_format.lower() == "tar":
                with tarfile.open(archive_path, "r:*") as tar:
                    extract_kwargs: Dict[str, Any] = {}
                    if sys.version_info >= (3, 12):
                        extract_kwargs["filter"] = "data"
                    tar.extractall(extract_dir, **extract_kwargs)
            elif entry.archive_format.lower() == "zip":
                with ZipFile(archive_path, "r") as zip_file:
                    zip_file.extractall(extract_dir)
            else:
                raise ValueError(f"Unsupported archive format: {entry.archive_format}")
            source = self._strip_components(extract_dir, entry.strip_components)
            target_dir = self.mirror_dir / entry.target
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(source, target_dir)
            self._write_metadata(entry, target_dir)

    def _sync_http_entry(self, entry: DocEntry, force: bool) -> None:
        pages = self._resolve_http_pages(entry)
        if not pages:
            raise ValueError(f"HTTP entry {entry.name} has no pages defined")

        target_dir = self.mirror_dir / entry.target
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        for page in pages:
            relative_path = self._sanitize_relative_path(page.path or self._derive_http_relative_path(page.url))
            content = self._fetch_http_content(page.url, entry.http_headers, entry.http_timeout)
            destination = target_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

        self._write_metadata(entry, target_dir, extra={"http_pages": len(pages)})

    def _download_file(self, url: str, destination: Path) -> None:
        if url.startswith("file://"):
            source_path = Path(url[7:])
            shutil.copy(source_path, destination)
            return
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with destination.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def _strip_components(self, extract_dir: Path, strip_components: int) -> Path:
        path = extract_dir
        for _ in range(strip_components):
            entries = [item for item in path.iterdir() if item.is_dir()]
            if len(entries) == 1:
                path = entries[0]
            else:
                break
        return path

    def _write_metadata(self, entry: DocEntry, target_dir: Path, extra: Optional[Dict[str, Any]] = None) -> None:
        metadata = {
            "name": entry.name,
            "version": entry.version,
            "target": str(target_dir.relative_to(self.mirror_dir)),
            "last_synced": datetime.now(timezone.utc).isoformat()
        }
        if extra:
            metadata.update(extra)
        meta_path = target_dir / self.metadata_name
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _iter_doc_targets(self, name: Optional[str] = None) -> List[Path]:
        targets = []
        if name:
            for candidate in self.mirror_dir.glob(f"{name}/**"):
                if candidate.is_dir():
                    targets.append(candidate)
        else:
            for candidate in self.mirror_dir.glob("**"):
                if candidate.is_dir():
                    targets.append(candidate)
        return targets

    def _make_snippet(self, text: str, keyword_lower: str, radius: int = 120) -> str:
        lower_text = text.lower()
        idx = lower_text.find(keyword_lower)
        if idx == -1:
            return text[:radius] + "..."
        start = max(0, idx - radius)
        end = min(len(text), idx + radius)
        snippet = text[start:end].replace("\n", " ")
        return snippet + ("..." if end < len(text) else "")

    # HTTP helpers

    def _resolve_http_pages(self, entry: DocEntry) -> List[HttpPage]:
        raw_pages: List[Dict[str, Any]] = []
        if entry.http_pages:
            raw_pages.extend(entry.http_pages)
        if entry.http_pages_file:
            raw_pages.extend(self._load_http_pages_file(entry.http_pages_file))

        pages: List[HttpPage] = []
        for raw in raw_pages:
            if not isinstance(raw, dict) or "url" not in raw:
                continue
            pages.append(HttpPage(url=raw["url"], path=raw.get("path") or raw.get("filename")))
        return pages

    def _load_http_pages_file(self, relative_path: str) -> List[Dict[str, Any]]:
        file_path = Path(relative_path)
        if not file_path.is_absolute():
            file_path = (self.docs_dir / relative_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"HTTP pages file not found: {file_path}")

        if file_path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        elif file_path.suffix.lower() == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8")) or {}
        else:
            raise ValueError("pages_file must be a JSON or YAML document")

        if isinstance(data, dict):
            pages = data.get("pages", [])
        elif isinstance(data, list):
            pages = data
        else:
            raise ValueError("Invalid pages_file format")

        if not isinstance(pages, list):
            raise ValueError("pages_file must contain a list of page definitions")
        return pages

    def _sanitize_relative_path(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe relative path detected: {relative}")
        return path

    def _derive_http_relative_path(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or ""
        if path.endswith("/"):
            path = f"{path}index.html"
        if not path:
            path = "index.html"
        return path.lstrip("/") or "index.html"

    def _fetch_http_content(self, url: str, headers: Optional[Dict[str, str]], timeout: int) -> str:
        if url.startswith("file://"):
            source_path = Path(url[7:])
            return source_path.read_text(encoding="utf-8")
        response = requests.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.encoding or "utf-8"
        return response.text


__all__ = ["OfficialDocsService"]
