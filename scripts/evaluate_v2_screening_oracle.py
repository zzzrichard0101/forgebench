"""Evaluate every frozen V2 screening base with external development graders."""

from __future__ import annotations

import argparse
import hashlib
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


EXPECTED_GRADER_SEAL_SHA256: str | None = None


def verify_grader_seal(grader_root: Path, seal: dict) -> None:
    if seal.get("content_sha256") != payload_hash(seal):
        raise ValueError("V2 development grader seal content hash is invalid")
    if seal.get("development_only") is not True:
        raise ValueError("invalid V2 development grader seal scope")
    expected = {
        record["task_id"]: record["grader_sha256"]
        for record in seal.get("task_graders", [])
    }
    actual_ids = {path.name for path in grader_root.iterdir() if path.is_dir()}
    if not expected or set(expected) != actual_ids:
        raise ValueError("grader directories do not match the sealed task set")
    for task_id, expected_hash in expected.items():
        task_root = grader_root / task_id
        files = sorted(path for path in task_root.rglob("*") if path.is_file())
        if not files:
            raise ValueError(f"grader directory is empty: {task_id}")
        digest = hashlib.sha256()
        for path in files:
            relative = path.relative_to(task_root).as_posix().encode("utf-8")
            file_hash = canonical_file_hash(path).encode("ascii")
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(file_hash)
        actual_hash = "sha256:" + digest.hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"grader content differs from seal: {task_id}")


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
    grader_root = args.grader_root.resolve(strict=True)
    verify_grader_seal(grader_root, seal)
    if (
        EXPECTED_GRADER_SEAL_SHA256 is not None
        and seal["content_sha256"] != EXPECTED_GRADER_SEAL_SHA256
    ):
        raise ValueError("grader seal differs from the frozen public population")
    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    by_task = {bundle.task["id"]: bundle for bundle in catalog.list()}
    store = BaseCompletionStore(args.base_root)
    grader = DeterministicGrader(grader_root)
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
