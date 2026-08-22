"""Plan or execute the frozen no-model held-out policy replay batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.comparison_manifest import load_comparison_manifest, validate_assignment
from forgebench.heldout_public_replay import HeldoutPublicReplayRunner
from run_codex_baseline import ROOT


ASSIGNMENT_PATH = (
    ROOT / "experiments" / "configs" / "heldout-policy-assignment-v1.json"
)
HELDOUT_MANIFEST = ROOT / "heldout-public" / "manifest.json"
BASE_ROOT = ROOT / "runs" / "heldout-v1" / "base-completions-attempt-2"
RUNS_ROOT = ROOT / "runs" / "heldout-v1" / "public-policy-replays-v1"
BATCH_ID = "heldout-v1-public-policies-v1"
POLICIES = ("accept_all", "probe_all")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest = load_comparison_manifest(ASSIGNMENT_PATH)
    plan = build_plan(manifest.payload)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    batch_root = RUNS_ROOT / BATCH_ID
    if batch_root.exists():
        raise FileExistsError("public policy batch already exists")
    batch_root.mkdir(parents=True)
    _write_json(batch_root / "plan.json", plan)
    state = {
        "schema_version": 1,
        "batch_version": "heldout-public-policy-batch-v1",
        "batch_id": BATCH_ID,
        "plan_sha256": plan["content_sha256"],
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "slots": [{**slot, "status": "pending"} for slot in plan["slots"]],
    }
    state_path = batch_root / "execution.json"
    _write_json(state_path, state)

    catalog = BenchmarkCatalog(ROOT, HELDOUT_MANIFEST)
    store = BaseCompletionStore(BASE_ROOT)
    runner = HeldoutPublicReplayRunner(batch_root / "runs")
    for slot in state["slots"]:
        slot["status"] = "running"
        _write_json(state_path, state)
        try:
            bundle = catalog.get(slot["task_id"])
            base = store.load(slot["base_id"])
            assignment = validate_assignment(
                manifest=manifest,
                base=base,
                task=bundle.task,
                policy=slot["policy"],
            )
            result = runner.run(
                task=bundle.task,
                seed=bundle.seed_path,
                base=base,
                policy=slot["policy"],
                assignment=assignment,
                assignment_manifest_id=manifest.manifest_id,
                assignment_manifest_sha256=manifest.content_sha256,
                run_id=slot["run_id"],
            )
            slot.update(
                {
                    "status": "completed",
                    "record_sha256": result.record_sha256,
                    "replay_workspace_hash": result.replay_workspace_hash,
                    "public_completion_passed_after": result.completion_after.passed,
                    "probe_attempted": result.deterministic_probe is not None,
                    "probe_supported": (
                        result.deterministic_probe.supported
                        if result.deterministic_probe is not None
                        else None
                    ),
                    "probe_passed": (
                        result.deterministic_probe.passed
                        if result.deterministic_probe is not None
                        else None
                    ),
                    "duration_seconds": result.duration_seconds,
                    "private_grader_invoked": False,
                }
            )
        except Exception as exc:
            slot["status"] = "infrastructure_failure"
            slot["detail"] = f"{type(exc).__name__}: {exc}"
        _write_json(state_path, state)

    state["status"] = "completed"
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    state["counts"] = {
        status: sum(slot["status"] == status for slot in state["slots"])
        for status in ("completed", "infrastructure_failure")
    }
    _write_json(state_path, state)
    print(json.dumps(state["counts"], ensure_ascii=False, indent=2))
    return 1 if state["counts"]["infrastructure_failure"] else 0


def build_plan(assignment: dict[str, Any]) -> dict[str, Any]:
    slots = [
        {
            "policy": policy,
            "task_id": item["task_id"],
            "base_id": item["base_id"],
            "base_workspace_hash": item["base_workspace_hash"],
            "run_id": _run_id(policy, item["base_id"]),
        }
        for policy in POLICIES
        for item in assignment["bases"]
    ]
    plan = {
        "schema_version": 1,
        "plan_version": "heldout-public-policy-batch-plan-v1",
        "batch_id": BATCH_ID,
        "assignment_manifest_id": assignment["manifest_id"],
        "assignment_manifest_sha256": assignment["content_sha256"],
        "policies": list(POLICIES),
        "slot_count": len(slots),
        "model_calls": 0,
        "private_grader_available": False,
        "slots": slots,
    }
    plan["content_sha256"] = _payload_hash(plan)
    return plan


def _run_id(policy: str, base_id: str) -> str:
    digest = hashlib.sha256(f"{policy}\0{base_id}".encode()).hexdigest()[:20]
    return f"public-v1--{policy}--{digest}"


def _payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
