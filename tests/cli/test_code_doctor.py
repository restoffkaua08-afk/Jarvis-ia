"""Tests for Jarvis Code preflight diagnostics."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from openjarvis.cli.code_doctor import run_code_checks


def _config(*, code_model: str = "coder-model") -> SimpleNamespace:
    return SimpleNamespace(
        intelligence=SimpleNamespace(
            model_code=code_model,
            default_model="fallback-model",
        )
    )


def test_code_checks_report_specialized_model_and_engine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    engine = MagicMock()
    engine.health.return_value = True

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(
        "openjarvis.engine.get_engine",
        lambda config, key: ("mock", engine),
    )

    checks = run_code_checks(project, config=_config())
    by_name = {check.name: check for check in checks}

    assert by_name["Project"].status == "ok"
    assert by_name["Git"].status == "ok"
    assert by_name["Code model"].status == "ok"
    assert by_name["Coding tools"].status == "ok"
    assert by_name["Engine"].status == "ok"


def test_code_checks_warn_when_using_default_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    engine = MagicMock()
    engine.health.return_value = True

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(
        "openjarvis.engine.get_engine",
        lambda config, key: ("mock", engine),
    )

    checks = run_code_checks(project, config=_config(code_model=""))
    code_model = next(check for check in checks if check.name == "Code model")

    assert code_model.status == "warn"
    assert "default_model" in code_model.message
