from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from .adaptive_verification import build_deep_verification_prompt
from .base_completion import SealedBaseCompletion
from .codex_trace import CodexTraceSummary, summarize_codex_trace
from .completion import CompletionResult, CompletionVerifier
from .completion_risk import (
    CompletionRiskDecision,
    CompletionRiskPolicy,
    RiskSignal,
)
from .deterministic_probe import DeterministicProbeResult, DeterministicProbeRunner
from .evidence_packet import EvidencePacket, build_evidence_packet
from .external_agent import decode_process_output
from .heldout_public_replay import payload_hash
from .workspace import WorkspaceError, create_isolated_workspace, hash_workspace


ModelPolicy = Literal[
    "verify_all",
    "random_k_call_matched",
    "risk_model_direct",
    "risk_hierarchical",
]
CommandFactory = Callable[[str, Path], list[str]]
MODEL_REPLAY_VERSION = "heldout-model-policy-replay-v1"


@dataclass(frozen=True)
class HeldoutModelReplayResult:
    run_id: str
    policy: ModelPolicy
    workspace: Path
    replay_workspace_hash: str
    model_attempted: bool
    probe: DeterministicProbeResult | None
    completion_before: CompletionResult
    completion_after: CompletionResult
    exit_code: int | None
    timed_out: bool
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    duration_seconds: float
    record_sha256: str
    process_error_category: str | None


