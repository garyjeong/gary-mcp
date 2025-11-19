"""Shell 환경 변수 로더 및 시크릿 관리."""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

_EXPORT_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _should_include(name: str, prefixes: Sequence[str] | None, keys: Sequence[str] | None) -> bool:
    if keys and name in keys:
        return True
    if prefixes:
        return any(name.startswith(prefix) for prefix in prefixes)
    return not prefixes and not keys


def load_shell_env(
    *,
    prefixes: Sequence[str] | None = None,
    keys: Sequence[str] | None = None,
    rc_path: str | Path | None = None
) -> Dict[str, str]:
    """zshrc 등 shell rc 파일에서 환경 변수를 읽습니다."""
    resolved_path = Path(rc_path or os.getenv("SHELL_RC_PATH", Path.home() / ".zshrc")).expanduser()
    collected: Dict[str, str] = {}

    if resolved_path.exists():
        for line in resolved_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _EXPORT_PATTERN.match(stripped)
            if not match:
                continue
            name, raw_value = match.groups()
            if not _should_include(name, prefixes, keys):
                continue
            collected[name] = _strip_quotes(raw_value)

    for name, value in os.environ.items():
        if _should_include(name, prefixes, keys):
            collected[name] = value

    return collected


def load_dotenv_file(env_path: str | Path | None = None) -> Dict[str, str]:
    """프로젝트의 .env 파일에서 환경 변수를 로드합니다."""
    if not DOTENV_AVAILABLE:
        return {}
    
    collected: Dict[str, str] = {}
    
    if env_path:
        env_file = Path(env_path).expanduser()
    else:
        # 현재 디렉토리부터 상위로 .env 파일 찾기
        current = Path.cwd()
        env_file = None
        for parent in [current, *current.parents]:
            candidate = parent / ".env"
            if candidate.exists():
                env_file = candidate
                break
    
    if env_file and env_file.exists():
        load_dotenv(env_file, override=False)
        # 로드된 환경 변수 수집
        for key, value in os.environ.items():
            if key.startswith(("DB_", "DATABASE_", "POSTGRES_", "MYSQL_", "SQLITE_")):
                collected[key] = value
    
    return collected


async def load_aws_secret(secret_name: str, region: str = "ap-northeast-2") -> Dict[str, str]:
    """AWS Secrets Manager에서 시크릿을 조회합니다."""
    if not BOTO3_AVAILABLE:
        return {}
    
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString", "")
        
        try:
            return json.loads(secret_string)
        except json.JSONDecodeError:
            # JSON이 아닌 경우 키=값 형식으로 파싱 시도
            result: Dict[str, str] = {}
            for line in secret_string.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    result[key.strip()] = value.strip()
            return result
    except ClientError:
        return {}
    except Exception:
        return {}


async def load_github_secret(secret_name: str, repo: str | None = None) -> Optional[str]:
    """GitHub CLI를 통해 시크릿을 조회합니다."""
    try:
        cmd = ["gh", "secret", "get", secret_name]
        if repo:
            cmd.extend(["--repo", repo])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return stdout.decode("utf-8").strip()
    except Exception:
        pass
    
    return None


def get_db_credentials(
    db_name: Optional[str] = None,
    use_dotenv: bool = True,
    use_aws_secrets: bool = False,
    aws_secret_name: Optional[str] = None,
    use_github_secrets: bool = False,
    github_secret_name: Optional[str] = None,
    github_repo: Optional[str] = None
) -> Dict[str, str]:
    """DB 자격 증명을 다양한 소스에서 수집합니다."""
    credentials: Dict[str, str] = {}
    
    # 1. 환경 변수 (최우선)
    env_vars = load_shell_env(
        prefixes=("DB_", "DATABASE_", "POSTGRES_", "MYSQL_", "SQLITE_"),
        keys=None
    )
    credentials.update(env_vars)
    
    # 2. .env 파일
    if use_dotenv:
        dotenv_vars = load_dotenv_file()
        credentials.update(dotenv_vars)
    
    # 3. AWS Secrets Manager
    if use_aws_secrets and aws_secret_name:
        secret_data = asyncio.run(load_aws_secret(aws_secret_name))
        credentials.update(secret_data)
    
    # 4. GitHub Secrets
    if use_github_secrets and github_secret_name:
        github_value = asyncio.run(load_github_secret(github_secret_name, github_repo))
        if github_value:
            # JSON 형식일 수 있음
            try:
                github_data = json.loads(github_value)
                credentials.update(github_data)
            except json.JSONDecodeError:
                credentials[github_secret_name] = github_value
    
    return credentials
