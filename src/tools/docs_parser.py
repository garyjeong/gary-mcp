"""문서 파서: HTML/Markdown을 구조화."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup  # type: ignore
import markdown as md  # type: ignore


@dataclass(frozen=True, slots=True)
class ParsedSection:
    title: str
    content: str
    code_blocks: List[str]
    anchors: List[str]


class DocsParser:
    """단순한 HTML/Markdown 파서 (기본 구현)."""

    def parse_html(self, html: str) -> List[ParsedSection]:
        soup = BeautifulSoup(html, "html.parser")
        sections: List[ParsedSection] = []
        for heading in soup.find_all(["h1", "h2", "h3"]):
            title = heading.get_text(strip=True)
            content_parts: List[str] = []
            code_blocks: List[str] = []
            anchors: List[str] = []
            # siblings until next heading
            for sibling in heading.next_siblings:
                if getattr(sibling, "name", None) in ["h1", "h2", "h3"]:
                    break
                text = ""
                if hasattr(sibling, "get_text"):
                    text = sibling.get_text(" ", strip=True)
                elif isinstance(sibling, str):
                    text = sibling.strip()
                if text:
                    content_parts.append(text)
                if getattr(sibling, "name", None) == "pre":
                    code_text = sibling.get_text("\n", strip=True)
                    if code_text:
                        code_blocks.append(code_text)
            if title or content_parts:
                sections.append(
                    ParsedSection(
                        title=title or "Untitled",
                        content="\n".join(content_parts),
                        code_blocks=code_blocks,
                        anchors=anchors,
                    )
                )
        return sections

    def parse_markdown(self, markdown_text: str) -> List[ParsedSection]:
        # Convert markdown to HTML then reuse html parser
        html = md.markdown(markdown_text)
        return self.parse_html(html)


__all__ = ["DocsParser", "ParsedSection"]

