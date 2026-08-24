"""Tests for secure strong-model selection in Jarvis Code."""

from __future__ import annotations

from openjarvis.cli.code_model import (
    select_strong_code_model,
    strong_model_setup_hint,
)


def test_strong_model_prefers_openai_when_multiple_keys_exist() -> None:
    selection = select_strong_code_model(
        {
            "OPENAI_API_KEY": "secret-a",
            "ANTHROPIC_API_KEY": "secret-b",
        }
    )

    assert selection is not None
    assert selection.engine == "cloud"
    assert selection.provider == "openai"
    assert selection.model == "gpt-5.4"
    assert selection.credential_variable == "OPENAI_API_KEY"


def test_strong_model_supports_anthropic() -> None:
    selection = select_strong_code_model({"ANTHROPIC_API_KEY": "secret"})

    assert selection is not None
    assert selection.model == "claude-opus-4-6"


def test_strong_model_supports_google_alias() -> None:
    selection = select_strong_code_model({"GOOGLE_API_KEY": "secret"})

    assert selection is not None
    assert selection.provider == "google"
    assert selection.credential_variable == "GOOGLE_API_KEY"


def test_strong_model_ignores_blank_credentials() -> None:
    assert select_strong_code_model({"OPENAI_API_KEY": "  "}) is None


def test_setup_hint_never_contains_credential_values() -> None:
    hint = strong_model_setup_hint()

    assert "OPENAI_API_KEY" in hint
    assert "Do not paste API keys" in hint
    assert "secret" not in hint.lower()
