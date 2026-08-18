"""Create an evaluation-only hidden label for a sealed base completion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore, HiddenLabelStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.grader import DeterministicGrader
from run_codex_baseline import GRADERS, MANIFEST_PATH, ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--base-id", required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--labels-root", type=Path)
    args = parser.parse_args()

    bundle = BenchmarkCatalog(ROOT, MANIFEST_PATH).get(args.task_id)
    base_root = args.base_root or (args.runs_root / "base-completions")
    labels_root = args.labels_root or (args.runs_root / "hidden-base-labels")
    base = BaseCompletionStore(base_root).load(args.base_id)
    grade = HiddenLabelStore(
        labels_root, DeterministicGrader(GRADERS)
    ).evaluate(base=base, task=bundle.task, seed=bundle.seed_path)
    output = {
        "schema_version": 1,
        "base_id": base.base_id,
        "task_id": base.task_id,
        "workspace_hash": base.workspace_hash,
        "hidden_task_passed": grade.passed,
        "label_path": str(labels_root / f"{base.base_id}.json"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
