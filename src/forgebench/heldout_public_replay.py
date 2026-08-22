from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .base_completion import SealedBaseCompletion
from .completion import CompletionResult, CompletionVerifier
from .completion_risk import CompletionRiskDecision, CompletionRiskPolicy
from .deterministic_probe import DeterministicProbeResult, DeterministicProbeRunner
from .workspace import WorkspaceError, create_isolated_workspace, hash_workspace


PublicOnlyPolicy = Literal["accept_all", "probe_all"]
PUBLIC_REPLAY_VERSION = "heldout-public-policy-replay-v1"


@dataclass(frozen=True)
class HeldoutPublicReplayResult:
    run_id: str
    policy: PublicOnlyPolicy
    base_id: str
    base_workspace_hash: str
    replay_workspace_hash: str
    workspace: Path
    completion_after: CompletionResult
    risk_decision: CompletionRiskDecision
    deterministic_probe: DeterministicProbeResult | None
    duration_seconds: float
    record_sha256: str


class HeldoutPublicReplayRunner:
    """Replay no-model policies without accepting any hidden evaluator."""

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
        policy: PublicOnlyPolicy,
        assignment: dict[str, Any],
        assignment_manifest_id: str,
        assignment_manifest_sha256: str,
        run_id: str,
    ) -> HeldoutPublicReplayResult:
        if policy not in {"accept_all", "probe_all"}:
            raise ValueError("public-only replay permits accept_all or probe_all")
        if base.task_id != task["id"] or base.task_version != int(task["version"]):
            raise ValueError("base completion task identity does not match replay task")
        if not base.eligible:
            raise ValueError("public replay requires a public-gate-passing base")
        if bool(assignment.get("model_selected")):
            raise ValueError("public-only replay cannot execute a model-selected assignment")
        expected_probe = policy == "probe_all"
        if bool(assignment.get("probe_selected")) != expected_probe:
            raise ValueError("observed public replay would differ from frozen assignment")
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("sealed base changed before public replay")

        started = time.perf_counter()
        workspace = create_isolated_workspace(
            base.workspace, self.runs_root, run_id, preserve_symlinks=True
        )
        completion = self.verifier.verify(task, workspace, seed)
        decision = self.risk_policy.evaluate(
            task=task, workspace=workspace, completion=completion
        )
        probe = (
            self.probe_runner.run(task=task, workspace=workspace, decision=decision)
            if expected_probe and completion.passed
            else None
        )
        run_root = workspace.parent
        if probe is not None:
            _write_json(run_root / "deterministic-probe.json", probe.as_dict())
        replay_workspace_hash = hash_workspace(workspace)
        record = {
            "schema_version": 1,
            "replay_version": PUBLIC_REPLAY_VERSION,
            "run_id": run_id,
            "policy": policy,
            "task_id": task["id"],
            "task_version": int(task["version"]),
            "base_id": base.base_id,
            "base_workspace_hash": base.workspace_hash,
            "replay_workspace_hash": replay_workspace_hash,
            "assignment_manifest": {
                "manifest_id": assignment_manifest_id,
                "content_sha256": assignment_manifest_sha256,
            },
            "routing": {
                "risk_decision": decision.as_dict(),
                "deterministic_probe": probe.as_dict() if probe is not None else None,
                "probe_attempted": probe is not None,
                "model_attempted": False,
            },
            "evaluation": {
                "public_completion_passed_after": completion.passed,
                "hidden_task_passed_after": None,
                "hidden_evaluation_deferred": True,
            },
            "usage": {
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "duration_seconds": round(time.perf_counter() - started, 3),
            },
            "private_grader_invoked": False,
        }
        record["content_sha256"] = payload_hash(record)
        _write_json(run_root / "public-policy-replay.json", record)
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("public replay mutated the sealed base")
        return HeldoutPublicReplayResult(
            run_id=run_id,
            policy=policy,
            base_id=base.base_id,
            base_workspace_hash=base.workspace_hash,
            replay_workspace_hash=replay_workspace_hash,
            workspace=workspace,
            completion_after=completion,
            risk_decision=decision,
            deterministic_probe=probe,
            duration_seconds=record["usage"]["duration_seconds"],
            record_sha256=record["content_sha256"],
        )


def payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
