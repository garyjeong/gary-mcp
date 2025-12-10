# Gary MCP Server

개인 워크스페이스 관리를 위한 커스텀 MCP (Model Context Protocol) 서버입니다. Cursor IDE에서 사용하는 AI Agent Token을 절약하고, 프로젝트 문서 자동 참조, AWS/Fly.io 인프라 접근, 마크다운 PDF 변환, 코드 분석 기능을 제공합니다.

## 주요 기능

- **프로젝트 문서 자동 참조**: 워크스페이스의 문서를 자동으로 스캔하고 참조하여 개발 언어와 프레임워크 정보를 제공합니다.
- **AWS 인프라 접근**: AWS CLI를 통해 jongmun 프로필로 AWS 리소스를 조회하고 관리합니다.
- **Fly.io 앱 관리**: Fly.io에 배포된 앱의 상태, 로그, 정보를 조회합니다.
- **마크다운 PDF 변환**: 프로젝트의 마크다운 문서를 PDF로 변환합니다.
- **코드 분석**: 프로젝트의 코드 흐름을 분석하고, 연관된 코드를 찾아 재사용 가능한 함수/변수를 식별합니다.
- **MCP 서버 통합**: Cursor에서 사용하는 다른 MCP 서버들을 자동으로 통합하여 단일 서버에서 모든 도구를 사용할 수 있습니다.
  - **sequential-thinking**: 사고 과정 도구
  - **chrome-devtools**: Chrome 디버깅

## 아키텍처

이 프로젝트는 **기능별로 독립적인 MCP 서버**로 구성되어 있습니다. 각 서버는 Docker 컨테이너로 실행되며, 필요한 기능만 선택적으로 사용할 수 있습니다.

### 사용 가능한 독립 서버

- **aws-mcp**: AWS CLI 실행 및 리소스 조회
- **flyio-mcp**: Fly.io 앱 관리
- **github-mcp**: GitHub CLI 실행 및 레포지토리 관리
- **db-mcp**: 데이터베이스 접근 및 쿼리 실행
- **pdf-mcp**: 마크다운→PDF 변환
- **official-docs-mcp**: 공식 문서 미러링 및 검색

## 요구사항

- Python 3.12 이상
- Docker
- AWS CLI (jongmun 프로필 설정 필요)
- Fly.io CLI (선택사항)

## 설치 및 실행

### 방법 1: Docker Compose로 모든 서버 실행 (권장)

```bash
# 모든 MCP 서버를 한 번에 실행
docker-compose -f docker-compose.mcp.yml up -d

# 특정 서버만 실행
docker-compose -f docker-compose.mcp.yml up -d aws-mcp db-mcp

# 서버 중지
docker-compose -f docker-compose.mcp.yml down
```

### 방법 2: 개별 Docker 이미지 빌드 및 실행

각 서버를 독립적으로 빌드하고 실행할 수 있습니다:

```bash
# AWS 서버 빌드 및 실행
docker build -f docker/aws-cli-mcp.Dockerfile -t aws-mcp .
docker run -it --rm \
  -v ~/.aws:/root/.aws:ro \
  -v ~/.zshrc:/root/.zshrc:ro \
  -e AWS_PROFILE=jongmun \
  -e SHELL_RC_PATH=/root/.zshrc \
  aws-mcp
```

**볼륨/환경 설명:**
- `/Users/gary/Documents/workspace:/workspace:ro`: 워크스페이스 디렉토리를 읽기 전용으로 마운트
- `~/.aws:/root/.aws:ro`: AWS 설정 파일을 읽기 전용으로 마운트
- `~/.zshrc:/root/.zshrc:ro`: 호스트 zshrc를 컨테이너에 제공 (AWS/Fly.io 토큰 자동 로드)
- `WORKSPACE_PATH`: 컨테이너 내에서 참조할 워크스페이스 경로
- `SHELL_RC_PATH`: CLI 서비스가 참조할 shell rc 파일 경로(기본 `/root/.zshrc`)

- **환경 변수 구성**
  - `WORKSPACE_PATH`: MCP 서버가 문서를 탐색할 기본 경로. Docker 빌드 시 `--build-arg`, 실행 시 `-e`로 덮어쓸 수 있습니다.
  - `SHELL_RC_PATH`: AWS/Fly.io CLI가 참조할 shell rc 파일 경로. 호스트의 `.zshrc`를 마운트한 뒤 해당 경로를 지정하면 CLI 서비스가 `export AWS_*`, `export FLY_*` 값을 자동 로드합니다.
  - `AWS_PROFILE`, `FLY_*`: 필요한 경우 추가 `-e` 플래그로 주입하거나 `.zshrc`에 `export` 후 마운트하세요.

