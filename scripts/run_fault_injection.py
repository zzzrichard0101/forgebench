"""Run the predeclared deterministic H2 fault-injection experiment."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from forgebench.fault_injection import run_fault_injection_experiment


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "experiments" / "configs" / "h2-fault-injection-v0.1.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    experiment_root = args.runs_root / "fault-injection" / uuid.uuid4().hex
    seed = experiment_root / "seed"
    seed.mkdir(parents=True, exist_ok=True)
    result = run_fault_injection_experiment(
        runs_root=experiment_root / "runs", seed=seed, config=config
    )
    output_path = experiment_root / "result.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"result_path": str(output_path), **result["summary"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["summary"]["mechanism_acceptance_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
