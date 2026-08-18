"""Seal one completed H1a-lite workspace for shared policy replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from run_codex_baseline import MANIFEST_PATH, ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--base-id")
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, MANIFEST_PATH)
    bundle = catalog.get(args.task_id)
    source_root = args.runs_root / args.source_run_id
    source_workspace = source_root / "workspace"
    summary_path = source_root / "run-summary.json"
    if not source_workspace.is_dir() or not summary_path.is_file():
        raise FileNotFoundError(f"source run is incomplete: {source_root}")
    source_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if source_summary.get("task_id") != args.task_id:
        raise ValueError("source run task does not match --task-id")
    if source_summary.get("profile") != "planning-lite":
        raise ValueError("base completion requires a planning-lite source run")

    base_root = args.base_root or (args.runs_root / "base-completions")
    base = BaseCompletionStore(base_root).seal(
        task=bundle.task,
        seed=bundle.seed_path,
        source_workspace=source_workspace,
        source_run_id=args.source_run_id,
        base_id=args.base_id,
    )
    output = {
        "schema_version": 1,
        "base_id": base.base_id,
        "source_run_id": base.source_run_id,
        "task_id": base.task_id,
        "task_version": base.task_version,
        "workspace_hash": base.workspace_hash,
        "public_completion_eligible": base.eligible,
        "base_root": str(base.root),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if base.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