### 3. 로컬 개발 환경 (Docker 없이)

```bash
# uv 설치
pip install uv

# 의존성 설치
uv pip install -e .

# 서버 실행
python -m src.server
```

## Cursor IDE 연동

### 설정 파일 위치

Cursor IDE의 MCP 설정 파일은 다음 위치에 있습니다:
- **macOS**: `~/.cursor/mcp.json` 또는 `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### 방법 1: Docker를 사용하는 경우 (권장)

Docker 컨테이너로 실행하는 방법입니다. 모든 의존성이 컨테이너에 포함되어 있어 안정적입니다.

```json
{
  "mcpServers": {
    "gary-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/Users/gary/Documents/workspace:/workspace:ro",
        "-v", "/Users/gary/.aws:/root/.aws:ro",
        "-v", "/Users/gary/.zshrc:/root/.zshrc:ro",
        "-v", "/Users/gary/Documents/workspace/gary-mcp/.env:/app/.env:ro",
        "-e", "WORKSPACE_PATH=/workspace",
        "-e", "AWS_PROFILE=jongmun",
        "-e", "SHELL_RC_PATH=/root/.zshrc",
        "gary-mcp-server"
      ]
    }
  }
}
```

**주의사항:**
- Docker 이미지가 먼저 빌드되어 있어야 합니다: `docker build -t gary-mcp-server .`
- `.env` 파일이 있다면 볼륨 마운트로 포함시킬 수 있습니다.

### 방법 2: 로컬 Python 환경을 사용하는 경우

로컬에서 직접 실행하는 방법입니다. 개발 중이거나 Docker 없이 테스트할 때 유용합니다.

```json
{
  "mcpServers": {
    "gary-mcp": {
      "command": "python3",
      "args": [
        "-m",
        "src.server"
      ],
      "cwd": "/Users/gary/Documents/workspace/gary-mcp",
      "env": {
        "WORKSPACE_PATH": "/Users/gary/Documents/workspace",
        "AWS_PROFILE": "jongmun",
        "SHELL_RC_PATH": "/Users/gary/.zshrc"
      }
    }
  }
}
```

**주의사항:**
- 프로젝트 디렉토리에서 의존성이 설치되어 있어야 합니다: `uv pip install -e .`
- `WORKSPACE_PATH`는 절대 경로로 지정하는 것을 권장합니다.

### 방법 3: uv를 사용하는 경우

uv를 통해 가상 환경을 자동으로 관리하면서 실행하는 방법입니다.

```json
{
  "mcpServers": {
    "gary-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/Users/gary/Documents/workspace/gary-mcp",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "WORKSPACE_PATH": "/Users/gary/Documents/workspace",
        "AWS_PROFILE": "jongmun",
        "SHELL_RC_PATH": "/Users/gary/.zshrc"
      }
    }
  }
}
```

### 설정 적용 및 확인

1. **설정 파일에 JSON 추가**: 위의 설정 중 하나를 선택하여 `~/.cursor/mcp.json`에 추가합니다.
2. **Cursor IDE 재시작**: 설정을 저장한 후 Cursor IDE를 완전히 재시작합니다.
3. **연결 확인**: Cursor 왼쪽 사이드바의 MCP 섹션에서 `gary-mcp` 서버가 연결되었는지 확인합니다.
4. **도구 사용**: AI 채팅에서 `list_databases`, `run_query`, `read_document` 등의 도구를 사용할 수 있습니다.

### 환경 변수 설정

#### 워크스페이스 경로
- `WORKSPACE_PATH`: 문서를 탐색할 워크스페이스 경로
  - Docker: 컨테이너 내부 경로 (예: `/workspace`)
  - 로컬: 호스트 절대 경로 (예: `/Users/gary/Documents/workspace`)

#### AWS 설정
- `AWS_PROFILE`: 사용할 AWS 프로필 이름 (기본값: `jongmun`)
- AWS 자격 증명은 `~/.aws` 디렉토리 또는 `.zshrc`의 환경 변수에서 자동으로 로드됩니다.

#### Fly.io 설정
- Fly.io 자격 증명은 `.zshrc`의 `FLY_*` 환경 변수에서 자동으로 로드됩니다.

#### GitHub 설정
- GitHub CLI는 `GH_*`/`GITHUB_*` 환경 변수(`GH_TOKEN`, `GITHUB_TOKEN` 등)를 자동으로 가져옵니다.
- `gh auth login`으로 인증되어 있다면 추가 설정 없이 사용 가능합니다.

#### 데이터베이스 설정
- `.env` 파일 또는 환경 변수로 DB 연결 정보를 설정할 수 있습니다.
- 자세한 내용은 [데이터베이스 연결 오류](#데이터베이스-연결-오류) 섹션을 참조하세요.

## 공식 문서 미러링

LLM이 인터넷 없이도 공식 문서를 사용할 수 있도록 `docs/manifest.yaml`에 정의된 소스를 로컬에 캐시합니다. `type: git`, `type: archive` 외에도 `type: http` 항목으로 AWS/Python/FastAPI/Docker/Kubernetes/Fly.io/PostgreSQL/Redis/Next.js/Tailwind CSS와 같은 문서 메인 URL을 바로 관리할 수 있습니다.

### 1. 문서 동기화

```bash
# 모든 문서를 동기화
python scripts/sync_docs.py

