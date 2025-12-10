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

# GitHub CLI 설치
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system mcp[cli]>=1.0.0 aiohttp>=3.9.0 python-dotenv>=1.0.0
RUN uv pip install --system -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.servers.github_server"]

