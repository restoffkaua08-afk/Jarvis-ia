"""Diagnostics for the Jarvis Code terminal workflow."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CodeCheck:
    """One actionable Jarvis Code diagnostic result."""

    name: str
    status: str
    message: str


def run_code_checks(
    project: Path,
    *,
    config: Any | None = None,
) -> list[CodeCheck]:
    """Check project, model routing, tools, Git and engine availability."""
    checks: list[CodeCheck] = []
    project = project.resolve()

    if project.is_dir():
        checks.append(CodeCheck("Project", "ok", str(project)))
    else:
        checks.append(CodeCheck("Project", "fail", "Directory does not exist"))

    git = shutil.which("git")
    if git is None:
        checks.append(CodeCheck("Git", "fail", "git is not available on PATH"))
    elif (project / ".git").exists():
        checks.append(CodeCheck("Git", "ok", "Repository detected"))
    else:
        checks.append(CodeCheck("Git", "warn", "Directory is not a Git repository"))

    if config is None:
        try:
            from openjarvis.core.config import load_config

            config = load_config()
        except Exception as exc:
            checks.append(CodeCheck("Configuration", "fail", str(exc)))
            return checks

    code_model = (config.intelligence.model_code or "").strip()
    default_model = (config.intelligence.default_model or "").strip()
    if code_model:
        checks.append(CodeCheck("Code model", "ok", code_model))
    elif default_model:
        checks.append(
            CodeCheck(
                "Code model",
                "warn",
                f"model_code is unset; using default_model {default_model}",
            )
        )
    else:
        checks.append(CodeCheck("Code model", "fail", "No model configured"))

    from openjarvis.cli.code_cmd import DEFAULT_CODE_TOOLS
    from openjarvis.core.registry import ToolRegistry

    import openjarvis.tools  # noqa: F401

    required_tools = DEFAULT_CODE_TOOLS.split(",")
    missing = [name for name in required_tools if not ToolRegistry.contains(name)]
    if missing:
        checks.append(
            CodeCheck("Coding tools", "fail", "Missing: " + ", ".join(missing))
        )
    else:
        checks.append(
            CodeCheck(
                "Coding tools",
                "ok",
                f"{len(required_tools)} required tools registered",
            )
        )

    try:
        from openjarvis.engine import get_engine

        resolved = get_engine(config, None)
        if resolved is None:
            checks.append(CodeCheck("Engine", "fail", "No engine available"))
        else:
            engine_name, engine = resolved
            if engine.health():
                checks.append(CodeCheck("Engine", "ok", f"{engine_name} reachable"))
            else:
                checks.append(
                    CodeCheck("Engine", "fail", f"{engine_name} unreachable")
                )
    except Exception as exc:
        checks.append(CodeCheck("Engine", "fail", str(exc)))

    return checks


__all__ = ["CodeCheck", "run_code_checks"]
