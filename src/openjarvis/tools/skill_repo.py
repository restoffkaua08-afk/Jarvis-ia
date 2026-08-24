"""Inspect and install OpenJarvis skills from public GitHub repositories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from openjarvis.core.paths import get_config_dir
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.skills.importer import SkillImporter
from openjarvis.skills.parser import SkillParser
from openjarvis.skills.security import has_dangerous_capabilities
from openjarvis.skills.sources.base import ResolvedSkill
from openjarvis.skills.sources.github import GitHubResolver
from openjarvis.skills.tool_translator import ToolTranslator
from openjarvis.tools._stubs import BaseTool, ToolSpec


def normalize_github_repo_url(repo_url: str) -> tuple[str, str]:
    """Validate a public GitHub repository URL and return URL plus cache key."""
    parsed = urlparse(repo_url.strip())
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Only https://github.com/<owner>/<repo> URLs are allowed")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("GitHub URLs with credentials or custom ports are refused")
    if parsed.query or parsed.fragment:
        raise ValueError("GitHub repository URL must not contain query or fragment")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or any(part in {".", ".."} for part in parts):
        raise ValueError("Expected a GitHub repository URL with owner and repo")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        raise ValueError("GitHub owner and repository name are required")
    normalized = f"https://github.com/{owner}/{repo}.git"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return normalized, f"{owner}-{repo}-{digest}"


def _resolver_for_url(repo_url: str) -> tuple[GitHubResolver, str]:
    normalized, cache_key = normalize_github_repo_url(repo_url)
    cache = get_config_dir() / "skill-cache" / "github" / cache_key
    return GitHubResolver(cache_root=cache, repo_url=normalized), normalized


def _read_frontmatter(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}
    rest = raw[3:].lstrip("\n")
    end = rest.find("\n---")
    if end < 0:
        return {}
    parsed = yaml.safe_load(rest[:end])
    return parsed if isinstance(parsed, dict) else {}


def _skill_report(resolved: ResolvedSkill) -> dict[str, Any]:
    skill_md = resolved.path / "SKILL.md"
    if not skill_md.exists():
        skill_md = resolved.path / "skill.md"
    report: dict[str, Any] = {
        "name": resolved.name,
        "category": resolved.category,
        "description": resolved.description,
        "commit": resolved.commit,
        "scripts_present": (resolved.path / "scripts").exists(),
        "valid_manifest": False,
        "dangerous_capabilities": [],
        "parse_error": "",
    }
    try:
        frontmatter = _read_frontmatter(skill_md)
        manifest = SkillParser().parse_frontmatter(frontmatter)
        report["valid_manifest"] = True
        report["dangerous_capabilities"] = has_dangerous_capabilities(manifest)
        report["required_capabilities"] = list(manifest.required_capabilities)
    except Exception as exc:
        report["parse_error"] = str(exc)
    return report


def inspect_repository(repo_url: str) -> dict[str, Any]:
    """Synchronize and statically inspect every discoverable skill."""
    resolver, normalized = _resolver_for_url(repo_url)
    resolver.sync()
    skills = resolver.list_skills()
    return {
        "repository": normalized,
        "skill_count": len(skills),
        "skills": [_skill_report(skill) for skill in skills],
        "policy": {
            "scripts_imported_by_default": False,
            "dangerous_capabilities_require_explicit_approval": True,
        },
    }


def _select_skill(
    skills: list[ResolvedSkill],
    skill_name: str,
) -> ResolvedSkill:
    if skill_name:
        matches = [skill for skill in skills if skill.name == skill_name]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one skill named {skill_name!r}; found {len(matches)}"
            )
        return matches[0]
    if len(skills) != 1:
        raise ValueError(
            "Repository contains multiple skills; provide the exact skill_name"
        )
    return skills[0]


@ToolRegistry.register("skill_repo_inspect")
class SkillRepoInspectTool(BaseTool):
    """Inspect skills in a public GitHub repository without installing them."""

    tool_id = "skill_repo_inspect"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "Clone or update a public GitHub skill repository in cache, "
                "then report skills, scripts and requested capabilities. "
                "Always use this before skill_repo_install."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "Public https://github.com/owner/repo URL.",
                    }
                },
                "required": ["repo_url"],
            },
            category="skill",
            timeout_seconds=180.0,
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            report = inspect_repository(str(params.get("repo_url", "")))
            return ToolResult(
                tool_name=self.tool_id,
                success=True,
                content=json.dumps(report, ensure_ascii=False, indent=2),
                metadata=report,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.tool_id,
                success=False,
                content=f"Skill repository inspection failed: {exc}",
            )


@ToolRegistry.register("skill_repo_install")
class SkillRepoInstallTool(BaseTool):
    """Install one previously reviewed skill from a GitHub repository."""

    tool_id = "skill_repo_install"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "Install one skill from a public GitHub repository. Inspect "
                "first. Scripts and dangerous capabilities require explicit "
                "arguments and interactive confirmation."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string"},
                    "skill_name": {"type": "string"},
                    "with_scripts": {
                        "type": "boolean",
                        "default": False,
                    },
                    "allow_dangerous": {
                        "type": "boolean",
                        "default": False,
                    },
                    "force": {
                        "type": "boolean",
                        "default": False,
                    },
                },
                "required": ["repo_url"],
            },
            category="skill",
            requires_confirmation=True,
            timeout_seconds=180.0,
            required_capabilities=[
                "network:fetch",
                "file:write",
                "system:admin",
            ],
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            resolver, normalized = _resolver_for_url(
                str(params.get("repo_url", ""))
            )
            resolver.sync()
            selected = _select_skill(
                resolver.list_skills(),
                str(params.get("skill_name", "")),
            )
            report = _skill_report(selected)
            if not report["valid_manifest"]:
                raise ValueError(
                    "Skill manifest is invalid: " + report["parse_error"]
                )
            dangerous = report["dangerous_capabilities"]
            allow_dangerous = bool(params.get("allow_dangerous", False))
            if dangerous and not allow_dangerous:
                raise ValueError(
                    "Skill requests dangerous capabilities "
                    f"{dangerous}; review the inspection report and explicitly "
                    "set allow_dangerous=true only after user approval"
                )

            importer = SkillImporter(
                parser=SkillParser(),
                tool_translator=ToolTranslator(),
            )
            result = importer.import_skill(
                selected,
                with_scripts=bool(params.get("with_scripts", False)),
                force=bool(params.get("force", False)),
                confirm_dangerous=allow_dangerous,
            )
            payload = {
                "repository": normalized,
                "skill": selected.name,
                "commit": selected.commit,
                "success": result.success,
                "skipped": result.skipped,
                "target_path": (
                    str(result.target_path) if result.target_path else ""
                ),
                "scripts_imported": result.scripts_imported,
                "trust_tier": result.trust_tier.value,
                "dangerous_capabilities": result.dangerous_capabilities,
                "translated_tools": result.translated_tools,
                "untranslated_tools": result.untranslated_tools,
                "warnings": result.warnings,
            }
            return ToolResult(
                tool_name=self.tool_id,
                success=result.success,
                content=json.dumps(payload, ensure_ascii=False, indent=2),
                metadata=payload,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.tool_id,
                success=False,
                content=f"Skill repository installation failed: {exc}",
            )


__all__ = [
    "SkillRepoInspectTool",
    "SkillRepoInstallTool",
    "inspect_repository",
    "normalize_github_repo_url",
]
