"""Tests for GitHub skill repository tools."""

from __future__ import annotations

import pytest

from openjarvis.tools.skill_repo import (
    SkillRepoInspectTool,
    SkillRepoInstallTool,
    normalize_github_repo_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/example/skills",
        "https://gitlab.com/example/skills",
        "file:///tmp/skills",
        "https://github.com/example",
        "https://github.com/example/skills/extra",
        "https://user:token@github.com/example/skills",
        "https://github.com/example/skills?ref=main",
    ],
)
def test_rejects_unsafe_or_non_repository_urls(url: str) -> None:
    with pytest.raises(ValueError):
        normalize_github_repo_url(url)


def test_normalizes_public_github_repository_url() -> None:
    normalized, cache_key = normalize_github_repo_url(
        "https://github.com/example/skills"
    )

    assert normalized == "https://github.com/example/skills.git"
    assert cache_key.startswith("example-skills-")


def test_inspection_is_read_only_but_network_scoped() -> None:
    spec = SkillRepoInspectTool().spec

    assert spec.requires_confirmation is False
    assert spec.required_capabilities == ["network:fetch"]


def test_installation_requires_confirmation_and_admin_scope() -> None:
    spec = SkillRepoInstallTool().spec

    assert spec.requires_confirmation is True
    assert "file:write" in spec.required_capabilities
    assert "system:admin" in spec.required_capabilities
    assert "network:fetch" in spec.required_capabilities
