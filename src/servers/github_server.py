"""GitHub CLI MCP 서버."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.servers.base_server import BaseMCPServer, ToolDefinition, require, schema
from src.tools.github_tool import GitHubService

github_service = GitHubService()


async def _handle_github_cli_execute(arguments: dict[str, Any]) -> Any:
    command = require(arguments, "command")
    args_list = arguments.get("args") or []
    if not isinstance(args_list, list):
        raise ValueError("args must be an array of strings")
    return await github_service.execute([command, *args_list])


async def _handle_github_list_repos(arguments: dict[str, Any]) -> Any:
    return await github_service.list_repos(
        owner=arguments.get("owner"),
        visibility=arguments.get("visibility"),
        limit=arguments.get("limit", 20),
        sort=arguments.get("sort", "updated")
    )


async def _handle_github_list_prs(arguments: dict[str, Any]) -> Any:
    return await github_service.list_pull_requests(
        repo=require(arguments, "repo"),
        state=arguments.get("state", "open"),
        limit=arguments.get("limit", 20)
    )


async def _handle_github_list_issues(arguments: dict[str, Any]) -> Any:
    return await github_service.list_issues(
        repo=require(arguments, "repo"),
        state=arguments.get("state", "open"),
        limit=arguments.get("limit", 20)
    )


def build_tool_definitions() -> list[ToolDefinition]:
    """GitHub 도구 정의를 생성합니다."""
    return [
        ToolDefinition(
            name="github_cli_execute",
            description="GitHub CLI 명령을 실행합니다.",
            schema=schema(
                {
                    "command": {"type": "string", "description": "실행할 gh 하위 커맨드 (예: 'repo', 'issue', 'pr')"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "추가 인자 목록 (선택)"}
                },
                ["command"]
            ),
            handler=_handle_github_cli_execute
        ),
        ToolDefinition(
            name="github_list_repos",
            description="GitHub CLI로 레포지토리 목록을 조회합니다.",
            schema=schema(
                {
                    "owner": {"type": "string", "description": "특정 사용자/조직 (선택)"},
                    "visibility": {"type": "string", "description": "public, private, internal 중 하나 (선택)"},
                    "limit": {"type": "integer", "description": "조회할 레포 수 (기본값 20)", "default": 20},
                    "sort": {"type": "string", "description": "정렬 기준 (기본값 updated)", "default": "updated"}
                },
                None
            ),
            handler=_handle_github_list_repos
        ),
        ToolDefinition(
            name="github_list_pull_requests",
            description="지정한 레포지토리의 PR을 조회합니다.",
            schema=schema(
                {
                    "repo": {"type": "string", "description": "레포지토리 (예: owner/repo)"},
                    "state": {"type": "string", "description": "open, closed, all 중 하나", "default": "open"},
                    "limit": {"type": "integer", "description": "조회할 PR 수 (기본값 20)", "default": 20}
                },
                ["repo"]
            ),
            handler=_handle_github_list_prs
        ),
        ToolDefinition(
            name="github_list_issues",
            description="지정한 레포지토리의 이슈를 조회합니다.",
            schema=schema(
                {
                    "repo": {"type": "string", "description": "레포지토리 (예: owner/repo)"},
                    "state": {"type": "string", "description": "open, closed, all 중 하나", "default": "open"},
                    "limit": {"type": "integer", "description": "조회할 이슈 수 (기본값 20)", "default": 20}
                },
                ["repo"]
            ),
            handler=_handle_github_list_issues
        )
    ]


def create_server() -> BaseMCPServer:
    """GitHub 서버를 생성합니다."""
    return BaseMCPServer("github-mcp", build_tool_definitions())


async def main() -> None:
    """서버 실행."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

