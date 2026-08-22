"""Recover attempt 2 after the public base-store namespace collision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.heldout_execution_recovery import (
    build_recovery_plan,
    execute_recovery,
)


ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_ROOT = ROOT / "runs" / "heldout-v1" / "heldout-v1-attempt-2"
BASE_ROOT = ROOT / "runs" / "heldout-v1" / "base-completions-attempt-2"
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "heldout-attempt-2-recovery-freeze-v1.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = build_recovery_plan(
        attempt_root=ATTEMPT_ROOT, isolated_base_root=BASE_ROOT.relative_to(ROOT)
    )
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    record = execute_recovery(
        repository_root=ROOT,
        attempt_root=ATTEMPT_ROOT,
        isolated_base_root=BASE_ROOT,
        expected_plan_sha256=freeze["recovery_plan_sha256"],
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
