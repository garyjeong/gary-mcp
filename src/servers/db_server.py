"""데이터베이스 MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.db_tool import DatabaseService

db_service = DatabaseService()


async def _handle_list_databases(arguments: dict[str, Any]) -> Any:
    return await db_service.list_databases(
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


async def _handle_describe_tables(arguments: dict[str, Any]) -> Any:
    return await db_service.describe_tables(
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("database"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


async def _handle_run_query(arguments: dict[str, Any]) -> Any:
    return await db_service.run_query(
        require(arguments, "query"),
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("parameters"),
        arguments.get("limit", 100),
        arguments.get("mode", "read_only"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


def build_tool_definitions() -> list[ToolDefinition]:
    """데이터베이스 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="list_databases",
            description="데이터베이스 목록을 조회합니다.",
            schema=schema(
                {
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                None
            ),
            handler=_handle_list_databases
        ),
        ToolDefinition(
            name="describe_tables",
            description="테이블 스키마를 조회합니다.",
            schema=schema(
                {
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "database": {"type": "string", "description": "특정 데이터베이스 이름 (선택)"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                None
            ),
            handler=_handle_describe_tables
        ),
        ToolDefinition(
            name="run_query",
            description="SQL 쿼리를 실행합니다 (기본 read-only, 필요시 read-write 모드 지정).",
            schema=schema(
                {
                    "query": {"type": "string", "description": "실행할 SQL 쿼리"},
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "parameters": {"type": "object", "description": "쿼리 파라미터 (선택)"},
                    "limit": {"type": "integer", "description": "결과 행 수 제한 (기본값 100)", "default": 100},
                    "mode": {"type": "string", "description": "실행 모드: read_only 또는 read_write (기본값 read_only)", "default": "read_only"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                ["query"]
            ),
            handler=_handle_run_query
        )
    ]


def create_server() -> BaseMCPServer:
    """데이터베이스 서버를 생성합니다."""
    return BaseMCPServer("db-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

