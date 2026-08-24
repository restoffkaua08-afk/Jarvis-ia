"""Tests for project-scoped Jarvis Code sessions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openjarvis.cli.code_session import (
    clear_project_session,
    load_project_session,
    save_project_session,
    session_path_for_project,
)
from openjarvis.core.types import Message, Role


def test_project_session_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENJARVIS_HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    messages = [
        Message(role=Role.SYSTEM, content="fresh prompt only"),
        Message(role=Role.USER, content="Implement feature"),
        Message(role=Role.ASSISTANT, content="Done"),
    ]

    target = save_project_session(project, messages)
    restored = load_project_session(project)

    assert target == session_path_for_project(project)
    assert [message.role for message in restored] == [
        Role.USER,
        Role.ASSISTANT,
    ]
    assert [message.content for message in restored] == [
        "Implement feature",
        "Done",
    ]


def test_session_refuses_different_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENJARVIS_HOME", str(tmp_path / "home"))
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    target = save_project_session(
        first,
        [Message(role=Role.USER, content="private context")],
    )

    with pytest.raises(ValueError, match="different project"):
        load_project_session(second, path=target)


def test_session_refuses_unsupported_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENJARVIS_HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    target = session_path_for_project(project)
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(
            {
                "version": 999,
                "project_path": str(project.resolve()),
                "messages": [],
            }
        )
    )

    with pytest.raises(ValueError, match="Unsupported"):
        load_project_session(project)


def test_clear_removes_only_resolved_project_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENJARVIS_HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    target = save_project_session(
        project,
        [Message(role=Role.USER, content="hello")],
    )

    clear_project_session(project)

    assert not target.exists()
