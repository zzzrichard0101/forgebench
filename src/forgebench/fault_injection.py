from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context_policy import BoundedContextPolicy, UnboundedContextPolicy
from .model import ScriptedModelAdapter
from .recovery import BoundedToolRecoveryPolicy
from .runner import AgentRunner
from .types import ModelAction, ToolCall, ToolResult


class FirstAttemptTimeoutGateway:
    schemas: tuple[dict[str, Any], ...] = ()

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> ToolResult:
        self.calls += 1
        if self.calls == 1:
            return ToolResult(
                call.name,
                False,
                "injected first-attempt timeout",
                {"error_kind": "timeout", "injected": True},
            )
        return ToolResult(call.name, True, "recovered on retry", {"injected": True})


class DeterministicFailureGateway:
    schemas: tuple[dict[str, Any], ...] = ()

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> ToolResult:
        self.calls += 1
        return ToolResult(
            call.name,
            False,
            "injected invalid workspace path",
            {"error_kind": "deterministic", "injected": True},
        )


def run_fault_injection_experiment(
    *, runs_root: Path, seed: Path, config: dict[str, Any]
) -> dict[str, Any]:
    repetitions = int(config["repetitions_per_injection"])
    treatment = config["treatment"]
    context_config = treatment["context_policy"]
    recovery_config = treatment["recovery_policy"]
    records: list[dict[str, Any]] = []

    for repetition in range(1, repetitions + 1):
        for variant in ("control", "treatment"):
            records.append(
                _run_gateway_case(
                    runs_root=runs_root,
                    seed=seed,
                    scenario="transient-timeout",
                    variant=variant,
                    repetition=repetition,
                    gateway=FirstAttemptTimeoutGateway(),
                    recovery=(
                        _recovery_policy(recovery_config)
                        if variant == "treatment"
                        else None
                    ),
                )
            )
            records.append(
                _run_gateway_case(
                    runs_root=runs_root,
                    seed=seed,
                    scenario="deterministic-invalid-call",
                    variant=variant,
                    repetition=repetition,
                    gateway=DeterministicFailureGateway(),
                    recovery=(
                        _recovery_policy(recovery_config)
                        if variant == "treatment"
                        else None
                    ),
                )
            )

        observations = [
            ToolResult("read_file", True, f"stale-{index}:" + "x" * 4_000)
            for index in range(10)
        ]
        observations.append(
            ToolResult(
                "run_command",
                False,
                "decisive injected failure",
                {"error_kind": "deterministic", "injected": True},
            )
        )
        for variant, policy in (
            ("control", UnboundedContextPolicy()),
            (
                "treatment",
                BoundedContextPolicy(
                    max_observations=int(context_config["max_observations"]),
                    max_chars=int(context_config["max_chars"]),
                    max_item_chars=int(context_config["max_item_chars"]),
                ),
            ),
        ):
            snapshot = policy.select(observations)
            records.append(
                {
                    "scenario": "stale-output-pressure",
                    "variant": variant,
                    "repetition": repetition,
                    "original_count": snapshot.original_count,
                    "retained_count": len(snapshot.observations),
                    "original_chars": snapshot.original_chars,
                    "retained_chars": snapshot.retained_chars,
                    "failure_retained": any(not item.ok for item in snapshot.observations),
                    "context_within_limit": (
                        snapshot.retained_chars <= int(context_config["max_chars"])
                        if variant == "treatment"
                        else None
                    ),
                }
            )

    return {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "repetitions_per_injection": repetitions,
        "records": records,
        "summary": _summarize(records, config),
    }


def _run_gateway_case(
    *,
    runs_root: Path,
    seed: Path,
    scenario: str,
    variant: str,
    repetition: int,
    gateway: FirstAttemptTimeoutGateway | DeterministicFailureGateway,
    recovery: BoundedToolRecoveryPolicy | None,
) -> dict[str, Any]:
    runner = AgentRunner(
        runs_root,
        recovery_policy=recovery,
        tool_gateway_factory=lambda _workspace: gateway,
    )
    result = runner.run(
        seed=seed,
        task_instruction="Execute the injected tool once, observe its result, then finish.",
        model=ScriptedModelAdapter(
            [ModelAction.call("injected_tool"), ModelAction.finish("finished")],
            model_id="deterministic-fault-probe-v1",
        ),
        max_steps=2,
    )
    events = [
        json.loads(line)
        for line in result.trace_path.read_text(encoding="utf-8").splitlines()
    ]
    tool_results = [
        event["payload"]["result"]
        for event in events
        if event["kind"] == "tool_result"
    ]
    decisions = [
        event["payload"] for event in events if event["kind"] == "recovery_decision"
    ]
    return {
        "scenario": scenario,
        "variant": variant,
        "repetition": repetition,
        "run_id": result.run_id,
        "tool_calls": gateway.calls,
        "retries": sum(bool(item["retry"]) for item in decisions),
        "final_tool_ok": bool(tool_results and tool_results[-1]["ok"]),
        "recovery_reasons": [item["reason"] for item in decisions],
        "termination_reason": result.termination_reason,
    }


def _recovery_policy(config: dict[str, Any]) -> BoundedToolRecoveryPolicy:
    return BoundedToolRecoveryPolicy(
        max_retries=int(config["max_retries"]),
        timeout_multiplier=int(config["timeout_multiplier"]),
    )


def _summarize(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    transient_treatment = _select(records, "transient-timeout", "treatment")
    transient_control = _select(records, "transient-timeout", "control")
    deterministic_treatment = _select(
        records, "deterministic-invalid-call", "treatment"
    )
    context_treatment = _select(records, "stale-output-pressure", "treatment")
    treatment_recovery_rate = sum(
        item["final_tool_ok"] for item in transient_treatment
    ) / len(transient_treatment)
    control_recovery_rate = sum(
        item["final_tool_ok"] for item in transient_control
    ) / len(transient_control)
    deterministic_retries = sum(item["retries"] for item in deterministic_treatment)
    context_limit_passed = all(item["context_within_limit"] for item in context_treatment)
    failures_retained = sum(item["failure_retained"] for item in context_treatment)
    acceptance = config["acceptance"]
    accepted = (
        treatment_recovery_rate >= acceptance["minimum_transient_recovery_rate"]
        and deterministic_retries <= acceptance["maximum_deterministic_retries"]
        and context_limit_passed
        and failures_retained == len(context_treatment)
    )
    return {
        "transient_recovery_rate": {
            "control": control_recovery_rate,
            "treatment": treatment_recovery_rate,
        },
        "deterministic_treatment_retries": deterministic_retries,
        "context_treatment_limit_passed": context_limit_passed,
        "context_treatment_failures_retained": failures_retained,
        "context_treatment_runs": len(context_treatment),
        "mechanism_acceptance_passed": accepted,
        "claim_scope": "deterministic harness mechanism; not a model-quality benchmark",
    }


def _select(
    records: list[dict[str, Any]], scenario: str, variant: str
) -> list[dict[str, Any]]:
    return [
        item
        for item in records
        if item["scenario"] == scenario and item["variant"] == variant
    ]
