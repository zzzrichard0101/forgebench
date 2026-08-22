"""Evaluate every frozen V2 screening base with external development graders."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.grader import DeterministicGrader
from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import (
    audit_v2_labeled_corpus,
    payload_hash,
    validate_v2_public_corpus,
)
from prepare_v2_screening_corpus import MECHANISMS, ROOT, TASK_MANIFEST, V1_EXCLUSIONS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-manifest", type=Path, required=True)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--grader-root", type=Path, required=True)
    parser.add_argument("--grader-seal", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--oracle-output", type=Path, required=True)
    args = parser.parse_args()
    public = validate_v2_public_corpus(
        public_root=ROOT,
        manifest_path=args.public_manifest,
        repository_root=ROOT,
        exclusion_manifest_paths=V1_EXCLUSIONS,
    )
    seal = json.loads(args.grader_seal.resolve(strict=True).read_text(encoding="utf-8"))
    if seal.get("content_sha256") is None or seal.get("development_only") is not True:
        raise ValueError("invalid V2 development grader seal")
    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    by_task = {bundle.task["id"]: bundle for bundle in catalog.list()}
    store = BaseCompletionStore(args.base_root)
    grader = DeterministicGrader(args.grader_root)
    result_root = args.result_root.resolve(strict=False)
    result_root.mkdir(parents=True, exist_ok=True)
    labels = []
    for case in public.payload["cases"]:
        bundle = by_task[case["task_id"]]
        base = store.load(case["base_id"])
        grade = grader.grade(bundle.task, base.workspace, bundle.seed_path)
        result_path = result_root / f"{case['case_id']}.json"
        result_path.write_text(
            json.dumps(asdict(grade), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        hidden_success = grade.passed
        labels.append(
            {
                "case_id": case["case_id"],
                "cohort": "passing_control" if hidden_success else "false_completion",
                "hidden_success_before": hidden_success,
                "failure_mechanism": None if hidden_success else MECHANISMS[case["task_id"]],
                "hard_safety_violation_before": False,
                "grader_version": "v2-dev-grader-v1",
                "grader_result_sha256": canonical_file_hash(result_path),
            }
        )
    oracle = {
        "schema_version": 1,
        "catalog_version": "v2-development-oracle-catalog-v1",
        "public_manifest_sha256": public.content_sha256,
        "grader_seal_sha256": seal["content_sha256"],
        "labels": labels,
    }
    oracle["content_sha256"] = payload_hash(oracle)
    oracle_output = args.oracle_output.resolve(strict=False)
    oracle_output.parent.mkdir(parents=True, exist_ok=True)
    oracle_output.write_text(json.dumps(oracle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = audit_v2_labeled_corpus(public, oracle_catalog_path=oracle_output)
    aggregate = audit.as_dict()
    aggregate["cohort_counts"] = {
        cohort: sum(label["cohort"] == cohort for label in labels)
        for cohort in ("false_completion", "passing_control")
    }
    task_by_case = {case["case_id"]: case["task_cluster_id"] for case in public.payload["cases"]}
    false_clusters = {
        task_by_case[label["case_id"]]
        for label in labels
        if label["cohort"] == "false_completion"
    }
    passing_clusters = {
        task_by_case[label["case_id"]]
        for label in labels
        if label["cohort"] == "passing_control"
    }
    false_mechanisms = {
        label["failure_mechanism"]
        for label in labels
        if label["cohort"] == "false_completion"
    }
    aggregate["screening_population"] = {
        "false_completion_clusters": len(false_clusters),
        "passing_control_clusters": len(passing_clusters),
        "failure_mechanisms": len(false_mechanisms),
        "ready": (
            len(false_clusters) >= 6
            and len(passing_clusters) >= 6
            and len(false_mechanisms) >= 4
        ),
    }
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
