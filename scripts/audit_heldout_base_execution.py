"""Audit a held-out base-generation execution without hidden grader access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.heldout_execution_audit import audit_heldout_base_execution
from run_codex_baseline import ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execution",
        type=Path,
        default=(
            ROOT
            / "runs"
            / "heldout-v1"
            / "heldout-v1-attempt-1"
            / "execution.json"
        ),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=(
            ROOT / "runs" / "heldout-v1" / "heldout-v1-attempt-1" / "runs"
        ),
    )
    parser.add_argument(
        "--base-root",
        type=Path,
        default=ROOT / "runs" / "heldout-v1" / "base-completions",
    )
    args = parser.parse_args()
    report = audit_heldout_base_execution(
        execution_path=args.execution,
        runs_root=args.runs_root,
        base_root=args.base_root,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["decision"]["primary_comparison_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
