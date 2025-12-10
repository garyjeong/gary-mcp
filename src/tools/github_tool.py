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
        # GitHub CLI는 --sort 플래그를 지원하지 않으므로 limit을 늘려서 받고 Python에서 정렬
        fetch_limit = limit * 2 if limit > 10 else 50  # 정렬을 위해 더 많이 가져옴
        
        args = [
            "repo",
            "list",
            "--limit",
            str(fetch_limit),
            "--json",
            "nameWithOwner,description,visibility,updatedAt",
        ]
        if owner:
            args.extend(["--owner", owner])
        if visibility:
            args.extend(["--visibility", visibility])
        
        result = await self.execute(args)
        
        # Python에서 정렬
        if isinstance(result.get("output"), list):
            repos = result["output"]
            reverse = sort in ("updated", "created", "pushed")
            if sort == "updated":
                repos.sort(key=lambda x: x.get("updatedAt", ""), reverse=reverse)
            elif sort == "name":
                repos.sort(key=lambda x: x.get("nameWithOwner", ""), reverse=reverse)
            # limit 적용
            result["output"] = repos[:limit]
        
        return result

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
