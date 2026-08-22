"""Audit the completed grader-free held-out model-policy replay batch."""

from __future__ import annotations

import json
from pathlib import Path

from forgebench.heldout_model_replay_audit import audit_heldout_model_replays


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = (
    ROOT
    / "runs"
    / "heldout-v1"
    / "model-policy-replays-v1"
    / "heldout-v1-model-policies-v1"
)


def main() -> int:
    report = audit_heldout_model_replays(
        execution_path=BATCH_ROOT / "execution.json",
        runs_root=BATCH_ROOT / "runs",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
