from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_completion import BaseCompletionStore, SealedBaseCompletion
from .codex_trace import CodexTraceSummary, summarize_codex_trace
from .completion import CompletionResult, CompletionVerifier
from .external_agent import decode_process_output
from .h1_runner import CommandFactory, build_h1_prompt
from .workspace import create_isolated_workspace, initialize_git_workspace


RUN_RECORD_VERSION = "heldout-public-base-run-v1"


@dataclass(frozen=True)
class HeldoutBaseRunResult:
    run_id: str
    task_id: str
    repetition: int
    workspace: Path
    process_exit_code: int
    timed_out: bool
    duration_seconds: float
    completion: CompletionResult
    trace: CodexTraceSummary
    base: SealedBaseCompletion | None

    @property
    def public_completion_eligible(self) -> bool:
        return (
            self.process_exit_code == 0
            and not self.timed_out
            and self.completion.passed
            and self.base is not None
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "record_version": RUN_RECORD_VERSION,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "repetition": self.repetition,
            "process_exit_code": self.process_exit_code,
            "timed_out": self.timed_out,
            "duration_seconds": self.duration_seconds,
            "public_completion_eligible": self.public_completion_eligible,
            "completion": self.completion.as_dict(),
            "trace": self.trace.as_dict(),
            "base_id": self.base.base_id if self.base is not None else None,
            "base_workspace_hash": (
                self.base.workspace_hash if self.base is not None else None
            ),
        }


class HeldoutBaseRunner:
    """Generate and seal one public-only H1a-lite held-out completion."""

    def __init__(
        self,
        runs_root: Path,
        base_root: Path,
        *,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.base_store = BaseCompletionStore(base_root, verifier=verifier)
        self.verifier = verifier or CompletionVerifier()

    def run(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        repetition: int,
        base_id: str,
        command_factory: CommandFactory,
        run_id: str | None = None,
    ) -> HeldoutBaseRunResult:
        if repetition < 1:
            raise ValueError("repetition must be positive")
        run_id = run_id or uuid.uuid4().hex
        workspace = create_isolated_workspace(seed, self.runs_root, run_id)
        initialize_git_workspace(workspace)
        run_root = workspace.parent
        started_at = datetime.now(timezone.utc)
        started_clock = time.perf_counter()
        trace_path = run_root / "attempt-1.jsonl"
        stderr_path = run_root / "attempt-1.stderr.txt"
        command = command_factory(build_h1_prompt(task, style="lite"), workspace)
        exit_code = -1
        timed_out = False
        try:
            process = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=False,
                timeout=int(task["budgets"]["max_seconds"]),
                shell=False,
                check=False,
            )
            exit_code = process.returncode
            trace_path.write_text(
                decode_process_output(process.stdout), encoding="utf-8"
            )
            stderr_path.write_text(
                decode_process_output(process.stderr), encoding="utf-8"
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            trace_path.write_text(
                decode_process_output(exc.stdout), encoding="utf-8"
            )
            stderr_path.write_text(
                decode_process_output(exc.stderr), encoding="utf-8"
            )

        completion = self.verifier.verify(task, workspace, seed)
        trace = _safe_trace_summary(trace_path)
        process_succeeded = exit_code == 0 and not timed_out
        base = (
            self.base_store.seal(
                task=task,
                seed=seed,
                source_workspace=workspace,
                source_run_id=run_id,
                base_id=base_id,
            )
            if process_succeeded and completion.passed
            else None
        )
        result = HeldoutBaseRunResult(
            run_id=run_id,
            task_id=str(task["id"]),
            repetition=repetition,
            workspace=workspace,
            process_exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=round(time.perf_counter() - started_clock, 3),
            completion=completion,
            trace=trace,
            base=base,
        )
        record = result.as_dict()
        record.update(
            {
                "harness": "H1a-lite-bounded-planning",
                "profile": "planning-lite",
                "task_version": int(task["version"]),
                "started_at": started_at.isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "hidden_grader_invoked": False,
            }
        )
        (run_root / "heldout-base-run.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result


def build_base_matrix(
    tasks: list[dict[str, Any]], *, repetitions: int, snapshot: str
) -> list[dict[str, Any]]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    return [
        {
            "task_id": str(task["id"]),
            "task_version": int(task["version"]),
            "family": str(task["family"]),
            "repetition": repetition,
            "base_id": f"{snapshot}--{task['id']}--r{repetition}",
        }
        for task in tasks
        for repetition in range(1, repetitions + 1)
    ]


def _safe_trace_summary(path: Path) -> CodexTraceSummary:
    try:
        return summarize_codex_trace(path)
    except ValueError:
        return CodexTraceSummary(0, 0, 0, 0, 0, 0, 0, 0)
