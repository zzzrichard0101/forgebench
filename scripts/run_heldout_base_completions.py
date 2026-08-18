"""Generate the frozen held-out v1 public base-completion population."""

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

from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command
from forgebench.heldout_base import HeldoutBaseRunner, build_base_matrix
from forgebench.heldout_intake import validate_heldout_intake
from run_codex_baseline import (
    PINNED_CODEX_VERSION,
    ROOT,
    find_local_codex,
    find_local_linux_codex,
    windows_to_wsl,
)


HELDOUT_MANIFEST = ROOT / "heldout-public" / "manifest.json"
PRIVATE_SEAL = ROOT / "private-seal.json"
DEVELOPMENT_MANIFEST = ROOT / "benchmark" / "manifest.json"
POLICY_FREEZE = (
    ROOT / "experiments" / "configs" / "selective-verification-policy-freeze-v1.json"
)
FROZEN_MODEL = "gpt-5.6-sol"
FROZEN_REASONING_EFFORT = "medium"
FROZEN_REPETITIONS = 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--attempt-id", default="heldout-v1-attempt-1")
    parser.add_argument("--task-id", action="append")
    parser.add_argument("--repetitions", type=int, default=FROZEN_REPETITIONS)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "heldout-v1")
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument(
        "--execution-host", choices=["auto", "windows", "wsl"], default="auto"
    )
    args = parser.parse_args()
    if args.resume and not args.execute:
        parser.error("--resume requires --execute")

    intake = validate_heldout_intake(
        public_root=ROOT,
        heldout_manifest_path=HELDOUT_MANIFEST,
        development_manifest_path=DEVELOPMENT_MANIFEST,
        private_seal_path=PRIVATE_SEAL,
        policy_freeze_path=POLICY_FREEZE,
        policy_repository_root=ROOT,
    )
    catalog = BenchmarkCatalog(ROOT, HELDOUT_MANIFEST)
    bundles = list(catalog.list())
    if args.task_id:
        requested = list(dict.fromkeys(args.task_id))
        bundles = [catalog.get(task_id) for task_id in requested]
    tasks = [bundle.task for bundle in bundles]
    matrix = build_base_matrix(
        tasks, repetitions=args.repetitions, snapshot=intake.snapshot
    )
    plan = {
        "schema_version": 1,
        "plan_version": "heldout-base-generation-plan-v1",
        "attempt_id": args.attempt_id,
        "snapshot": intake.snapshot,
        "public_catalog_sha256": intake.public_catalog_sha256,
        "private_seal_sha256": intake.private_seal_sha256,
        "policy_freeze_sha256": intake.policy_freeze_sha256,
        "harness": "H1a-lite-bounded-planning",
        "model": FROZEN_MODEL,
        "reasoning_effort": FROZEN_REASONING_EFFORT,
        "cli_version": PINNED_CODEX_VERSION,
        "hidden_grader_available_to_runner": False,
        "slots": matrix,
    }
    plan["content_sha256"] = _payload_hash(plan)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if args.task_id or args.repetitions != FROZEN_REPETITIONS:
        parser.error(
            "a real held-out attempt must execute all tasks with exactly 3 repetitions"
        )

    attempt_root = args.runs_root / args.attempt_id
    plan_path = attempt_root / "plan.json"
    state_path = attempt_root / "execution.json"
    if plan_path.exists():
        if not args.resume:
            raise FileExistsError("attempt already exists; use --resume")
        existing = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing != plan:
            raise ValueError("existing held-out attempt plan does not match frozen plan")
    else:
        if args.resume:
            raise FileNotFoundError("cannot resume a missing held-out attempt")
        attempt_root.mkdir(parents=True, exist_ok=False)
        _write_json(plan_path, plan)

    state = _load_or_create_state(state_path, plan)
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
    os.environ["CODEX_HOME"] = str(codex_home)
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
            model=FROZEN_MODEL,
            reasoning_effort=FROZEN_REASONING_EFFORT,
            persist_session=False,
        )

    runner = HeldoutBaseRunner(
        attempt_root / "runs",
        args.base_root or (args.runs_root / "base-completions"),
    )
    by_task = {bundle.task["id"]: bundle for bundle in bundles}
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
                "eligible_public"
                if result.public_completion_eligible
                else "visible_failure"
            )
        except Exception as exc:  # retain failures and continue the frozen matrix
            slot["status"] = "infrastructure_failure"
            slot["detail"] = f"{type(exc).__name__}: {exc}"
        slot["finished_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(state_path, state)

    state["status"] = "completed"
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    state["counts"] = {
        status: sum(slot["status"] == status for slot in state["slots"])
        for status in (
            "eligible_public",
            "visible_failure",
            "infrastructure_failure",
        )
    }
    _write_json(state_path, state)
    print(json.dumps(state["counts"], ensure_ascii=False, indent=2))
    return 1 if state["counts"]["infrastructure_failure"] else 0


def _codex_prefix(
    *, execution_host: str, codex_bin: Path | None, codex_home: Path
) -> tuple[list[str], Any]:
    if execution_host == "wsl":
        codex = (codex_bin or find_local_linux_codex()).resolve(strict=True)
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        if wsl is None:
            raise FileNotFoundError("WSL executable not found")
        return (
            [
                wsl,
                "-d",
                "Ubuntu",
                "--",
                "env",
                f"CODEX_HOME={windows_to_wsl(codex_home)}",
                windows_to_wsl(codex),
            ],
            windows_to_wsl,
        )
    codex = (codex_bin or find_local_codex()).resolve(strict=True)
    return [str(codex)], str


def _load_or_create_state(path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    state = {
        "schema_version": 1,
        "execution_version": "heldout-base-generation-execution-v1",
        "attempt_id": plan["attempt_id"],
        "plan_sha256": plan["content_sha256"],
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "slots": [{**slot, "status": "pending"} for slot in plan["slots"]],
    }
    _write_json(path, state)
    return state


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
