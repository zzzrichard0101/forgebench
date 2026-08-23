"""Evaluate the frozen V2 screening wave-3 population externally."""

from __future__ import annotations

import evaluate_v2_screening_oracle as evaluator
from prepare_v2_screening_wave3_corpus import EXCLUSIONS, MECHANISMS, ROOT, TASK_MANIFEST


EXPECTED_GRADER_SEAL_SHA256 = (
    "sha256:57bd25d24c9810cfe3a84e15efaf5cede1ebba6ed3d7185b98327f1ba5dfaf96"
)


def main() -> int:
    evaluator.ROOT = ROOT
    evaluator.TASK_MANIFEST = TASK_MANIFEST
    evaluator.V1_EXCLUSIONS = EXCLUSIONS
    evaluator.MECHANISMS = MECHANISMS
    evaluator.EXPECTED_GRADER_SEAL_SHA256 = EXPECTED_GRADER_SEAL_SHA256
    return evaluator.main()


if __name__ == "__main__":
    raise SystemExit(main())
