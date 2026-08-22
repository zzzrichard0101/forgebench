"""Create a sanitized aggregate report from an external private result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.private_evaluation_analysis import analyze_private_evaluation


ROOT = Path(__file__).resolve().parents[1]
BATCH_RUNS = (
    ROOT
    / "runs/heldout-v1/model-policy-replays-v1/heldout-v1-model-policies-v1/runs"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-result", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze_private_evaluation(
        request_path=ROOT / "experiments/configs/heldout-private-evaluation-request-v1.json",
        result_path=args.private_result,
        replay_runs_root=BATCH_RUNS,
        policy_freeze_path=(
            ROOT / "experiments/configs/selective-verification-policy-freeze-v1.json"
        ),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
