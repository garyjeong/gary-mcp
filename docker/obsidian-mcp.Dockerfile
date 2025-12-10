# Obsidian MCP Server Dockerfile
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# mcp-obsidian 설치
RUN pip install --no-cache-dir mcp-obsidian

# 환경 변수 설정
ENV OBSIDIAN_VAULT_PATH=/vault
ENV OBSIDIAN_API_TOKEN=""
ENV OBSIDIAN_PORT=27123
ENV PYTHONUNBUFFERED=1

# MCP 서버 실행 (STDIO 모드)
# mcp-obsidian은 일반적으로 Python 모듈로 실행되므로
# 환경 변수를 통해 vault 경로와 API 토큰을 전달
CMD ["python", "-m", "mcp_obsidian.server"]

