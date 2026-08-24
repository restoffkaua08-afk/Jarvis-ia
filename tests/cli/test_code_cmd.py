"""Tests for the Jarvis Code terminal command."""

from click.testing import CliRunner

from openjarvis.cli.code_cmd import (
    CODE_SYSTEM_PROMPT,
    DEFAULT_CODE_TOOLS,
    build_code_chat_kwargs,
    code,
)


def test_code_help_exposes_terminal_coding_options() -> None:
    result = CliRunner().invoke(code, ["--help"])

    assert result.exit_code == 0
    assert "--model" in result.output
    assert "--engine" in result.output
    assert "--tools" in result.output
    assert "--resume" in result.output
    assert "--new-session" in result.output
    assert "--check" in result.output


def test_code_defaults_to_native_react_and_engineering_tools() -> None:
    kwargs = build_code_chat_kwargs(
        engine_key=None,
        model_name=None,
        tools=None,
        pick_model=False,
        max_turns=30,
        session_file="session.json",
    )

    assert kwargs["agent_name"] == "native_react"
    assert kwargs["tools"] == DEFAULT_CODE_TOOLS
    assert kwargs["system_prompt"] == CODE_SYSTEM_PROMPT
    assert kwargs["voice_mode"] is False
    assert kwargs["agent_max_turns"] == 30
    assert kwargs["model_variant"] == "code"
    assert kwargs["quality_gate"] is True
    assert kwargs["session_file"] == "session.json"


def test_code_tool_set_covers_edit_execute_and_review() -> None:
    enabled = set(DEFAULT_CODE_TOOLS.split(","))

    assert {"file_read", "file_write", "apply_patch"} <= enabled
    assert {"shell_exec", "git_status", "git_diff"} <= enabled


def test_code_prompt_requires_evidence_and_preserves_user_work() -> None:
    assert "Never claim" in CODE_SYSTEM_PROMPT
    assert "Preserve unrelated user changes" in CODE_SYSTEM_PROMPT
    assert "Inspect git_diff" in CODE_SYSTEM_PROMPT
