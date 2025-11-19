"""DB 연결 관리자 - 다양한 DB 타입 지원."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from src.utils.env_loader import get_db_credentials


class DatabaseType(str, Enum):
    """지원하는 데이터베이스 타입."""
    
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MSSQL = "mssql"


class ConnectionMode(str, Enum):
    """연결 모드."""
    
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


class DatabaseConnectionManager:
    """다양한 DB에 대한 연결을 관리합니다."""
    
    def __init__(
        self,
        db_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        mode: ConnectionMode = ConnectionMode.READ_ONLY,
        use_dotenv: bool = True,
        use_aws_secrets: bool = False,
        aws_secret_name: Optional[str] = None,
        use_github_secrets: bool = False,
        github_secret_name: Optional[str] = None,
        github_repo: Optional[str] = None
    ):
        self.db_name = db_name
        self.mode = mode
        self._engine: Optional[AsyncEngine] = None
        self._connection_string = connection_string or self._build_connection_string(
            db_name,
            use_dotenv,
            use_aws_secrets,
            aws_secret_name,
            use_github_secrets,
            github_secret_name,
            github_repo
        )
    
    def _build_connection_string(
        self,
        db_name: Optional[str],
        use_dotenv: bool,
        use_aws_secrets: bool,
        aws_secret_name: Optional[str],
        use_github_secrets: bool,
        github_secret_name: Optional[str],
        github_repo: Optional[str]
    ) -> str:
        """환경 변수와 시크릿에서 연결 문자열을 구성합니다."""
        credentials = get_db_credentials(
            db_name=db_name,
            use_dotenv=use_dotenv,
            use_aws_secrets=use_aws_secrets,
            aws_secret_name=aws_secret_name,
            use_github_secrets=use_github_secrets,
            github_secret_name=github_secret_name,
            github_repo=github_repo
        )
        
        # DATABASE_URL이 있으면 우선 사용
        if "DATABASE_URL" in credentials:
            return credentials["DATABASE_URL"]
        
        # 개별 파라미터로 구성
        db_type = credentials.get("DB_TYPE", "postgresql").lower()
        host = credentials.get("DB_HOST") or credentials.get("POSTGRES_HOST") or credentials.get("MYSQL_HOST", "localhost")
        port = credentials.get("DB_PORT") or credentials.get("POSTGRES_PORT") or credentials.get("MYSQL_PORT", "5432" if db_type == "postgresql" else "3306")
        user = credentials.get("DB_USER") or credentials.get("POSTGRES_USER") or credentials.get("MYSQL_USER", "root")
        password = credentials.get("DB_PASSWORD") or credentials.get("POSTGRES_PASSWORD") or credentials.get("MYSQL_PASSWORD", "")
        database = credentials.get("DB_NAME") or credentials.get("POSTGRES_DB") or credentials.get("MYSQL_DB") or db_name or "postgres"
        
        if db_type == "sqlite":
            db_path = credentials.get("SQLITE_PATH") or database
            return f"sqlite+aiosqlite:///{db_path}"
        elif db_type == "mysql":
            return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"
        elif db_type == "postgresql":
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    async def get_engine(self) -> AsyncEngine:
        """비동기 엔진을 반환합니다 (연결 풀 사용)."""
        if self._engine is None:
            self._engine = create_async_engine(
                self._connection_string,
                poolclass=NullPool if self.mode == ConnectionMode.READ_ONLY else None,
                echo=False
            )
        return self._engine
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """쿼리를 실행하고 결과를 반환합니다."""
        engine = await self.get_engine()
        
        # 읽기 전용 모드에서 DDL/DML 차단
        if self.mode == ConnectionMode.READ_ONLY:
            query_upper = query.strip().upper()
            forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
            if any(keyword in query_upper for keyword in forbidden_keywords):
                return {
                    "success": False,
                    "error": "Write operations are not allowed in read-only mode",
                    "rows": []
                }
        
        # LIMIT 추가 (SELECT 쿼리인 경우)
        if query.strip().upper().startswith("SELECT") and "LIMIT" not in query.upper():
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text(query), parameters or {})
                
                if result.returns_rows:
                    rows = [dict(row._mapping) for row in result.fetchall()]
                    return {
                        "success": True,
                        "rows": rows,
                        "row_count": len(rows)
                    }
                else:
                    return {
                        "success": True,
                        "rows": [],
                        "row_count": result.rowcount if hasattr(result, "rowcount") else 0
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows": []
            }
    
    async def list_databases(self) -> Dict[str, Any]:
        """데이터베이스 목록을 조회합니다."""
        try:
            # PostgreSQL
            if "postgresql" in self._connection_string:
                result = await self.execute_query("SELECT datname FROM pg_database WHERE datistemplate = false")
                return {
                    "success": True,
                    "databases": [row["datname"] for row in result.get("rows", [])]
                }
            # MySQL
            elif "mysql" in self._connection_string:
                result = await self.execute_query("SHOW DATABASES")
                return {
                    "success": True,
                    "databases": [row["Database"] for row in result.get("rows", [])]
                }
            # SQLite
            elif "sqlite" in self._connection_string:
                return {
                    "success": True,
                    "databases": ["main"]
                }
            else:
                return {
                    "success": False,
                    "error": "Database type not supported for listing databases",
                    "databases": []
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "databases": []
            }
    
    async def describe_tables(self, database: Optional[str] = None) -> Dict[str, Any]:
        """테이블 목록과 스키마를 조회합니다."""
        try:
            engine = await self.get_engine()
            
            # DB 타입에 따라 적절한 쿼리 사용
            if "postgresql" in self._connection_string:
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = COALESCE(:schema, 'public')
                    AND table_type = 'BASE TABLE'
                """
                columns_query = """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = COALESCE(:schema, 'public') AND table_name = :table_name
                    ORDER BY ordinal_position
                """
            elif "mysql" in self._connection_string:
                db_name = database or "information_schema"
                tables_query = f"SHOW TABLES FROM {db_name}"
                columns_query = f"SHOW COLUMNS FROM {{table_name}} FROM {db_name}"
            elif "sqlite" in self._connection_string:
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                columns_query = "PRAGMA table_info({table_name})"
            else:
                return {
                    "success": False,
                    "error": "Database type not supported for describing tables",
                    "tables": []
                }
            
            # 테이블 목록 조회
            tables_result = await self.execute_query(tables_query, {"schema": database} if database else {})
            if not tables_result.get("success"):
                return tables_result
            
            table_names = []
            if "postgresql" in self._connection_string:
                table_names = [row["table_name"] for row in tables_result.get("rows", [])]
            elif "mysql" in self._connection_string:
                table_names = [list(row.values())[0] for row in tables_result.get("rows", [])]
            elif "sqlite" in self._connection_string:
                table_names = [row["name"] for row in tables_result.get("rows", [])]
            
            table_info = []
            for table_name in table_names:
                if "sqlite" in self._connection_string:
                    cols_result = await self.execute_query(columns_query.format(table_name=table_name))
                else:
                    cols_result = await self.execute_query(columns_query, {"table_name": table_name, "schema": database} if database else {"table_name": table_name})
                
                if cols_result.get("success"):
                    columns = []
                    for col in cols_result.get("rows", []):
                        if "sqlite" in self._connection_string:
                            columns.append({
                                "name": col["name"],
                                "type": col["type"],
                                "nullable": col.get("notnull", 1) == 0
                            })
                        else:
                            col_name = col.get("column_name") or list(col.values())[0]
                            col_type = col.get("data_type") or col.get("Type", "unknown")
                            nullable = col.get("is_nullable") == "YES" if "postgresql" in self._connection_string else col.get("Null") == "YES"
                            columns.append({
                                "name": col_name,
                                "type": col_type,
                                "nullable": nullable
                            })
                    
                    table_info.append({
                        "name": table_name,
                        "columns": columns
                    })
            
            return {
                "success": True,
                "tables": table_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tables": []
            }
    
    async def close(self) -> None:
        """연결을 종료합니다."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

