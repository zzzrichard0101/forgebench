from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .adaptive_verification import AdaptiveVerificationRunner, CommandFactory
from .completion import CompletionResult, CompletionVerifier, VerificationFinding
from .completion_risk import (
    CompletionRiskDecision,
    CompletionRiskPolicy,
    RiskSignal,
)
from .deterministic_probe import DeterministicProbeResult, DeterministicProbeRunner
from .grader import DeterministicGrader, GradeResult
from .workspace import WorkspaceError, create_isolated_workspace, hash_workspace


PolicyName = Literal[
    "accept_all",
    "verify_all",
    "random_k_call_matched",
    "probe_all",
    "risk_model_direct",
    "risk_hierarchical",
]


@dataclass(frozen=True)
class SealedBaseCompletion:
    base_id: str
    root: Path
    workspace: Path
    source_run_id: str
    task_id: str
    task_version: int
    workspace_hash: str
    completion: CompletionResult

    @property
    def eligible(self) -> bool:
        return self.completion.passed


@dataclass(frozen=True)
class PolicyReplayResult:
    run_id: str
    policy: PolicyName
    base_id: str
    base_workspace_hash: str
    workspace: Path
    selected: bool
    risk_decision: CompletionRiskDecision
    deterministic_probe: DeterministicProbeResult | None
    model_attempted: bool
    completion_after: CompletionResult
    grade_after: GradeResult
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    duration_seconds: float


class BaseCompletionStore:
    """Seal public completion evidence without placing hidden labels beside it."""

    def __init__(
        self,
        root: Path,
        *,
        verifier: CompletionVerifier | None = None,
    ) -> None:
        self.root = root
        self.verifier = verifier or CompletionVerifier()

    def seal(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        source_workspace: Path,
        source_run_id: str,
        base_id: str | None = None,
    ) -> SealedBaseCompletion:
        base_id = base_id or uuid.uuid4().hex
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", base_id):
            raise ValueError("base_id must be a simple 1-128 character identifier")
        source_workspace = source_workspace.resolve(strict=True)
        source_hash = hash_workspace(source_workspace)
        workspace = create_isolated_workspace(
            source_workspace,
            self.root,
            base_id,
            preserve_symlinks=True,
        )
        copied_hash = hash_workspace(workspace)
        if copied_hash != source_hash:
            raise WorkspaceError("sealed base workspace hash differs from source")
        completion = self.verifier.verify(task, workspace, seed)
        # Public checks may create benign execution artifacts such as bytecode
        # caches. Freeze the canonical base only after those checks complete.
        sealed_hash = hash_workspace(workspace)
        record = {
            "schema_version": 1,
            "record_type": "public_base_completion",
            "base_id": base_id,
            "source_run_id": source_run_id,
            "task_id": task["id"],
            "task_version": task["version"],
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "workspace_hash": sealed_hash,
            "eligible": completion.passed,
            "public_completion": completion.as_dict(),
        }
        root = workspace.parent
        (root / "public-base-record.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return SealedBaseCompletion(
            base_id=base_id,
            root=root,
            workspace=workspace,
            source_run_id=source_run_id,
            task_id=task["id"],
            task_version=task["version"],
            workspace_hash=sealed_hash,
            completion=completion,
        )

    def load(self, base_id: str) -> SealedBaseCompletion:
        store_root = self.root.resolve(strict=True)
        root = (store_root / base_id).resolve(strict=True)
        if root != store_root and not root.is_relative_to(store_root):
            raise WorkspaceError("base completion path escapes the store root")
        record = json.loads(
            (root / "public-base-record.json").read_text(encoding="utf-8")
        )
        if record.get("record_type") != "public_base_completion":
            raise ValueError("not a public base completion record")
        workspace = (root / "workspace").resolve(strict=True)
        current_hash = hash_workspace(workspace)
        if current_hash != record["workspace_hash"]:
            raise WorkspaceError("sealed base workspace hash mismatch")
        completion_data = record["public_completion"]
        completion = CompletionResult(
            passed=bool(completion_data["passed"]),
            findings=tuple(
                VerificationFinding(**finding)
                for finding in completion_data["findings"]
            ),
        )
        return SealedBaseCompletion(
            base_id=record["base_id"],
            root=root,
            workspace=workspace,
            source_run_id=record["source_run_id"],
            task_id=record["task_id"],
            task_version=int(record["task_version"]),
            workspace_hash=current_hash,
            completion=completion,
        )


