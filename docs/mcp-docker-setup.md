# MCP 서버 Docker Compose 설정 가이드

이 가이드는 Docker Compose를 사용하여 각 MCP 서버를 독립적으로 실행하고 Cursor에 연결하는 방법을 설명합니다.

## 사전 요구사항

- Docker 및 Docker Compose 설치
- Cursor IDE 설치
- 각 MCP 서버에 필요한 인증 정보

## 설정 단계

### 1. 환경 변수 파일 생성

프로젝트 루트에 `.env.mcp` 파일을 생성하고 필요한 환경 변수를 설정합니다:

```bash
cp env.mcp.example .env.mcp
```

`.env.mcp` 파일을 편집하여 실제 값으로 채워주세요:

```env
# Notion MCP
NOTION_TOKEN=ntn_your_actual_token_here
```

### 2. Notion API 토큰 발급

1. [Notion 통합 페이지](https://www.notion.so/my-integrations)에 접속
2. "새 통합" 클릭
3. 통합 이름 입력 후 "제출" 클릭
4. "시크릿" 섹션에서 토큰 복사 (형식: `ntn_...`)
5. `.env.mcp` 파일의 `NOTION_TOKEN`에 붙여넣기

### 3. Docker Compose로 서버 실행

모든 MCP 서버를 한 번에 실행:

```bash
docker-compose -f docker-compose.mcp.yml up -d
```

개별 서버만 실행:

```bash
# Notion MCP만 실행
docker-compose -f docker-compose.mcp.yml up -d notion-mcp

# Sequential Thinking MCP만 실행
docker-compose -f docker-compose.mcp.yml up -d sequential-thinking-mcp

# Chrome Devtools MCP만 실행
docker-compose -f docker-compose.mcp.yml up -d chrome-devtools-mcp
```

서버 중지:

```bash
docker-compose -f docker-compose.mcp.yml down
```

### 5. Cursor 설정

Cursor의 MCP 설정 파일에 각 서버를 추가합니다.

#### macOS 설정 파일 위치
- `~/.cursor/mcp.json` 또는
- `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

#### 설정 예시

```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "notion-mcp-server"
      ]
    },
    "sequential-thinking-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "sequential-thinking-mcp-server"
      ]
    },
    "chrome-devtools-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "chrome-devtools-mcp-server"
      ]
    }
  }
}
```

**참고**: Docker Compose로 실행한 컨테이너에 연결하려면 `docker exec -i` 명령을 사용합니다.

### 6. 연결 테스트

1. Cursor IDE 재시작
2. 왼쪽 사이드바의 MCP 섹션에서 각 서버가 연결되었는지 확인
3. AI 채팅에서 각 MCP 서버의 도구를 사용해보기

## 서비스별 상세 정보

### Notion MCP

- **이미지**: `mcp/notion:latest` (공식)
- **필수 환경 변수**: `NOTION_TOKEN`
- **기능**: Notion 페이지 생성, 검색, 편집

### Sequential Thinking MCP

- **빌드**: `docker/node-mcp.Dockerfile`
- **환경 변수**: 없음
- **기능**: 사고 과정 도구

### Chrome Devtools MCP

- **빌드**: `docker/node-mcp.Dockerfile`
- **환경 변수**: 없음
- **기능**: Chrome 디버깅 도구

## 문제 해결

### 서버가 시작되지 않는 경우

1. 로그 확인:
   ```bash
   docker-compose -f docker-compose.mcp.yml logs [서비스명]
   ```

2. 환경 변수 확인:
   ```bash
   docker-compose -f docker-compose.mcp.yml config
   ```

3. 컨테이너 상태 확인:
   ```bash
   docker-compose -f docker-compose.mcp.yml ps
   ```

### Cursor에서 연결되지 않는 경우

1. Docker 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps | grep mcp-server
   ```

2. 컨테이너 이름이 설정 파일과 일치하는지 확인

3. Cursor IDE 재시작

## 추가 리소스

- [Notion MCP 서버](https://github.com/makenotion/notion-mcp-server)
- [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers)
- [Chrome Devtools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)

