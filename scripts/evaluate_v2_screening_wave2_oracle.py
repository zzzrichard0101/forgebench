"""Evaluate the frozen V2 screening wave-2 population with external graders."""

from __future__ import annotations

import evaluate_v2_screening_oracle as evaluator
from prepare_v2_screening_wave2_corpus import EXCLUSIONS, MECHANISMS, ROOT, TASK_MANIFEST


def main() -> int:
    evaluator.ROOT = ROOT
    evaluator.TASK_MANIFEST = TASK_MANIFEST
    evaluator.V1_EXCLUSIONS = EXCLUSIONS
    evaluator.MECHANISMS = MECHANISMS
    return evaluator.main()


if __name__ == "__main__":
    raise SystemExit(main())
