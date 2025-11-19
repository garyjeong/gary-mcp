from pathlib import Path

import pytest

from src.tools.pdf_tool import PDFService, WEASYPRINT_IMPORT_ERROR


@pytest.mark.skipif(WEASYPRINT_IMPORT_ERROR is not None, reason="WeasyPrint dependencies missing")
@pytest.mark.asyncio
async def test_pdf_service_generates_pdf(tmp_path):
    markdown_path = tmp_path / "notes.md"
    markdown_path.write_text("# Title\nThis is a sample.", encoding="utf-8")

    service = PDFService()
    result = await service.convert(str(markdown_path))

    assert result["success"] is True
    output_path = Path(result["output_path"])
    assert output_path.exists()
    assert output_path.suffix == ".pdf"
