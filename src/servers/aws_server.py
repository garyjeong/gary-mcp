"""AWS CLI MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.aws_tool import AWSService

aws_service = AWSService()


async def _handle_aws_cli_execute(arguments: dict[str, Any]) -> Any:
    service = require(arguments, "service")
    operation = require(arguments, "operation")
    additional_args = arguments.get("additional_args") or []
    return await aws_service.execute(service, operation, additional_args)


async def _handle_aws_list_resources(arguments: dict[str, Any]) -> Any:
    return await aws_service.list_resources(
        require(arguments, "service"),
        arguments.get("resource_type")
    )


async def _handle_aws_get_account_info(_: dict[str, Any]) -> Any:
    return await aws_service.get_account_info()


def build_tool_definitions() -> list[ToolDefinition]:
    """AWS 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="aws_cli_execute",
            description="AWS CLI 명령을 실행합니다 (jongmun 프로필).",
            schema=schema(
                {
                    "service": {"type": "string", "description": "AWS 서비스 이름"},
                    "operation": {"type": "string", "description": "작업 이름"},
                    "additional_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추가 인자 목록"
                    }
                },
                ["service", "operation"]
            ),
            handler=_handle_aws_cli_execute
        ),
        ToolDefinition(
            name="aws_list_resources",
            description="AWS 리소스 목록을 조회합니다.",
            schema=schema(
                {
                    "service": {"type": "string", "description": "AWS 서비스 이름"},
                    "resource_type": {"type": "string", "description": "리소스 타입 (선택)"}
                },
                ["service"]
            ),
            handler=_handle_aws_list_resources
        ),
        ToolDefinition(
            name="aws_get_account_info",
            description="AWS 계정 정보를 조회합니다.",
            schema=schema({}),
            handler=_handle_aws_get_account_info
        )
    ]


def create_server() -> BaseMCPServer:
    """AWS 서버를 생성합니다."""
    return BaseMCPServer("aws-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

