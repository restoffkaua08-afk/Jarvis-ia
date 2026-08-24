"""Regression tests for capability enforcement at tool dispatch."""

from __future__ import annotations

from typing import Any

from openjarvis.core.types import ToolCall, ToolResult
from openjarvis.tools._stubs import BaseTool, ToolExecutor, ToolSpec
from openjarvis.tools.file_read import FileReadTool


class _MappedToolWithoutLocalCapabilities(BaseTool):
    """Model a built-in that relies on the central capability registry."""

    tool_id = "file_read"

    def __init__(self) -> None:
        self.executed = False

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="file_read",
            description="Capability fallback regression stub.",
            parameters={"type": "object", "properties": {}},
        )

    def execute(self, **params: Any) -> ToolResult:
        self.executed = True
        return ToolResult(
            tool_name="file_read",
            content="executed",
            success=True,
        )


class _RecordingPolicy:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.checks: list[tuple[str, str, str]] = []

    def check(self, agent_id: str, capability: str, resource: str) -> bool:
        self.checks.append((agent_id, capability, resource))
        return self.allowed


def test_file_read_declares_its_capability() -> None:
    assert FileReadTool().spec.required_capabilities == ["file:read"]


def test_executor_enforces_central_capability_fallback() -> None:
    tool = _MappedToolWithoutLocalCapabilities()
    policy = _RecordingPolicy(allowed=False)
    executor = ToolExecutor(
        [tool],
        capability_policy=policy,
        agent_id="restricted-agent",
    )

    result = executor.execute(
        ToolCall(id="call-1", name="file_read", arguments="{}")
    )

    assert result.success is False
    assert "file:read" in result.content
    assert tool.executed is False
    assert policy.checks == [
        ("restricted-agent", "file:read", "file_read")
    ]


def test_executor_runs_mapped_tool_when_capability_is_allowed() -> None:
    tool = _MappedToolWithoutLocalCapabilities()
    policy = _RecordingPolicy(allowed=True)
    executor = ToolExecutor(
        [tool],
        capability_policy=policy,
        agent_id="reader-agent",
    )

    result = executor.execute(
        ToolCall(id="call-2", name="file_read", arguments="{}")
    )

    assert result.success is True
    assert tool.executed is True
    assert policy.checks == [
        ("reader-agent", "file:read", "file_read")
    ]
