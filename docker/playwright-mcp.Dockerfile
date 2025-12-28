# Playwright MCP 서버용 Dockerfile
FROM mcr.microsoft.com/playwright:v1.49.1-noble

WORKDIR /app

# npm 캐시 정리 및 패키지 설치
RUN npm install -g @playwright/mcp

# STDIO 모드로 실행
CMD ["npx", "-y", "@playwright/mcp"]

