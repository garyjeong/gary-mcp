"""Code analysis service for understanding code flow and finding related code."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional

from src.utils.file_utils import get_file_extension, list_files_async, read_file_async


class CodeAnalysisService:
    """코드 흐름과 재사용성을 분석하는 서비스."""

    SUPPORTED_EXTENSIONS = [".py", ".go", ".ts", ".tsx", ".js", ".jsx"]

    async def analyze_code_flow(self, project_path: str, entry_point: Optional[str] = None) -> Dict[str, Any]:
        root = Path(project_path)
        result: Dict[str, Any] = {
            "project_structure": {},
            "dependencies": defaultdict(list),
            "entry_points": []
        }

        if not root.exists():
            return result

        for item in root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                result["project_structure"][item.name] = {
                    "type": "directory",
                    "path": str(item)
                }

        code_files = await list_files_async(project_path, extensions=self.SUPPORTED_EXTENSIONS, recursive=True)
        for file_path in code_files:
            if get_file_extension(file_path) != ".py":
                continue

            analysis = await self._analyze_python_code(file_path)
            if not analysis["success"]:
                continue

            for imp in analysis["imports"]:
                result["dependencies"][file_path].append(imp)

            for func in analysis["functions"]:
                if func["name"] in {"main", "__main__"}:
                    result["entry_points"].append({
                        "file": file_path,
                        "function": func["name"],
                        "line": func["line"]
                    })

        return result

    async def find_related_code(
        self,
        project_path: str,
        target_function: Optional[str] = None,
        target_class: Optional[str] = None,
        target_import: Optional[str] = None
    ) -> Dict[str, Any]:
        code_files = await list_files_async(project_path, extensions=self.SUPPORTED_EXTENSIONS, recursive=True)
        matches: List[Dict[str, Any]] = []

        for file_path in code_files:
            if get_file_extension(file_path) != ".py":
                continue

            analysis = await self._analyze_python_code(file_path)
            if not analysis["success"]:
                continue

            matches.extend(self._collect_matches(file_path, analysis, target_function, target_class, target_import))

        return {"matches": matches, "total_files_scanned": len(code_files)}

    async def get_code_reusability(self, project_path: str, language: str = "python") -> Dict[str, Any]:
        if language.lower() != "python":
            return {"common_functions": [], "common_classes": [], "reusable_modules": []}

        code_files = await list_files_async(project_path, extensions=[".py"], recursive=True)
        function_counts = defaultdict(int)
        class_counts = defaultdict(int)

        for file_path in code_files:
            analysis = await self._analyze_python_code(file_path)
            if not analysis["success"]:
                continue
            for func in analysis["functions"]:
                function_counts[func["name"]] += 1
            for cls in analysis["classes"]:
                class_counts[cls["name"]] += 1

        return {
            "common_functions": self._format_usage_summary(function_counts),
            "common_classes": self._format_usage_summary(class_counts),
            "reusable_modules": []
        }

    async def _analyze_python_code(self, file_path: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": False,
            "imports": [],
            "functions": [],
            "classes": [],
            "error": None
        }

        try:
            content = await read_file_async(file_path)
            tree = ast.parse(content, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    result["imports"].append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    result["functions"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "decorators": [self._extract_decorator_name(d) for d in node.decorator_list]
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    result["classes"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "bases": [self._extract_base_name(base) for base in node.bases],
                            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        }
                    )

            result["success"] = True
        except Exception as exc:  # pragma: no cover - AST 파싱 오류 보호
            result["error"] = str(exc)
        return result

    @staticmethod
    def _collect_matches(
        file_path: str,
        analysis: Dict[str, Any],
        target_function: Optional[str],
        target_class: Optional[str],
        target_import: Optional[str]
    ) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        if target_function:
            lowered = target_function.lower()
            for func in analysis["functions"]:
                if lowered in func["name"].lower():
                    matches.append({"type": "function", "name": func["name"], "line": func["line"], "file": file_path})

        if target_class:
            lowered = target_class.lower()
            for cls in analysis["classes"]:
                if lowered in cls["name"].lower():
                    matches.append({"type": "class", "name": cls["name"], "line": cls["line"], "file": file_path})

        if target_import:
            lowered = target_import.lower()
            for imp in analysis["imports"]:
                if lowered in imp.lower():
                    matches.append({"type": "import", "name": imp, "file": file_path})
        return matches

    @staticmethod
    def _extract_decorator_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "unknown"

    @staticmethod
    def _extract_base_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "unknown"

    @staticmethod
    def _format_usage_summary(counter: DefaultDict[str, int]) -> List[Dict[str, Any]]:
        return [
            {"name": name, "usage_count": count}
            for name, count in counter.items()
            if count > 1
        ]
