"""Markdown to PDF conversion service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from markdown import markdown

try:  # pragma: no cover - may fail when native libs are missing
    from weasyprint import CSS, HTML  # type: ignore
    WEASYPRINT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover
    CSS = HTML = None  # type: ignore[assignment]
    WEASYPRINT_IMPORT_ERROR = exc

from src.utils.file_utils import is_markdown_file, read_file_async


class PDFService:
    """마크다운을 PDF로 변환하는 서비스."""

    def __init__(self, default_css: Optional[str] = None) -> None:
        self.default_css = default_css

    async def convert(self, markdown_path: str, output_path: Optional[str] = None, css_path: Optional[str] = None) -> Dict[str, object]:
        if WEASYPRINT_IMPORT_ERROR is not None:  # pragma: no cover - runtime guard
            raise RuntimeError("WeasyPrint is not available") from WEASYPRINT_IMPORT_ERROR

        absolute_input = Path(markdown_path).expanduser().resolve()
        result: Dict[str, object] = {
            "success": False,
            "output_path": "",
            "error": None
        }

        if not absolute_input.exists():
            result["error"] = f"Markdown file not found: {absolute_input}"
            return result

        if not is_markdown_file(str(absolute_input)):
            result["error"] = f"File is not a markdown file: {absolute_input}"
            return result

        output_path = output_path or f"{absolute_input.stem}.pdf"
        absolute_output = Path(output_path).expanduser().resolve()

        try:
            html_payload = await self._render_html(absolute_input)
            html_doc = HTML(string=html_payload)
            stylesheets = self._collect_stylesheets(css_path)
            html_doc.write_pdf(str(absolute_output), stylesheets=stylesheets)
            result.update({"success": True, "output_path": str(absolute_output)})
        except Exception as exc:  # pragma: no cover - conversion failure reporting
            result["error"] = str(exc)
        return result

    async def batch_convert(self, markdown_files: List[str], output_dir: Optional[str] = None) -> Dict[str, object]:
        summary = {
            "success": [],
            "failed": [],
            "total": len(markdown_files)
        }

        for md_file in markdown_files:
            destination = None
            if output_dir:
                destination = str(Path(output_dir).expanduser() / (Path(md_file).stem + ".pdf"))

            result = await self.convert(md_file, destination)
            bucket = "success" if result.get("success") else "failed"
            summary[bucket].append({
                "input": md_file,
                "output": result.get("output_path"),
                "error": result.get("error")
            })
        return summary

    async def _render_html(self, markdown_path: Path) -> str:
        md_content = await read_file_async(str(markdown_path))
        body = markdown(md_content, extensions=["extra", "codehilite"])
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset=\"UTF-8\">
            </head>
            <body>{body}</body>
        </html>
        """

    def _collect_stylesheets(self, css_path: Optional[str]) -> Optional[List[CSS]]:
        if WEASYPRINT_IMPORT_ERROR is not None:  # pragma: no cover
            return None
        styles: List[CSS] = []
        css_candidates = [css_path, self.default_css]
        for candidate in css_candidates:
            if not candidate:
                continue
            path = Path(candidate).expanduser()
            if path.exists():
                styles.append(CSS(filename=str(path)))
        return styles or None
