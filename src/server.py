"""MCP Server main entry point with OOP-friendly architecture."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.tools.aws_tool import AWSService
from src.tools.code_analysis_tool import CodeAnalysisService
from src.tools.db_tool import DatabaseService
from src.tools.document_tool import DocumentService
from src.tools.flyio_tool import FlyioService
from src.tools.official_docs import OfficialDocsService
from src.tools.pdf_tool import PDFService

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]
JSON_INDENT = 2


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """개별 MCP 도구 정의."""

    name: str
    description: str
    schema: Dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    """ToolDefinition을 관리하고 MCP Server에 노출합니다."""

    def __init__(self, definitions: Sequence[ToolDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def list_tools(self) -> List[Tool]:
        return [
            Tool(
                name=definition.name,
                description=definition.description,
                inputSchema=definition.schema
            )
            for definition in self._definitions.values()
        ]

    def get_handler(self, name: str) -> ToolHandler | None:
        definition = self._definitions.get(name)
        return definition.handler if definition else None


document_service = DocumentService()
aws_service = AWSService()
flyio_service = FlyioService()
pdf_service = PDFService()
code_analysis_service = CodeAnalysisService()
db_service = DatabaseService()
official_docs_service = OfficialDocsService()


def _schema(properties: Dict[str, Any], required: Sequence[str] | None = None) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required or [])
    }


def _require(arguments: dict[str, Any], key: str) -> Any:
    if key not in arguments:
        raise ValueError(f"Missing required argument: {key}")
    return arguments[key]


async def _handle_read_document(arguments: dict[str, Any]) -> Any:
    return await document_service.read_document(_require(arguments, "file_path"))


async def _handle_list_workspace_projects(_: dict[str, Any]) -> Any:
    return await document_service.scan_projects()


async def _handle_search_documents(arguments: dict[str, Any]) -> Any:
    return await document_service.search_documents(
        _require(arguments, "query"),
        arguments.get("project_name")
    )


async def _handle_aws_cli_execute(arguments: dict[str, Any]) -> Any:
    service = _require(arguments, "service")
    operation = _require(arguments, "operation")
    additional_args = arguments.get("additional_args") or []
    return await aws_service.execute(service, operation, additional_args)


async def _handle_aws_list_resources(arguments: dict[str, Any]) -> Any:
    return await aws_service.list_resources(
        _require(arguments, "service"),
        arguments.get("resource_type")
    )


async def _handle_aws_get_account_info(_: dict[str, Any]) -> Any:
    return await aws_service.get_account_info()


async def _handle_flyio_list_apps(_: dict[str, Any]) -> Any:
    return await flyio_service.list_apps()


async def _handle_flyio_get_status(arguments: dict[str, Any]) -> Any:
    return await flyio_service.get_status(_require(arguments, "app_name"))


async def _handle_flyio_get_logs(arguments: dict[str, Any]) -> Any:
    return await flyio_service.get_logs(
        _require(arguments, "app_name"),
        arguments.get("lines", 50)
    )


async def _handle_markdown_to_pdf(arguments: dict[str, Any]) -> Any:
    return await pdf_service.convert(
        _require(arguments, "markdown_path"),
        arguments.get("output_path"),
        arguments.get("css_path")
    )


async def _handle_analyze_code_flow(arguments: dict[str, Any]) -> Any:
    return await code_analysis_service.analyze_code_flow(
        _require(arguments, "project_path"),
        arguments.get("entry_point")
    )


async def _handle_find_related_code(arguments: dict[str, Any]) -> Any:
    return await code_analysis_service.find_related_code(
        _require(arguments, "project_path"),
        arguments.get("target_function"),
        arguments.get("target_class"),
        arguments.get("target_import")
    )


async def _handle_code_reusability(arguments: dict[str, Any]) -> Any:
    return await code_analysis_service.get_code_reusability(
        _require(arguments, "project_path"),
        arguments.get("language", "python")
    )


async def _handle_list_databases(arguments: dict[str, Any]) -> Any:
    return await db_service.list_databases(
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


async def _handle_describe_tables(arguments: dict[str, Any]) -> Any:
    return await db_service.describe_tables(
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("database"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


async def _handle_run_query(arguments: dict[str, Any]) -> Any:
    return await db_service.run_query(
        _require(arguments, "query"),
        arguments.get("db_name"),
        arguments.get("connection_string"),
        arguments.get("parameters"),
        arguments.get("limit", 100),
        arguments.get("mode", "read_only"),
        arguments.get("use_dotenv", True),
        arguments.get("use_aws_secrets", False),
        arguments.get("aws_secret_name"),
        arguments.get("use_github_secrets", False),
        arguments.get("github_secret_name"),
        arguments.get("github_repo")
    )


async def _handle_sync_official_docs(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        official_docs_service.sync_docs,
        arguments.get("names"),
        arguments.get("force", False)
    )


async def _handle_list_official_docs(_: dict[str, Any]) -> Any:
    return await asyncio.to_thread(official_docs_service.list_docs)


async def _handle_search_official_docs(arguments: dict[str, Any]) -> Any:
    return await asyncio.to_thread(
        official_docs_service.search_docs,
        _require(arguments, "query"),
        arguments.get("name"),
        arguments.get("limit", 5)
    )


def _build_tool_definitions() -> List[ToolDefinition]:
    return [
        ToolDefinition(
            name="read_document",
            description="워크스페이스의 문서 파일을 읽습니다.",
            schema=_schema(
                {
                    "file_path": {
                        "type": "string",
                        "description": "읽을 문서 파일의 경로 (절대 또는 워크스페이스 상대 경로)"
                    }
                },
                ["file_path"]
            ),
            handler=_handle_read_document
        ),
        ToolDefinition(
            name="list_workspace_projects",
            description="워크스페이스의 프로젝트 목록을 스캔합니다.",
            schema=_schema({}),
            handler=_handle_list_workspace_projects
        ),
        ToolDefinition(
            name="search_documents",
            description="워크스페이스의 문서에서 검색합니다.",
            schema=_schema(
                {
                    "query": {"type": "string", "description": "검색할 키워드"},
                    "project_name": {"type": "string", "description": "특정 프로젝트 내에서만 검색 (선택)"}
                },
                ["query"]
            ),
            handler=_handle_search_documents
        ),
        ToolDefinition(
            name="aws_cli_execute",
            description="AWS CLI 명령을 실행합니다 (jongmun 프로필).",
            schema=_schema(
                {
                    "service": {"type": "string", "description": "AWS 서비스 이름"},
                    "operation": {"type": "string", "description": "작업 이름"},
                    "additional_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추가 인자 목록"
                    }
                },
                ["service", "operation"]
            ),
            handler=_handle_aws_cli_execute
        ),
        ToolDefinition(
            name="aws_list_resources",
            description="AWS 리소스 목록을 조회합니다.",
            schema=_schema(
                {
                    "service": {"type": "string", "description": "AWS 서비스 이름"},
                    "resource_type": {"type": "string", "description": "리소스 타입 (선택)"}
                },
                ["service"]
            ),
            handler=_handle_aws_list_resources
        ),
        ToolDefinition(
            name="aws_get_account_info",
            description="AWS 계정 정보를 조회합니다.",
            schema=_schema({}),
            handler=_handle_aws_get_account_info
        ),
        ToolDefinition(
            name="flyio_list_apps",
            description="Fly.io 앱 목록을 조회합니다.",
            schema=_schema({}),
            handler=_handle_flyio_list_apps
        ),
        ToolDefinition(
            name="flyio_get_app_status",
            description="Fly.io 앱 상태를 조회합니다.",
            schema=_schema(
                {
                    "app_name": {"type": "string", "description": "앱 이름"}
                },
                ["app_name"]
            ),
            handler=_handle_flyio_get_status
        ),
        ToolDefinition(
            name="flyio_get_app_logs",
            description="Fly.io 앱 로그를 조회합니다.",
            schema=_schema(
                {
                    "app_name": {"type": "string", "description": "앱 이름"},
                    "lines": {"type": "integer", "description": "조회할 로그 라인 수", "default": 50}
                },
                ["app_name"]
            ),
            handler=_handle_flyio_get_logs
        ),
        ToolDefinition(
            name="markdown_to_pdf",
            description="마크다운 파일을 PDF로 변환합니다.",
            schema=_schema(
                {
                    "markdown_path": {"type": "string", "description": "입력 마크다운 경로"},
                    "output_path": {"type": "string", "description": "출력 PDF 경로 (선택)"},
                    "css_path": {"type": "string", "description": "CSS 파일 경로 (선택)"}
                },
                ["markdown_path"]
            ),
            handler=_handle_markdown_to_pdf
        ),
        ToolDefinition(
            name="analyze_code_flow",
            description="프로젝트의 코드 흐름을 분석합니다.",
            schema=_schema(
                {
                    "project_path": {"type": "string", "description": "분석할 프로젝트 경로"},
                    "entry_point": {"type": "string", "description": "진입점 파일 (선택)"}
                },
                ["project_path"]
            ),
            handler=_handle_analyze_code_flow
        ),
        ToolDefinition(
            name="find_related_code",
            description="연관된 코드를 찾습니다.",
            schema=_schema(
                {
                    "project_path": {"type": "string", "description": "검색할 프로젝트 경로"},
                    "target_function": {"type": "string", "description": "함수 이름 (선택)"},
                    "target_class": {"type": "string", "description": "클래스 이름 (선택)"},
                    "target_import": {"type": "string", "description": "import 이름 (선택)"}
                },
                ["project_path"]
            ),
            handler=_handle_find_related_code
        ),
        ToolDefinition(
            name="get_code_reusability",
            description="코드 재사용성을 분석합니다.",
            schema=_schema(
                {
                    "project_path": {"type": "string", "description": "분석할 프로젝트 경로"},
                    "language": {"type": "string", "description": "언어 (기본값 python)", "default": "python"}
                },
                ["project_path"]
            ),
            handler=_handle_code_reusability
        ),
        ToolDefinition(
            name="list_databases",
            description="데이터베이스 목록을 조회합니다.",
            schema=_schema(
                {
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                None
            ),
            handler=_handle_list_databases
        ),
        ToolDefinition(
            name="describe_tables",
            description="테이블 스키마를 조회합니다.",
            schema=_schema(
                {
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "database": {"type": "string", "description": "특정 데이터베이스 이름 (선택)"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                None
            ),
            handler=_handle_describe_tables
        ),
        ToolDefinition(
            name="run_query",
            description="SQL 쿼리를 실행합니다 (기본 read-only, 필요시 read-write 모드 지정).",
            schema=_schema(
                {
                    "query": {"type": "string", "description": "실행할 SQL 쿼리"},
                    "db_name": {"type": "string", "description": "DB 이름 (선택)"},
                    "connection_string": {"type": "string", "description": "직접 연결 문자열 (선택)"},
                    "parameters": {"type": "object", "description": "쿼리 파라미터 (선택)"},
                    "limit": {"type": "integer", "description": "결과 행 수 제한 (기본값 100)", "default": 100},
                    "mode": {"type": "string", "description": "실행 모드: read_only 또는 read_write (기본값 read_only)", "default": "read_only"},
                    "use_dotenv": {"type": "boolean", "description": ".env 파일 사용 (기본값 true)", "default": True},
                    "use_aws_secrets": {"type": "boolean", "description": "AWS Secrets Manager 사용", "default": False},
                    "aws_secret_name": {"type": "string", "description": "AWS 시크릿 이름 (선택)"},
                    "use_github_secrets": {"type": "boolean", "description": "GitHub Secrets 사용", "default": False},
                    "github_secret_name": {"type": "string", "description": "GitHub 시크릿 이름 (선택)"},
                    "github_repo": {"type": "string", "description": "GitHub 저장소 (선택)"}
                },
                ["query"]
            ),
            handler=_handle_run_query
        ),
        ToolDefinition(
            name="sync_official_docs",
            description="공식 문서를 로컬에 미러링합니다.",
            schema=_schema(
                {
                    "names": {"type": "array", "items": {"type": "string"}, "description": "동기화할 문서 이름 목록 (선택)"},
                    "force": {"type": "boolean", "description": "향후 확장용 플래그", "default": False}
                },
                None
            ),
            handler=_handle_sync_official_docs
        ),
        ToolDefinition(
            name="list_official_docs",
            description="미러링된 공식 문서 목록을 조회합니다.",
            schema=_schema({}, None),
            handler=_handle_list_official_docs
        ),
        ToolDefinition(
            name="search_official_docs",
            description="미러링된 공식 문서에서 키워드를 검색합니다.",
            schema=_schema(
                {
                    "query": {"type": "string", "description": "검색할 키워드"},
                    "name": {"type": "string", "description": "특정 문서 이름 (선택)"},
                    "limit": {"type": "integer", "description": "결과 수 제한 (기본값 5)", "default": 5}
                },
                ["query"]
            ),
            handler=_handle_search_official_docs
        )
    ]


tool_registry = ToolRegistry(_build_tool_definitions())
app = Server("gary-mcp-server")


def _to_text_content(payload: Any) -> TextContent:
    return TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=JSON_INDENT))


@app.list_tools()
async def list_tools() -> List[Tool]:
    return tool_registry.list_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    handler = tool_registry.get_handler(name)
    if handler is None:
        return [_to_text_content({"error": f"Unknown tool: {name}"})]

    try:
        result = await handler(arguments)
        return [_to_text_content(result)]
    except ValueError as exc:
        return [_to_text_content({"error": str(exc)})]
    except Exception as exc:  # pragma: no cover - 최상위 보호
        return [_to_text_content({"error": str(exc)})]


async def main() -> None:
    """MCP 서버를 실행합니다."""
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
