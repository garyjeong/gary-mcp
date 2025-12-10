# Node.js 기반 MCP 서버 공통 Dockerfile
FROM node:20-slim

# 작업 디렉토리 설정
WORKDIR /app

# npx를 사용하여 MCP 패키지 실행
# 빌드 인자로 MCP_PACKAGE를 받아서 사용
ARG MCP_PACKAGE
ENV MCP_PACKAGE=${MCP_PACKAGE}

# npx는 패키지가 없으면 자동으로 다운로드하므로
# 별도의 설치 과정이 필요 없음
# STDIO 모드로 실행
CMD ["sh", "-c", "npx -y ${MCP_PACKAGE}"]

