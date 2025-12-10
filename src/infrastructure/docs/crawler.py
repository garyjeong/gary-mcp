"""간단한 문서 크롤러 유틸."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import requests


def fetch_http(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> str:
    resp = requests.get(url, headers=headers or {}, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text


def fetch_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


__all__ = ["fetch_http", "fetch_file"]

