"""Seal every eligible V2 screening base into a public corpus manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import payload_hash, validate_v2_public_corpus


ROOT = Path(__file__).resolve().parents[1]
TASK_MANIFEST = ROOT / "benchmark" / "v2-development" / "manifest.json"
V1_EXCLUSIONS = [ROOT / "benchmark" / "manifest.json", ROOT / "heldout-public" / "manifest.json"]
MECHANISMS = {
    "v2-canonical-handle-registry": "unicode_normalization",
    "v2-converter-command-boundary": "injection",
    "v2-package-member-policy": "containment",
    "v2-recursive-schema-contract": "schema",
    "v2-retry-after-policy": "temporal_retry",
    "v2-upload-budget-ledger": "numeric_aggregate",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attempt-root",
        type=Path,
        default=ROOT / "runs" / "v2-screening-v1" / "v2-screening-base-attempt-1",
    )
    parser.add_argument(
        "--base-root",
        type=Path,
        default=ROOT / "runs" / "v2-screening-v1" / "base-completions",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "runs" / "v2-screening-v1" / "corpus" / "public-manifest.json",
    )
    args = parser.parse_args()
    state_path = args.attempt_root.resolve(strict=True) / "execution.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "completed" or state.get("counts", {}).get("infrastructure_failure") != 0:
        raise ValueError("V2 screening execution is incomplete or has infrastructure failures")
    if len(state.get("slots", [])) != 18:
        raise ValueError("V2 screening execution must contain all 18 frozen slots")
    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    by_task = {bundle.task["id"]: bundle for bundle in catalog.list()}
    base_store = BaseCompletionStore(args.base_root)
    cases = []
    eligible_slots = [slot for slot in state["slots"] if slot["status"] == "eligible_public"]
    for index, slot in enumerate(eligible_slots, start=1):
        bundle = by_task[slot["task_id"]]
        base = base_store.load(slot["base_id"])
        if not base.eligible or base.task_id != bundle.task["id"]:
            raise ValueError(f"ineligible or mismatched sealed base: {slot['base_id']}")
        task_path = Path(next(record["task_path"] for record in json.loads(TASK_MANIFEST.read_text(encoding="utf-8"))["tasks"] if record["id"] == slot["task_id"]))
        base_record = base.root / "public-base-record.json"
        evidence = args.attempt_root / "runs" / slot["run_id"] / "heldout-base-run.json"
        cases.append(
            {
                "case_id": f"v2-screening-case-{index:02d}",
                "task_id": bundle.task["id"],
                "task_version": bundle.task["version"],
                "task_cluster_id": bundle.task["id"],
                "repository_lineage": f"{bundle.task['id']}-lineage",
                "seed_revision_sha256": bundle.task["seed_repo"]["revision"],
                "split": "repair_dev",
                "task_path": task_path.as_posix(),
                "task_content_sha256": canonical_file_hash(ROOT / task_path),
                "base_id": base.base_id,
                "base_artifact_path": base_record.relative_to(ROOT).as_posix(),
                "base_content_sha256": canonical_file_hash(base_record),
                "public_evidence_path": evidence.relative_to(ROOT).as_posix(),
                "public_evidence_sha256": canonical_file_hash(evidence),
                "public_completion_gate_passed": True,
            }
        )
    payload = {
        "schema_version": 1,
        "corpus_version": "v2-development-corpus-v1",
        "snapshot": "v2-dev-screening-bases-v1",
        "frozen": True,
        "cases": cases,
    }
    payload["content_sha256"] = payload_hash(payload)
    output = args.output.resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_v2_public_corpus(
        public_root=ROOT,
        manifest_path=output,
        repository_root=ROOT,
        exclusion_manifest_paths=V1_EXCLUSIONS,
    )
    summary = {
        "status": "public_corpus_frozen",
        "total_slots": 18,
        "eligible_cases": len(cases),
        "visible_failures": state["counts"]["visible_failure"],
        "mechanisms": sorted(set(MECHANISMS[case["task_id"]] for case in cases)),
        "public_manifest_sha256": payload["content_sha256"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

