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
    git \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

RUN uv pip install --system \
    mcp[cli]>=1.0.0 \
    aiohttp>=3.9.0 \
    python-dotenv>=1.0.0 \
    markdown>=3.5.0 \
    beautifulsoup4>=4.12.0 \
    pyyaml>=6.0 \
    requests>=2.31.0
RUN uv pip install --system -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.servers.official_docs_server"]

