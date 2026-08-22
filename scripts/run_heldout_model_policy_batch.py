"""Plan or execute all frozen held-out model-policy replays."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command
from forgebench.comparison_manifest import load_comparison_manifest, validate_assignment
from forgebench.heldout_model_replay import HeldoutModelReplayRunner
from run_codex_baseline import (
    PINNED_CODEX_VERSION,
    ROOT,
    find_local_linux_codex,
    windows_to_wsl,
)


ASSIGNMENT_PATH = ROOT / "experiments" / "configs" / "heldout-policy-assignment-v1.json"
HELDOUT_MANIFEST = ROOT / "heldout-public" / "manifest.json"
BASE_ROOT = ROOT / "runs" / "heldout-v1" / "base-completions-attempt-2"
RUNS_ROOT = ROOT / "runs" / "heldout-v1" / "model-policy-replays-v1"
BATCH_ID = "heldout-v1-model-policies-v1"
POLICIES = (
    "verify_all",
    "random_k_call_matched",
    "risk_model_direct",
    "risk_hierarchical",
)
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "medium"
TIMEOUT_SECONDS = 300


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--codex-home", type=Path)
    args = parser.parse_args()
    if args.resume and not args.execute:
        parser.error("--resume requires --execute")
    manifest = load_comparison_manifest(ASSIGNMENT_PATH)
    plan = build_plan(manifest.payload)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    batch_root = RUNS_ROOT / BATCH_ID
    plan_path = batch_root / "plan.json"
    state_path = batch_root / "execution.json"
    if batch_root.exists():
        if not args.resume:
            raise FileExistsError("model policy batch already exists; use --resume")
        if json.loads(plan_path.read_text(encoding="utf-8")) != plan:
            raise ValueError("existing batch plan differs from frozen plan")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        for slot in state["slots"]:
            if slot["status"] == "running":
                slot["status"] = "infrastructure_failure"
                slot["detail"] = "previous process ended before slot finalization"
    else:
        if args.resume:
            raise FileNotFoundError("cannot resume missing model policy batch")
        batch_root.mkdir(parents=True)
        _write_json(plan_path, plan)
        state = {
            "schema_version": 1,
            "batch_version": "heldout-model-policy-batch-v1",
            "batch_id": BATCH_ID,
            "plan_sha256": plan["content_sha256"],
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "slots": [{**slot, "status": "pending"} for slot in plan["slots"]],
        }
    _write_json(state_path, state)

    codex_home = (args.codex_home or (Path.home() / ".codex")).resolve(strict=True)
    os.environ["CODEX_HOME"] = str(codex_home)
    codex = (args.codex_bin or find_local_linux_codex()).resolve(strict=True)
    wsl = shutil.which("wsl.exe") or shutil.which("wsl")
    if wsl is None or platform.system() != "Windows":
        raise RuntimeError("frozen model replay requires the Windows WSL host")
    prefix = [
        wsl,
        "-d",
        "Ubuntu",
        "--",
        "env",
        f"CODEX_HOME={windows_to_wsl(codex_home)}",
        windows_to_wsl(codex),
    ]

    def command_factory(prompt: str, workspace: Path) -> list[str]:
        return build_exec_command(
            prefix=prefix,
            prompt=prompt,
            workspace=windows_to_wsl(workspace),
            model=MODEL,
            reasoning_effort=REASONING_EFFORT,
            persist_session=False,
        )

    catalog = BenchmarkCatalog(ROOT, HELDOUT_MANIFEST)
    store = BaseCompletionStore(BASE_ROOT)
    runner = HeldoutModelReplayRunner(batch_root / "runs")
    for slot in state["slots"]:
        if slot["status"] != "pending":
            continue
        slot["status"] = "running"
        slot["started_at"] = datetime.now(timezone.utc).isoformat()
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
                command_factory=command_factory,
                timeout_seconds=TIMEOUT_SECONDS,
                run_id=slot["run_id"],
            )
            infrastructure = bool(
                result.timed_out
                or (result.exit_code is not None and result.exit_code != 0)
                or result.process_error_category is not None
            )
            slot.update(
                {
                    "status": "infrastructure_failure" if infrastructure else "completed",
                    "record_sha256": result.record_sha256,
                    "replay_workspace_hash": result.replay_workspace_hash,
                    "model_attempted": result.model_attempted,
                    "probe_attempted": result.probe is not None,
                    "public_completion_passed_before": result.completion_before.passed,
                    "public_completion_passed_after": result.completion_after.passed,
                    "process_exit_code": result.exit_code,
                    "timed_out": result.timed_out,
                    "process_error_category": result.process_error_category,
                    "input_tokens": result.input_tokens,
                    "cached_input_tokens": result.cached_input_tokens,
                    "output_tokens": result.output_tokens,
                    "duration_seconds": result.duration_seconds,
                    "private_grader_invoked": False,
                }
            )
        except Exception as exc:
            slot["status"] = "infrastructure_failure"
            slot["detail"] = f"{type(exc).__name__}: {exc}"
        slot["finished_at"] = datetime.now(timezone.utc).isoformat()
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
    slots = []
    for policy in POLICIES:
        for item in assignment["bases"]:
            route = item["policies"][policy]
            slots.append(
                {
                    "policy": policy,
                    "task_id": item["task_id"],
                    "base_id": item["base_id"],
                    "base_workspace_hash": item["base_workspace_hash"],
                    "expected_probe": bool(route["probe_selected"]),
                    "expected_model": bool(route["model_selected"]),
                    "run_id": _run_id(policy, item["base_id"]),
                }
            )
    plan = {
        "schema_version": 1,
        "plan_version": "heldout-model-policy-batch-plan-v1",
        "batch_id": BATCH_ID,
        "assignment_manifest_id": assignment["manifest_id"],
        "assignment_manifest_sha256": assignment["content_sha256"],
        "policies": list(POLICIES),
        "slot_count": len(slots),
        "expected_model_calls": sum(slot["expected_model"] for slot in slots),
        "expected_probe_calls": sum(slot["expected_probe"] for slot in slots),
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "codex_cli_version": PINNED_CODEX_VERSION,
        "timeout_seconds": TIMEOUT_SECONDS,
        "private_grader_available": False,
        "slots": slots,
    }
    plan["content_sha256"] = _payload_hash(plan)
    return plan


def _run_id(policy: str, base_id: str) -> str:
    digest = hashlib.sha256(f"{policy}\0{base_id}".encode()).hexdigest()[:20]
    return f"model-v1--{policy}--{digest}"


def _payload_hash(payload: dict[str, Any]) -> str:
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


if __name__ == "__main__":
    raise SystemExit(main())