# 특정 문서만 동기화 (예시)
python scripts/sync_docs.py python fastapi aws-main docker-main
```

- Python, FastAPI, React, TypeScript, Go, AWS, Docker, Kubernetes, Fly.io, PostgreSQL, Redis, Next.js, Tailwind CSS 문서를 기본으로 포함하고 있습니다.
- 결과는 `docs/mirror/<이름>/<버전>` 구조로 저장되며, `.gitignore`에 의해 저장소 커밋 대상에서 제외됩니다.

### 2. HTTP 기반 문서 정의

`type: http` 항목은 간단히 이름과 URL만으로 정의할 수 있습니다.

```yaml
- name: python-main
  type: http
  version: "3.x"
  target: python/main
  pages:
    - url: https://docs.python.org/3/
```

- `pages`: manifest 항목 안에서 직접 URL 목록을 정의합니다. `path`를 생략하면 URL 경로를 기반으로 자동으로 파일명이 결정됩니다.
- `pages_file`: 필요한 경우 `docs/` 기준 JSON/YAML 파일로 URL 목록을 따로 관리할 수 있습니다. (테스트 예시는 `docs/pages/python-main.yaml` 참고)
- 각 페이지 정의는 최소 `url`과 저장할 상대 경로(`path`)를 포함합니다. 경로가 없으면 URL을 기반으로 `index.html` 등을 자동 생성합니다.
- 기본 제공 HTTP 문서 목록
  - `aws-main`: https://docs.aws.amazon.com/
  - `python-main`: https://docs.python.org/3/
  - `fastapi-main`: https://fastapi.tiangolo.com/
  - `docker-main`: https://docs.docker.com/
  - `kubernetes-main`: https://kubernetes.io/docs/home/
  - `flyio-main`: https://fly.io/docs/
  - `postgresql-main`: https://www.postgresql.org/docs/current/index.html
  - `redis-main`: https://redis.io/docs/latest/
  - `nextjs-main`: https://nextjs.org/docs
  - `tailwindcss-main`: https://tailwindcss.com/docs

### 3. MCP 도구

- `sync_official_docs`: MCP 내부에서 문서를 동기화합니다 (`names` 배열로 특정 문서만 선택 가능).
- `list_official_docs`: 현재 캐시된 문서 목록과 버전을 조회합니다.
- `search_official_docs`: 미러된 공식 문서를 빠르게 검색합니다 (`name`으로 범위를 제한할 수 있음).

### 4. DocumentService 연동

`WORKSPACE_PATH=/Users/gary/Documents/workspace`로 설정하면 `docs/mirror`가 자동으로 인덱싱되므로 기존 `read_document`/`search_documents` 도구에서도 공식 문서를 참조할 수 있습니다. 새로운 문서를 추가하려면 `docs/manifest.yaml`에 항목을 추가한 뒤 `scripts/sync_docs.py`를 실행하면 됩니다.

## 사용 가능한 도구

### 문서 관련 도구

#### `read_document`
워크스페이스의 문서 파일을 읽습니다.

**파라미터:**
- `file_path` (필수): 읽을 문서 파일의 경로

**예시:**
```json
{
  "file_path": "/workspace/my-project/README.md"
}
```

#### `list_workspace_projects`
워크스페이스의 프로젝트 목록을 스캔합니다.

**예시:**
```json
{}
```

#### `search_documents`
워크스페이스의 문서에서 검색합니다.

**파라미터:**
- `query` (필수): 검색할 키워드
- `project_name` (선택): 특정 프로젝트 내에서만 검색

**예시:**
```json
{
  "query": "FastAPI",
  "project_name": "my-api-project"
}
```

### AWS 관련 도구

#### `aws_cli_execute`
AWS CLI 명령을 실행합니다 (jongmun 프로필 사용).

**파라미터:**
- `service` (필수): AWS 서비스 이름 (예: s3, ec2, lambda)
- `operation` (필수): 작업 이름 (예: list, describe-instances)
- `additional_args` (선택): 추가 인자 목록

**예시:**
```json
{
  "service": "s3",
  "operation": "ls"
}
```

#### `aws_list_resources`
AWS 리소스 목록을 조회합니다.

**파라미터:**
- `service` (필수): AWS 서비스 이름
- `resource_type` (선택): 리소스 타입

**예시:**
```json
{
  "service": "ec2",
  "resource_type": "instances"
}
```

#### `aws_get_account_info`
AWS 계정 정보를 조회합니다.

**예시:**
```json
{}
```

### Fly.io 관련 도구

#### `flyio_list_apps`
Fly.io 앱 목록을 조회합니다.

**예시:**
```json
{}
```

#### `flyio_get_app_status`
Fly.io 앱 상태를 조회합니다.

**파라미터:**
- `app_name` (필수): 앱 이름

**예시:**
```json
{
  "app_name": "my-app"
}
```

#### `flyio_get_app_logs`
Fly.io 앱 로그를 조회합니다.

**파라미터:**
- `app_name` (필수): 앱 이름
- `lines` (선택): 조회할 로그 라인 수 (기본값: 50)

**예시:**
```json
{
  "app_name": "my-app",
  "lines": 100
}
```

### GitHub 관련 도구

#### `github_cli_execute`
GitHub CLI 명령을 직접 실행합니다.

**파라미터:**
- `command` (필수): 실행할 하위 커맨드 (예: `"repo"`, `"issue"`, `"pr"`)
- `args` (선택): 추가 인자 배열

#### `github_list_repos`
레포지토리 목록을 조회합니다.

**파라미터:**
- `owner` (선택): 특정 사용자/조직
- `visibility` (선택): `public`, `private`, `internal`
- `limit` (선택): 조회할 레포 수 (기본값 20)
- `sort` (선택): 정렬 기준 (기본값 `updated`)

#### `github_list_pull_requests`
지정 레포지토리의 PR을 조회합니다.

**파라미터:**
- `repo` (필수): `owner/repo` 형식
- `state` (선택): `open`, `closed`, `all` (기본 `open`)
- `limit` (선택): 결과 수 (기본값 20)

#### `github_list_issues`
지정 레포지토리의 이슈를 조회합니다.

**파라미터:**
- `repo` (필수)
- `state` (선택): `open`, `closed`, `all`
- `limit` (선택): 결과 수 (기본값 20)

### PDF 변환 도구

#### `markdown_to_pdf`
마크다운 파일을 PDF로 변환합니다.

**파라미터:**
- `markdown_path` (필수): 변환할 마크다운 파일 경로
- `output_path` (선택): 출력 PDF 파일 경로
- `css_path` (선택): CSS 스타일 파일 경로

**예시:**
```json
{
  "markdown_path": "/workspace/my-project/README.md",
  "output_path": "/workspace/my-project/README.pdf"
}
```

### 코드 분석 도구

#### `analyze_code_flow`
프로젝트의 코드 흐름을 분석합니다.

**파라미터:**
- `project_path` (필수): 분석할 프로젝트 경로
- `entry_point` (선택): 진입점 파일

**예시:**
```json
{
  "project_path": "/workspace/my-project",
  "entry_point": "main.py"
}
```

#### `find_related_code`
연관된 코드를 찾습니다.

**파라미터:**
- `project_path` (필수): 검색할 프로젝트 경로
- `target_function` (선택): 찾을 함수 이름
- `target_class` (선택): 찾을 클래스 이름
- `target_import` (선택): 찾을 import 모듈 이름

**예시:**
```json
{
  "project_path": "/workspace/my-project",
  "target_function": "process_data"
}
```

#### `get_code_reusability`
코드 재사용성을 분석합니다.

**파라미터:**
- `project_path` (필수): 분석할 프로젝트 경로
- `language` (선택): 프로그래밍 언어 (기본값: python)

**예시:**
```json
{
  "project_path": "/workspace/my-project",
  "language": "python"
}
```

### 데이터베이스 관련 도구

#### `list_databases`
데이터베이스 목록을 조회합니다.

**파라미터:**
- `db_name` (선택): DB 이름
- `connection_string` (선택): 직접 연결 문자열 (예: `postgresql+asyncpg://user:pass@host:5432/db`)
- `use_dotenv` (선택): .env 파일 사용 (기본값: true)
- `use_aws_secrets` (선택): AWS Secrets Manager 사용
- `aws_secret_name` (선택): AWS 시크릿 이름
- `use_github_secrets` (선택): GitHub Secrets 사용
- `github_secret_name` (선택): GitHub 시크릿 이름
- `github_repo` (선택): GitHub 저장소

