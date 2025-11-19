# Python 3.12 slim 베이스 이미지
FROM python:3.12-slim

ARG WORKSPACE_PATH=/workspace
ENV WORKSPACE_PATH=${WORKSPACE_PATH}
ENV SHELL_RC_PATH=/root/.zshrc

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    zsh \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# AWS CLI 설치
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Fly.io CLI 설치
RUN curl -L https://fly.io/install.sh | sh \
    && mv /root/.fly/bin/flyctl /usr/local/bin/flyctl \
    && chmod +x /usr/local/bin/flyctl

# 프로젝트 파일 복사
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# uv를 사용하여 의존성 설치
RUN uv pip install --system -e .

# 환경 변수 설정
ENV AWS_PROFILE=jongmun
ENV PYTHONUNBUFFERED=1

# MCP 서버 실행
CMD ["python", "-m", "src.server"]
