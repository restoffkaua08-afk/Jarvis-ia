"""Strong-model selection for Jarvis Code without reading secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class StrongModelSelection:
    """Resolved cloud engine and model identifier."""

    engine: str
    model: str
    provider: str
    credential_variable: str


_CANDIDATES = (
    ("OPENAI_API_KEY", "openai", "gpt-5.4"),
    ("ANTHROPIC_API_KEY", "anthropic", "claude-opus-4-6"),
    ("GEMINI_API_KEY", "google", "gemini-3.1-pro-preview"),
    ("GOOGLE_API_KEY", "google", "gemini-3.1-pro-preview"),
    ("OPENROUTER_API_KEY", "openrouter", "openrouter/auto"),
)


def select_strong_code_model(
    environment: Mapping[str, str] | None = None,
) -> StrongModelSelection | None:
    """Choose the strongest configured code provider by credential presence."""

    values = os.environ if environment is None else environment
    for variable, provider, model in _CANDIDATES:
        if values.get(variable, "").strip():
            return StrongModelSelection(
                engine="cloud",
                model=model,
                provider=provider,
                credential_variable=variable,
            )
    return None


def strong_model_setup_hint() -> str:
    """Return instructions that name variables but never request secret output."""

    variables = ", ".join(item[0] for item in _CANDIDATES)
    return (
        "No strong cloud model credential is configured. Set one of these "
        f"environment variables on the machine running Jarvis: {variables}. "
        "Do not paste API keys into chat, source files, Git commits or logs."
    )


__all__ = [
    "StrongModelSelection",
    "select_strong_code_model",
    "strong_model_setup_hint",
]
