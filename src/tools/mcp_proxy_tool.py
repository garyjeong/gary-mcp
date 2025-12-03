"""MCP Proxy tool integration for external MCP servers."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from src.infrastructure.mcp_client import MCPProxyConfig, MCPProxyManager
from src.utils.config_loader import extract_proxy_configs, load_mcp_config


class MCPProxyService:
    """외부 MCP 서버를 통합하는 서비스."""
    
    def __init__(self) -> None:
        self.manager = MCPProxyManager()
        self._initialized = False
    
    async def initialize(self, configs: Optional[List[Dict[str, Any]]] = None) -> None:
        """프록시 설정을 초기화합니다."""
        if self._initialized:
            return
        
        # 설정 파일에서 자동으로 로드 시도
        if configs is None:
            try:
                mcp_config = load_mcp_config()
                configs = extract_proxy_configs(mcp_config, exclude_names=["gary-mcp"])
            except Exception:
                configs = []
        
        # 설정 파일에서 로드 실패 시 기본 설정 사용
        if not configs:
            default_configs = [
                {
                    "name": "sequential-thinking",
                    "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
                    "namespace_prefix": "thinking_"
                },
                {
                    "name": "playwright",
                    "command": ["npx", "@playwright/mcp@latest"],
                    "namespace_prefix": "playwright_"
                },
                {
                    "name": "aws-docs",
                    "url": "https://knowledge-mcp.global.api.aws",
                    "namespace_prefix": "aws_docs_"
                },
                {
                    "name": "chrome-devtools",
                    "command": ["npx", "chrome-devtools-mcp@latest"],
                    "namespace_prefix": "chrome_"
                },
                {
                    "name": "context7",
                    "url": "https://mcp.context7.com/mcp",
                    "namespace_prefix": "context7_"
                }
            ]
            configs = default_configs
        
        configs_to_use = configs
        
        for config_dict in configs_to_use:
            try:
                config = MCPProxyConfig(
                    name=config_dict["name"],
                    command=config_dict.get("command"),
                    url=config_dict.get("url"),
                    env=config_dict.get("env"),
                    cwd=config_dict.get("cwd"),
                    namespace_prefix=config_dict.get("namespace_prefix", "")
                )
                self.manager.register_proxy(config)
            except Exception as e:
                # 설정 실패는 로깅만 하고 계속 진행
                print(f"Warning: Failed to register MCP proxy {config_dict.get('name')}: {e}")
        
        self._initialized = True
    
    async def list_proxy_tools(self) -> Dict[str, Any]:
        """모든 프록시 서버의 도구 목록을 반환합니다."""
        if not self._initialized:
            await self.initialize()
        
        tools = await self.manager.get_all_tools()
        return {
            "tools": tools,
            "count": len(tools)
        }
    
    async def call_proxy_tool(
        self,
        proxy_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """프록시 도구를 호출합니다."""
        if not self._initialized:
            await self.initialize()
        
        return await self.manager.call_proxy_tool(proxy_name, tool_name, arguments)


# 전역 서비스 인스턴스
mcp_proxy_service = MCPProxyService()

