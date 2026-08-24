"""RBAC capability system — fine-grained permission model for tool dispatch."""

from __future__ import annotations

import fnmatch
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Capability(str, Enum):
    """Fine-grained capability labels."""

    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    NETWORK_FETCH = "network:fetch"
    CODE_EXECUTE = "code:execute"
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    CHANNEL_SEND = "channel:send"
    TOOL_INVOKE = "tool:invoke"
    SCHEDULE_CREATE = "schedule:create"
    SYSTEM_ADMIN = "system:admin"


@dataclass(slots=True)
class CapabilityGrant:
    """A single capability grant for an agent."""

    capability: str  # Capability value or glob pattern
    pattern: str = "*"  # resource glob pattern


@dataclass(slots=True)
class AgentPolicy:
    """Policy for a specific agent."""

    agent_id: str
    grants: List[CapabilityGrant] = field(default_factory=list)
    deny: List[str] = field(default_factory=list)  # explicit denials


class CapabilityPolicy:
    """RBAC capability policy for tool dispatch.

    Checks whether an agent has the required capability to invoke a tool.
    Policy can be loaded from a JSON file or configured programmatically.

    Default policy: if no explicit policy exists for an agent, all
    capabilities are granted (open by default). Set ``default_deny=True``
    to flip to deny-by-default.
    """

    def __init__(
        self,
        *,
        policy_path: Optional[str] = None,
        default_deny: bool = False,
    ) -> None:
        self._policies: Dict[str, AgentPolicy] = {}
        self._default_deny = default_deny

        from openjarvis._rust_bridge import get_rust_module

        _rust = get_rust_module()
        self._rust_impl = _rust.CapabilityPolicy(default_deny=default_deny)

        if policy_path:
            self._load_file(Path(policy_path))

    def grant(self, agent_id: str, capability: str, pattern: str = "*") -> None:
        """Grant a capability to an agent."""
        policy = self._policies.setdefault(
            agent_id,
            AgentPolicy(agent_id=agent_id),
        )
        policy.grants.append(CapabilityGrant(capability=capability, pattern=pattern))
        self._rust_impl.grant(agent_id, capability, pattern)

    def deny(self, agent_id: str, capability: str) -> None:
        """Explicitly deny a capability to an agent."""
        policy = self._policies.setdefault(
            agent_id,
            AgentPolicy(agent_id=agent_id),
        )
        policy.deny.append(capability)
        self._rust_impl.deny(agent_id, capability)

    def check(self, agent_id: str, capability: str, resource: str = "") -> bool:
        """Check whether *agent_id* has *capability* for *resource*.

        Returns True if allowed, False if denied.
        """
        return self._rust_impl.check(agent_id, capability, resource)

    def _check_python(self, agent_id: str, capability: str, resource: str = "") -> bool:
        """Legacy Python check — kept for reference only."""
        policy = self._policies.get(agent_id)
        if policy is None:
            # No explicit policy — use default
            return not self._default_deny

        # Explicit denials take precedence
        for denied in policy.deny:
            if fnmatch.fnmatch(capability, denied):
                return False

        # Check grants
        for grant in policy.grants:
            if fnmatch.fnmatch(capability, grant.capability):
                if resource and grant.pattern != "*":
                    if fnmatch.fnmatch(resource, grant.pattern):
                        return True
                else:
                    return True

        # No matching grant found
        return not self._default_deny

    def list_grants(self, agent_id: str) -> List[CapabilityGrant]:
        """List all grants for an agent."""
        policy = self._policies.get(agent_id)
        return list(policy.grants) if policy else []

    def list_agents(self) -> List[str]:
        """List all agents with explicit policies."""
        return list(self._policies.keys())

    def _load_file(self, path: Path) -> None:
        """Load policy from a JSON file."""
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
            for agent_data in data.get("agents", []):
                agent_id = agent_data["agent_id"]
                for grant_data in agent_data.get("grants", []):
                    self.grant(
                        agent_id,
                        grant_data["capability"],
                        grant_data.get("pattern", "*"),
                    )
                for denied in agent_data.get("deny", []):
                    self.deny(agent_id, denied)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Failed to parse capability policy: %s", exc)

    def save(self, path: Path) -> None:
        """Save policy to a JSON file."""
        agents = []
        for agent_id, policy in self._policies.items():
            agents.append(
                {
                    "agent_id": agent_id,
                    "grants": [
                        {"capability": g.capability, "pattern": g.pattern}
                        for g in policy.grants
                    ],
                    "deny": policy.deny,
                }
            )
        path.write_text(json.dumps({"agents": agents}, indent=2))