class HiddenLabelStore:
    """Write evaluation-only labels outside the public base-completion tree."""

    def __init__(self, root: Path, grader: DeterministicGrader) -> None:
        self.root = root
        self.grader = grader

    def evaluate(
        self,
        *,
        base: SealedBaseCompletion,
        task: dict[str, Any],
        seed: Path,
    ) -> GradeResult:
        _validate_base(base, task)
        grade = self.grader.grade(task, base.workspace, seed)
        self.root.mkdir(parents=True, exist_ok=True)
        label = {
            "schema_version": 1,
            "record_type": "hidden_base_label",
            "base_id": base.base_id,
            "workspace_hash": base.workspace_hash,
            "task_id": task["id"],
            "task_version": task["version"],
            "hidden_task_passed": grade.passed,
            "grade": asdict(grade),
        }
        (self.root / f"{base.base_id}.json").write_text(
            json.dumps(label, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return grade


class PolicyReplayRunner:
    """Replay one immutable base completion under one declared policy."""

    def __init__(
        self,
        runs_root: Path,
        grader: DeterministicGrader,
        *,
        verifier: CompletionVerifier | None = None,
        risk_policy: CompletionRiskPolicy | None = None,
        probe_runner: DeterministicProbeRunner | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.grader = grader
        self.verifier = verifier or CompletionVerifier()
        self.risk_policy = risk_policy or CompletionRiskPolicy()
        self.probe_runner = probe_runner or DeterministicProbeRunner()

    def run(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        base: SealedBaseCompletion,
        policy: PolicyName,
        command_factory: CommandFactory | None = None,
        random_selected: bool | None = None,
        timeout_seconds: int = 300,
        run_id: str | None = None,
    ) -> PolicyReplayResult:
        _validate_base(base, task)
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("sealed base workspace changed before replay")
        if not base.eligible:
            raise ValueError("policy replay requires a public-gate-passing base completion")
        if policy == "random_k_call_matched" and random_selected is None:
            raise ValueError("random-k replay requires a frozen selection decision")
        if policy != "random_k_call_matched" and random_selected is not None:
            raise ValueError("random_selected is valid only for random-k")

        run_id = run_id or uuid.uuid4().hex
        selected = policy != "random_k_call_matched" or bool(random_selected)
        if policy == "accept_all" or (
            policy == "random_k_call_matched" and not selected
        ):
            result = self._run_without_model(
                task=task,
                seed=seed,
                base=base,
                policy=policy,
                run_id=run_id,
                run_probe=False,
                selected=selected,
            )
        elif policy == "probe_all":
            result = self._run_without_model(
                task=task,
                seed=seed,
                base=base,
                policy=policy,
                run_id=run_id,
                run_probe=True,
                selected=True,
            )
        else:
            if command_factory is None:
                raise ValueError(f"{policy} requires a model command factory")
            risk_policy = (
                _AlwaysEscalatePolicy()
                if policy in {"verify_all", "random_k_call_matched"}
                else self.risk_policy
            )
            evidence_mode = (
                "probe-packet" if policy == "risk_hierarchical" else "packet"
            )
            adaptive = AdaptiveVerificationRunner(
                self.runs_root,
                self.grader,
                verifier=self.verifier,
                risk_policy=risk_policy,
                probe_runner=self.probe_runner,
            ).run(
                task=task,
                seed=seed,
                source_workspace=base.workspace,
                source_run_id=base.source_run_id,
                command_factory=command_factory,
                timeout_seconds=timeout_seconds,
                evidence_mode=evidence_mode,
                run_id=run_id,
            )
            result = PolicyReplayResult(
                run_id=run_id,
                policy=policy,
                base_id=base.base_id,
                base_workspace_hash=base.workspace_hash,
                workspace=adaptive.workspace,
                selected=selected,
                risk_decision=adaptive.risk_decision,
                deterministic_probe=adaptive.deterministic_probe,
                model_attempted=adaptive.attempted,
                completion_after=adaptive.completion_after,
                grade_after=adaptive.grade_after,
                input_tokens=adaptive.input_tokens,
                cached_input_tokens=adaptive.cached_input_tokens,
                output_tokens=adaptive.output_tokens,
                duration_seconds=adaptive.duration_seconds,
            )

        self._write_manifest(result)
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("policy replay mutated the sealed base workspace")
        return result

    def _run_without_model(
        self,
        *,
        task: dict[str, Any],
        seed: Path,
        base: SealedBaseCompletion,
        policy: PolicyName,
        run_id: str,
        run_probe: bool,
        selected: bool,
    ) -> PolicyReplayResult:
        started = time.perf_counter()
        workspace = create_isolated_workspace(
            base.workspace,
            self.runs_root,
            run_id,
            preserve_symlinks=True,
        )
        completion = self.verifier.verify(task, workspace, seed)
        decision = self.risk_policy.evaluate(
            task=task,
            workspace=workspace,
            completion=completion,
        )
        probe = (
            self.probe_runner.run(task=task, workspace=workspace, decision=decision)
            if run_probe and completion.passed
            else None
        )
        if probe is not None:
            (workspace.parent / "deterministic-probe.json").write_text(
                json.dumps(probe.as_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        # Evaluation follows the sealed routing action and never affects it.
        grade = self.grader.grade(task, workspace, seed)
        grade.write(workspace.parent / "grader-result.json")
        return PolicyReplayResult(
            run_id=run_id,
            policy=policy,
            base_id=base.base_id,
            base_workspace_hash=base.workspace_hash,
            workspace=workspace,
            selected=selected,
            risk_decision=decision,
            deterministic_probe=probe,
            model_attempted=False,
            completion_after=completion,
            grade_after=grade,
            input_tokens=0,
            cached_input_tokens=0,
            output_tokens=0,
            duration_seconds=round(time.perf_counter() - started, 3),
        )

    def _write_manifest(self, result: PolicyReplayResult) -> None:
        manifest = {
            "schema_version": 1,
            "harness": "policy-replay-v1",
            "run_id": result.run_id,
            "policy": result.policy,
            "base_id": result.base_id,
            "base_workspace_hash": result.base_workspace_hash,
            "selected": result.selected,
            "routing": {
                "risk_decision": result.risk_decision.as_dict(),
                "deterministic_probe": (
                    result.deterministic_probe.as_dict()
                    if result.deterministic_probe is not None
                    else None
                ),
                "model_attempted": result.model_attempted,
            },
            "evaluation": {
                "completion_passed_after": result.completion_after.passed,
                "hidden_task_passed_after": result.grade_after.passed,
            },
            "usage": {
                "input_tokens": result.input_tokens,
                "cached_input_tokens": result.cached_input_tokens,
                "output_tokens": result.output_tokens,
                "duration_seconds": result.duration_seconds,
            },
        }
        (result.workspace.parent / "policy-replay-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
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


def _validate_base(base: SealedBaseCompletion, task: dict[str, Any]) -> None:
    if base.task_id != task["id"] or base.task_version != task["version"]:
        raise ValueError("base completion task identity does not match replay task")
