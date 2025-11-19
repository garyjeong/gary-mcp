"""Database tool tests."""

import pytest

from src.infrastructure.db.connection_manager import (
    ConnectionMode,
    DatabaseConnectionManager
)
from src.tools.db_tool import DatabaseService


@pytest.mark.asyncio
async def test_sqlite_connection_and_query(tmp_path):
    """SQLite 연결 및 쿼리 실행 테스트."""
    db_path = tmp_path / "test.db"
    connection_string = f"sqlite+aiosqlite:///{db_path}"
    
    manager = DatabaseConnectionManager(
        connection_string=connection_string,
        mode=ConnectionMode.READ_WRITE
    )
    
    # 테이블 생성 및 데이터 삽입
    create_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """
    result = await manager.execute_query(create_table)
    assert result["success"] is True
    
    insert_query = "INSERT INTO users (name, email) VALUES ('Test User', 'test@example.com')"
    result = await manager.execute_query(insert_query)
    assert result["success"] is True
    
    # 데이터 조회
    select_query = "SELECT * FROM users"
    result = await manager.execute_query(select_query)
    assert result["success"] is True
    assert len(result["rows"]) == 1
    assert result["rows"][0]["name"] == "Test User"
    
    # 읽기 전용 모드에서 쓰기 차단
    read_only_manager = DatabaseConnectionManager(
        connection_string=connection_string,
        mode=ConnectionMode.READ_ONLY
    )
    insert_result = await read_only_manager.execute_query(insert_query)
    assert insert_result["success"] is False
    assert "not allowed" in insert_result["error"].lower()
    
    await manager.close()
    await read_only_manager.close()


@pytest.mark.asyncio
async def test_database_service_list_databases(tmp_path):
    """DatabaseService의 list_databases 테스트."""
    db_path = tmp_path / "test.db"
    connection_string = f"sqlite+aiosqlite:///{db_path}"
    
    service = DatabaseService()
    result = await service.list_databases(connection_string=connection_string)
    
    assert result["success"] is True
    assert "main" in result["databases"]


@pytest.mark.asyncio
async def test_database_service_describe_tables(tmp_path):
    """DatabaseService의 describe_tables 테스트."""
    db_path = tmp_path / "test.db"
    connection_string = f"sqlite+aiosqlite:///{db_path}"
    
    # 테이블 생성
    manager = DatabaseConnectionManager(
        connection_string=connection_string,
        mode=ConnectionMode.READ_WRITE
    )
    await manager.execute_query("CREATE TABLE test (id INTEGER, name TEXT)")
    await manager.close()
    
    service = DatabaseService()
    result = await service.describe_tables(connection_string=connection_string)
    
    assert result["success"] is True
    assert len(result["tables"]) == 1
    assert result["tables"][0]["name"] == "test"
    assert len(result["tables"][0]["columns"]) == 2


@pytest.mark.asyncio
async def test_database_service_run_query(tmp_path):
    """DatabaseService의 run_query 테스트."""
    db_path = tmp_path / "test.db"
    connection_string = f"sqlite+aiosqlite:///{db_path}"
    
    # 테이블 생성 및 데이터 삽입
    manager = DatabaseConnectionManager(
        connection_string=connection_string,
        mode=ConnectionMode.READ_WRITE
    )
    await manager.execute_query("CREATE TABLE items (id INTEGER, value TEXT)")
    await manager.execute_query("INSERT INTO items VALUES (1, 'test')")
    await manager.close()
    
    service = DatabaseService()
    result = await service.run_query(
        "SELECT * FROM items",
        connection_string=connection_string,
        mode="read_only"
    )
    
    assert result["success"] is True
    assert len(result["rows"]) == 1
    assert result["rows"][0]["value"] == "test"

