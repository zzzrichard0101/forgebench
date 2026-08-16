from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


HARNESS_ARTIFACTS = {"workspace.diff", "trace.jsonl", "grader-result.json"}


@dataclass(frozen=True)
class VerificationFinding:
    check_id: str
    passed: bool
    detail: str
    repair_instruction: str


@dataclass(frozen=True)
class CompletionResult:
    passed: bool
    findings: tuple[VerificationFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def repair_prompt(self) -> str:
        failed = [finding for finding in self.findings if not finding.passed]
        lines = [
            "The ForgeBench completion verifier blocked termination.",
            "Repair only the following public completion failures, then rerun public checks:",
        ]
        lines.extend(
            f"- {finding.check_id}: {finding.repair_instruction} ({finding.detail})"
            for finding in failed
        )
        lines.append(
            "Do not access hidden graders. Do not modify immutable source evidence."
        )
        return "\n".join(lines)


class CompletionVerifier:
    def verify(self, task: dict[str, Any], workspace: Path, seed: Path) -> CompletionResult:
        findings: list[VerificationFinding] = []
        protected_paths = _protected_paths(task)
        findings.append(self._verify_plan(workspace, protected_paths))
        findings.extend(self._verify_protected(workspace, seed, protected_paths))
        findings.extend(self._verify_required_artifacts(task, workspace))
        findings.extend(self._run_public_checks(task, workspace))
        return CompletionResult(
            all(finding.passed for finding in findings), tuple(findings)
        )

    def _verify_plan(
        self, workspace: Path, protected_paths: tuple[str, ...]
    ) -> VerificationFinding:
        plan_path = workspace / ".forgebench" / "plan.json"
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            steps = plan.get("steps")
            completion_checks = plan.get("completion_checks")
            immutable = set(plan.get("immutable_paths", []))
            passed = (
                isinstance(plan.get("objective"), str)
                and bool(plan["objective"].strip())
                and isinstance(steps, list)
                and bool(steps)
                and all(
                    isinstance(step, dict)
                    and step.get("action")
                    and step.get("verification")
                    for step in steps
                )
                and isinstance(completion_checks, list)
                and bool(completion_checks)
                and set(protected_paths) <= immutable
            )
            detail = "structured plan is valid" if passed else "plan schema or immutable paths are incomplete"
        except (OSError, json.JSONDecodeError, TypeError):
            passed = False
            detail = ".forgebench/plan.json is missing or invalid JSON"
        return VerificationFinding(
            "structured_plan",
            passed,
            detail,
            "Create a valid .forgebench/plan.json with objective, steps containing action and verification, completion_checks, and every immutable path.",
        )

    def _verify_protected(
        self, workspace: Path, seed: Path, protected_paths: tuple[str, ...]
    ) -> list[VerificationFinding]:
        findings = []
        for relative in protected_paths:
            unchanged = _digest(seed / relative) == _digest(workspace / relative)
            findings.append(
                VerificationFinding(
                    f"protected:{relative}",
                    unchanged,
                    "unchanged" if unchanged else "workspace differs from seed",
                    f"Restore {relative} exactly to its baseline state; put proposed changes only in the requested deliverable.",
                )
            )
        return findings

    def _verify_required_artifacts(
        self, task: dict[str, Any], workspace: Path
    ) -> list[VerificationFinding]:
        findings = []
        for relative in task["evidence"]["required_artifacts"]:
            if relative in HARNESS_ARTIFACTS:
                continue
            exists = (workspace / relative).is_file()
            findings.append(
                VerificationFinding(
                    f"artifact:{relative}",
                    exists,
                    "present" if exists else "missing",
                    f"Create the required workspace artifact {relative}.",
                )
            )
        return findings

    def _run_public_checks(
        self, task: dict[str, Any], workspace: Path
    ) -> list[VerificationFinding]:
        findings = []
        for check in task.get("public_checks", []):
            if check["type"] != "command":
                continue
            argv = [value.replace("{python}", sys.executable) for value in check["argv"]]
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
            passed = completed.returncode == expected
            findings.append(
                VerificationFinding(
                    f"public:{check['id']}",
                    passed,
                    f"exit {completed.returncode}, expected {expected}",
                    f"Run and fix the public check: {' '.join(check['argv'])}.",
                )
            )
        return findings


def protected_paths(task: dict[str, Any]) -> tuple[str, ...]:
    return _protected_paths(task)


def _protected_paths(task: dict[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for check in task["grader"]["checks"]:
        if check["type"] == "workspace_policy":
            paths.extend(check.get("protected_paths", []))
    return tuple(dict.fromkeys(paths))


def _digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()