**예시:**
```json
{
  "connection_string": "postgresql+asyncpg://user:pass@localhost:5432/mydb"
}
```

#### `describe_tables`
테이블 스키마를 조회합니다.

**파라미터:**
- `db_name` (선택): DB 이름
- `connection_string` (선택): 직접 연결 문자열
- `database` (선택): 특정 데이터베이스 이름
- `use_dotenv`, `use_aws_secrets`, `aws_secret_name`, `use_github_secrets`, `github_secret_name`, `github_repo` (선택): 자격 증명 소스

**예시:**
```json
{
  "connection_string": "sqlite+aiosqlite:///./test.db"
}
```

#### `run_query`
SQL 쿼리를 실행합니다 (기본 read-only, 필요시 read-write 모드 지정).

**파라미터:**
- `query` (필수): 실행할 SQL 쿼리
- `db_name` (선택): DB 이름
- `connection_string` (선택): 직접 연결 문자열
- `parameters` (선택): 쿼리 파라미터 (dict)
- `limit` (선택): 결과 행 수 제한 (기본값: 100)
- `mode` (선택): 실행 모드 - `read_only` 또는 `read_write` (기본값: `read_only`)
- `use_dotenv`, `use_aws_secrets`, `aws_secret_name`, `use_github_secrets`, `github_secret_name`, `github_repo` (선택): 자격 증명 소스

