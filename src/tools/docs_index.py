"""간단한 문서 인덱스 관리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.tools.docs_parser import ParsedSection


@dataclass(frozen=True, slots=True)
class IndexedDoc:
    name: str
    sections: List[ParsedSection]


class DocsIndex:
    """경량 인메모리 인덱스 (향후 확장 가능)."""

    def __init__(self) -> None:
        self._docs: Dict[str, IndexedDoc] = {}

    def add_document(self, name: str, sections: List[ParsedSection]) -> None:
        self._docs[name] = IndexedDoc(name=name, sections=sections)

    def search(self, keyword: str, limit: int = 5, doc_name: Optional[str] = None) -> Dict[str, any]:
        keyword_lower = keyword.lower()
        matches: List[Dict[str, str]] = []
        targets = [doc_name] if doc_name else list(self._docs.keys())
        for target in targets:
            doc = self._docs.get(target)
            if not doc:
                continue
            for section in doc.sections:
                if keyword_lower in section.title.lower() or keyword_lower in section.content.lower():
                    matches.append(
                        {
                            "doc": target,
                            "title": section.title,
                            "snippet": section.content[:200] + ("..." if len(section.content) > 200 else ""),
                        }
                    )
                if len(matches) >= limit:
                    return {"matches": matches, "count": len(matches)}
        return {"matches": matches, "count": len(matches)}


__all__ = ["DocsIndex", "IndexedDoc"]

