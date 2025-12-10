#!/bin/bash
# MCP 서버 Docker Compose 관리 스크립트

set -e

COMPOSE_FILE="docker-compose.mcp.yml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 사용법 출력
usage() {
    echo "사용법: $0 [명령] [서비스명]"
    echo ""
    echo "명령:"
    echo "  start       - 모든 MCP 서버 시작"
    echo "  stop        - 모든 MCP 서버 중지"
    echo "  restart     - 모든 MCP 서버 재시작"
    echo "  status      - 서버 상태 확인"
    echo "  logs        - 서버 로그 확인 (서비스명 선택 가능)"
    echo "  up          - 서버 시작 (foreground)"
    echo "  down        - 서버 중지 및 제거"
    echo "  build       - 이미지 빌드"
    echo ""
    echo "서비스명 (선택사항):"
    echo "  notion-mcp"
    echo "  obsidian-mcp"
    echo "  sequential-thinking-mcp"
    echo "  chrome-devtools-mcp"
    echo ""
    echo "예시:"
    echo "  $0 start                          # 모든 서버 시작"
    echo "  $0 start notion-mcp               # Notion MCP만 시작"
    echo "  $0 logs obsidian-mcp              # Obsidian MCP 로그 확인"
}

# 함수: 환경 변수 파일 확인
check_env_file() {
    if [ ! -f ".env.mcp" ]; then
        echo -e "${YELLOW}경고: .env.mcp 파일이 없습니다.${NC}"
        if [ -f "env.mcp.example" ]; then
            echo -e "${YELLOW}env.mcp.example 파일을 복사하여 .env.mcp를 생성하세요:${NC}"
            echo "  cp env.mcp.example .env.mcp"
        fi
        echo ""
        read -p "계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 함수: Docker Compose 명령 실행
run_compose() {
    docker-compose -f "$COMPOSE_FILE" "$@"
}

# 메인 로직
case "${1:-}" in
    start)
        check_env_file
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${GREEN}모든 MCP 서버를 시작합니다...${NC}"
            run_compose up -d
        else
            echo -e "${GREEN}$SERVICE 서버를 시작합니다...${NC}"
            run_compose up -d "$SERVICE"
        fi
        echo -e "${GREEN}완료!${NC}"
        echo ""
        echo "서버 상태 확인: $0 status"
        echo "로그 확인: $0 logs"
        ;;
    stop)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${YELLOW}모든 MCP 서버를 중지합니다...${NC}"
            run_compose stop
        else
            echo -e "${YELLOW}$SERVICE 서버를 중지합니다...${NC}"
            run_compose stop "$SERVICE"
        fi
        echo -e "${GREEN}완료!${NC}"
        ;;
    restart)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${YELLOW}모든 MCP 서버를 재시작합니다...${NC}"
            run_compose restart
        else
            echo -e "${YELLOW}$SERVICE 서버를 재시작합니다...${NC}"
            run_compose restart "$SERVICE"
        fi
        echo -e "${GREEN}완료!${NC}"
        ;;
    status)
        echo -e "${GREEN}MCP 서버 상태:${NC}"
        run_compose ps
        ;;
    logs)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${GREEN}모든 서버 로그 (Ctrl+C로 종료):${NC}"
            run_compose logs -f
        else
            echo -e "${GREEN}$SERVICE 로그 (Ctrl+C로 종료):${NC}"
            run_compose logs -f "$SERVICE"
        fi
        ;;
    up)
        check_env_file
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${GREEN}모든 MCP 서버를 시작합니다 (foreground)...${NC}"
            run_compose up
        else
            echo -e "${GREEN}$SERVICE 서버를 시작합니다 (foreground)...${NC}"
            run_compose up "$SERVICE"
        fi
        ;;
    down)
        echo -e "${RED}모든 MCP 서버를 중지하고 제거합니다...${NC}"
        read -p "계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_compose down
            echo -e "${GREEN}완료!${NC}"
        else
            echo "취소되었습니다."
        fi
        ;;
    build)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo -e "${GREEN}모든 MCP 서버 이미지를 빌드합니다...${NC}"
            run_compose build
        else
            echo -e "${GREEN}$SERVICE 이미지를 빌드합니다...${NC}"
            run_compose build "$SERVICE"
        fi
        echo -e "${GREEN}완료!${NC}"
        ;;
    *)
        usage
        exit 1
        ;;
esac