**예시:**
```json
{
  "query": "SELECT * FROM users WHERE id = :id",
  "parameters": {"id": 1},
  "connection_string": "postgresql+asyncpg://user:pass@localhost:5432/mydb",
  "mode": "read_only"
}
```

**주의사항:**
- 기본 모드는 `read_only`이며, INSERT/UPDATE/DELETE 등의 쓰기 작업은 차단됩니다.
- 쓰기 작업이 필요한 경우 `mode: "read_write"`를 명시적으로 지정해야 합니다.
- 환경 변수나 `.env` 파일에서 `DATABASE_URL` 또는 개별 DB 파라미터를 설정할 수 있습니다.
- AWS Secrets Manager나 GitHub Secrets를 사용하여 자격 증명을 안전하게 관리할 수 있습니다.

### 공식 문서 도구

#### `sync_official_docs`
공식 문서를 로컬에 동기화합니다.

**파라미터:**
- `names` (선택): 동기화할 문서 이름 배열
- `force` (선택): 향후 확장용 플래그 (기본 false)

#### `list_official_docs`
현재 미러된 공식 문서 목록을 반환합니다.

#### `search_official_docs`
미러된 문서에서 키워드를 검색합니다.

**파라미터:**
- `query` (필수): 검색 키워드
- `name` (선택): 특정 문서 이름
- `limit` (선택): 결과 수 제한 (기본 5)
- `structured` (선택): `true` 시 파서/인덱스 기반 섹션 검색

#### `resolve_library_id`
라이브러리 이름으로 ID와 메타데이터를 조회합니다.

**파라미터:**
- `name` (필수): 예) react, next.js, typescript, python, spring, mysql

