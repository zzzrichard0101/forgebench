from __future__ import annotations

import json
import locale
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .grader import DeterministicGrader, GradeResult
from .workspace import create_isolated_workspace, initialize_git_workspace


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
        workspace_path_mapper: Callable[[Path], str] = str,
    ) -> ExternalAgentResult:
        run_id = run_id or uuid.uuid4().hex
        workspace = create_isolated_workspace(seed, self.runs_root, run_id)
        initialize_git_workspace(workspace)
        run_root = workspace.parent
        trace_path = run_root / "external-agent.jsonl"
        manifest_path = run_root / "external-manifest.json"
        mapped_workspace = workspace_path_mapper(workspace)
        resolved = [value.replace("{workspace}", mapped_workspace) for value in command]
        started_at = datetime.now(timezone.utc)
        started_clock = time.perf_counter()
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task["id"],
            "task_version": task["version"],
            "command": resolved,
            "timeout_seconds": timeout_seconds,
            "started_at": started_at.isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        timed_out = False
        exit_code = -1
        try:
            completed = subprocess.run(
                resolved,
                cwd=workspace,
                capture_output=True,
                text=False,
                timeout=timeout_seconds,
                shell=False,
                check=False,
            )
            exit_code = completed.returncode
            trace_path.write_text(_decode_output(completed.stdout), encoding="utf-8")
            (run_root / "external-agent.stderr.txt").write_text(
                _decode_output(completed.stderr), encoding="utf-8"
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = _decode_output(exc.stdout)
            stderr = _decode_output(exc.stderr)
            trace_path.write_text(stdout, encoding="utf-8")
            (run_root / "external-agent.stderr.txt").write_text(stderr, encoding="utf-8")

        grade = self.grader.grade(task, workspace, seed)
        grade.write(run_root / "grader-result.json")
        finished_at = datetime.now(timezone.utc)
        duration_seconds = time.perf_counter() - started_clock
        eligible = exit_code == 0 and not timed_out
        manifest.update(
            {
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round(duration_seconds, 3),
                "exit_code": exit_code,
                "timed_out": timed_out,
                "eligible_for_agent_metrics": eligible,
                "task_passed": grade.passed,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return ExternalAgentResult(
            run_id,
            workspace,
            trace_path,
            exit_code,
            timed_out,
            eligible,
            grade,
        )


def _decode_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    for encoding in ("utf-8", locale.getpreferredencoding(False)):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("utf-8", errors="replace")
