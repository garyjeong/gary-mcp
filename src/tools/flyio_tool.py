"""Fly.io service for managing Fly.io applications."""

from __future__ import annotations

from typing import Dict, Optional, Sequence

from src.tools.cli_executor import CLIService
from src.utils.env_loader import load_shell_env


class FlyioService:
    """Fly.io CLI 호출을 담당하는 서비스."""

    def __init__(self) -> None:
        extra_env = load_shell_env(prefixes=("FLY_",), keys=("FLY_API_TOKEN", "FLY_ACCESS_TOKEN"))
        self.cli = CLIService("flyctl", json_flag=["--json"], extra_env=extra_env)

    async def list_apps(self) -> Dict[str, object]:
        return await self._execute("apps", ["list"])

    async def get_status(self, app_name: str) -> Dict[str, object]:
        return await self._execute("status", ["-a", app_name])

    async def get_info(self, app_name: str) -> Dict[str, object]:
        return await self._execute("apps", ["show", app_name])

    async def get_logs(self, app_name: str, lines: int = 50) -> Dict[str, object]:
        return await self._execute("logs", ["-a", app_name, "-n", str(lines)])

    async def list_machines(self, app_name: str) -> Dict[str, object]:
        return await self._execute("machines", ["list", "-a", app_name])

    async def _execute(self, command: str, args: Optional[Sequence[str]] = None) -> Dict[str, object]:
        args = args or []
        result = await self.cli.run(command, *args)
        return result.to_dict()
