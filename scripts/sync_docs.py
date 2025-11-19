#!/usr/bin/env python3
"""CLI helper to synchronize official documentation mirrors."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from src.tools.official_docs import OfficialDocsService


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync official documentation cache")
    parser.add_argument("names", nargs="*", help="Specific documentation names to sync (default: all)")
    parser.add_argument("--force", action="store_true", help="Force re-sync (reserved for future use)")
    args = parser.parse_args()

    service = OfficialDocsService(base_dir=Path(__file__).resolve().parents[1])
    result = service.sync_docs(names=args.names or None, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
