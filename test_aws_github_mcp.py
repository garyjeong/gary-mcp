#!/usr/bin/env python3
"""AWS와 GitHub MCP 서버 실제 동작 검증 스크립트."""

import asyncio
import json
import subprocess
from typing import Any, Dict


async def test_mcp_tool_call(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 서버의 도구를 실제로 호출하여 테스트합니다."""
    print(f"\n{'='*60}")
    print(f"Testing: {server_name} -> {tool_name}")
    print(f"Arguments: {arguments}")
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
        
        # Tool call 요청
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # 서버별 명령
        commands = {
            "aws-mcp-server": "docker exec -i aws-mcp-server python -m src.servers.aws_server",
            "github-mcp-server": "docker exec -i github-mcp-server python -m src.servers.github_server",
        }
        
        command = commands.get(server_name)
        if not command:
            return {"success": False, "error": f"Unknown server: {server_name}"}
        
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
        
        # Initialize 응답 읽기
        try:
            init_response = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            init_result = json.loads(init_response.decode())
            if "error" in init_result:
                print(f"✗ Initialize failed: {init_result['error']}")
                process.kill()
                return {"success": False, "error": init_result["error"]}
        except (asyncio.TimeoutError, json.JSONDecodeError) as e:
            print(f"✗ Initialize error: {e}")
            process.kill()
            return {"success": False, "error": str(e)}
        
        # Initialized 알림
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        initialized_json = json.dumps(initialized_notification) + "\n"
        process.stdin.write(initialized_json.encode())
        await process.stdin.drain()
        
        # Tool call 전송
        tool_json = json.dumps(tool_request) + "\n"
        process.stdin.write(tool_json.encode())
        await process.stdin.drain()
        
        # Tool call 응답 읽기
        try:
            tool_response = await asyncio.wait_for(
                process.stdout.readline(), timeout=30.0
            )
            tool_result = json.loads(tool_response.decode())
            
            if "error" in tool_result:
                print(f"✗ Tool call failed: {tool_result['error']}")
                process.kill()
                return {"success": False, "error": tool_result["error"]}
            
            # 결과 파싱
            result_content = tool_result.get("result", {}).get("content", [])
            if result_content:
                text_content = result_content[0].get("text", "")
                parsed_result = json.loads(text_content)
                
                if parsed_result.get("success"):
                    print(f"✓ Tool call succeeded")
                    print(f"Output: {json.dumps(parsed_result, indent=2, ensure_ascii=False)[:500]}...")
                else:
                    print(f"✗ Tool call returned error: {parsed_result.get('error', 'Unknown error')}")
                
                process.kill()
                await process.wait()
                
                return {"success": parsed_result.get("success", False), "result": parsed_result}
            else:
                print(f"✗ No content in response")
                process.kill()
                return {"success": False, "error": "No content in response"}
            
        except asyncio.TimeoutError:
            print(f"✗ Tool call timeout (30s)")
            process.kill()
            return {"success": False, "error": "Timeout"}
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Response parsing error: {e}")
            process.kill()
            return {"success": False, "error": f"Parse error: {e}"}
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """AWS와 GitHub MCP 서버를 테스트합니다."""
    print("AWS & GitHub MCP 서버 실제 동작 검증")
    print("=" * 60)
    
    tests = [
        # AWS 테스트
        {
            "server": "aws-mcp-server",
            "tool": "aws_get_account_info",
            "args": {}
        },
        # GitHub 테스트
        {
            "server": "github-mcp-server",
            "tool": "github_list_repos",
            "args": {"limit": 5}
        },
    ]
    
    results = {}
    for test in tests:
        result = await test_mcp_tool_call(
            test["server"],
            test["tool"],
            test["args"]
        )
        results[f"{test['server']}:{test['tool']}"] = result
        await asyncio.sleep(1)  # 서버 간 간격
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("검증 결과 요약")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✓ PASS" if result.get("success") else "✗ FAIL"
        print(f"{status} {test_name}")
        if not result.get("success"):
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)
    
    print(f"\n총 {total_count}개 테스트 중 {success_count}개 성공")
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

