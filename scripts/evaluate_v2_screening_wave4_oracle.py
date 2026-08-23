"""Evaluate the frozen V2 screening wave-4 population externally."""

from __future__ import annotations

import evaluate_v2_screening_oracle as evaluator
from prepare_v2_screening_wave4_corpus import EXCLUSIONS, MECHANISMS, ROOT, TASK_MANIFEST


EXPECTED_GRADER_SEAL_SHA256 = (
    "sha256:1edb5b46d0f214535b0320848bed45f9dc795b150e8069916ec6f8fd33383b9a"
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
