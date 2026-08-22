from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .heldout_public_replay import payload_hash
from .policy_freeze import canonical_file_hash
from .workspace import hash_workspace


def audit_heldout_model_replays(
    *, execution_path: Path, runs_root: Path
) -> dict[str, Any]:
    """Verify and summarize a completed grader-free model-policy batch."""

    execution_path = execution_path.resolve(strict=True)
    runs_root = runs_root.resolve(strict=True)
    state = json.loads(execution_path.read_text(encoding="utf-8"))
    if len(state["slots"]) != 120:
        raise ValueError("model replay batch must contain 120 slots")

    policies: dict[str, dict[str, int]] = {}
    catalog = []
    record_hash_failures = 0
    workspace_hash_failures = 0
    hidden_boundary_failures = 0
    model_calls = 0
    probe_attempts = 0
    probe_supported = 0
    probe_passed = 0
    completion_before = 0
    completion_after = 0
    input_tokens = 0
    cached_input_tokens = 0
    output_tokens = 0
    duration_seconds = 0.0

    for slot in state["slots"]:
        policy = str(slot["policy"])
        policy_counts = policies.setdefault(
            policy,
            {
                "completed": 0,
                "infrastructure_failure": 0,
                "model_calls": 0,
                "probe_attempts": 0,
                "completion_passed_before": 0,
                "completion_passed_after": 0,
            },
        )
        status = str(slot["status"])
        if status not in {"completed", "infrastructure_failure"}:
            raise ValueError(f"nonterminal slot: {slot['run_id']}")
        policy_counts[status] += 1
        if status != "completed":
            continue

        record_path = runs_root / str(slot["run_id"]) / "model-policy-replay.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        stored_hash = str(record["content_sha256"])
        if payload_hash(record) != stored_hash or slot["record_sha256"] != stored_hash:
            record_hash_failures += 1
        actual_workspace_hash = hash_workspace(record_path.parent / "workspace")
        if (
            actual_workspace_hash != record["replay_workspace_hash"]
            or actual_workspace_hash != slot["replay_workspace_hash"]
        ):
            workspace_hash_failures += 1

        evaluation = record["evaluation"]
        if (
            record["private_grader_invoked"] is not False
            or evaluation["hidden_task_passed_before"] is not None
            or evaluation["hidden_task_passed_after"] is not None
            or evaluation["hidden_evaluation_deferred"] is not True
        ):
            hidden_boundary_failures += 1

        routing = record["routing"]
        attempted_model = bool(routing["model_attempted"])
        attempted_probe = bool(routing["probe_attempted"])
        model_calls += attempted_model
        probe_attempts += attempted_probe
        policy_counts["model_calls"] += attempted_model
        policy_counts["probe_attempts"] += attempted_probe
        probe = routing["deterministic_probe"]
        if probe is not None:
            probe_supported += bool(probe["supported"])
            probe_passed += bool(probe["passed"])

        before = bool(evaluation["public_completion_before"]["passed"])
        after = bool(evaluation["public_completion_after"]["passed"])
        completion_before += before
        completion_after += after
        policy_counts["completion_passed_before"] += before
        policy_counts["completion_passed_after"] += after

        usage = record["usage"]
        input_tokens += int(usage["input_tokens"])
        cached_input_tokens += int(usage["cached_input_tokens"])
        output_tokens += int(usage["output_tokens"])
        duration_seconds += float(usage["duration_seconds"])
        catalog.append(
            {
                "run_id": record["run_id"],
                "policy": record["policy"],
                "base_id": record["base_id"],
                "record_sha256": stored_hash,
                "replay_workspace_hash": record["replay_workspace_hash"],
            }
        )

    encoded_catalog = json.dumps(
        sorted(catalog, key=lambda item: item["run_id"]),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    failures = sum(
        slot["status"] == "infrastructure_failure" for slot in state["slots"]
    )
    recovery_attempts = sum(bool(slot.get("retry_history")) for slot in state["slots"])
    return {
        "schema_version": 1,
        "report": "heldout-model-policy-replay-v1",
        "batch_id": state["batch_id"],
        "status": "complete" if failures == 0 and len(catalog) == 120 else "incomplete",
        "plan_sha256": state["plan_sha256"],
        "raw_execution_sha256": canonical_file_hash(execution_path),
        "replay_record_catalog_sha256": "sha256:"
        + hashlib.sha256(encoded_catalog).hexdigest(),
        "counts": {
            "completed": len(catalog),
            "infrastructure_failure": failures,
            "by_policy": policies,
        },
        "public_evaluation": {
            "completion_passed_before": completion_before,
            "completion_passed_after": completion_after,
            "probe_attempted": probe_attempts,
            "probe_supported": probe_supported,
            "probe_passed": probe_passed,
            "record_hash_failures": record_hash_failures,
            "workspace_hash_failures": workspace_hash_failures,
        },
        "usage": {
            "model_calls": model_calls,
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "output_tokens": output_tokens,
            "summed_duration_seconds": round(duration_seconds, 3),
        },
        "evaluation_boundary": {
            "private_grader_invocations": 0,
            "hidden_labels_read": False,
            "hidden_task_outcomes": "deferred",
            "boundary_failures": hidden_boundary_failures,
        },
        "execution_recovery": {
            "retried_slots": recovery_attempts,
            "cause": (
                "Windows Git long-path handling affected nine long-policy-path slots; "
                "one in-flight slot was operator-interrupted during diagnosis. Original "
                "attempt directories remain archived beside the batch runs."
            ),
            "correction": "rerun only the ten affected slots with core.longpaths enabled",
        },
        "required_next_action": (
            "seal this public replay report, then join external sealed labels and run "
            "the private grader without committing either private artifact"
        ),
    }
