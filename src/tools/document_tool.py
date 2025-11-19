"""Document reference service for workspace scanning and reading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.file_utils import list_files_async, read_file_async


class DocumentService:
    """워크스페이스 문서를 인덱싱하고 조회하는 서비스."""

    def __init__(self, workspace_path: Optional[str | Path] = None, max_documents: int = 10) -> None:
        resolved_path = workspace_path or os.getenv("WORKSPACE_PATH", "/workspace")
        self.workspace_path = Path(resolved_path)
        self.max_documents = max_documents

    async def scan_projects(self) -> List[Dict[str, Any]]:
        """워크스페이스의 프로젝트 목록을 스캔합니다."""
        projects: List[Dict[str, Any]] = []
        if not self.workspace_path.exists():
            return projects

        for item in self.workspace_path.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            project_info: Dict[str, Any] = {
                "name": item.name,
                "path": str(item),
                "has_readme": False,
                "document_files": []
            }

            self._attach_readme_files(item, project_info)
            md_files = await list_files_async(
                str(item),
                extensions=[".md", ".markdown"],
                recursive=True
            )
            project_info["document_files"].extend(md_files[: self.max_documents])
            projects.append(project_info)

        return projects

    async def read_document(self, file_path: str) -> Dict[str, Any]:
        """문서 파일을 읽습니다."""
        absolute_path = self._resolve_path(file_path)
        result: Dict[str, Any] = {
            "success": False,
            "content": "",
            "error": None,
            "file_path": str(absolute_path)
        }

        if not absolute_path.exists():
            result["error"] = f"File not found: {absolute_path}"
            return result

        try:
            result["content"] = await read_file_async(str(absolute_path))
            result["success"] = True
        except Exception as exc:  # pragma: no cover - defensive logging
            result["error"] = str(exc)
        return result

    async def search_documents(self, query: str, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """문서에서 검색합니다."""
        search_root = self._resolve_project_path(project_name)
        md_files = await list_files_async(
            str(search_root),
            extensions=[".md", ".markdown"],
            recursive=True
        )

        lowered_query = query.lower()
        results: List[Dict[str, Any]] = []
        for file_path in md_files:
            try:
                content = await read_file_async(file_path)
            except Exception:
                continue

            if lowered_query not in content.lower():
                continue

            preview = content[:200] + "..." if len(content) > 200 else content
            results.append(
                {
                    "file_path": file_path,
                    "matches": content.lower().count(lowered_query),
                    "preview": preview
                }
            )
        return results

    def _resolve_project_path(self, project_name: Optional[str]) -> Path:
        if not project_name:
            return self.workspace_path
        return (self.workspace_path / project_name).resolve()

    def _resolve_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        return (self.workspace_path / file_path).resolve()

    def _attach_readme_files(self, project_path: Path, project_info: Dict[str, Any]) -> None:
        readme_candidates = [
            "README.md",
            "README.txt",
            "readme.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "LICENSE.md"
        ]
        for candidate in readme_candidates:
            readme_path = project_path / candidate
            if readme_path.exists():
                project_info["has_readme"] = True
                project_info["document_files"].append(str(readme_path))
                break
