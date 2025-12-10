"""공통 MCP 서버 베이스 클래스."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]
JSON_INDENT = 2


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """개별 MCP 도구 정의."""

    name: str
    description: str
    schema: Dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    """ToolDefinition을 관리하고 MCP Server에 노출합니다."""

    def __init__(self, definitions: Sequence[ToolDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def list_tools(self) -> List[Tool]:
        return [
            Tool(
                name=definition.name,
                description=definition.description,
                inputSchema=definition.schema
            )
            for definition in self._definitions.values()
        ]

    def get_handler(self, name: str) -> ToolHandler | None:
        definition = self._definitions.get(name)
        return definition.handler if definition else None


def schema(properties: Dict[str, Any], required: Sequence[str] | None = None) -> Dict[str, Any]:
    """JSON 스키마 생성 헬퍼."""
    return {
        "type": "object",
        "properties": properties,
        "required": list(required or [])
    }


def require(arguments: dict[str, Any], key: str) -> Any:
    """필수 인자 검증."""
    if key not in arguments:
        raise ValueError(f"Missing required argument: {key}")
    return arguments[key]


def to_text_content(payload: Any) -> TextContent:
    """결과를 TextContent로 변환."""
    return TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=JSON_INDENT))


class BaseMCPServer:
    """공통 MCP 서버 베이스 클래스."""

    def __init__(self, server_name: str, tool_definitions: Sequence[ToolDefinition]) -> None:
        self.server_name = server_name
        self.tool_registry = ToolRegistry(tool_definitions)
        self.app = Server(server_name)

        # MCP 핸들러 등록
        self.app.list_tools()(self.list_tools)
        self.app.call_tool()(self.call_tool)

    async def list_tools(self) -> List[Tool]:
        """사용 가능한 도구 목록을 반환합니다."""
        return self.tool_registry.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
        """도구를 호출합니다."""
        handler = self.tool_registry.get_handler(name)
        if handler is None:
            return [to_text_content({"error": f"Unknown tool: {name}"})]

        try:
            result = await handler(arguments)
            return [to_text_content(result)]
        except ValueError as exc:
            return [to_text_content({"error": str(exc)})]
        except Exception as exc:  # pragma: no cover
            return [to_text_content({"error": str(exc)})]

    async def run(self) -> None:
        """MCP 서버를 실행합니다."""
        async with stdio_server() as streams:
            await self.app.run(streams[0], streams[1], self.app.create_initialization_options())


async def main(server: BaseMCPServer) -> None:
    """서버 실행 진입점."""
    await server.run()