class HeldoutModelReplayRunner:
    """Execute frozen model-policy routing with hidden evaluation deferred."""

    def __init__(
        self,
        runs_root: Path,
        *,
        verifier: CompletionVerifier | None = None,
        risk_policy: CompletionRiskPolicy | None = None,
        probe_runner: DeterministicProbeRunner | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.verifier = verifier or CompletionVerifier()
        self.risk_policy = risk_policy or CompletionRiskPolicy()
        self.probe_runner = probe_runner or DeterministicProbeRunner()

    def run(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        base: SealedBaseCompletion,
        policy: ModelPolicy,
        assignment: dict[str, Any],
        assignment_manifest_id: str,
        assignment_manifest_sha256: str,
        command_factory: CommandFactory,
        timeout_seconds: int,
        run_id: str,
    ) -> HeldoutModelReplayResult:
        if policy not in {
            "verify_all",
            "random_k_call_matched",
            "risk_model_direct",
            "risk_hierarchical",
        }:
            raise ValueError("unsupported held-out model policy")
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        if base.task_id != task["id"] or base.task_version != int(task["version"]):
            raise ValueError("base task identity does not match replay task")
        if not base.eligible:
            raise ValueError("model replay requires a public-gate-passing base")
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("sealed base changed before model replay")

        started_at = datetime.now(timezone.utc)
        started_clock = time.perf_counter()
        workspace = create_isolated_workspace(
            base.workspace, self.runs_root, run_id, preserve_symlinks=True
        )
        run_root = workspace.parent
        completion_before = self.verifier.verify(task, workspace, seed)
        random_selected = bool(assignment["model_selected"])
        force_verify = policy == "verify_all" or (
            policy == "random_k_call_matched" and random_selected
        )
        decision = (
            _AlwaysEscalatePolicy().evaluate(
                task=task, workspace=workspace, completion=completion_before
            )
            if force_verify
            else self.risk_policy.evaluate(
                task=task, workspace=workspace, completion=completion_before
            )
        )
        probe = None
        if bool(assignment["probe_selected"]):
            probe = self.probe_runner.run(
                task=task, workspace=workspace, decision=decision
            )
            _write_json(run_root / "deterministic-probe.json", probe.as_dict())
        observed_model = bool(
            assignment["model_selected"]
            and not (probe is not None and probe.supported and probe.passed)
        )
        if observed_model != bool(assignment["model_selected"]):
            raise RuntimeError("probe result differs from frozen model routing")
        if policy in {"risk_model_direct", "risk_hierarchical"}:
            expected_model = bool(
                decision.escalate
                and not (probe is not None and probe.supported and probe.passed)
            )
            if expected_model != bool(assignment["model_selected"]):
                raise RuntimeError("risk routing differs from frozen assignment")

        snapshot = None
        if decision.escalate:
            snapshot = run_root / "pre-escalation-workspace"
            shutil.copytree(workspace, snapshot, symlinks=True)
        packet: EvidencePacket | None = None
        exit_code: int | None = None
        timed_out = False
        trace = CodexTraceSummary(0, 0, 0, 0, 0, 0, 0, 0)
        process_error = None
        attempt_record = None
        if observed_model:
            packet = build_evidence_packet(
                task=task, workspace=workspace, decision=decision, max_chars=24_000
            )
            _write_json(run_root / "evidence-packet.json", packet.as_dict())
            prompt = build_deep_verification_prompt(
                task, decision, packet=packet, probe=probe
            )
            raw_trace_path = run_root / "deep-verification.jsonl"
            stderr_path = run_root / "deep-verification.stderr.txt"
            attempt_started = time.perf_counter()
            try:
                process = subprocess.run(
                    command_factory(prompt, workspace),
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
            trace = _safe_trace_summary(raw_trace_path)
            process_error = _process_error(raw_trace_path)
            attempt_record = {
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": round(time.perf_counter() - attempt_started, 3),
                "trace": trace.as_dict(),
                "process_error_category": process_error,
            }

        completion_after = self.verifier.verify(task, workspace, seed)
        replay_hash = hash_workspace(workspace)
        duration = round(time.perf_counter() - started_clock, 3)
        record = {
            "schema_version": 1,
            "replay_version": MODEL_REPLAY_VERSION,
            "run_id": run_id,
            "policy": policy,
            "task_id": task["id"],
            "task_version": int(task["version"]),
            "base_id": base.base_id,
            "base_workspace_hash": base.workspace_hash,
            "replay_workspace_hash": replay_hash,
            "assignment_manifest": {
                "manifest_id": assignment_manifest_id,
                "content_sha256": assignment_manifest_sha256,
            },
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "routing": {
                "risk_decision": decision.as_dict(),
                "deterministic_probe": probe.as_dict() if probe is not None else None,
                "probe_attempted": probe is not None,
                "model_attempted": observed_model,
            },
            "evidence_packet": (
                {
                    "packet_version": packet.packet_version,
                    "content_sha256": packet.content_sha256,
                    "total_chars": packet.total_chars,
                }
                if packet is not None
                else None
            ),
            "deep_verification": attempt_record,
            "evaluation": {
                "public_completion_before": completion_before.as_dict(),
                "public_completion_after": completion_after.as_dict(),
                "hidden_task_passed_before": None,
                "hidden_task_passed_after": None,
                "hidden_evaluation_deferred": True,
            },
            "usage": {
                "input_tokens": trace.input_tokens,
                "cached_input_tokens": trace.cached_input_tokens,
                "output_tokens": trace.output_tokens,
                "duration_seconds": duration,
            },
            "private_grader_invoked": False,
        }
        record["content_sha256"] = payload_hash(record)
        _write_json(run_root / "model-policy-replay.json", record)
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("model replay mutated the sealed base")
        return HeldoutModelReplayResult(
            run_id=run_id,
            policy=policy,
            workspace=workspace,
            replay_workspace_hash=replay_hash,
            model_attempted=observed_model,
            probe=probe,
            completion_before=completion_before,
            completion_after=completion_after,
            exit_code=exit_code,
            timed_out=timed_out,
            input_tokens=trace.input_tokens,
            cached_input_tokens=trace.cached_input_tokens,
            output_tokens=trace.output_tokens,
            duration_seconds=duration,
            record_sha256=record["content_sha256"],
            process_error_category=process_error,
        )


class _AlwaysEscalatePolicy:
    def evaluate(
        self,
        *,
        task: dict[str, Any],
        workspace: Path,
        completion: CompletionResult,
    ) -> CompletionRiskDecision:
        eligible = completion.passed
        signal = RiskSignal(
            rule_id="P_VERIFY_ALL",
            triggered=eligible,
            weight=0,
            detail="uniform verification policy",
            evidence=(),
        )
        return CompletionRiskDecision(
            policy_version="verify-all-v1",
            eligible=eligible,
            score=1 if eligible else 0,
            threshold=1,
            level="high" if eligible else "not_evaluated",
            escalate=eligible,
            signals=(signal,),
        )


def _safe_trace_summary(path: Path) -> CodexTraceSummary:
    try:
        return summarize_codex_trace(path)
    except ValueError:
        return CodexTraceSummary(0, 0, 0, 0, 0, 0, 0, 0)


def _process_error(path: Path) -> str | None:
    if not path.is_file():
        return "missing_trace"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return "invalid_trace"
        if event.get("type") == "turn.failed":
            message = str(event.get("error", {}).get("message", ""))
            return (
                "model_credits_exhausted"
                if "out of credits" in message.lower()
                else "codex_turn_failed"
            )
    return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
