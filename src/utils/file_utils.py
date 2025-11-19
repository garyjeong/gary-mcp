"""File utility functions for async file operations."""

import asyncio
from pathlib import Path
from typing import Iterable, List, Optional


async def read_file_async(file_path: str) -> str:
    """비동기적으로 파일을 읽습니다."""

    def _read() -> str:
        with open(file_path, "r", encoding="utf-8") as file_handle:
            return file_handle.read()

    return await asyncio.to_thread(_read)


async def file_exists_async(file_path: str) -> bool:
    """비동기적으로 파일 존재 여부를 확인합니다."""
    path = Path(file_path)
    return await asyncio.to_thread(path.exists)


async def list_files_async(
    directory: str,
    extensions: Optional[Iterable[str]] = None,
    recursive: bool = True
) -> List[str]:
    """비동기적으로 디렉토리의 파일 목록을 가져옵니다."""

    def _collect_files() -> List[str]:
        files: List[str] = []
        path = Path(directory)

        if not path.exists():
            return files

        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file():
                if extensions is None or file_path.suffix in extensions:
                    files.append(str(file_path))
        return files

    return await asyncio.to_thread(_collect_files)


def get_file_extension(file_path: str) -> str:
    """파일 확장자를 반환합니다."""
    return Path(file_path).suffix.lower()


def is_markdown_file(file_path: str) -> bool:
    """마크다운 파일인지 확인합니다."""
    md_extensions = {".md", ".markdown", ".mdown", ".mkd"}
    return get_file_extension(file_path) in md_extensions


def is_code_file(file_path: str) -> bool:
    """코드 파일인지 확인합니다."""
    code_extensions = {
        ".py", ".go", ".ts", ".tsx", ".js", ".jsx",
        ".java", ".cpp", ".c", ".h", ".rs", ".rb"
    }
    return get_file_extension(file_path) in code_extensions
