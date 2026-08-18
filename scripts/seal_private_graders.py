"""Run only in the independent grader custodian environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.heldout_intake import create_private_grader_seal


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grader-root", type=Path, required=True)
    parser.add_argument("--task-id", action="append", required=True)
    parser.add_argument("--custodian-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attest-untouched-seed-fails", action="store_true", required=True)
    parser.add_argument("--attest-known-good-outcome-passes", action="store_true", required=True)
    parser.add_argument("--attest-protected-mutation-detected", action="store_true", required=True)
    parser.add_argument("--attest-three-repeat-grade-deterministic", action="store_true", required=True)
    args = parser.parse_args()
    payload = create_private_grader_seal(
        args.grader_root,
        args.task_id,
        custodian_id=args.custodian_id,
        output_path=args.output,
        attest_untouched_seed_fails=args.attest_untouched_seed_fails,
        attest_known_good_outcome_passes=args.attest_known_good_outcome_passes,
        attest_protected_mutation_detected=args.attest_protected_mutation_detected,
        attest_three_repeat_grade_deterministic=args.attest_three_repeat_grade_deterministic,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
