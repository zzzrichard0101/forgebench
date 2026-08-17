from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from .codex_trace import CodexTraceSummary, summarize_codex_trace
from .completion import CompletionResult, CompletionVerifier
from .completion_risk import CompletionRiskDecision, CompletionRiskPolicy
from .external_agent import decode_process_output
from .evidence_packet import EvidencePacket, build_evidence_packet
from .grader import DeterministicGrader, GradeResult
from .trace import TraceWriter
from .workspace import create_isolated_workspace


CommandFactory = Callable[[str, Path], list[str]]


@dataclass(frozen=True)
class AdaptiveVerificationResult:
    run_id: str
    workspace: Path
    pre_escalation_workspace: Path | None
    risk_decision: CompletionRiskDecision
    attempted: bool
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    completion_before: CompletionResult
    completion_after: CompletionResult
    grade_before: GradeResult
    grade_after: GradeResult
    evidence_packet: EvidencePacket | None


class AdaptiveVerificationRunner:
    """Replay one completed workspace through bounded selective verification."""

    def __init__(
        self,
        runs_root: Path,
        grader: DeterministicGrader,
        *,
        verifier: CompletionVerifier | None = None,
        risk_policy: CompletionRiskPolicy | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.grader = grader
        self.verifier = verifier or CompletionVerifier()
        self.risk_policy = risk_policy or CompletionRiskPolicy()

    def run(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        source_workspace: Path,
        source_run_id: str,
        command_factory: CommandFactory,
        timeout_seconds: int = 300,
        evidence_mode: Literal["full", "packet"] = "full",
        evidence_max_chars: int = 24_000,
        run_id: str | None = None,
    ) -> AdaptiveVerificationResult:
        if timeout_seconds <= 0:
            raise ValueError("adaptive verification timeout must be positive")
        if evidence_mode not in {"full", "packet"}:
            raise ValueError(f"unknown evidence mode: {evidence_mode}")
        run_id = run_id or uuid.uuid4().hex
        source_workspace = source_workspace.resolve(strict=True)
        workspace = create_isolated_workspace(
            source_workspace,
            self.runs_root,
            run_id,
            preserve_symlinks=True,
        )
        run_root = workspace.parent
        trace = TraceWriter(run_root / "harness-trace.jsonl", run_id)
        started_at = datetime.now(timezone.utc)
        started_clock = time.perf_counter()

        completion_before = self.verifier.verify(task, workspace, seed)
        decision = self.risk_policy.evaluate(
            task=task,
            workspace=workspace,
            completion=completion_before,
        )
        trace.append("completion_risk_decision", decision.as_dict())

        snapshot: Path | None = None
        if decision.escalate:
            snapshot = run_root / "pre-escalation-workspace"
            shutil.copytree(workspace, snapshot, symlinks=True)
        grade_before = self.grader.grade(task, snapshot or workspace, seed)
        grade_before.write(run_root / "pre-escalation-grader-result.json")

        attempted = False
        exit_code: int | None = None
        timed_out = False
        input_tokens = 0
        output_tokens = 0
        attempt_record: dict[str, Any] | None = None
        packet: EvidencePacket | None = None

        if decision.escalate:
            attempted = True
            if evidence_mode == "packet":
                packet = build_evidence_packet(
                    task=task,
                    workspace=workspace,
                    decision=decision,
                    max_chars=evidence_max_chars,
                )
                (run_root / "evidence-packet.json").write_text(
                    json.dumps(packet.as_dict(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                trace.append(
                    "evidence_packet_created",
                    {
                        "packet_version": packet.packet_version,
                        "content_sha256": packet.content_sha256,
                        "total_chars": packet.total_chars,
                        "changed_paths": list(packet.changed_paths),
                    },
                )
            prompt = build_deep_verification_prompt(task, decision, packet=packet)
            command = command_factory(prompt, workspace)
            raw_trace_path = run_root / "deep-verification.jsonl"
            stderr_path = run_root / "deep-verification.stderr.txt"
            attempt_started = time.perf_counter()
            try:
                process = subprocess.run(
                    command,
                    cwd=workspace,
                    capture_output=True,
                    text=False,
                    timeout=timeout_seconds,
                    shell=False,
                    check=False,
                )
                exit_code = process.returncode
                raw_trace_path.write_text(
                    decode_process_output(process.stdout), encoding="utf-8"
                )
                stderr_path.write_text(
                    decode_process_output(process.stderr), encoding="utf-8"
                )
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                exit_code = -1
                raw_trace_path.write_text(
                    decode_process_output(exc.stdout), encoding="utf-8"
                )
                stderr_path.write_text(
                    decode_process_output(exc.stderr), encoding="utf-8"
                )
            summary = _safe_trace_summary(raw_trace_path)
            input_tokens = summary.input_tokens
            output_tokens = summary.output_tokens
            attempt_record = {
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": round(time.perf_counter() - attempt_started, 3),
                "trace_path": raw_trace_path.name,
                "trace": summary.as_dict(),
            }
            trace.append("deep_verification_attempt", attempt_record)

        completion_after = self.verifier.verify(task, workspace, seed)
        grade_after = self.grader.grade(task, workspace, seed)
        grade_after.write(run_root / "grader-result.json")
        duration = round(time.perf_counter() - started_clock, 3)
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "harness": "H1a-adaptive-replay-v0.1",
            "task_id": task["id"],
            "task_version": task["version"],
            "source_run_id": source_run_id,
            "source_workspace_hash": _hash_workspace_without_following_symlinks(
                source_workspace
            ),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout_seconds,
            "evidence_mode": evidence_mode,
            "evidence_packet": (
                {
                    "packet_version": packet.packet_version,
                    "content_sha256": packet.content_sha256,
                    "total_chars": packet.total_chars,
                    "path": "evidence-packet.json",
                }
                if packet is not None
                else None
            ),
            "risk_decision": decision.as_dict(),
            "deep_verification_attempted": attempted,
            "deep_verification": attempt_record,
            "completion_before": completion_before.as_dict(),
            "completion_after": completion_after.as_dict(),
            "task_passed_before": grade_before.passed,
            "task_passed_after": grade_after.passed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_seconds": duration,
        }
        (run_root / "adaptive-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return AdaptiveVerificationResult(
            run_id=run_id,
            workspace=workspace,
            pre_escalation_workspace=snapshot,
            risk_decision=decision,
            attempted=attempted,
            exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            completion_before=completion_before,
            completion_after=completion_after,
            grade_before=grade_before,
            grade_after=grade_after,
            evidence_packet=packet,
        )


def build_deep_verification_prompt(
    task: dict[str, Any],
    decision: CompletionRiskDecision,
    *,
    packet: EvidencePacket | None = None,
) -> str:
    fired = [signal for signal in decision.signals if signal.triggered]
    evidence = "\n".join(
        f"- {signal.rule_id}: {signal.detail}; evidence={list(signal.evidence)}"
        for signal in fired
    )
    if packet is not None:
        packet_json = json.dumps(packet.as_dict(), ensure_ascii=False, separators=(",", ":"))
        return f"""ForgeBench focused adaptive verification.

Use the bounded evidence packet below as the starting context. Do not inventory the repository or reread unrelated files. Inspect a packet-listed file only when needed to edit it, derive one focused check for each missing contract dimension, run the declared public check, and stop after one bounded repair.
Do not access hidden graders or author metadata. Preserve immutable files and the public API.

EVIDENCE_PACKET_JSON
{packet_json}
END_EVIDENCE_PACKET
"""
    return f"""{task['instruction']}

ForgeBench adaptive deep-verification pass:
The public completion gate passed, but the following public-evidence risk rules fired:
{evidence}

Inspect the current implementation, public interfaces, existing public tests, and final diff.
Derive at least one focused negative or boundary case from the task contract without reading hidden graders.
Run that focused check. If it exposes a defect, repair the implementation and rerun both the focused check and existing public checks.
Preserve the public API and immutable files. Make no unrelated changes. Stop after this single bounded verification pass.
"""


def _safe_trace_summary(path: Path) -> CodexTraceSummary:
    try:
        return summarize_codex_trace(path)
    except ValueError:
        return CodexTraceSummary(0, 0, 0, 0, 0, 0, 0, 0)


def _hash_workspace_without_following_symlinks(root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        (path for path in root.rglob("*") if ".git" not in path.relative_to(root).parts),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            kind = b"symlink"
            content = os.readlink(path).encode("utf-8", errors="surrogateescape")
        elif path.is_file():
            kind = b"file"
            content = path.read_bytes()
        else:
            continue
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(kind)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()