#### `list_libraries`
지원 라이브러리 목록을 반환합니다.

**파라미터:**
- `category` (선택): framework | language | orm | database | cloud
- `available_only` (선택): 동기화 가능한 항목만 필터

#### `get_library_docs`
Context7 스타일로 라이브러리 문서를 조회합니다.

**파라미터:**
- `library_id` (필수): 예) `/libraries/react`
- `mode` (선택): `info` | `code` (기본 info)
- `topic` (선택): 특정 주제 키워드 (예: hooks, routing)
- `limit` (선택): 검색 결과 제한 (기본 5, topic 지정 시 적용)

## MCP 서버 통합

gary-mcp는 Cursor에서 사용하는 다른 MCP 서버들을 자동으로 통합합니다. 이를 통해 단일 MCP 서버에서 모든 도구를 사용할 수 있습니다.

### 자동 통합

gary-mcp는 다음 위치의 설정 파일을 자동으로 읽어 외부 MCP 서버를 통합합니다:

1. `~/.cursor/mcp.json`
2. `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
3. 프로젝트의 `cursor-mcp-local.json`

### 통합된 MCP 서버

다음 MCP 서버들이 자동으로 통합됩니다 (설정 파일에 정의된 경우):

- **sequential-thinking**: 사고 과정 도구 (도구 이름: `thinking_*`)
- **chrome-devtools**: Chrome 디버깅 (도구 이름: `chrome_*`)

### 네임스페이스

외부 MCP 서버의 도구는 네임스페이스 접두사가 자동으로 추가되어 이름 충돌을 방지합니다. 예를 들어:

- `sequential-thinking`의 도구는 `thinking_` 접두사가 추가됩니다
- `chrome-devtools`의 도구는 `chrome_` 접두사가 추가됩니다

### 통합 비활성화

특정 MCP 서버의 통합을 비활성화하려면, 해당 서버를 설정 파일에서 제거하거나 `gary-mcp` 서버만 사용하도록 설정하세요.

## 프로젝트 구조

```
gary-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # 통합 MCP 서버 (레거시)
│   ├── servers/               # 독립적인 MCP 서버들
│   │   ├── __init__.py
│   │   ├── base_server.py     # 공통 서버 베이스 클래스
│   │   ├── aws_server.py       # AWS 서버
│   │   ├── flyio_server.py    # Fly.io 서버
│   │   ├── github_server.py   # GitHub 서버
│   │   ├── db_server.py       # 데이터베이스 서버
│   │   ├── pdf_server.py      # PDF 변환 서버
│   │   └── official_docs_server.py  # 공식 문서 서버
│   ├── tools/                 # 도구 서비스 클래스들
│   │   ├── __init__.py
│   │   ├── document_tool.py   # 문서 참조 도구
│   │   ├── aws_tool.py        # AWS CLI 도구
│   │   ├── flyio_tool.py      # Fly.io 도구
│   │   ├── pdf_tool.py        # 마크다운→PDF 변환
│   │   ├── code_analysis_tool.py  # 코드 분석 도구
│   │   └── db_tool.py         # 데이터베이스 접근 도구
│   ├── infrastructure/
│   │   └── db/
│   │       └── connection_manager.py  # DB 연결 관리
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py      # 파일 유틸리티
│       └── env_loader.py      # 환경 변수/시크릿 로더
├── docker/                    # 각 서버용 Dockerfile
│   ├── base.Dockerfile        # 공통 베이스
│   ├── aws-cli-mcp.Dockerfile
│   ├── flyio-mcp.Dockerfile
│   ├── github-cli-mcp.Dockerfile
│   ├── db-mcp.Dockerfile
│   ├── pdf-mcp.Dockerfile
│   └── official-docs-mcp.Dockerfile
├── docker-compose.mcp.yml     # 모든 서버를 위한 Docker Compose 설정
├── tests/
│   ├── __init__.py
│   ├── test_document_service.py
│   ├── test_pdf_service.py
│   ├── test_code_analysis_service.py
│   ├── test_cli_services.py
│   └── test_db_tool.py        # DB 도구 테스트
├── pyproject.toml             # uv 프로젝트 설정
├── Dockerfile                 # 통합 서버용 Docker 이미지 (레거시)
├── .dockerignore              # Docker 빌드 제외 파일
├── .env.example               # 환경 변수 예시
└── README.md                  # 이 파일
```

## 기술 스택

- **Python 3.12**: 최신 Python 버전 사용
- **uv**: 빠른 Python 패키지 관리자
- **MCP SDK**: Model Context Protocol Python SDK
- **asyncio**: 비동기 파일/프로세스 처리
- **SQLAlchemy**: ORM 및 DB 연결 관리
- **asyncpg/aiomysql/aiosqlite**: 비동기 DB 드라이버
- **weasyprint**: 마크다운→PDF 변환
- **AWS CLI**: AWS 리소스 관리
- **Fly.io CLI**: Fly.io 앱 관리
- **boto3**: AWS Secrets Manager 연동
- **python-dotenv**: .env 파일 로딩

## 트러블슈팅

### AWS CLI 오류

**문제**: AWS CLI 명령이 실패합니다.

**해결 방법:**
1. AWS 프로필이 올바르게 설정되어 있는지 확인:
   ```bash
   aws configure list --profile jongmun
   ```
2. Docker 컨테이너에 AWS 설정 파일이 마운트되었는지 확인:
   ```bash
   docker run -it --rm -v ~/.aws:/root/.aws:ro gary-mcp-server ls /root/.aws
   ```

### Fly.io CLI 오류

**문제**: Fly.io 명령이 실패합니다.

**해결 방법:**
1. Fly.io CLI가 컨테이너에 설치되어 있는지 확인:
   ```bash
   docker run -it --rm gary-mcp-server flyctl version
   ```
2. Fly.io 인증이 필요할 수 있습니다:
   ```bash
   docker run -it --rm gary-mcp-server flyctl auth login
   ```

### PDF 변환 오류

**문제**: 마크다운→PDF 변환이 실패합니다.

**해결 방법:**
1. WeasyPrint 의존성 라이브러리가 설치되어 있는지 확인
2. 마크다운 파일 경로가 올바른지 확인
3. 출력 디렉토리에 쓰기 권한이 있는지 확인

### 워크스페이스 접근 오류

**문제**: 워크스페이스 파일에 접근할 수 없습니다.

**해결 방법:**
1. Docker 볼륨 마운트가 올바르게 설정되었는지 확인
2. 파일 경로가 `/workspace`로 시작하는지 확인 (Docker 컨테이너 내부 경로)

### 데이터베이스 연결 오류

**문제**: DB 연결이 실패합니다.

**해결 방법:**
1. 환경 변수나 `.env` 파일에 올바른 연결 정보가 설정되었는지 확인:
   ```bash
   # .env 파일 예시
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
   # 또는
   DB_TYPE=postgresql
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=user
   DB_PASSWORD=password
   DB_NAME=dbname
   ```
2. AWS Secrets Manager 사용 시:
   - IAM 권한이 올바르게 설정되었는지 확인
   - `aws_secret_name`이 정확한지 확인
3. GitHub Secrets 사용 시:
   - `gh auth login`으로 인증이 완료되었는지 확인
   - 저장소에 대한 접근 권한이 있는지 확인
4. Docker 컨테이너에서 로컬 DB에 접근하는 경우:
   - `--network host` 옵션 사용 또는 포트 포워딩 설정

### 공식 문서 동기화 오류

**문제**: `sync_official_docs` 또는 `scripts/sync_docs.py` 실행 시 실패합니다.

**해결 방법:**
1. `git`, `tar`, `zip` 등이 시스템에 설치되어 있는지 확인합니다.
2. 인터넷/프록시 설정을 확인하고 필요한 경우 `HTTPS_PROXY` 환경 변수를 설정합니다.
3. `docs/manifest.yaml`의 URL과 브랜치가 유효한지 확인합니다.
4. 캐시를 초기화하려면 `rm -rf docs/mirror docs/sources` 후 다시 동기화합니다.

## 개발

### 로컬 개발 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd gary-mcp

# uv 설치
pip install uv

# 의존성 설치
uv pip install -e .

# 서버 실행
python -m src.server
```

### 코드 스타일

- Python 3.12+ 기능 활용
- 비동기 작업은 `async/await` 사용
- 타입 힌트 사용 권장
- 함수와 클래스에 docstring 작성

## 라이선스

이 프로젝트는 개인 사용 목적으로 개발되었습니다.

## 기여

이 프로젝트는 개인 프로젝트이지만, 버그 리포트나 개선 제안은 환영합니다.

