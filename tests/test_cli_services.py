import asyncio

import pytest

from src.tools.aws_tool import AWSService
from src.tools.cli_executor import CLIResult, CLIService
from src.tools.flyio_tool import FlyioService
from src.tools.github_tool import GitHubService


@pytest.mark.asyncio
async def test_cli_service_runs_command():
    service = CLIService(
        "python",
        base_args=["-c"],
        extra_env={"TEST_CLI": "ok"}
    )
    script = "import json, os; print(json.dumps({'value': os.environ['TEST_CLI']}))"
    result = await service.run(script)
    assert result.success is True
    assert result.output["value"] == "ok"


@pytest.mark.asyncio
async def test_aws_service_uses_cli(monkeypatch, tmp_path):
    rc_path = tmp_path / ".zshrc"
    rc_path.write_text("export AWS_PROFILE=test\n", encoding="utf-8")
    monkeypatch.setenv("SHELL_RC_PATH", str(rc_path))

    service = AWSService(profile="test")

    async def fake_run(*args):
        return CLIResult(True, {"account": "123"}, None, "aws sts get-caller-identity")

    service.cli.run = fake_run  # type: ignore[assignment]
    result = await service.get_account_info()
    assert result["output"]["account"] == "123"


@pytest.mark.asyncio
async def test_flyio_service_uses_cli(monkeypatch, tmp_path):
    rc_path = tmp_path / ".zshrc"
    rc_path.write_text("export FLY_API_TOKEN=token\n", encoding="utf-8")
    monkeypatch.setenv("SHELL_RC_PATH", str(rc_path))

    service = FlyioService()

    async def fake_run(*args):
        return CLIResult(True, [{"name": "app"}], None, "flyctl apps list")

    service.cli.run = fake_run  # type: ignore[assignment]
    result = await service.list_apps()
    assert result["output"][0]["name"] == "app"


@pytest.mark.asyncio
async def test_github_service_uses_cli(monkeypatch):
    service = GitHubService()

    async def fake_run(*args):
        return CLIResult(True, [{"nameWithOwner": "owner/repo"}], None, "gh repo list")

    service.cli.run = fake_run  # type: ignore[assignment]
    result = await service.list_repos(owner="owner")
    assert result["output"][0]["nameWithOwner"] == "owner/repo"
