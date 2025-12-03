"""MCP Client for connecting to external MCP servers."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import aiohttp


@dataclass
class MCPProxyConfig:
    """외부 MCP 서버 프록시 설정."""
    
    name: str
    command: Optional[Sequence[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    namespace_prefix: str = ""  # 도구 이름 충돌 방지용 접두사


class MCPProxyClient:
    """외부 MCP 서버를 프록시하는 클라이언트."""
    
    def __init__(self, config: MCPProxyConfig) -> None:
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._tools_cache: List[Dict[str, Any]] = []
        self._connected = False
        self._request_id = 0
    
    async def connect(self) -> None:
        """MCP 서버에 연결합니다."""
        if self.config.url:
            # URL 기반 MCP 서버 (HTTP)
            self._http_session = aiohttp.ClientSession()
            self._connected = True
        elif self.config.command:
            # stdio 기반 MCP 서버 (subprocess)
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            self._process = await asyncio.create_subprocess_exec(
                *self.config.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.cwd
            )
            self._connected = True
        else:
            raise ValueError(f"Invalid MCP proxy config for {self.config.name}: need either url or command")
    
    async def disconnect(self) -> None:
        """연결을 종료합니다."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
        self._connected = False
    
    def _get_next_request_id(self) -> int:
        """다음 요청 ID를 반환합니다."""
        self._request_id += 1
        return self._request_id
    
    async def _send_jsonrpc_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """JSON-RPC 요청을 전송하고 응답을 받습니다."""
        if not self._connected:
            await self.connect()
        
        request_id = self._get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        if self.config.url:
            # HTTP 기반 MCP 서버
            async with self._http_session.post(
                self.config.url,
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": {
                            "code": response.status,
                            "message": error_text
                        }
                    }
        else:
            # stdio 기반 MCP 서버
            if not self._process or not self._process.stdin:
                raise RuntimeError("Process not initialized")
            
            request_json = json.dumps(request) + "\n"
            self._process.stdin.write(request_json.encode('utf-8'))
            await self._process.stdin.drain()
            
            # 응답 읽기 (한 줄씩)
            if not self._process.stdout:
                raise RuntimeError("Process stdout not available")
            
            line = await self._process.stdout.readline()
            response = json.loads(line.decode('utf-8'))
            
            # 요청 ID 확인
            if response.get("id") != request_id:
                raise ValueError(f"Request ID mismatch: expected {request_id}, got {response.get('id')}")
            
            return response
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록을 조회합니다."""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self._send_jsonrpc_request("tools/list")
            
            if "error" in response:
                return []
            
            result = response.get("result", {})
            tools = result.get("tools", [])
            
            # 네임스페이스 접두사 추가
            prefixed_tools = []
            for tool in tools:
                prefixed_name = f"{self.config.namespace_prefix}{tool['name']}" if self.config.namespace_prefix else tool['name']
                prefixed_tool = tool.copy()
                prefixed_tool["name"] = prefixed_name
                prefixed_tool["original_name"] = tool["name"]  # 원본 이름 보존
                prefixed_tools.append(prefixed_tool)
            
            self._tools_cache = prefixed_tools
            return prefixed_tools
        except Exception as e:
            # 오류 발생 시 빈 리스트 반환
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구를 호출합니다."""
        if not self._connected:
            await self.connect()
        
        # 네임스페이스 접두사 제거하여 원본 이름 찾기
        original_name = tool_name
        if self.config.namespace_prefix and tool_name.startswith(self.config.namespace_prefix):
            original_name = tool_name[len(self.config.namespace_prefix):]
        
        try:
            response = await self._send_jsonrpc_request(
                "tools/call",
                params={
                    "name": original_name,
                    "arguments": arguments
                }
            )
            
            if "error" in response:
                return {"error": response["error"]}
            
            result = response.get("result", {})
            return result
        except Exception as e:
            return {"error": str(e)}


class MCPProxyManager:
    """여러 MCP 프록시 클라이언트를 관리합니다."""
    
    def __init__(self) -> None:
        self._proxies: Dict[str, MCPProxyClient] = {}
    
    def register_proxy(self, config: MCPProxyConfig) -> None:
        """프록시 클라이언트를 등록합니다."""
        proxy = MCPProxyClient(config)
        self._proxies[config.name] = proxy
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """모든 프록시 서버의 도구를 조회합니다."""
        all_tools = []
        for proxy in self._proxies.values():
            try:
                tools = await proxy.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                # 개별 프록시 실패는 무시하고 계속 진행
                all_tools.append({
                    "name": f"{proxy.config.namespace_prefix}error",
                    "description": f"Failed to load tools from {proxy.config.name}: {str(e)}",
                    "inputSchema": {},
                    "error": True
                })
        return all_tools
    
    async def call_proxy_tool(self, proxy_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """특정 프록시의 도구를 호출합니다."""
        if proxy_name not in self._proxies:
            raise ValueError(f"Proxy {proxy_name} not found")
        
        proxy = self._proxies[proxy_name]
        return await proxy.call_tool(tool_name, arguments)
    
    async def disconnect_all(self) -> None:
        """모든 프록시 연결을 종료합니다."""
        for proxy in self._proxies.values():
            try:
                await proxy.disconnect()
            except Exception:
                pass

