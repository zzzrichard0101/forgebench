"""Generate the frozen public-only V2 screening wave-4 base population."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command
from forgebench.heldout_base import HeldoutBaseRunner, build_base_matrix
from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import payload_hash
from run_v2_screening_bases import _codex_prefix, _write_json


ROOT = Path(__file__).resolve().parents[1]
TASK_MANIFEST = ROOT / "benchmark" / "v2-development-wave4" / "manifest.json"
FREEZE_PATH = (
    ROOT
    / "experiments"
    / "configs"
    / "v2-screening-wave4-base-generation-freeze-v1.json"
)


def load_freeze(path: Path = FREEZE_PATH) -> dict[str, Any]:
    freeze = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
    if freeze.get("freeze_version") != "v2-screening-wave4-base-generation-freeze-v1":
        raise ValueError("unsupported V2 screening wave-4 base freeze")
    if freeze.get("status") != "frozen" or freeze.get("content_sha256") != payload_hash(freeze):
        raise ValueError("V2 screening wave-4 freeze hash or status is invalid")
    for artifact in freeze.get("artifacts", []):
        candidate = (ROOT / artifact["path"]).resolve(strict=True)
        if not candidate.is_relative_to(ROOT):
            raise ValueError("V2 screening wave-4 freeze artifact escapes repository")
        if canonical_file_hash(candidate) != artifact["sha256"]:
            raise ValueError(f"V2 screening wave-4 artifact mismatch: {artifact['path']}")
    return freeze


def build_plan(freeze: dict[str, Any]) -> dict[str, Any]:
    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    tasks = [bundle.task for bundle in catalog.list()]
    if [task["id"] for task in tasks] != list(freeze["dataset"]["task_ids"]):
        raise ValueError("V2 screening wave-4 task order differs from freeze")
    matrix = build_base_matrix(
        tasks,
        repetitions=int(freeze["execution"]["repetitions_per_task"]),
        snapshot=str(freeze["dataset"]["snapshot"]),
    )
    plan = {
        "schema_version": 1,
        "plan_version": "v2-screening-wave4-base-generation-plan-v1",
        "freeze_sha256": freeze["content_sha256"],
        "snapshot": freeze["dataset"]["snapshot"],
        "public_catalog_sha256": freeze["dataset"]["public_catalog_sha256"],
        "private_grader_seal_sha256": freeze["dataset"]["private_grader_seal_sha256"],
        "harness": freeze["execution"]["harness"],
        "model": freeze["execution"]["model"],
        "reasoning_effort": freeze["execution"]["reasoning_effort"],
        "cli_version": freeze["execution"]["cli_version"],
        "hidden_grader_available_to_runner": False,
        "slots": matrix,
    }
    plan["content_sha256"] = payload_hash(plan)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--attempt-id", default="v2-screening-wave4-base-attempt-1")
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=ROOT / "runs" / "v2-screening-wave4-v1",
    )
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument(
        "--execution-host",
        choices=["auto", "windows", "wsl"],
        default="auto",
    )
    args = parser.parse_args()
    if args.resume and not args.execute:
        parser.error("--resume requires --execute")
    freeze = load_freeze()
    plan = build_plan(freeze)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    attempt_root = args.runs_root / args.attempt_id
    plan_path = attempt_root / "plan.json"
    state_path = attempt_root / "execution.json"
    if plan_path.exists():
        if not args.resume:
            raise FileExistsError("attempt exists; use --resume")
        if json.loads(plan_path.read_text(encoding="utf-8")) != plan:
            raise ValueError("existing V2 screening wave-4 plan differs from freeze")
    else:
        if args.resume:
            raise FileNotFoundError("cannot resume a missing attempt")
        attempt_root.mkdir(parents=True, exist_ok=False)
        _write_json(plan_path, plan)
    state = _load_or_create_state(state_path, plan, args.attempt_id)
    if args.resume:
        for slot in state["slots"]:
            if slot["status"] == "running":
                slot["status"] = "infrastructure_failure"
                slot["detail"] = "previous process ended before slot finalization"
        _write_json(state_path, state)

    execution_host = args.execution_host
    if execution_host == "auto":
        execution_host = "wsl" if platform.system() == "Windows" else "windows"
    codex_home = (args.codex_home or (Path.home() / ".codex")).resolve(strict=True)
    prefix, workspace_mapper = _codex_prefix(
        execution_host=execution_host,
        codex_bin=args.codex_bin,
        codex_home=codex_home,
    )

    def command_factory(prompt: str, workspace: Path) -> list[str]:
        return build_exec_command(
            prefix=prefix,
            prompt=prompt,
            workspace=workspace_mapper(workspace),
            model=str(freeze["execution"]["model"]),
            reasoning_effort=str(freeze["execution"]["reasoning_effort"]),
            persist_session=False,
        )

    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    by_task = {bundle.task["id"]: bundle for bundle in catalog.list()}
    runner = HeldoutBaseRunner(
        attempt_root / "runs",
        args.runs_root / "base-completions",
    )
    for slot in state["slots"]:
        if slot["status"] != "pending":
            continue
        slot["status"] = "running"
        slot["started_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(state_path, state)
        bundle = by_task[slot["task_id"]]
        try:
            result = runner.run(
                task=bundle.task,
                seed=bundle.seed_path,
                repetition=int(slot["repetition"]),
                base_id=slot["base_id"],
                command_factory=command_factory,
            )
            slot.update(result.as_dict())
            slot["status"] = (
                "eligible_public" if result.public_completion_eligible else "visible_failure"
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
        for status in ("eligible_public", "visible_failure", "infrastructure_failure")
    }
    _write_json(state_path, state)
    print(json.dumps(state["counts"], ensure_ascii=False, indent=2))
    return 1 if state["counts"]["infrastructure_failure"] else 0


def _load_or_create_state(
    path: Path, plan: dict[str, Any], attempt_id: str
) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    state = {
        "schema_version": 1,
        "execution_version": "v2-screening-wave4-base-generation-execution-v1",
        "attempt_id": attempt_id,
        "plan_sha256": plan["content_sha256"],
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "slots": [{**slot, "status": "pending"} for slot in plan["slots"]],
    }
    _write_json(path, state)
    return state


if __name__ == "__main__":
    raise SystemExit(main())
