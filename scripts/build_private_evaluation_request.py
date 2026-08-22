"""Build the public, hash-bound handoff for an external private evaluator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.private_evaluation_handoff import build_private_evaluation_request


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = (
    ROOT
    / "runs"
    / "heldout-v1"
    / "model-policy-replays-v1"
    / "heldout-v1-model-policies-v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    request = build_private_evaluation_request(
        assignment_path=ROOT / "experiments/configs/heldout-policy-assignment-v1.json",
        execution_path=BATCH_ROOT / "execution.json",
        base_root=ROOT / "runs/heldout-v1/base-completions-attempt-2",
        replay_runs_root=BATCH_ROOT / "runs",
        repo_root=ROOT,
        public_result_freeze_path=(
            ROOT / "experiments/configs/heldout-model-policy-result-freeze-v1.json"
        ),
    )
    rendered = json.dumps(request, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
