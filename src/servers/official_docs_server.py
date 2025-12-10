"""공식 문서 MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.docs_service import DocsService

docs_service = DocsService()


async def _handle_sync_official_docs(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        docs_service.sync_official_docs,
        arguments.get("names"),
        arguments.get("force", False)
    )


async def _handle_list_official_docs(_: dict[str, Any]) -> Any:
    return await asyncio.to_thread(docs_service.list_official_docs)


async def _handle_search_official_docs(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        docs_service.search_docs,
        require(arguments, "query"),
        arguments.get("name"),
        arguments.get("limit", 5),
        arguments.get("structured", False),
    )


async def _handle_resolve_library_id(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(docs_service.resolve_library_id, require(arguments, "name"))


async def _handle_get_library_docs(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        docs_service.get_library_docs,
        require(arguments, "library_id"),
        arguments.get("mode", "info"),
        arguments.get("topic"),
        arguments.get("limit", 5),
    )


async def _handle_list_libraries(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        docs_service.list_libraries,
        arguments.get("category"),
        arguments.get("available_only", False),
    )


def build_tool_definitions() -> list[ToolDefinition]:
    """공식 문서 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="sync_official_docs",
            description="공식 문서를 로컬에 미러링합니다.",
            schema=schema(
                {
                    "names": {"type": "array", "items": {"type": "string"}, "description": "동기화할 문서 이름 목록 (선택)"},
                    "force": {"type": "boolean", "description": "향후 확장용 플래그", "default": False}
                },
                None
            ),
            handler=_handle_sync_official_docs
        ),
        ToolDefinition(
            name="list_official_docs",
            description="미러링된 공식 문서 목록을 조회합니다.",
            schema=schema({}, None),
            handler=_handle_list_official_docs
        ),
        ToolDefinition(
            name="search_official_docs",
            description="미러링된 공식 문서에서 키워드를 검색합니다.",
            schema=schema(
                {
                    "query": {"type": "string", "description": "검색할 키워드"},
                    "name": {"type": "string", "description": "특정 문서 이름 (선택)"},
                    "limit": {"type": "integer", "description": "결과 수 제한 (기본값 5)", "default": 5},
                    "structured": {"type": "boolean", "description": "구조화 파서 기반 검색 사용", "default": False},
                },
                ["query"]
            ),
            handler=_handle_search_official_docs
        ),
        ToolDefinition(
            name="resolve_library_id",
            description="라이브러리 이름으로 ID와 메타데이터를 조회합니다.",
            schema=schema(
                {"name": {"type": "string", "description": "라이브러리 이름 (예: react, next.js)"}},
                ["name"]
            ),
            handler=_handle_resolve_library_id
        ),
        ToolDefinition(
            name="get_library_docs",
            description="라이브러리 문서를 조회합니다 (Context7 스타일).",
            schema=schema(
                {
                    "library_id": {"type": "string", "description": "라이브러리 ID (예: /libraries/react)"},
                    "mode": {"type": "string", "description": "info|code (기본 info)", "default": "info"},
                    "topic": {"type": "string", "description": "특정 주제 필터 (선택)"},
                    "limit": {"type": "integer", "description": "검색 결과 제한 (기본 5)", "default": 5},
                },
                ["library_id"]
            ),
            handler=_handle_get_library_docs
        ),
        ToolDefinition(
            name="list_libraries",
            description="지원 라이브러리 목록을 반환합니다.",
            schema=schema(
                {
                    "category": {"type": "string", "description": "필터: framework|language|orm|database|cloud"},
                    "available_only": {"type": "boolean", "description": "동기화 가능한 항목만", "default": False},
                },
                None
            ),
            handler=_handle_list_libraries
        )
    ]


def create_server() -> BaseMCPServer:
    """공식 문서 서버를 생성합니다."""
    return BaseMCPServer("official-docs-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

