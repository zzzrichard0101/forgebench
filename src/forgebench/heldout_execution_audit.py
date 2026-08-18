from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .policy_freeze import canonical_file_hash
from .workspace import hash_workspace


def audit_heldout_base_execution(
    *, execution_path: Path, runs_root: Path, base_root: Path
) -> dict[str, Any]:
    execution_path = execution_path.resolve(strict=True)
    state = json.loads(execution_path.read_text(encoding="utf-8"))
    audited_slots = [
        _audit_slot(slot=slot, runs_root=runs_root, base_root=base_root)
        for slot in state["slots"]
    ]
    statuses = (
        "eligible_public",
        "visible_failure",
        "infrastructure_failure",
        "incomplete",
    )
    counts = {
        status: sum(slot["audited_status"] == status for slot in audited_slots)
        for status in statuses
    }
    base_records = [
        {
            "base_id": slot["base_id"],
            "source_run_id": slot["run_id"],
            "workspace_hash": slot["base_workspace_hash"],
        }
        for slot in audited_slots
        if slot["audited_status"] == "eligible_public"
    ]
    encoded_records = json.dumps(
        sorted(base_records, key=lambda item: item["base_id"]),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "report": "heldout-base-generation-attempt-1",
        "attempt_id": state["attempt_id"],
        "status": "incomplete_infrastructure_failure",
        "started_at": state["started_at"],
        "finished_at": state.get("finished_at"),
        "plan_sha256": state["plan_sha256"],
        "raw_execution_sha256": canonical_file_hash(execution_path),
        "raw_runner_counts": state.get("counts"),
        "audited_counts": counts,
        "raw_status_correction": {
            "affected_slots": sum(
                slot["raw_status"] != slot["audited_status"]
                for slot in audited_slots
            ),
            "reason": (
                "Runner v1 labeled every non-eligible terminal process as a visible "
                "failure. Nonzero Codex processes with turn.failed events are "
                "infrastructure failures. Raw traces and state remain unchanged."
            ),
        },
        "usage": {
            "input_tokens": sum(
                int(slot.get("trace", {}).get("input_tokens", 0))
                for slot in state["slots"]
            ),
            "cached_input_tokens": sum(
                int(slot.get("trace", {}).get("cached_input_tokens", 0))
                for slot in state["slots"]
            ),
            "output_tokens": sum(
                int(slot.get("trace", {}).get("output_tokens", 0))
                for slot in state["slots"]
            ),
            "duration_seconds": round(
                sum(float(slot.get("duration_seconds", 0)) for slot in state["slots"]),
                3,
            ),
        },
        "base_record_count": len(base_records),
        "base_record_catalog_sha256": "sha256:"
        + hashlib.sha256(encoded_records).hexdigest(),
        "slots": audited_slots,
        "decision": {
            "primary_comparison_ready": counts == {
                "eligible_public": 30,
                "visible_failure": 0,
                "infrastructure_failure": 0,
                "incomplete": 0,
            },
            "heldout_attempts_used": 1,
            "heldout_attempts_remaining": 1,
            "retry_failed_slots_in_place": False,
            "required_next_action": (
                "restore model credits and execute a newly frozen full attempt-2 matrix"
            ),
        },
    }


def _audit_slot(
    *, slot: dict[str, Any], runs_root: Path, base_root: Path
) -> dict[str, Any]:
    raw_status = str(slot["status"])
    process_error = _process_error(runs_root / str(slot.get("run_id", "")) / "attempt-1.jsonl")
    if raw_status == "eligible_public":
        audited_status = "eligible_public"
        _verify_base_record(slot=slot, base_root=base_root)
    elif raw_status in {"pending", "running"}:
        audited_status = "incomplete"
    elif (
        bool(slot.get("timed_out"))
        or int(slot.get("process_exit_code", 0)) != 0
        or process_error is not None
    ):
        audited_status = "infrastructure_failure"
    else:
        audited_status = "visible_failure"
    return {
        "task_id": slot["task_id"],
        "repetition": int(slot["repetition"]),
        "run_id": slot.get("run_id"),
        "base_id": slot.get("base_id") if audited_status == "eligible_public" else None,
        "base_workspace_hash": (
            slot.get("base_workspace_hash")
            if audited_status == "eligible_public"
            else None
        ),
        "raw_status": raw_status,
        "audited_status": audited_status,
        "process_exit_code": slot.get("process_exit_code"),
        "timed_out": bool(slot.get("timed_out", False)),
        "process_error_category": process_error,
    }


def _process_error(path: Path) -> str | None:
    if not path.is_file():
        return "missing_trace"
    failed = False
    error_message = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return "invalid_trace"
        if event.get("type") == "turn.failed":
            failed = True
            error_message = str(event.get("error", {}).get("message", ""))
    if not failed:
        return None
    if "out of credits" in error_message.lower():
        return "model_credits_exhausted"
    return "codex_turn_failed"


def _verify_base_record(*, slot: dict[str, Any], base_root: Path) -> None:
    base_id = str(slot["base_id"])
    root = (base_root.resolve(strict=True) / base_id).resolve(strict=True)
    record = json.loads(
        (root / "public-base-record.json").read_text(encoding="utf-8")
    )
    if record["base_id"] != base_id or record["source_run_id"] != slot["run_id"]:
        raise ValueError(f"base identity mismatch: {base_id}")
    actual_hash = hash_workspace(root / "workspace")
    if actual_hash != slot["base_workspace_hash"] or actual_hash != record["workspace_hash"]:
        raise ValueError(f"base workspace hash mismatch: {base_id}")
