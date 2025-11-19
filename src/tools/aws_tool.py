"""AWS CLI service for executing AWS commands with jongmun profile."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from src.tools.cli_executor import CLIService
from src.utils.env_loader import load_shell_env


class AWSService:
    """AWS 관련 기능을 캡슐화한 서비스."""

    def __init__(
        self,
        profile: str = "jongmun",
        env_prefixes: Sequence[str] | None = ("AWS_",),
        env_keys: Sequence[str] | None = ("AWS_PROFILE",)
    ) -> None:
        extra_env = load_shell_env(prefixes=env_prefixes, keys=env_keys)
        self.cli = CLIService(
            "aws",
            base_args=["--profile", profile],
            json_flag=["--output", "json"],
            extra_env=extra_env
        )

    async def execute(
        self,
        service: str,
        operation: Optional[str] = None,
        additional_args: Optional[Sequence[str]] = None
    ) -> Dict[str, Any]:
        args = [service]
        if operation:
            args.append(operation)
        if additional_args:
            args.extend(additional_args)

        result = await self.cli.run(*args)
        return result.to_dict()

    async def list_resources(self, service: str, resource_type: Optional[str] = None) -> Dict[str, Any]:
        operation = "list" if not resource_type else f"list-{resource_type}"
        return await self.execute(service, operation)

    async def describe_resource(
        self,
        service: str,
        resource_id: str,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        operation = "describe" if not resource_type else f"describe-{resource_type}"
        return await self.execute(service, operation, [resource_id])

    async def get_account_info(self) -> Dict[str, Any]:
        return await self.execute("sts", "get-caller-identity")

    async def list_s3_buckets(self) -> Dict[str, Any]:
        return await self.execute("s3", "ls")

    async def list_ec2_instances(self) -> Dict[str, Any]:
        return await self.execute("ec2", "describe-instances")
