"""Secure, project-scoped persistence for Jarvis Code conversations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from openjarvis.core.paths import get_config_dir
from openjarvis.core.types import Message, Role
from openjarvis.security.file_utils import secure_write_json

SESSION_VERSION = 1
MAX_SESSION_MESSAGES = 200
MAX_SESSION_BYTES = 2 * 1024 * 1024


def canonical_project_path(project: Path | str) -> Path:
    """Return an absolute project path without requiring a Git repository."""
    return Path(project).expanduser().resolve()


def session_path_for_project(project: Path | str) -> Path:
    """Return the stable private session file for a project directory."""
    canonical = canonical_project_path(project)
    digest = hashlib.sha256(str(canonical).encode("utf-8")).hexdigest()
    return get_config_dir() / "code-sessions" / f"{digest[:24]}.json"


def _serialize_messages(messages: Iterable[Message]) -> list[dict[str, str]]:
    allowed = {Role.USER, Role.ASSISTANT}
    serialized = [
        {"role": message.role.value, "content": message.text}
        for message in messages
        if message.role in allowed and message.text
    ]
    return serialized[-MAX_SESSION_MESSAGES:]


def save_project_session(
    project: Path | str,
    messages: Iterable[Message],
    *,
    path: Path | None = None,
) -> Path:
    """Atomically save owner-only conversation history for one project."""
    canonical = canonical_project_path(project)
    target = path or session_path_for_project(canonical)
    payload = {
        "version": SESSION_VERSION,
        "project_path": str(canonical),
        "updated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "messages": _serialize_messages(messages),
    }
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_SESSION_BYTES:
        payload["messages"] = payload["messages"][-50:]
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_SESSION_BYTES:
        raise ValueError("Code session exceeds the safe persistence limit")
    return secure_write_json(target, payload)


def load_project_session(
    project: Path | str,
    *,
    path: Path | None = None,
) -> list[Message]:
    """Load a session only when its version and canonical project match."""
    canonical = canonical_project_path(project)
    target = path or session_path_for_project(canonical)
    if not target.exists():
        return []
    if target.stat().st_size > MAX_SESSION_BYTES:
        raise ValueError("Refusing oversized code session file")
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("version") != SESSION_VERSION:
        raise ValueError("Unsupported code session version")
    if payload.get("project_path") != str(canonical):
        raise ValueError("Code session belongs to a different project")

    result: list[Message] = []
    for raw in payload.get("messages", [])[-MAX_SESSION_MESSAGES:]:
        if not isinstance(raw, dict):
            continue
        role_value = raw.get("role")
        content = raw.get("content")
        if role_value not in {Role.USER.value, Role.ASSISTANT.value}:
            continue
        if not isinstance(content, str) or not content:
            continue
        result.append(Message(role=Role(role_value), content=content))
    return result


def clear_project_session(
    project: Path | str,
    *,
    path: Path | None = None,
) -> None:
    """Delete only the current project's resolved session file."""
    target = path or session_path_for_project(project)
    target.unlink(missing_ok=True)


__all__ = [
    "MAX_SESSION_BYTES",
    "MAX_SESSION_MESSAGES",
    "SESSION_VERSION",
    "canonical_project_path",
    "clear_project_session",
    "load_project_session",
    "save_project_session",
    "session_path_for_project",
]
