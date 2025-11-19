"""Database access tool for MCP server."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.infrastructure.db.connection_manager import (
    ConnectionMode,
    DatabaseConnectionManager
)


class DatabaseService:
    """데이터베이스 접근 서비스."""
    
    def __init__(self) -> None:
        self._managers: Dict[str, DatabaseConnectionManager] = {}
    
    async def list_databases(
        self,
        db_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        use_dotenv: bool = True,
        use_aws_secrets: bool = False,
        aws_secret_name: Optional[str] = None,
        use_github_secrets: bool = False,
        github_secret_name: Optional[str] = None,
        github_repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """데이터베이스 목록을 조회합니다."""
        manager = DatabaseConnectionManager(
            db_name=db_name,
            connection_string=connection_string,
            mode=ConnectionMode.READ_ONLY,
            use_dotenv=use_dotenv,
            use_aws_secrets=use_aws_secrets,
            aws_secret_name=aws_secret_name,
            use_github_secrets=use_github_secrets,
            github_secret_name=github_secret_name,
            github_repo=github_repo
        )
        
        try:
            result = await manager.list_databases()
            await manager.close()
            return result
        except Exception as e:
            await manager.close()
            return {
                "success": False,
                "error": str(e),
                "databases": []
            }
    
    async def describe_tables(
        self,
        db_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        database: Optional[str] = None,
        use_dotenv: bool = True,
        use_aws_secrets: bool = False,
        aws_secret_name: Optional[str] = None,
        use_github_secrets: bool = False,
        github_secret_name: Optional[str] = None,
        github_repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """테이블 스키마를 조회합니다."""
        manager = DatabaseConnectionManager(
            db_name=db_name,
            connection_string=connection_string,
            mode=ConnectionMode.READ_ONLY,
            use_dotenv=use_dotenv,
            use_aws_secrets=use_aws_secrets,
            aws_secret_name=aws_secret_name,
            use_github_secrets=use_github_secrets,
            github_secret_name=github_secret_name,
            github_repo=github_repo
        )
        
        try:
            result = await manager.describe_tables(database=database)
            await manager.close()
            return result
        except Exception as e:
            await manager.close()
            return {
                "success": False,
                "error": str(e),
                "tables": []
            }
    
    async def run_query(
        self,
        query: str,
        db_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        mode: str = "read_only",
        use_dotenv: bool = True,
        use_aws_secrets: bool = False,
        aws_secret_name: Optional[str] = None,
        use_github_secrets: bool = False,
        github_secret_name: Optional[str] = None,
        github_repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """쿼리를 실행합니다."""
        connection_mode = ConnectionMode.READ_WRITE if mode == "read_write" else ConnectionMode.READ_ONLY
        
        manager = DatabaseConnectionManager(
            db_name=db_name,
            connection_string=connection_string,
            mode=connection_mode,
            use_dotenv=use_dotenv,
            use_aws_secrets=use_aws_secrets,
            aws_secret_name=aws_secret_name,
            use_github_secrets=use_github_secrets,
            github_secret_name=github_secret_name,
            github_repo=github_repo
        )
        
        try:
            result = await manager.execute_query(query, parameters, limit)
            await manager.close()
            return result
        except Exception as e:
            await manager.close()
            return {
                "success": False,
                "error": str(e),
                "rows": []
            }

