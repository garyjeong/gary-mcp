# Cursor MCP 설정 가이드 (Docker Compose 버전)

이 가이드는 Docker Compose로 실행한 MCP 서버들을 Cursor에 연결하는 방법을 설명합니다.

## 사전 준비

1. Docker Compose로 MCP 서버들이 실행 중이어야 합니다:
   ```bash
   docker-compose -f docker-compose.mcp.yml up -d
   ```

2. 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps | grep mcp-server
   ```

## Cursor 설정 파일 위치

### macOS
- `~/.cursor/mcp.json` 또는
- `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

## 설정 방법

### 방법 1: 예시 파일 복사 및 수정

1. 예시 파일을 Cursor 설정 위치로 복사:
   ```bash
   cp cursor-mcp-docker-example.json ~/.cursor/mcp.json
   ```

2. 파일 편집하여 실제 값으로 변경:
   - `NOTION_TOKEN`: 실제 Notion API 토큰

### 방법 2: 기존 설정 파일에 추가

기존 `~/.cursor/mcp.json` 파일이 있다면, `cursor-mcp-docker.json`의 내용을 `mcpServers` 섹션에 추가하세요.

## 설정 예시

```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "notion-mcp-server"],
      "env": {
        "NOTION_TOKEN": "ntn_your_token_here"
      }
    },
    "sequential-thinking-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "sequential-thinking-mcp-server"]
    },
    "chrome-devtools-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "chrome-devtools-mcp-server"]
    }
  }
}
```

## 중요 사항

### Docker 컨테이너 실행 필수

Cursor에서 MCP 서버를 사용하려면 **반드시 Docker 컨테이너가 실행 중**이어야 합니다.

컨테이너가 실행되지 않은 상태에서 Cursor가 연결을 시도하면 오류가 발생합니다.

### 컨테이너 이름 확인

설정 파일의 컨테이너 이름이 실제 컨테이너 이름과 일치하는지 확인:

```bash
docker ps --format "{{.Names}}"
```

예상되는 컨테이너 이름:
- `notion-mcp-server`
- `sequential-thinking-mcp-server`
- `chrome-devtools-mcp-server`

### 환경 변수

Docker Compose의 `.env.mcp` 파일에 설정한 환경 변수는 컨테이너 내부에서만 사용됩니다.

Cursor 설정 파일의 `env` 섹션은 **선택사항**입니다. Docker Compose에서 이미 환경 변수를 설정했다면 생략할 수 있습니다.

## 연결 테스트

1. Cursor IDE 완전히 재시작
2. 왼쪽 사이드바의 MCP 섹션 확인
3. 각 서버가 "Connected" 상태인지 확인
4. AI 채팅에서 각 MCP 서버의 도구 사용 테스트

## 문제 해결

### 서버가 연결되지 않는 경우

1. **컨테이너 실행 확인**:
   ```bash
   docker ps | grep mcp-server
   ```

2. **컨테이너 로그 확인**:
   ```bash
   docker logs notion-mcp-server
   docker logs sequential-thinking-mcp-server
   docker logs chrome-devtools-mcp-server
   ```

3. **컨테이너 재시작**:
   ```bash
   docker-compose -f docker-compose.mcp.yml restart
   ```

### 환경 변수 오류

Docker Compose의 `.env.mcp` 파일을 확인하고, 필요한 환경 변수가 모두 설정되어 있는지 확인하세요.

### 컨테이너 이름 불일치

`docker-compose.mcp.yml`의 `container_name`과 Cursor 설정 파일의 컨테이너 이름이 일치하는지 확인하세요.

## 자동 시작 설정 (선택사항)

시스템 부팅 시 자동으로 MCP 서버를 시작하려면:

```bash
# Docker Compose 자동 시작 설정
docker-compose -f docker-compose.mcp.yml up -d
```

또는 macOS의 경우 LaunchAgent를 사용할 수 있습니다.

