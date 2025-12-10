"""Fly.io MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.flyio_tool import FlyioService

flyio_service = FlyioService()


async def _handle_flyio_list_apps(_: dict[str, Any]) -> Any:
    return await flyio_service.list_apps()


async def _handle_flyio_get_status(arguments: dict[str, Any]) -> Any:
    return await flyio_service.get_status(require(arguments, "app_name"))


async def _handle_flyio_get_logs(arguments: dict[str, Any]) -> Any:
    return await flyio_service.get_logs(
        require(arguments, "app_name"),
        arguments.get("lines", 50)
    )


def build_tool_definitions() -> list[ToolDefinition]:
    """Fly.io 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="flyio_list_apps",
            description="Fly.io 앱 목록을 조회합니다.",
            schema=schema({}),
            handler=_handle_flyio_list_apps
        ),
        ToolDefinition(
            name="flyio_get_app_status",
            description="Fly.io 앱 상태를 조회합니다.",
            schema=schema(
                {
                    "app_name": {"type": "string", "description": "앱 이름"}
                },
                ["app_name"]
            ),
            handler=_handle_flyio_get_status
        ),
        ToolDefinition(
            name="flyio_get_app_logs",
            description="Fly.io 앱 로그를 조회합니다.",
            schema=schema(
                {
                    "app_name": {"type": "string", "description": "앱 이름"},
                    "lines": {"type": "integer", "description": "조회할 로그 라인 수", "default": 50}
                },
                ["app_name"]
            ),
            handler=_handle_flyio_get_logs
        )
    ]


def create_server() -> BaseMCPServer:
    """Fly.io 서버를 생성합니다."""
    return BaseMCPServer("flyio-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

