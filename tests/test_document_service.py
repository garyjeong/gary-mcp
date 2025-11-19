import asyncio

import pytest

from src.tools.document_tool import DocumentService


@pytest.mark.asyncio
async def test_document_service_scan_and_read(tmp_path):
    workspace = tmp_path / "workspace"
    project = workspace / "alpha"
    project.mkdir(parents=True)

    readme = project / "README.md"
    readme.write_text("Alpha project", encoding="utf-8")

    doc = project / "guide.md"
    doc.write_text("FastAPI guide", encoding="utf-8")

    service = DocumentService(workspace_path=workspace, max_documents=5)

    projects = await service.scan_projects()
    assert len(projects) == 1
    assert projects[0]["has_readme"] is True
    assert doc.as_posix() in projects[0]["document_files"]

    read_result = await service.read_document(str(doc))
    assert read_result["success"] is True
    assert "FastAPI" in read_result["content"]

    search_results = await service.search_documents("fastapi")
    assert len(search_results) == 1
    assert search_results[0]["file_path"].endswith("guide.md")
