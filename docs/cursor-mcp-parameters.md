# Cursor MCP 설정 매개변수 가이드

## 개요

`cursor-mcp.json` 파일 자체에는 매개변수를 입력할 필요가 없습니다. 대신 **Docker Compose의 `.env.mcp` 파일**에 환경 변수를 설정해야 합니다.

## 필요한 매개변수

### 1. Notion MCP (`notion-mcp`)

**필수 환경 변수:**
- `NOTION_TOKEN`: Notion API 토큰

**설정 방법:**
1. [Notion 통합 페이지](https://www.notion.so/my-integrations)에서 통합 생성
2. 생성된 토큰 복사 (형식: `ntn_...`)
3. `.env.mcp` 파일에 추가:
   ```env
   NOTION_TOKEN=ntn_your_actual_token_here
   ```

### 2. Sequential Thinking MCP (`sequential-thinking-mcp`)

**필요한 매개변수:** 없음

Docker Compose로 실행하면 자동으로 작동합니다.

### 3. Chrome Devtools MCP (`chrome-devtools-mcp`)

**필요한 매개변수:** 없음

Docker Compose로 실행하면 자동으로 작동합니다.

## 설정 파일 생성 방법

1. **환경 변수 파일 생성:**
   ```bash
   cp env.mcp.example .env.mcp
   ```

2. **`.env.mcp` 파일 편집:**
   ```env
   # Notion MCP (필수)
   NOTION_TOKEN=ntn_your_actual_token_here
   ```

3. **Docker Compose로 서버 시작:**
   ```bash
   docker-compose -f docker-compose.mcp.yml up -d
   ```

4. **Cursor 설정 파일 복사:**
   ```bash
   cp cursor-mcp.json ~/.cursor/mcp.json
   ```

## 요약

| MCP 서버 | 필요한 매개변수 | 설정 위치 |
|---------|---------------|----------|
| **notion-mcp** | `NOTION_TOKEN` (필수) | `.env.mcp` |
| **sequential-thinking-mcp** | 없음 | - |
| **chrome-devtools-mcp** | 없음 | - |

## 중요 사항

- `cursor-mcp.json` 파일에는 매개변수를 입력할 필요가 없습니다
- 모든 환경 변수는 `.env.mcp` 파일에서 관리됩니다
- Docker Compose 서버들은 `.env.mcp` 파일의 환경 변수를 자동으로 읽습니다
- `cursor-mcp.json`은 Docker 컨테이너에 연결하는 방법만 정의합니다

