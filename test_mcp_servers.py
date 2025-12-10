#!/usr/bin/env python3
"""MCP 서버 테스트 스크립트."""

import asyncio
import json
import subprocess
from typing import Any, Dict

MCP_SERVERS = {
    "aws-mcp-server": "docker exec -i aws-mcp-server python -m src.servers.aws_server",
    "flyio-mcp-server": "docker exec -i flyio-mcp-server python -m src.servers.flyio_server",
    "github-mcp-server": "docker exec -i github-mcp-server python -m src.servers.github_server",
    "db-mcp-server": "docker exec -i db-mcp-server python -m src.servers.db_server",
    "pdf-mcp-server": "docker exec -i pdf-mcp-server python -m src.servers.pdf_server",
    "official-docs-mcp-server": "docker exec -i official-docs-mcp-server python -m src.servers.official_docs_server",
}


async def test_mcp_server(server_name: str, command: str) -> Dict[str, Any]:
    """MCP 서버를 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"Testing: {server_name}")
    print(f"{'='*60}")
    
    try:
        # Initialize 요청
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        # Tools list 요청
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        # 프로세스 시작
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Initialize 전송
        init_json = json.dumps(init_request) + "\n"
        process.stdin.write(init_json.encode())
        await process.stdin.drain()
        
        # Initialize 응답 읽기 (타임아웃 5초)
        try:
            init_response = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            init_result = json.loads(init_response.decode())
            print(f"✓ Initialize: {init_result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        except asyncio.TimeoutError:
            print("✗ Initialize: Timeout")
            process.kill()
            return {"success": False, "error": "Initialize timeout"}
        except json.JSONDecodeError as e:
            print(f"✗ Initialize: JSON decode error - {e}")
            process.kill()
            return {"success": False, "error": f"JSON decode error: {e}"}
        
        # Initialized 알림
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        initialized_json = json.dumps(initialized_notification) + "\n"
        process.stdin.write(initialized_json.encode())
        await process.stdin.drain()
        
        # Tools list 전송
        tools_json = json.dumps(tools_request) + "\n"
        process.stdin.write(tools_json.encode())
        await process.stdin.drain()
        
        # Tools list 응답 읽기 (타임아웃 5초)
        try:
            tools_response = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            tools_result = json.loads(tools_response.decode())
            
            if "error" in tools_result:
                print(f"✗ Tools list: Error - {tools_result['error']}")
                return {"success": False, "error": tools_result["error"]}
            
            tools = tools_result.get("result", {}).get("tools", [])
            print(f"✓ Tools list: {len(tools)} tools found")
            for tool in tools[:5]:  # 처음 5개만 출력
                print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:60]}")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more")
            
            process.kill()
            await process.wait()
            
            return {"success": True, "tools_count": len(tools), "tools": tools}
            
        except asyncio.TimeoutError:
            print("✗ Tools list: Timeout")
            process.kill()
            return {"success": False, "error": "Tools list timeout"}
        except json.JSONDecodeError as e:
            print(f"✗ Tools list: JSON decode error - {e}")
            process.kill()
            return {"success": False, "error": f"JSON decode error: {e}"}
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """모든 MCP 서버를 테스트합니다."""
    print("MCP 서버 테스트 시작")
    print("=" * 60)
    
    results = {}
    for server_name, command in MCP_SERVERS.items():
        result = await test_mcp_server(server_name, command)
        results[server_name] = result
        await asyncio.sleep(0.5)  # 서버 간 간격
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)
    
    for server_name, result in results.items():
        status = "✓ PASS" if result.get("success") else "✗ FAIL"
        tools_count = result.get("tools_count", 0)
        print(f"{status} {server_name}: {tools_count} tools")
        if not result.get("success"):
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n총 {total_count}개 서버 중 {success_count}개 성공")
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

