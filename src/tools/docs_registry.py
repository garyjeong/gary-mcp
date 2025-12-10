"""라이브러리 레지스트리: 이름→ID 매핑 및 메타데이터 관리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True, slots=True)
class LibraryMeta:
    """라이브러리 메타데이터."""

    id: str  # 예: /libraries/react
    name: str  # 예: react
    category: str  # framework, library, orm, database, cloud 등
    source_type: str  # official_site | github | http | unsupported
    manifest_name: Optional[str] = None  # manifest.yaml docs 항목 이름
    docs_url: Optional[str] = None  # 공식 문서 URL
    repo: Optional[str] = None  # GitHub repo
    available: bool = True  # 동기화 가능 여부


class DocsRegistry:
    """라이브러리 메타데이터 조회."""

    def __init__(self) -> None:
        self._by_name: Dict[str, LibraryMeta] = {}
        self._init_registry()

    def _init_registry(self) -> None:
        # manifest.yaml에 이미 존재하거나 곧 추가할 대상 위주
        entries: List[LibraryMeta] = [
            # JS/TS
            LibraryMeta("/libraries/nodejs", "node.js", "runtime", "http", docs_url="https://nodejs.org/docs", available=False),
            LibraryMeta("/libraries/nextjs", "next.js", "framework", "http", manifest_name="nextjs-main", docs_url="https://nextjs.org/docs"),
            LibraryMeta("/libraries/nestjs", "nestjs", "framework", "http", docs_url="https://docs.nestjs.com", available=False),
            LibraryMeta("/libraries/react", "react", "framework", "git", manifest_name="react", repo="https://github.com/reactjs/react.dev"),
            LibraryMeta("/libraries/vue", "vue", "framework", "http", docs_url="https://vuejs.org/guide", available=False),
            LibraryMeta("/libraries/typescript", "typescript", "language", "git", manifest_name="typescript", repo="https://github.com/microsoft/TypeScript-Website"),
            # Python
            LibraryMeta("/libraries/python", "python", "language", "archive", manifest_name="python"),
            LibraryMeta("/libraries/flask", "flask", "framework", "http", docs_url="https://flask.palletsprojects.com", available=False),
            LibraryMeta("/libraries/fastapi", "fastapi", "framework", "git", manifest_name="fastapi"),
            LibraryMeta("/libraries/django", "django", "framework", "http", docs_url="https://docs.djangoproject.com/en/stable/", available=False),
            # Java
            LibraryMeta("/libraries/java", "java", "language", "http", docs_url="https://docs.oracle.com/en/java/", available=False),
            LibraryMeta("/libraries/spring", "spring", "framework", "http", docs_url="https://docs.spring.io/spring-framework/reference/", available=False),
            # ORM
            LibraryMeta("/libraries/typeorm", "typeorm", "orm", "http", docs_url="https://typeorm.io/", available=False),
            LibraryMeta("/libraries/prisma", "prisma", "orm", "http", docs_url="https://www.prisma.io/docs", available=False),
            # DB
            LibraryMeta("/libraries/mysql", "mysql", "database", "http", docs_url="https://dev.mysql.com/doc/", available=False),
            LibraryMeta("/libraries/postgresql", "postgresql", "database", "http", manifest_name="postgresql-main", docs_url="https://www.postgresql.org/docs/current/index.html"),
            # Cloud
            LibraryMeta("/libraries/aws", "aws", "cloud", "http", manifest_name="aws-main", docs_url="https://docs.aws.amazon.com/"),
        ]
        for entry in entries:
            self._by_name[entry.name.lower()] = entry
            # 별칭 처리
            alias = entry.name.replace(".", "").lower()
            self._by_name.setdefault(alias, entry)

    def resolve(self, name: str) -> Optional[LibraryMeta]:
        """라이브러리 이름을 메타데이터로 변환."""
        key = name.strip().lower()
        return self._by_name.get(key)

    def list_all(self, category: Optional[str] = None, available_only: bool = False) -> List[LibraryMeta]:
        metas = list(self._by_name.values())
        if category:
            metas = [m for m in metas if m.category == category]
        if available_only:
            metas = [m for m in metas if m.available]
        # 중복 제거(별칭 방지)
        seen = set()
        deduped = []
        for meta in metas:
            if meta.id in seen:
                continue
            seen.add(meta.id)
            deduped.append(meta)
        return deduped


registry = DocsRegistry()


__all__ = ["LibraryMeta", "DocsRegistry", "registry"]

