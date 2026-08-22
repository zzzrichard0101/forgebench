"""Audit V2 development graders in an external curator workspace."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog
from forgebench.grader import DeterministicGrader
from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmark" / "v2-development" / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grader-root", type=Path, required=True)
    parser.add_argument("--known-good-root", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repetitions < 3:
        parser.error("at least three repetitions are required")

    grader_root = args.grader_root.resolve(strict=True)
    known_good_root = args.known_good_root.resolve(strict=True)
    output = args.output.resolve(strict=False)
    if output == grader_root or output.is_relative_to(grader_root):
        raise ValueError("audit output must be outside the grader root")
    grader = DeterministicGrader(grader_root)
    catalog = BenchmarkCatalog(ROOT, MANIFEST)
    records = []
    for bundle in catalog.list():
        task_id = bundle.task["id"]
        overlay = (known_good_root / task_id).resolve(strict=True)
        seed_outcomes = [
            grader.grade(bundle.task, bundle.seed_path, bundle.seed_path).passed
            for _ in range(args.repetitions)
        ]
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            shutil.copytree(bundle.seed_path, workspace)
            shutil.copytree(overlay, workspace, dirs_exist_ok=True)
            known_good_outcomes = [
                grader.grade(bundle.task, workspace, bundle.seed_path).passed
                for _ in range(args.repetitions)
            ]
            protected = workspace / "requirements.txt"
            protected.write_text("# unauthorized mutation\n", encoding="utf-8")
            mutation_grade = grader.grade(bundle.task, workspace, bundle.seed_path)
            protected_detection = any(
                check.check_type == "workspace_policy" and not check.passed
                for check in mutation_grade.checks
            )
        records.append(
            {
                "task_id": task_id,
                "seed_outcomes": seed_outcomes,
                "known_good_outcomes": known_good_outcomes,
                "protected_mutation_detected": protected_detection,
                "grader_sha256": canonical_file_hash(
                    grader_root / task_id / "test_contract.py"
                ),
            }
        )
    passed = all(
        not any(record["seed_outcomes"])
        and all(record["known_good_outcomes"])
        and record["protected_mutation_detected"]
        for record in records
    )
    payload = {
        "schema_version": 1,
        "audit_version": "v2-development-grader-audit-v1",
        "status": "passed" if passed else "failed",
        "repetitions": args.repetitions,
        "task_count": len(records),
        "outcome_counts": dict(
            Counter(
                "valid"
                if not any(record["seed_outcomes"])
                and all(record["known_good_outcomes"])
                and record["protected_mutation_detected"]
                else "invalid"
                for record in records
            )
        ),
        "tasks": records,
        "privacy": {
            "grader_source_committed": False,
            "known_good_committed": False,
            "output_contains_test_source": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
