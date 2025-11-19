"""공통 CLI 실행 유틸리티."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
import os
from typing import Any, Iterable, List, Optional, Sequence


@dataclass(slots=True)
class CLIResult:
    """CLI 실행 결과."""

    success: bool
    output: Any = ""
    error: Optional[str] = None
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        """MCP 응답에 활용하기 위한 dict 변환."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "command": self.command
        }


class CLIService:
    """CLI 실행을 표준화하는 기본 서비스."""

    def __init__(
        self,
        binary: str,
        base_args: Optional[Sequence[str]] = None,
        json_flag: Optional[Sequence[str]] = None,
        extra_env: Optional[dict[str, str]] = None
    ) -> None:
        self.binary = binary
        self.base_args = list(base_args or [])
        self.json_flag = list(json_flag) if json_flag else None
        self.extra_env = extra_env or {}

    async def run(self, *additional_args: str) -> CLIResult:
        command = [self.binary, *self.base_args, *additional_args]
        self._ensure_json_output(command)

        env = os.environ.copy()
        env.update(self.extra_env)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await process.communicate()

        result = CLIResult(success=process.returncode == 0, command=" ".join(command))

        if result.success:
            decoded = stdout.decode("utf-8").strip()
            result.output = self._parse_output(decoded)
        else:
            result.error = stderr.decode("utf-8").strip() or "Unknown error"

        return result

    def _ensure_json_output(self, command: List[str]) -> None:
        if not self.json_flag:
            return
        # json_flag 전체가 포함되어 있는지 확인
        if all(flag in command for flag in self.json_flag):
            return
        command.extend(self.json_flag)

    @staticmethod
    def _parse_output(payload: str) -> Any:
        try:
            return json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            return payload
