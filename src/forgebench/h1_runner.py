from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .codex_trace import CodexTraceSummary, summarize_codex_trace
from .completion import CompletionResult, CompletionVerifier, protected_paths
from .external_agent import decode_process_output
from .grader import DeterministicGrader, GradeResult
from .workspace import create_isolated_workspace, initialize_git_workspace


CommandFactory = Callable[[str, Path], list[str]]


@dataclass(frozen=True)
class H1Result:
    run_id: str
    workspace: Path
    attempts: int
    duration_seconds: float
    completion: CompletionResult
    grade: GradeResult
    input_tokens: int
    output_tokens: int


class H1Runner:
    """Run a planned Codex attempt and repair publicly verifiable failures."""

    def __init__(
        self,
        runs_root: Path,
        grader: DeterministicGrader,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.grader = grader
        self.verifier = verifier or CompletionVerifier()

    def run(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        command_factory: CommandFactory,
        harness_name: str = "H1c-planning-completion-repair",
        completion_gate: bool = True,
        max_repair_attempts: int = 1,
        run_id: str | None = None,
    ) -> H1Result:
        run_id = run_id or uuid.uuid4().hex
        workspace = create_isolated_workspace(seed, self.runs_root, run_id)
        initialize_git_workspace(workspace)
        run_root = workspace.parent
        started_at = datetime.now(timezone.utc)
        started_clock = time.perf_counter()
        prompt = build_h1_prompt(task)
        attempts: list[dict[str, Any]] = []
        completion: CompletionResult | None = None

        for attempt_number in range(1, max_repair_attempts + 2):
            elapsed = time.perf_counter() - started_clock
            remaining = max(1, int(task["budgets"]["max_seconds"] - elapsed))
            command = command_factory(prompt, workspace)
            trace_path = run_root / f"attempt-{attempt_number}.jsonl"
            stderr_path = run_root / f"attempt-{attempt_number}.stderr.txt"
            timed_out = False
            exit_code = -1
            try:
                process = subprocess.run(
                    command,
                    cwd=workspace,
                    capture_output=True,
                    text=False,
                    timeout=remaining,
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
            trace_summary = _safe_trace_summary(trace_path)
            attempts.append(
                {
                    "attempt": attempt_number,
                    "exit_code": exit_code,
                    "timed_out": timed_out,
                    "trace_path": trace_path.name,
                    "trace": trace_summary.as_dict(),
                    "completion": completion.as_dict(),
                }
            )
            process_succeeded = exit_code == 0 and not timed_out
            if process_succeeded and (completion.passed or not completion_gate):
                break
            if attempt_number <= max_repair_attempts:
                prompt = completion.repair_prompt()
                if exit_code != 0 or timed_out:
                    prompt += f"\nThe previous Codex process exit was {exit_code}; timed_out={timed_out}."

        grade = self.grader.grade(task, workspace, seed)
        if completion is None:
            raise RuntimeError("H1 runner completed without an attempt")
        grade.write(run_root / "grader-result.json")
        duration = round(time.perf_counter() - started_clock, 3)
        input_tokens = sum(item["trace"]["input_tokens"] for item in attempts)
        output_tokens = sum(item["trace"]["output_tokens"] for item in attempts)
        manifest = {
            "schema_version": 1,
            "harness": harness_name,
            "run_id": run_id,
            "task_id": task["id"],
            "task_version": task["version"],
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "max_repair_attempts": max_repair_attempts,
            "completion_gate": completion_gate,
            "attempts": attempts,
            "completion_passed": completion.passed,
            "task_passed": grade.passed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        (run_root / "h1-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return H1Result(
            run_id,
            workspace,
            len(attempts),
            duration,
            completion,
            grade,
            input_tokens,
            output_tokens,
        )


def build_h1_prompt(task: dict[str, Any]) -> str:
    immutable = list(protected_paths(task))
    return f"""{task['instruction']}

ForgeBench H1 protocol:
1. Before any task edit, create .forgebench/plan.json.
2. The JSON must contain a non-empty objective, steps (each with action and verification), completion_checks, and immutable_paths exactly covering: {json.dumps(immutable)}.
3. Never modify an immutable path. Recommendations belong only in the requested deliverable.
4. Execute the plan, run public checks, inspect the final diff, and stop only when every completion check passes.
5. Work only inside this repository. Do not use the network or access hidden graders.
"""


def _safe_trace_summary(path: Path) -> CodexTraceSummary:
    try:
        return summarize_codex_trace(path)
    except ValueError:
        return CodexTraceSummary(0, 0, 0, 0, 0, 0, 0, 0)
