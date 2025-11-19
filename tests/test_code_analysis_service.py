import pytest

from src.tools.code_analysis_tool import CodeAnalysisService


@pytest.mark.asyncio
async def test_code_analysis_flow_and_matches(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()

    file_a = project / "module_a.py"
    file_a.write_text(
        """import os\n\n\n"""
        "def main():\n    return os.name\n\n\n"""
        "class Sample:\n    def method(self):\n        return 42\n",
        encoding="utf-8"
    )

    file_b = project / "module_b.py"
    file_b.write_text(
        "from module_a import Sample\n\n\n"
        "def helper():\n    return Sample()\n",
        encoding="utf-8"
    )

    service = CodeAnalysisService()

    flow = await service.analyze_code_flow(str(project))
    assert "module_a.py" in "".join(flow["dependencies"].keys())
    assert any(entry["function"] == "main" for entry in flow["entry_points"])

    matches = await service.find_related_code(str(project), target_function="main")
    assert any(match["type"] == "function" for match in matches["matches"])

    reuse = await service.get_code_reusability(str(project))
    assert isinstance(reuse["common_functions"], list)
