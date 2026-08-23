"""Seal every eligible V2 screening wave-3 base into a public corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import payload_hash, validate_v2_public_corpus


ROOT = Path(__file__).resolve().parents[1]
TASK_MANIFEST = ROOT / "benchmark" / "v2-development-wave3" / "manifest.json"
EXCLUSIONS = [
    ROOT / "benchmark" / "manifest.json",
    ROOT / "heldout-public" / "manifest.json",
    ROOT / "benchmark" / "v2-development" / "manifest.json",
    ROOT / "benchmark" / "v2-development-wave2" / "manifest.json",
]
MECHANISMS = {
    "v2-callback-shutdown-stack": "lifecycle_resource",
    "v2-credit-reservation-ledger": "numeric_aggregate",
    "v2-delegated-scope-checker": "authorization",
    "v2-sandbox-path-mapper": "containment",
    "v2-subprocess-request-builder": "injection",
    "v2-tagged-event-decoder": "schema",
    "v2-typed-env-loader": "configuration_migration",
    "v2-unicode-namespace-map": "unicode_normalization",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attempt-root",
        type=Path,
        default=(
            ROOT
            / "runs"
            / "v2-screening-wave3-v1"
            / "v2-screening-wave3-base-attempt-1"
        ),
    )
    parser.add_argument(
        "--base-root",
        type=Path,
        default=ROOT / "runs" / "v2-screening-wave3-v1" / "base-completions",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "runs"
            / "v2-screening-wave3-v1"
            / "corpus"
            / "public-manifest.json"
        ),
    )
    args = parser.parse_args()
    attempt_root = args.attempt_root.resolve(strict=True)
    state_path = attempt_root / "execution.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if (
        state.get("status") != "completed"
        or state.get("counts", {}).get("infrastructure_failure") != 0
    ):
        raise ValueError("V2 screening wave-3 execution is incomplete")
    if len(state.get("slots", [])) != 24:
        raise ValueError("V2 screening wave-3 execution must contain all 24 slots")
    terminal = {"eligible_public", "visible_failure"}
    if any(slot.get("status") not in terminal for slot in state["slots"]):
        raise ValueError("every V2 screening wave-3 slot must be terminal")

    catalog = BenchmarkCatalog(ROOT, TASK_MANIFEST)
    by_task = {bundle.task["id"]: bundle for bundle in catalog.list()}
    manifest_records = json.loads(TASK_MANIFEST.read_text(encoding="utf-8"))["tasks"]
    base_store = BaseCompletionStore(args.base_root)
    eligible_slots = [
        slot for slot in state["slots"] if slot["status"] == "eligible_public"
    ]
    cases = []
    for index, slot in enumerate(eligible_slots, start=1):
        bundle = by_task[slot["task_id"]]
        base = base_store.load(slot["base_id"])
        if not base.eligible or base.task_id != bundle.task["id"]:
            raise ValueError(f"ineligible or mismatched sealed base: {slot['base_id']}")
        task_path = Path(
            next(
                record["task_path"]
                for record in manifest_records
                if record["id"] == slot["task_id"]
            )
        )
        base_record = base.root / "public-base-record.json"
        evidence = attempt_root / "runs" / slot["run_id"] / "heldout-base-run.json"
        cases.append(
            {
                "case_id": f"v2-screening-wave3-case-{index:02d}",
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
        "snapshot": "v2-dev-screening-wave3-bases-v1",
        "frozen": True,
        "cases": cases,
    }
    payload["content_sha256"] = payload_hash(payload)
    output = args.output.resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    validate_v2_public_corpus(
        public_root=ROOT,
        manifest_path=output,
        repository_root=ROOT,
        exclusion_manifest_paths=EXCLUSIONS,
    )
    summary = {
        "status": "public_corpus_frozen",
        "total_slots": 24,
        "eligible_cases": len(cases),
        "visible_failures": state["counts"]["visible_failure"],
        "mechanisms": sorted({MECHANISMS[case["task_id"]] for case in cases}),
        "public_manifest_sha256": payload["content_sha256"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
