from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_completion import BaseCompletionStore
from .catalog import BenchmarkCatalog
from .codex_trace import summarize_codex_trace
from .completion import CompletionVerifier
from .heldout_base import RUN_RECORD_VERSION


RECOVERY_VERSION = "heldout-attempt-2-storage-collision-recovery-v1"


class RecoveryError(RuntimeError):
    pass


def build_recovery_plan(
    *, attempt_root: Path, isolated_base_root: Path
) -> dict[str, Any]:
    state_path = attempt_root / "execution.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    failed = [
        slot
        for slot in state["slots"]
        if slot["status"] == "infrastructure_failure"
        and "run workspace already exists" in str(slot.get("detail", ""))
    ]
    running = [slot for slot in state["slots"] if slot["status"] == "running"]
    if len(failed) != 1 or len(running) != 1:
        raise RecoveryError("expected one storage collision and one interrupted slot")
    if failed[0]["task_id"] != running[0]["task_id"]:
        raise RecoveryError("recovery slots must belong to the same sequential task")

    run_dirs = sorted(
        (path for path in (attempt_root / "runs").iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime_ns,
    )
    completed = [path for path in run_dirs if _trace_completed(path / "attempt-1.jsonl")]
    interrupted = [
        path
        for path in run_dirs
        if not (path / "attempt-1.jsonl").exists()
        and not (path / "attempt-1.stderr.txt").exists()
    ]
    if len(completed) != 1 or len(interrupted) != 1:
        raise RecoveryError("expected one completed raw run and one trace-free run")

    plan = {
        "schema_version": 1,
        "recovery_version": RECOVERY_VERSION,
        "attempt_id": state["attempt_id"],
        "plan_sha256": state["plan_sha256"],
        "cause": "attempt-1 and attempt-2 used the same base store identifiers",
        "completed_slot": {
            "task_id": failed[0]["task_id"],
            "repetition": failed[0]["repetition"],
            "base_id": failed[0]["base_id"],
            "source_run_id": completed[0].name,
            "action": "verify publicly and seal without another model call",
        },
        "interrupted_slot": {
            "task_id": running[0]["task_id"],
            "repetition": running[0]["repetition"],
            "base_id": running[0]["base_id"],
            "source_run_id": interrupted[0].name,
            "action": "retain the trace-free workspace and return the slot to pending",
        },
        "isolated_base_root": isolated_base_root.as_posix(),
        "hidden_grader_available": False,
        "delete_or_replace_raw_evidence": False,
    }
    plan["content_sha256"] = payload_hash(plan)
    return plan


def execute_recovery(
    *,
    repository_root: Path,
    attempt_root: Path,
    isolated_base_root: Path,
    expected_plan_sha256: str,
) -> dict[str, Any]:
    plan = build_recovery_plan(
        attempt_root=attempt_root,
        isolated_base_root=isolated_base_root.relative_to(repository_root),
    )
    if plan["content_sha256"] != expected_plan_sha256:
        raise RecoveryError("live recovery plan does not match the frozen plan")
    if isolated_base_root.exists():
        raise RecoveryError("isolated attempt-2 base store already exists")

    state_path = attempt_root / "execution.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state_before_sha256 = payload_hash(state)
    completed_plan = plan["completed_slot"]
    interrupted_plan = plan["interrupted_slot"]
    catalog = BenchmarkCatalog(
        repository_root, repository_root / "heldout-public" / "manifest.json"
    )
    bundle = catalog.get(completed_plan["task_id"])
    source_run_id = completed_plan["source_run_id"]
    source_root = attempt_root / "runs" / source_run_id
    source_workspace = source_root / "workspace"
    verifier = CompletionVerifier()
    completion = verifier.verify(bundle.task, source_workspace, bundle.seed_path)
    if not completion.passed:
        raise RecoveryError("completed raw workspace no longer passes the public gate")

    base = BaseCompletionStore(isolated_base_root, verifier=verifier).seal(
        task=bundle.task,
        seed=bundle.seed_path,
        source_workspace=source_workspace,
        source_run_id=source_run_id,
        base_id=completed_plan["base_id"],
    )
    trace = summarize_codex_trace(source_root / "attempt-1.jsonl")
    completed_slot = _find_slot(
        state, completed_plan["task_id"], int(completed_plan["repetition"])
    )
    started_at = completed_slot.get("started_at")
    finished_at = completed_slot.get("finished_at")
    completed_slot.update(
        {
            "schema_version": 1,
            "record_version": RUN_RECORD_VERSION,
            "run_id": source_run_id,
            "process_exit_code": 0,
            "timed_out": False,
            "duration_seconds": _duration_seconds(started_at, finished_at),
            "public_completion_eligible": True,
            "completion": completion.as_dict(),
            "trace": trace.as_dict(),
            "base_id": base.base_id,
            "base_workspace_hash": base.workspace_hash,
            "status": "eligible_public",
            "recovery": {
                "version": RECOVERY_VERSION,
                "action": "sealed completed raw output after base-store collision",
                "additional_model_call": False,
            },
        }
    )
    run_record = {
        key: completed_slot[key]
        for key in (
            "schema_version",
            "record_version",
            "run_id",
            "task_id",
            "repetition",
            "process_exit_code",
            "timed_out",
            "duration_seconds",
            "public_completion_eligible",
            "completion",
            "trace",
            "base_id",
            "base_workspace_hash",
        )
    }
    run_record.update(
        {
            "harness": "H1a-lite-bounded-planning",
            "profile": "planning-lite",
            "task_version": int(bundle.task["version"]),
            "started_at": started_at,
            "finished_at": finished_at,
            "hidden_grader_invoked": False,
            "recovery": completed_slot["recovery"],
        }
    )
    _write_json(source_root / "heldout-base-run.json", run_record)

    interrupted_slot = _find_slot(
        state, interrupted_plan["task_id"], int(interrupted_plan["repetition"])
    )
    interrupted_slot["status"] = "pending"
    interrupted_slot["recovery"] = {
        "version": RECOVERY_VERSION,
        "action": "retained trace-free interrupted workspace; no output selected",
        "abandoned_run_id": interrupted_plan["source_run_id"],
    }
    interrupted_slot.pop("started_at", None)
    interrupted_slot.pop("finished_at", None)
    state.setdefault("recovery_events", []).append(
        {
            "version": RECOVERY_VERSION,
            "recovery_plan_sha256": plan["content_sha256"],
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_json(state_path, state)
    record = {
        "schema_version": 1,
        "recovery_version": RECOVERY_VERSION,
        "recovery_plan_sha256": plan["content_sha256"],
        "state_before_sha256": state_before_sha256,
        "state_after_sha256": payload_hash(state),
        "completed_source_run_id": source_run_id,
        "interrupted_source_run_id": interrupted_plan["source_run_id"],
        "base_workspace_hash": base.workspace_hash,
        "hidden_grader_invoked": False,
        "raw_evidence_deleted_or_replaced": False,
    }
    record["content_sha256"] = payload_hash(record)
    _write_json(attempt_root / "recovery-v1.json", record)
    return record


def payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _trace_completed(path: Path) -> bool:
    if not path.exists():
        return False
    events = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return any(event.get("type") == "turn.completed" for event in events) and not any(
        event.get("type") == "turn.failed" for event in events
    )


def _find_slot(state: dict[str, Any], task_id: str, repetition: int) -> dict[str, Any]:
    matches = [
        slot
        for slot in state["slots"]
        if slot["task_id"] == task_id and int(slot["repetition"]) == repetition
    ]
    if len(matches) != 1:
        raise RecoveryError("recovery slot is not unique")
    return matches[0]


def _duration_seconds(started_at: str | None, finished_at: str | None) -> float:
    if not started_at or not finished_at:
        raise RecoveryError("completed slot is missing timestamps")
    started = datetime.fromisoformat(started_at)
    finished = datetime.fromisoformat(finished_at)
    return round((finished - started).total_seconds(), 3)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
