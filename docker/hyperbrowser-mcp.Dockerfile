# Hyperbrowser MCP 서버 Dockerfile
# https://github.com/hyperbrowserai/mcp
FROM node:20-slim

# 작업 디렉토리 설정
WORKDIR /app

# 환경 변수 설정
ARG HYPERBROWSER_API_KEY
ENV HYPERBROWSER_API_KEY=${HYPERBROWSER_API_KEY}

# hyperbrowser-mcp 패키지 전역 설치 (캐싱 활용)
RUN npm install -g hyperbrowser-mcp

# STDIO 모드로 실행
CMD ["hyperbrowser-mcp"]
