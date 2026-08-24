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
            "    # Intentional benchmark defect.\n"
            "    return left + right\n",
            "    # Fixed by the benchmark participant.\n"
            "    return left - right\n",
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

def test_multifile_profile_requires_every_contract_change(tmp_path: Path) -> None:
    workspace = prepare_code_benchmark(tmp_path, profile="multifile")
    validator = workspace.path / "validators.py"
    validator.write_text(
        validator.read_text(encoding="utf-8").replace(
            "return email.lower()",
            "return email.strip().lower()",
        ),
        encoding="utf-8",
    )

    report = evaluate_code_benchmark(workspace.path)

    assert report.tests_passed is False
    assert report.required_changes_present is False
    assert report.missing_required_files == ("user_service.py",)
    assert report.passed is False


def test_multifile_profile_passes_only_after_coherent_repair(
    tmp_path: Path,
) -> None:
    workspace = prepare_code_benchmark(tmp_path, profile="multifile")
    validator = workspace.path / "validators.py"
    service = workspace.path / "user_service.py"
    validator.write_text(
        validator.read_text(encoding="utf-8").replace(
            "return email.lower()",
            "return email.strip().lower()",
        ),
        encoding="utf-8",
    )
    service.write_text(
        service.read_text(encoding="utf-8").replace(
            '"active": "yes"',
            '"active": True',
        ),
        encoding="utf-8",
    )

    report = evaluate_code_benchmark(workspace.path)

    assert report.profile == "multifile"
    assert report.score == 100
    assert report.passed is True
    assert report.changed_files == ("user_service.py", "validators.py")


def test_unknown_benchmark_profile_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown benchmark profile"):
        prepare_code_benchmark(tmp_path, profile="unknown")

