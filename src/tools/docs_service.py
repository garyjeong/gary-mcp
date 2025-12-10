"""Context7 스타일의 문서 서비스 래퍼."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pathlib import Path

from src.tools.docs_registry import LibraryMeta, registry
from src.tools.docs_parser import DocsParser
from src.tools.docs_index import DocsIndex
from src.tools.official_docs import DOCUMENT_EXTENSIONS, OfficialDocsService


class DocsService:
    """라이브러리 레지스트리 + 공식 문서 서비스 래핑."""

    def __init__(self) -> None:
        self._registry = registry
        self._official = OfficialDocsService()
        self._parser = DocsParser()
        self._structured_index = DocsIndex()

    # Registry helpers
    def resolve_library_id(self, name: str) -> Dict[str, Any]:
        meta = self._registry.resolve(name)
        if not meta:
            return {"success": False, "error": f"Library not found: {name}"}
        return {"success": True, "library": self._meta_to_dict(meta)}

    def list_libraries(self, category: Optional[str] = None, available_only: bool = False) -> Dict[str, Any]:
        metas = self._registry.list_all(category=category, available_only=available_only)
        return {"count": len(metas), "libraries": [self._meta_to_dict(m) for m in metas]}

    # Docs retrieval
    def get_library_docs(
        self,
        library_id: str,
        mode: str = "info",
        topic: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        meta = self._get_by_id(library_id)
        if not meta:
            return {"success": False, "error": f"Library not found: {library_id}"}
        if not meta.available or not meta.manifest_name:
            return {"success": False, "error": f"Library not available yet: {meta.name}"}

        # 간단 구현: topic이 있으면 검색, 없으면 list 결과 반환
        if topic:
            search = self._official.search_docs(topic, name=meta.manifest_name, limit=limit)
            return {"success": True, "mode": mode, "topic": topic, "results": search}

        # topic이 없으면 문서 목록 반환
        docs = self._official.list_docs()
        filtered = [
            doc for doc in docs.get("docs", []) if doc.get("name") == meta.manifest_name or doc.get("target", "").startswith(meta.manifest_name)
        ]
        return {"success": True, "mode": mode, "docs": filtered}

    # Search
    def search_docs(self, query: str, name: Optional[str] = None, limit: int = 5, structured: bool = False) -> Dict[str, Any]:
        if structured:
            structured_result = self._structured_search(query, name=name, limit=limit)
            structured_result["structured"] = True
            return structured_result
        return self._official.search_docs(query, name=name, limit=limit)

    # Existing passthroughs
    def sync_official_docs(self, names: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
        return self._official.sync_docs(names, force)

    def list_official_docs(self) -> Dict[str, Any]:
        return self._official.list_docs()

    # Internal helpers
    def _get_by_id(self, library_id: str) -> Optional[LibraryMeta]:
        for meta in self._registry.list_all():
            if meta.id == library_id:
                return meta
        return None

    def _structured_search(self, keyword: str, name: Optional[str], limit: int) -> Dict[str, Any]:
        mirror_dir = self._official.mirror_dir  # type: ignore[attr-defined]
        targets: List[Path] = []
        if name:
            for candidate in mirror_dir.glob(f"{name}/**"):
                if candidate.is_dir():
                    targets.append(candidate)
        else:
            for candidate in mirror_dir.glob("**"):
                if candidate.is_dir():
                    targets.append(candidate)

        # 인덱스 초기화
        self._structured_index = DocsIndex()

        for target in targets:
            doc_name = target.relative_to(mirror_dir).as_posix()
            for file_path in target.rglob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if file_path.suffix.lower() in {".md", ".mdx"}:
                    sections = self._parser.parse_markdown(text)
                else:
                    sections = self._parser.parse_html(text)
                if sections:
                    self._structured_index.add_document(doc_name, sections)

        return self._structured_index.search(keyword, limit=limit, doc_name=name)

    @staticmethod
    def _meta_to_dict(meta: LibraryMeta) -> Dict[str, Any]:
        return {
            "id": meta.id,
            "name": meta.name,
            "category": meta.category,
            "source_type": meta.source_type,
            "manifest_name": meta.manifest_name,
            "docs_url": meta.docs_url,
            "repo": meta.repo,
            "available": meta.available,
        }


__all__ = ["DocsService"]

