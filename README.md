# Gary MCP Server

개인 워크스페이스 관리를 위한 커스텀 MCP (Model Context Protocol) 서버입니다. Cursor IDE에서 사용하는 AI Agent Token을 절약하고, 프로젝트 문서 자동 참조, AWS/Fly.io 인프라 접근, 마크다운 PDF 변환, 코드 분석 기능을 제공합니다.

## 주요 기능

- **프로젝트 문서 자동 참조**: 워크스페이스의 문서를 자동으로 스캔하고 참조하여 개발 언어와 프레임워크 정보를 제공합니다.
- **AWS 인프라 접근**: AWS CLI를 통해 jongmun 프로필로 AWS 리소스를 조회하고 관리합니다.
- **Fly.io 앱 관리**: Fly.io에 배포된 앱의 상태, 로그, 정보를 조회합니다.
- **마크다운 PDF 변환**: 프로젝트의 마크다운 문서를 PDF로 변환합니다.
- **코드 분석**: 프로젝트의 코드 흐름을 분석하고, 연관된 코드를 찾아 재사용 가능한 함수/변수를 식별합니다.

## 요구사항

- Python 3.12 이상
- Docker
- AWS CLI (jongmun 프로필 설정 필요)
- Fly.io CLI (선택사항)

## 설치 및 실행

### 1. Docker 이미지 빌드

```bash
# 기본값(/workspace)을 그대로 사용
docker build -t gary-mcp-server .

# 또는 워크스페이스 기본 경로를 빌드 시 지정
docker build --build-arg WORKSPACE_PATH=/workspace -t gary-mcp-server .
```

### 2. Docker 컨테이너 실행

```bash
docker run -it --rm \
  -v /Users/gary/Documents/workspace:/workspace:ro \
  -v ~/.aws:/root/.aws:ro \
  -v ~/.zshrc:/root/.zshrc:ro \
  -e WORKSPACE_PATH=/workspace \
  -e AWS_PROFILE=jongmun \
  -e SHELL_RC_PATH=/root/.zshrc \
  gary-mcp-server
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

### 1. Cursor 설정 파일 생성

Cursor IDE의 설정 파일에 MCP 서버를 추가합니다:

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
        "-e", "WORKSPACE_PATH=/workspace",
        "-e", "AWS_PROFILE=jongmun",
        "-e", "SHELL_RC_PATH=/root/.zshrc",
        "gary-mcp-server"
      ]
    }
  }
}
```

### 2. Cursor 재시작

설정을 저장한 후 Cursor IDE를 재시작하면 MCP 서버가 연결됩니다.

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

## 프로젝트 구조

```
gary-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP 서버 메인 진입점
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── document_tool.py   # 문서 참조 도구
│   │   ├── aws_tool.py        # AWS CLI 도구
│   │   ├── flyio_tool.py      # Fly.io 도구
│   │   ├── pdf_tool.py        # 마크다운→PDF 변환
│   │   └── code_analysis_tool.py  # 코드 분석 도구
│   └── utils/
│       ├── __init__.py
│       └── file_utils.py      # 파일 유틸리티
├── pyproject.toml             # uv 프로젝트 설정
├── Dockerfile                 # Docker 이미지 정의
├── .dockerignore              # Docker 빌드 제외 파일
└── README.md                  # 이 파일
```

## 기술 스택

- **Python 3.12**: 최신 Python 버전 사용
- **uv**: 빠른 Python 패키지 관리자
- **MCP SDK**: Model Context Protocol Python SDK
- **asyncio**: 비동기 파일/프로세스 처리
- **weasyprint**: 마크다운→PDF 변환
- **AWS CLI**: AWS 리소스 관리
- **Fly.io CLI**: Fly.io 앱 관리

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

