"""Tests for the isolated Jarvis Code engineering benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openjarvis.cli.code_benchmark import (
    evaluate_code_benchmark,
    prepare_code_benchmark,
)


def test_prepared_benchmark_starts_failing(tmp_path: Path) -> None:
    workspace = prepare_code_benchmark(tmp_path)

    report = evaluate_code_benchmark(workspace.path)

    assert report.score == 0
    assert report.passed is False
    assert report.changed_files == ()


def test_fixed_benchmark_passes_with_machine_readable_report(
    tmp_path: Path,
) -> None:
    workspace = prepare_code_benchmark(tmp_path)
    target = workspace.path / "calculator.py"
    target.write_text(
        target.read_text(encoding="utf-8").replace(
            "return left + right\n",
            "return left + right\n",
            1,
        ).replace(
            "    return left + right\n",
            "    return left - right\n",
            1,
        ),
        encoding="utf-8",
    )

    report = evaluate_code_benchmark(workspace.path)
    payload = json.loads(report.to_json())

    assert report.passed is True
    assert report.score == 100
    assert report.changed_files == ("calculator.py",)
    assert payload["tests_passed"] is True


def test_benchmark_rejects_unprepared_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Not a prepared"):
        evaluate_code_benchmark(tmp_path)


def test_benchmark_detects_out_of_scope_change(tmp_path: Path) -> None:
    workspace = prepare_code_benchmark(tmp_path)
    (workspace.path / "notes.txt").write_text("unexpected\n", encoding="utf-8")

    report = evaluate_code_benchmark(workspace.path)

    assert report.diff_present is True
    assert report.scope_clean is False
    assert report.passed is False
