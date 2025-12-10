# 공통 베이스 Dockerfile
FROM python:3.12-slim

ARG WORKSPACE_PATH=/workspace
ENV WORKSPACE_PATH=${WORKSPACE_PATH}
ENV SHELL_RC_PATH=/root/.zshrc

WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    build-essential \
    zsh \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# 기본 의존성 설치 (모든 서버에 공통)
RUN uv pip install --system mcp[cli]>=1.0.0 aiohttp>=3.9.0 python-dotenv>=1.0.0

ENV PYTHONUNBUFFERED=1

