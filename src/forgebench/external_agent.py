from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from .grader import DeterministicGrader, GradeResult
from .workspace import create_isolated_workspace


@dataclass(frozen=True)
class ExternalAgentResult:
    run_id: str
    workspace: Path
    raw_trace_path: Path
    exit_code: int
    timed_out: bool
    eligible_for_agent_metrics: bool
    grade: GradeResult


class ExternalAgentRunner:
    """Run a complete external coding-agent harness against one copied task.

    This runner is a reference-baseline path. It is intentionally separate from
    AgentRunner because a CLI coding agent owns its own loop and tools.
    """

    def __init__(self, runs_root: Path, grader: DeterministicGrader) -> None:
        self.runs_root = runs_root
        self.grader = grader

    def run(
        self,
        *,
        task: dict,
        seed: Path,
        command: list[str],
        timeout_seconds: int,
        run_id: str | None = None,
    ) -> ExternalAgentResult:
        run_id = run_id or uuid.uuid4().hex
        workspace = create_isolated_workspace(seed, self.runs_root, run_id)
        run_root = workspace.parent
        trace_path = run_root / "external-agent.jsonl"
        manifest_path = run_root / "external-manifest.json"
        resolved = [value.replace("{workspace}", str(workspace)) for value in command]
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task["id"],
            "task_version": task["version"],
            "command": resolved,
            "timeout_seconds": timeout_seconds,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        timed_out = False
        exit_code = -1
        try:
            completed = subprocess.run(
                resolved,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False,
                check=False,
            )
            exit_code = completed.returncode
            trace_path.write_text(completed.stdout, encoding="utf-8")
            (run_root / "external-agent.stderr.txt").write_text(
                completed.stderr, encoding="utf-8"
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            trace_path.write_text(stdout, encoding="utf-8")
            (run_root / "external-agent.stderr.txt").write_text(stderr, encoding="utf-8")

        grade = self.grader.grade(task, workspace, seed)
        grade.write(run_root / "grader-result.json")
        return ExternalAgentResult(
            run_id,
            workspace,
            trace_path,
            exit_code,
            timed_out,
            exit_code == 0 and not timed_out,
            grade,
        )
