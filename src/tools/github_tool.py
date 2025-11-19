"""GitHub CLI integration for MCP server."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.tools.cli_executor import CLIService
from src.utils.env_loader import load_shell_env


class GitHubService:
    """Service to interact with GitHub CLI."""

    def __init__(self) -> None:
        extra_env = load_shell_env(
            prefixes=("GH_", "GITHUB_"),
            keys=("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_HOST", "GH_HOST")
        )
        self.cli = CLIService("gh", extra_env=extra_env)

    async def execute(self, args: List[str]) -> Dict[str, Any]:
        result = await self.cli.run(*args)
        return result.to_dict()

    async def list_repos(
        self,
        owner: Optional[str] = None,
        visibility: Optional[str] = None,
        limit: int = 20,
        sort: str = "updated"
    ) -> Dict[str, Any]:
        args = [
            "repo",
            "list",
            "--limit",
            str(limit),
            "--json",
            "nameWithOwner,description,visibility,updatedAt" ,
            "--sort",
            sort,
        ]
        if owner:
            args.extend(["--owner", owner])
        if visibility:
            args.extend(["--visibility", visibility])
        return await self.execute(args)

    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 20
    ) -> Dict[str, Any]:
        args = [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,author,updatedAt,headRefName,baseRefName,mergeable"
        ]
        return await self.execute(args)

    async def list_issues(
        self,
        repo: str,
        state: str = "open",
        limit: int = 20
    ) -> Dict[str, Any]:
        args = [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,author,updatedAt,labels"
        ]
        return await self.execute(args)
