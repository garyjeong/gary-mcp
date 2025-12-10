"""PDF 변환 MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.pdf_tool import PDFService

pdf_service = PDFService()


async def _handle_markdown_to_pdf(arguments: dict[str, Any]) -> Any:
    return await pdf_service.convert(
        require(arguments, "markdown_path"),
        arguments.get("output_path"),
        arguments.get("css_path")
    )


def build_tool_definitions() -> list[ToolDefinition]:
    """PDF 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="markdown_to_pdf",
            description="마크다운 파일을 PDF로 변환합니다.",
            schema=schema(
                {
                    "markdown_path": {"type": "string", "description": "입력 마크다운 경로"},
                    "output_path": {"type": "string", "description": "출력 PDF 경로 (선택)"},
                    "css_path": {"type": "string", "description": "CSS 파일 경로 (선택)"}
                },
                ["markdown_path"]
            ),
            handler=_handle_markdown_to_pdf
        )
    ]


def create_server() -> BaseMCPServer:
    """PDF 서버를 생성합니다."""
    return BaseMCPServer("pdf-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

