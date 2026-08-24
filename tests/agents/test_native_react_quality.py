"""Quality-gate tests for NativeReActAgent coding sessions."""

from __future__ import annotations

from unittest.mock import MagicMock

from openjarvis.agents.native_react import NativeReActAgent
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec


class _SuccessTool(BaseTool):
    def __init__(self, name: str) -> None:
        self.tool_id = name

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=f"Stub {self.tool_id}.",
            parameters={"type": "object", "properties": {}},
        )

    def execute(self, **params) -> ToolResult:
        return ToolResult(
            tool_name=self.tool_id,
            content="ok",
            success=True,
        )


def _response(content: str) -> dict:
    return {
        "content": content,
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
        },
    }


def test_quality_gate_requires_checks_after_project_edit() -> None:
    engine = MagicMock()
    engine.engine_id = "mock"
    engine.generate.side_effect = [
        _response(
            "Thought: edit\nAction: apply_patch\nAction Input: {}"
        ),
        _response("Thought: done\nFinal Answer: complete"),
        _response(
            "Thought: test\nAction: shell_exec\nAction Input: {}"
        ),
        _response(
            "Thought: review\nAction: git_diff\nAction Input: {}"
        ),
        _response("Thought: verified\nFinal Answer: complete"),
    ]
    tools = [
        _SuccessTool("apply_patch"),
        _SuccessTool("shell_exec"),
        _SuccessTool("git_diff"),
    ]
    agent = NativeReActAgent(
        engine,
        "test-model",
        tools=tools,
        max_turns=6,
        quality_gate=True,
    )

    result = agent.run("Implement feature")

    assert engine.generate.call_count == 5
    assert result.content == "complete"
    assert result.metadata["quality_gate_passed"] is True
    assert result.metadata["quality_gate_missing"] == []


def test_quality_gate_does_not_force_tools_for_advice_only() -> None:
    engine = MagicMock()
    engine.engine_id = "mock"
    engine.generate.return_value = _response(
        "Thought: explain\nFinal Answer: guidance"
    )
    agent = NativeReActAgent(
        engine,
        "test-model",
        quality_gate=True,
    )

    result = agent.run("Explain this architecture")

    assert engine.generate.call_count == 1
    assert result.content == "guidance"
    assert result.metadata["quality_gate_passed"] is True


def test_quality_gate_reports_missing_verification_at_budget_end() -> None:
    engine = MagicMock()
    engine.engine_id = "mock"
    engine.generate.side_effect = [
        _response(
            "Thought: edit\nAction: file_write\nAction Input: {}"
        ),
        _response("Thought: done\nFinal Answer: unverified"),
    ]
    agent = NativeReActAgent(
        engine,
        "test-model",
        tools=[_SuccessTool("file_write")],
        max_turns=2,
        quality_gate=True,
    )

    result = agent.run("Implement feature")

    assert result.metadata["quality_gate_passed"] is False
    assert "shell_exec" in result.metadata["quality_gate_missing"][0]
    assert "git_diff" in result.metadata["quality_gate_missing"][1]
