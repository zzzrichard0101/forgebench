"""Validate a private evaluator result against the frozen public request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.private_evaluation_handoff import validate_private_evaluation_result


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--request",
        type=Path,
        default=ROOT / "experiments/configs/heldout-private-evaluation-request-v1.json",
    )
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    counts = validate_private_evaluation_result(request=request, result=result)
    print(json.dumps({"status": "valid", **counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
