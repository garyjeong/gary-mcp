"""Shell 환경 변수 로더."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, Sequence

_EXPORT_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _should_include(name: str, prefixes: Sequence[str] | None, keys: Sequence[str] | None) -> bool:
    if keys and name in keys:
        return True
    if prefixes:
        return any(name.startswith(prefix) for prefix in prefixes)
    return not prefixes and not keys


def load_shell_env(
    *,
    prefixes: Sequence[str] | None = None,
    keys: Sequence[str] | None = None,
    rc_path: str | Path | None = None
) -> Dict[str, str]:
    """zshrc 등 shell rc 파일에서 환경 변수를 읽습니다."""
    resolved_path = Path(rc_path or os.getenv("SHELL_RC_PATH", Path.home() / ".zshrc")).expanduser()
    collected: Dict[str, str] = {}

    if resolved_path.exists():
        for line in resolved_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _EXPORT_PATTERN.match(stripped)
            if not match:
                continue
            name, raw_value = match.groups()
            if not _should_include(name, prefixes, keys):
                continue
            collected[name] = _strip_quotes(raw_value)

    for name, value in os.environ.items():
        if _should_include(name, prefixes, keys):
            collected[name] = value

    return collected
