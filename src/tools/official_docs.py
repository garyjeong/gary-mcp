"""Official documentation synchronization and search service."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

import requests
import yaml

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
                    tar.extractall(extract_dir, filter="data")
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

    def _write_metadata(self, entry: DocEntry, target_dir: Path) -> None:
        metadata = {
            "name": entry.name,
            "version": entry.version,
            "target": str(target_dir.relative_to(self.mirror_dir)),
            "last_synced": datetime.now(timezone.utc).isoformat()
        }
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


__all__ = ["OfficialDocsService"]
