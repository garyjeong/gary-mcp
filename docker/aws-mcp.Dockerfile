FROM python:3.12-slim

ARG WORKSPACE_PATH=/workspace
ENV WORKSPACE_PATH=${WORKSPACE_PATH}
ENV SHELL_RC_PATH=/root/.zshrc

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    build-essential \
    zsh \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# AWS CLI 설치
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

RUN uv pip install --system mcp[cli]>=1.0.0 aiohttp>=3.9.0 python-dotenv>=1.0.0 boto3>=1.34.0 requests>=2.31.0
RUN uv pip install --system -e .

ENV AWS_PROFILE=jongmun
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.servers.aws_server"]

