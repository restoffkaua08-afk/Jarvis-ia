"""Controlled engineering benchmarks for Jarvis Code."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

BENCHMARK_VERSION = "2"

TASKS = {
    "basic": """Fix the defect in calculator.py.

Requirements:
- inspect the existing implementation and tests;
- make subtraction return the arithmetic difference;
- preserve addition behavior;
- run the complete test suite;
- inspect the final Git diff;
- do not change files outside this benchmark project.
""",
    "multifile": """Repair the user-registration behavior.

Requirements:
- inspect validators.py, user_service.py and the complete test suite;
- normalize email addresses by trimming whitespace and lowercasing;
- return the active field as a boolean;
- preserve the public register_user function signature;
- make the smallest coherent changes;
- run the complete test suite and inspect the final Git diff;
- do not change files outside the allowed implementation files.
""",
}
TASK_PROMPT = TASKS["basic"]


@dataclass(frozen=True, slots=True)
class BenchmarkWorkspace:
    """Prepared isolated project and its task."""

    path: Path
    prompt: str
    profile: str


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Machine-readable benchmark result."""

    version: str
    profile: str
    passed: bool
    score: int
    tests_passed: bool
    diff_present: bool
    scope_clean: bool
    required_changes_present: bool
    changed_files: tuple[str, ...]
    missing_required_files: tuple[str, ...]
    test_output: str

    def to_json(self) -> str:
        """Serialize a stable report for CI and documentation."""

        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _write_basic_fixture(project: Path) -> tuple[list[str], list[str]]:
    (project / "calculator.py").write_text(
        '"""Small benchmark target."""\n\n'
        "def add(left: int, right: int) -> int:\n"
        "    return left + right\n\n"
        "def subtract(left: int, right: int) -> int:\n"
        "    # Intentional benchmark defect.\n"
        "    return left + right\n",
        encoding="utf-8",
    )
    (project / "tests" / "test_calculator.py").write_text(
        "import unittest\n\n"
        "from calculator import add, subtract\n\n\n"
        "class CalculatorTests(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(7, 5), 12)\n\n"
        "    def test_subtract(self):\n"
        "        self.assertEqual(subtract(7, 5), 2)\n\n\n"
        'if __name__ == "__main__":\n'
        "    unittest.main()\n",
        encoding="utf-8",
    )
    return ["calculator.py"], ["calculator.py"]


def _write_multifile_fixture(project: Path) -> tuple[list[str], list[str]]:
    (project / "validators.py").write_text(
        '"""Input normalization helpers."""\n\n'
        "def normalize_email(email: str) -> str:\n"
        "    return email.lower()\n",
        encoding="utf-8",
    )
    (project / "user_service.py").write_text(
        '"""User registration service."""\n\n'
        "from validators import normalize_email\n\n\n"
        "def register_user(email: str) -> dict[str, object]:\n"
        "    return {\"email\": normalize_email(email), \"active\": \"yes\"}\n",
        encoding="utf-8",
    )
    (project / "tests" / "test_user_service.py").write_text(
        "import unittest\n\n"
        "from user_service import register_user\n"
        "from validators import normalize_email\n\n\n"
        "class UserServiceTests(unittest.TestCase):\n"
        "    def test_normalize_email(self):\n"
        '        self.assertEqual(normalize_email("  DEV@EXAMPLE.COM  "), '
        '"dev@example.com")\n\n'
        "    def test_register_user_contract(self):\n"
        '        result = register_user("  DEV@EXAMPLE.COM  ")\n'
        '        self.assertEqual(result["email"], "dev@example.com")\n'
        '        self.assertIs(result["active"], True)\n\n\n'
        'if __name__ == "__main__":\n'
        "    unittest.main()\n",
        encoding="utf-8",
    )
    files = ["validators.py", "user_service.py"]
    return files, files


def prepare_code_benchmark(
    parent: Path | None = None,
    *,
    profile: str = "basic",
) -> BenchmarkWorkspace:
    """Create a disposable Git project with intentional coding defects."""

    if profile not in TASKS:
        raise ValueError(f"Unknown benchmark profile: {profile}")
    if parent is None:
        project = Path(tempfile.mkdtemp(prefix="jarvis-code-benchmark-"))
    else:
        parent = parent.resolve()
        parent.mkdir(parents=True, exist_ok=True)
        project = Path(tempfile.mkdtemp(prefix="jarvis-code-benchmark-", dir=parent))

    (project / "tests").mkdir()
    if profile == "basic":
        allowed, required = _write_basic_fixture(project)
    else:
        allowed, required = _write_multifile_fixture(project)

    (project / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n",
        encoding="utf-8",
    )
    (project / "BENCHMARK.json").write_text(
        json.dumps(
            {
                "version": BENCHMARK_VERSION,
                "profile": profile,
                "allowed_changes": allowed,
                "required_changes": required,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "benchmark@localhost"],
        ["git", "config", "user.name", "Jarvis Benchmark"],
        ["git", "add", "."],
        ["git", "commit", "-qm", "benchmark baseline"],
    ):
        result = _run(command, cwd=project)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Failed to prepare Git fixture")
    return BenchmarkWorkspace(path=project, prompt=TASKS[profile], profile=profile)


def evaluate_code_benchmark(project: Path) -> BenchmarkReport:
    """Evaluate tests, observable edits and change scope without an LLM judge."""

    project = project.resolve()
    manifest_path = project / "BENCHMARK.json"
    if not manifest_path.is_file() or not (project / ".git").exists():
        raise ValueError("Not a prepared Jarvis Code benchmark workspace")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != BENCHMARK_VERSION:
        raise ValueError("Unsupported benchmark version")

    tests = _run(
        ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
    )
    status = _run(["git", "status", "--porcelain"], cwd=project)
    if status.returncode:
        raise RuntimeError(status.stderr.strip() or "Failed to inspect Git status")

    changed = tuple(
        sorted(
            line[3:].strip()
            for line in status.stdout.splitlines()
            if line[3:].strip()
        )
    )
    allowed = set(manifest.get("allowed_changes", ()))
    required = set(manifest.get("required_changes", ()))
    missing = tuple(sorted(required.difference(changed)))
    diff_present = bool(changed)
    scope_clean = diff_present and set(changed).issubset(allowed)
    required_present = not missing
    tests_passed = tests.returncode == 0
    score = (
        int(tests_passed) * 60
        + int(diff_present) * 10
        + int(scope_clean) * 15
        + int(required_present) * 15
    )
    output = (tests.stdout + tests.stderr).strip()[-4000:]
    return BenchmarkReport(
        version=BENCHMARK_VERSION,
        profile=str(manifest.get("profile", "unknown")),
        passed=score == 100,
        score=score,
        tests_passed=tests_passed,
        diff_present=diff_present,
        scope_clean=scope_clean,
        required_changes_present=required_present,
        changed_files=changed,
        missing_required_files=missing,
        test_output=output,
    )


__all__ = [
    "BENCHMARK_VERSION",
    "BenchmarkReport",
    "BenchmarkWorkspace",
    "TASK_PROMPT",
    "TASKS",
    "evaluate_code_benchmark",
    "prepare_code_benchmark",
]
