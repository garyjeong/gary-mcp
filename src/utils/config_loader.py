"""MCP 설정 파일 로더."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_mcp_config(config_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """MCP 설정 파일을 로드합니다."""
    if config_path is None:
        # 기본 경로들 시도
        default_paths = [
            Path.home() / ".cursor" / "mcp.json",
            Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path(__file__).parent.parent.parent / "cursor-mcp-local.json"
        ]
        
        for path in default_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            return {}
    
    config_file = Path(config_path)
    if not config_file.exists():
        return {}
    
    try:
        with config_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def extract_proxy_configs(mcp_config: Dict[str, Any], exclude_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """MCP 설정에서 프록시 설정을 추출합니다."""
    exclude_names = exclude_names or ["gary-mcp"]
    servers = mcp_config.get("mcpServers", {})
    proxy_configs = []
    
    for name, server_config in servers.items():
        if name in exclude_names:
            continue
        
        # 네임스페이스 접두사 생성 (이름 기반)
        namespace_prefix = f"{name.replace('-', '_')}_"
        
        proxy_config = {
            "name": name,
            "namespace_prefix": namespace_prefix
        }
        
        if "url" in server_config:
            proxy_config["url"] = server_config["url"]
            if "headers" in server_config:
                proxy_config["headers"] = server_config["headers"]
        elif "command" in server_config:
            command = server_config["command"]
            args = server_config.get("args", [])
            # command가 문자열인 경우 공백으로 분리 (예: "npx @playwright/mcp@latest")
            if isinstance(command, str):
                # 공백이 포함된 경우 분리, 그렇지 않으면 그대로 사용
                if " " in command and not args:
                    # command 문자열을 공백으로 분리하여 command와 args로 나눔
                    parts = command.split()
                    proxy_config["command"] = parts
                else:
                    proxy_config["command"] = [command] + (args if isinstance(args, list) else [])
            else:
                proxy_config["command"] = list(command) + (args if isinstance(args, list) else [])
            if "env" in server_config:
                proxy_config["env"] = server_config["env"]
            if "cwd" in server_config:
                proxy_config["cwd"] = server_config["cwd"]
        
        proxy_configs.append(proxy_config)
    
    return proxy_configs