# Default capability requirements for built-in tools
DEFAULT_TOOL_CAPABILITIES: Dict[str, List[str]] = {
    # Filesystem and version-control access
    "file_read": [Capability.FILE_READ],
    "pdf_extract": [Capability.FILE_READ],
    "audio_transcribe": [Capability.FILE_READ],
    "git_status": [Capability.FILE_READ],
    "git_diff": [Capability.FILE_READ],
    "git_log": [Capability.FILE_READ],
    "file_write": [Capability.FILE_WRITE],
    "apply_patch": [Capability.FILE_WRITE],
    "git_commit": [Capability.FILE_WRITE],

    # Network, browser, and externally hosted media
    "web_search": [Capability.NETWORK_FETCH],
    "http_request": [Capability.NETWORK_FETCH],
    "browser_navigate": [Capability.NETWORK_FETCH],
    "browser_click": [Capability.NETWORK_FETCH],
    "browser_type": [Capability.NETWORK_FETCH],
    "browser_screenshot": [Capability.NETWORK_FETCH],
    "browser_extract": [Capability.NETWORK_FETCH],
    "browser_axtree": [Capability.NETWORK_FETCH],
    "image_generate": [Capability.NETWORK_FETCH],

    # Code, shell, database, and REPL execution
    "code_interpreter": [Capability.CODE_EXECUTE],
    "code_interpreter_docker": [Capability.CODE_EXECUTE],
    "shell_exec": [Capability.CODE_EXECUTE],
    "docker_shell_exec": [Capability.CODE_EXECUTE],
    "repl": [Capability.CODE_EXECUTE],
    "db_query": [Capability.CODE_EXECUTE],

    # Working memory and knowledge stores
    "memory_store": [Capability.MEMORY_WRITE],
    "memory_index": [Capability.MEMORY_WRITE],
    "memory_retrieve": [Capability.MEMORY_READ],
    "memory_search": [Capability.MEMORY_READ],
    "retrieval": [Capability.MEMORY_READ],
    "knowledge_search": [Capability.MEMORY_READ],
    "knowledge_sql": [Capability.MEMORY_READ],
    "scan_chunks": [Capability.MEMORY_READ],
    "kg_add_entity": [Capability.MEMORY_WRITE],
    "kg_add_relation": [Capability.MEMORY_WRITE],
    "kg_query": [Capability.MEMORY_READ],
    "kg_neighbors": [Capability.MEMORY_READ],

    # Communication, scheduling, and agent administration
    "channel_send": [Capability.CHANNEL_SEND],
    "schedule_task": [Capability.SCHEDULE_CREATE],
    "agent_spawn": [Capability.SYSTEM_ADMIN],
    "agent_send": [Capability.SYSTEM_ADMIN],
    "agent_list": [Capability.SYSTEM_ADMIN],
    "agent_kill": [Capability.SYSTEM_ADMIN],
    "skill_manage": [Capability.SYSTEM_ADMIN, Capability.FILE_WRITE],
}


__all__ = [
    "AgentPolicy",
    "Capability",
    "CapabilityGrant",
    "CapabilityPolicy",
    "DEFAULT_TOOL_CAPABILITIES",
]
