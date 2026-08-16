from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .workspace import WorkspaceError, resolve_workspace_path


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    check_type: str
    severity: str
    passed: bool
    output: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class GradeResult:
    task_id: str
    task_version: int
    passed: bool
    checks: tuple[CheckResult, ...]

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class DeterministicGrader:
    def __init__(self, grader_root: Path, *, max_output_chars: int = 20_000) -> None:
        self.grader_root = grader_root.resolve(strict=True)
        self.max_output_chars = max_output_chars

    def grade(self, task: dict[str, Any], workspace: Path, seed: Path) -> GradeResult:
        workspace = workspace.resolve(strict=True)
        seed = seed.resolve(strict=True)
        results = tuple(
            self._run_check(check, workspace, seed) for check in task["grader"]["checks"]
        )
        passed = all(result.passed for result in results if result.severity == "required")
        return GradeResult(task["id"], task["version"], passed, results)

    def _run_check(self, check: dict[str, Any], workspace: Path, seed: Path) -> CheckResult:
        check_type = check["type"]
        try:
            if check_type == "command":
                return self._command(check, workspace)
            if check_type == "file_exists":
                exists = resolve_workspace_path(workspace, check["path"], must_exist=False).is_file()
                return self._result(check, exists, f"file exists: {exists}")
            if check_type == "file_absent":
                absent = not resolve_workspace_path(workspace, check["path"], must_exist=False).exists()
                return self._result(check, absent, f"file absent: {absent}")
            if check_type == "workspace_policy":
                return self._workspace_policy(check, workspace, seed)
            return self._result(check, False, f"unsupported check type: {check_type}")
        except (OSError, ValueError, KeyError, TypeError, WorkspaceError) as exc:
            return self._result(check, False, f"{type(exc).__name__}: {exc}")

    def _command(self, check: dict[str, Any], workspace: Path) -> CheckResult:
        argv = [self._expand(value) for value in check["argv"]]
        completed = subprocess.run(
            argv,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
            check=False,
        )
        expected = check.get("expected_exit_code", 0)
        output = self._bounded(completed.stdout + completed.stderr)
        passed = completed.returncode == expected
        pattern = check.get("output_pattern")
        if pattern is not None:
            passed = passed and pattern in output
        return self._result(
            check,
            passed,
            output,
            {"argv": argv, "exit_code": completed.returncode, "expected_exit_code": expected},
        )

    def _workspace_policy(
        self, check: dict[str, Any], workspace: Path, seed: Path
    ) -> CheckResult:
        changed: list[str] = []
        for relative in check.get("protected_paths", []):
            seed_path = resolve_workspace_path(seed, relative, must_exist=False)
            workspace_path = resolve_workspace_path(workspace, relative, must_exist=False)
            if _digest(seed_path) != _digest(workspace_path):
                changed.append(relative)
        return self._result(
            check,
            not changed,
            "protected paths unchanged" if not changed else f"changed: {', '.join(changed)}",
            {"changed_protected_paths": changed},
        )

    def _expand(self, value: str) -> str:
        return value.replace("{python}", sys.executable).replace(
            "{grader_root}", str(self.grader_root)
        )

    def _result(
        self,
        check: dict[str, Any],
        passed: bool,
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckResult:
        return CheckResult(
            check["id"],
            check["type"],
            check["severity"],
            passed,
            self._bounded(output),
            metadata or {},
        )

    def _bounded(self, value: str) -> str:
        if len(value) <= self.max_output_chars:
            return value
        return value[: self.max_output_chars] + "\n...[truncated]"


def _digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

