"""Tests for RBAC capabilities system (Phase 14.4)."""

from __future__ import annotations

from openjarvis.security.capabilities import (
    DEFAULT_TOOL_CAPABILITIES,
    Capability,
    CapabilityPolicy,
    build_tool_scoped_policy,
)


class TestCapability:
    def test_capability_values(self):
        assert Capability.FILE_READ == "file:read"
        assert Capability.NETWORK_FETCH == "network:fetch"
        assert Capability.CODE_EXECUTE == "code:execute"
        assert Capability.SYSTEM_ADMIN == "system:admin"

    def test_all_capabilities_exist(self):
        expected = {
            "file:read",
            "file:write",
            "network:fetch",
            "code:execute",
            "memory:read",
            "memory:write",
            "channel:send",
            "tool:invoke",
            "schedule:create",
            "system:admin",
        }
        actual = {c.value for c in Capability}
        assert expected == actual


class TestCapabilityPolicy:
    def test_default_allow(self):
        policy = CapabilityPolicy()
        assert policy.check("agent1", "file:read")
        assert policy.check("agent1", "code:execute")

    def test_python_fallback_when_rust_extension_is_unavailable(
        self,
        monkeypatch,
    ):
        from openjarvis import _rust_bridge

        def _unavailable():
            raise ImportError("native extension not installed")

        monkeypatch.setattr(_rust_bridge, "get_rust_module", _unavailable)

        policy = CapabilityPolicy(default_deny=True)
        policy.grant("reader", "file:read", "/workspace/*")
        policy.deny("reader", "file:write")

        assert policy._rust_impl is None
        assert policy.check("reader", "file:read", "/workspace/data.txt")
        assert not policy.check("reader", "file:read", "/etc/passwd")
        assert not policy.check("reader", "file:write", "/workspace/data.txt")

    def test_default_deny(self):
        policy = CapabilityPolicy(default_deny=True)
        assert not policy.check("agent1", "file:read")

    def test_explicit_grant(self):
        policy = CapabilityPolicy(default_deny=True)
        policy.grant("agent1", "file:read")
        assert policy.check("agent1", "file:read")
        assert not policy.check("agent1", "code:execute")

    def test_explicit_deny(self):
        policy = CapabilityPolicy()
        policy.deny("agent1", "code:execute")
        assert not policy.check("agent1", "code:execute")
        assert policy.check("agent1", "file:read")

    def test_deny_overrides_grant(self):
        policy = CapabilityPolicy()
        policy.grant("agent1", "code:execute")
        policy.deny("agent1", "code:execute")
        assert not policy.check("agent1", "code:execute")

    def test_resource_pattern(self):
        policy = CapabilityPolicy(default_deny=True)
        policy.grant("agent1", "file:read", pattern="/safe/*")
        assert policy.check("agent1", "file:read", "/safe/data.txt")
        assert not policy.check("agent1", "file:read", "/etc/passwd")

    def test_glob_pattern(self):
        policy = CapabilityPolicy(default_deny=True)
        policy.grant("agent1", "file:*")
        assert policy.check("agent1", "file:read")
        assert policy.check("agent1", "file:write")
        assert not policy.check("agent1", "code:execute")

    def test_list_grants(self):
        policy = CapabilityPolicy()
        policy.grant("agent1", "file:read")
        policy.grant("agent1", "code:execute")
        grants = policy.list_grants("agent1")
        assert len(grants) == 2

    def test_list_agents(self):
        policy = CapabilityPolicy()
        policy.grant("agent1", "file:read")
        policy.grant("agent2", "code:execute")
        agents = policy.list_agents()
        assert set(agents) == {"agent1", "agent2"}

    def test_no_policy_agent(self):
        policy = CapabilityPolicy()
        assert policy.list_grants("unknown") == []

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "policy.json"
        policy = CapabilityPolicy()
        policy.grant("agent1", "file:read")
        policy.deny("agent1", "code:execute")
        policy.save(path)

        loaded = CapabilityPolicy(policy_path=str(path))
        assert loaded.check("agent1", "file:read")
        assert not loaded.check("agent1", "code:execute")

    def test_load_nonexistent_file(self):
        policy = CapabilityPolicy(policy_path="/nonexistent/path.json")
        # Should not raise, just have no policies
        assert policy.check("agent1", "file:read")

    def test_default_tool_capabilities(self):
        assert "file:read" in DEFAULT_TOOL_CAPABILITIES.get("file_read", [])
        assert "network:fetch" in DEFAULT_TOOL_CAPABILITIES.get("web_search", [])
        assert "code:execute" in DEFAULT_TOOL_CAPABILITIES.get("code_interpreter", [])

    def test_effectful_builtin_tools_have_central_capability_fallbacks(self):
        expected = {
            "apply_patch": Capability.FILE_WRITE,
            "browser_type": Capability.NETWORK_FETCH,
            "docker_shell_exec": Capability.CODE_EXECUTE,
            "git_commit": Capability.FILE_WRITE,
            "http_request": Capability.NETWORK_FETCH,
            "kg_add_entity": Capability.MEMORY_WRITE,
            "memory_retrieve": Capability.MEMORY_READ,
            "shell_exec": Capability.CODE_EXECUTE,
            "skill_manage": Capability.SYSTEM_ADMIN,
        }

        for tool_name, capability in expected.items():
            assert capability in DEFAULT_TOOL_CAPABILITIES[tool_name]


class TestToolScopedPolicy:
    def test_grants_only_selected_tool_resources(self) -> None:
        from openjarvis.tools.file_read import FileReadTool

        policy = build_tool_scoped_policy("native_react", [FileReadTool()])

        assert policy.check("native_react", "file:read", "file_read") is True
        assert policy.check("native_react", "file:read", "git_status") is False
        assert policy.check("native_react", "file:write", "file_write") is False

    def test_combines_multi_capability_tool_without_global_grants(self) -> None:
        from openjarvis.tools.skill_repo import SkillRepoInstallTool

        policy = build_tool_scoped_policy(
            "native_react",
            [SkillRepoInstallTool()],
        )

        for capability in ("network:fetch", "file:write", "system:admin"):
            assert (
                policy.check(
                    "native_react",
                    capability,
                    "skill_repo_install",
                )
                is True
            )
            assert policy.check("native_react", capability, "other_tool") is False

    def test_skill_management_requires_admin_and_file_write(self):
        assert DEFAULT_TOOL_CAPABILITIES["skill_manage"] == [
            Capability.SYSTEM_ADMIN,
            Capability.FILE_WRITE,
        ]
