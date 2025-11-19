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
