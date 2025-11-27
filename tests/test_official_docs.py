import json
import tarfile
from pathlib import Path

from src.tools.official_docs import OfficialDocsService

def create_sample_archive(base_dir: Path) -> Path:
    sample_dir = base_dir / "sample"
    sample_dir.mkdir(parents=True)
    (sample_dir / "index.md").write_text("Hello Official Docs", encoding="utf-8")
    archive_path = base_dir / "sample.tar"
    with tarfile.open(archive_path, "w") as tar:
        tar.add(sample_dir, arcname="sample")
    return archive_path


def test_official_docs_sync_and_search(tmp_path):
    base_dir = tmp_path
    docs_dir = base_dir / "docs"
    docs_dir.mkdir()

    archive_path = create_sample_archive(tmp_path)
    manifest = {
        "docs": [
            {
                "name": "sample",
                "type": "archive",
                "version": "test",
                "url": archive_path.as_uri(),
                "archive_format": "tar",
                "strip_components": 1,
                "target": "sample/test"
            }
        ]
    }
    manifest_path = docs_dir / "manifest.yaml"
    import yaml
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    service = OfficialDocsService(base_dir=base_dir)
    result = service.sync_docs()
    assert result["success"] is True

    listing = service.list_docs()
    assert listing["count"] == 1
    assert listing["docs"][0]["name"] == "sample"

    matches = service.search_docs("hello")
    assert matches["count"] >= 1
    assert "Hello Official Docs" in matches["matches"][0]["snippet"]


def test_official_docs_http_sync(tmp_path):
    base_dir = tmp_path
    docs_dir = base_dir / "docs"
    docs_dir.mkdir()
    pages_dir = docs_dir / "pages"
    pages_dir.mkdir()

    html_source = tmp_path / "http.html"
    html_source.write_text("<html><body>HTTP Doc Page</body></html>", encoding="utf-8")

    pages_payload = {
        "pages": [
            {
                "url": html_source.as_uri(),
                "path": "index.html"
            }
        ]
    }
    pages_file = pages_dir / "http-docs.json"
    pages_file.write_text(json.dumps(pages_payload), encoding="utf-8")

    manifest = {
        "docs": [
            {
                "name": "http-sample",
                "type": "http",
                "version": "test",
                "target": "http/test",
                "pages_file": f"pages/{pages_file.name}"
            }
        ]
    }

    import yaml
    manifest_path = docs_dir / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    service = OfficialDocsService(base_dir=base_dir)
    result = service.sync_docs()
    assert result["success"] is True

    stored_file = service.mirror_dir / "http/test/index.html"
    assert stored_file.exists()
    assert "HTTP Doc Page" in stored_file.read_text(encoding="utf-8")

    matches = service.search_docs("http doc")
    assert matches["count"] >= 1
