from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .policy_freeze import canonical_file_hash


CORPUS_VERSION = "v2-development-corpus-v1"
ORACLE_CATALOG_VERSION = "v2-development-oracle-catalog-v1"
SPLITS = {"repair_dev", "mechanism_validation"}
COHORTS = {"false_completion", "passing_control"}
MECHANISMS = {
    "authorization",
    "configuration_migration",
    "containment",
    "injection",
    "lifecycle_resource",
    "numeric_aggregate",
    "schema",
    "serialization_redaction",
    "temporal_retry",
    "unicode_normalization",
}
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PUBLIC_CASE_FIELDS = {
    "case_id",
    "task_id",
    "task_version",
    "task_cluster_id",
    "repository_lineage",
    "seed_revision_sha256",
    "split",
    "task_path",
    "task_content_sha256",
    "base_id",
    "base_artifact_path",
    "base_content_sha256",
    "public_evidence_path",
    "public_evidence_sha256",
    "public_completion_gate_passed",
}
ORACLE_LABEL_FIELDS = {
    "case_id",
    "cohort",
    "hidden_success_before",
    "failure_mechanism",
    "hard_safety_violation_before",
    "grader_version",
    "grader_result_sha256",
}


@dataclass(frozen=True)
class V2PublicCorpus:
    path: Path
    payload: dict[str, Any]

    @property
    def content_sha256(self) -> str:
        return str(self.payload["content_sha256"])


@dataclass(frozen=True)
class V2CorpusAudit:
    snapshot: str
    frozen: bool
    case_count: int
    split_counts: dict[str, int]
    task_cluster_count: int
    repository_lineage_count: int
    false_completion_clusters: int
    passing_control_clusters: int
    failure_mechanisms: int
    validation_gate_population_ready: bool
    public_manifest_sha256: str
    oracle_catalog_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "audit_version": "v2-development-corpus-audit-v1",
            "snapshot": self.snapshot,
            "frozen": self.frozen,
            "case_count": self.case_count,
            "split_counts": self.split_counts,
            "task_cluster_count": self.task_cluster_count,
            "repository_lineage_count": self.repository_lineage_count,
            "oracle_aggregate": {
                "false_completion_clusters": self.false_completion_clusters,
                "passing_control_clusters": self.passing_control_clusters,
                "failure_mechanisms": self.failure_mechanisms,
            },
            "validation_gate_population_ready": self.validation_gate_population_ready,
            "public_manifest_sha256": self.public_manifest_sha256,
            "oracle_catalog_sha256": self.oracle_catalog_sha256,
        }


def payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_v2_public_corpus(
    *,
    public_root: Path,
    manifest_path: Path,
    repository_root: Path,
    exclusion_manifest_paths: Sequence[Path],
) -> V2PublicCorpus:
    public_root = public_root.resolve(strict=True)
    repository_root = repository_root.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if set(payload) != {
        "schema_version",
        "corpus_version",
        "snapshot",
        "frozen",
        "cases",
        "content_sha256",
    }:
        raise ValueError("V2 public corpus manifest fields are invalid")
    if payload.get("schema_version") != 1 or payload.get("corpus_version") != CORPUS_VERSION:
        raise ValueError("unsupported V2 public corpus version")
    if not isinstance(payload.get("snapshot"), str) or not payload["snapshot"].startswith("v2-dev-"):
        raise ValueError("V2 public corpus snapshot is invalid")
    if not isinstance(payload.get("frozen"), bool):
        raise ValueError("V2 public corpus frozen flag must be boolean")
    if payload.get("content_sha256") != payload_hash(payload):
        raise ValueError("V2 public corpus content hash mismatch")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("V2 public corpus must contain cases")

    excluded_task_ids, excluded_seed_revisions = _excluded_v1_identity(
        repository_root, exclusion_manifest_paths
    )
    case_ids: set[str] = set()
    base_ids: set[str] = set()
    cluster_identity: dict[str, tuple[str, str]] = {}
    for case in cases:
        _validate_public_case(case, public_root)
        case_id = str(case["case_id"])
        base_id = str(case["base_id"])
        if case_id in case_ids:
            raise ValueError(f"duplicate V2 case ID: {case_id}")
        if base_id in base_ids:
            raise ValueError(f"duplicate V2 base ID: {base_id}")
        case_ids.add(case_id)
        base_ids.add(base_id)
        if case["task_id"] in excluded_task_ids:
            raise ValueError(f"V2 task ID overlaps excluded V1 data: {case['task_id']}")
        if case["seed_revision_sha256"] in excluded_seed_revisions:
            raise ValueError(f"V2 seed revision overlaps excluded V1 data: {case_id}")
        identity = (str(case["task_id"]), str(case["repository_lineage"]))
        previous = cluster_identity.setdefault(str(case["task_cluster_id"]), identity)
        if previous != identity:
            raise ValueError("one task cluster maps to multiple tasks or lineages")
    return V2PublicCorpus(path=manifest_path, payload=payload)


def audit_v2_labeled_corpus(
    public_corpus: V2PublicCorpus,
    *,
    oracle_catalog_path: Path,
) -> V2CorpusAudit:
    oracle_path = oracle_catalog_path.resolve(strict=True)
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    if set(oracle) != {
        "schema_version",
        "catalog_version",
        "public_manifest_sha256",
        "grader_seal_sha256",
        "labels",
        "content_sha256",
    }:
        raise ValueError("V2 oracle catalog fields are invalid")
    if oracle.get("schema_version") != 1 or oracle.get("catalog_version") != ORACLE_CATALOG_VERSION:
        raise ValueError("unsupported V2 oracle catalog version")
    if oracle.get("content_sha256") != payload_hash(oracle):
        raise ValueError("V2 oracle catalog content hash mismatch")
    if oracle.get("public_manifest_sha256") != public_corpus.content_sha256:
        raise ValueError("V2 oracle catalog targets a different public manifest")
    _require_hash(oracle.get("grader_seal_sha256"), "grader seal")
    labels = oracle.get("labels")
    if not isinstance(labels, list) or not labels:
        raise ValueError("V2 oracle catalog must contain labels")

    label_by_case: dict[str, dict[str, Any]] = {}
    for label in labels:
        _validate_oracle_label(label)
        case_id = str(label["case_id"])
        if case_id in label_by_case:
            raise ValueError(f"duplicate V2 oracle label: {case_id}")
        label_by_case[case_id] = label
    cases = public_corpus.payload["cases"]
    public_ids = {str(case["case_id"]) for case in cases}
    if set(label_by_case) != public_ids:
        raise ValueError("V2 oracle labels do not exactly match public cases")

    validation_cases = [case for case in cases if case["split"] == "mechanism_validation"]
    false_clusters = {
        case["task_cluster_id"]
        for case in validation_cases
        if label_by_case[case["case_id"]]["cohort"] == "false_completion"
    }
    passing_clusters = {
        case["task_cluster_id"]
        for case in validation_cases
        if label_by_case[case["case_id"]]["cohort"] == "passing_control"
    }
    mechanisms = {
        label_by_case[case["case_id"]]["failure_mechanism"]
        for case in validation_cases
        if label_by_case[case["case_id"]]["cohort"] == "false_completion"
    }
    ready = (
        public_corpus.payload["frozen"] is True
        and len(false_clusters) >= 15
        and len(passing_clusters) >= 15
        and len(mechanisms) >= 6
    )
    return V2CorpusAudit(
        snapshot=str(public_corpus.payload["snapshot"]),
        frozen=bool(public_corpus.payload["frozen"]),
        case_count=len(cases),
        split_counts=dict(sorted(Counter(case["split"] for case in cases).items())),
        task_cluster_count=len({case["task_cluster_id"] for case in cases}),
        repository_lineage_count=len({case["repository_lineage"] for case in cases}),
        false_completion_clusters=len(false_clusters),
        passing_control_clusters=len(passing_clusters),
        failure_mechanisms=len(mechanisms),
        validation_gate_population_ready=ready,
        public_manifest_sha256=public_corpus.content_sha256,
        oracle_catalog_sha256=str(oracle["content_sha256"]),
    )


def _validate_public_case(case: Any, public_root: Path) -> None:
    if not isinstance(case, dict) or set(case) != PUBLIC_CASE_FIELDS:
        raise ValueError("V2 public case fields are invalid")
    for field in ("case_id", "task_id", "task_cluster_id", "repository_lineage", "base_id"):
        if not isinstance(case[field], str) or SLUG_PATTERN.fullmatch(case[field]) is None:
            raise ValueError(f"V2 public case {field} is invalid")
    if not isinstance(case["task_version"], int) or isinstance(case["task_version"], bool) or case["task_version"] < 1:
        raise ValueError("V2 task version is invalid")
    if case["split"] not in SPLITS:
        raise ValueError("V2 public case split is invalid")
    if case["public_completion_gate_passed"] is not True:
        raise ValueError("V2 corpus accepts only public-gate-passing bases")
    _require_hash(case["seed_revision_sha256"], "seed revision")
    for path_field, hash_field in (
        ("task_path", "task_content_sha256"),
        ("base_artifact_path", "base_content_sha256"),
        ("public_evidence_path", "public_evidence_sha256"),
    ):
        path = _resolve_public_file(public_root, case[path_field])
        _require_hash(case[hash_field], hash_field)
        if canonical_file_hash(path) != case[hash_field]:
            raise ValueError(f"V2 public artifact hash mismatch: {case[path_field]}")


def _validate_oracle_label(label: Any) -> None:
    if not isinstance(label, dict) or set(label) != ORACLE_LABEL_FIELDS:
        raise ValueError("V2 oracle label fields are invalid")
    if not isinstance(label["case_id"], str) or SLUG_PATTERN.fullmatch(label["case_id"]) is None:
        raise ValueError("V2 oracle case ID is invalid")
    cohort = label["cohort"]
    if cohort not in COHORTS:
        raise ValueError("V2 oracle cohort is invalid")
    if label["hard_safety_violation_before"] is not False:
        raise ValueError("V2 base with a prior hard-safety violation is ineligible")
    if not isinstance(label["grader_version"], str) or SLUG_PATTERN.fullmatch(label["grader_version"]) is None:
        raise ValueError("V2 oracle grader version is invalid")
    _require_hash(label["grader_result_sha256"], "grader result")
    if cohort == "false_completion":
        if label["hidden_success_before"] is not False or label["failure_mechanism"] not in MECHANISMS:
            raise ValueError("false-completion label is inconsistent")
    elif label["hidden_success_before"] is not True or label["failure_mechanism"] is not None:
        raise ValueError("passing-control label is inconsistent")


def _excluded_v1_identity(
    repository_root: Path, manifest_paths: Sequence[Path]
) -> tuple[set[str], set[str]]:
    task_ids: set[str] = set()
    seed_revisions: set[str] = set()
    if not manifest_paths:
        raise ValueError("at least one V1 exclusion manifest is required")
    for manifest_path in manifest_paths:
        manifest = json.loads(manifest_path.resolve(strict=True).read_text(encoding="utf-8"))
        records = manifest.get("tasks")
        if not isinstance(records, list):
            raise ValueError("V1 exclusion manifest has no task records")
        for record in records:
            task_ids.add(str(record["id"]))
            task_path = _resolve_public_file(repository_root, record["task_path"])
            task = json.loads(task_path.read_text(encoding="utf-8"))
            revision = task.get("seed_repo", {}).get("revision")
            if isinstance(revision, str):
                seed_revisions.add(revision)
    return task_ids, seed_revisions


def _resolve_public_file(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("V2 public artifact path must be a non-empty string")
    candidate = (root / relative).resolve(strict=True)
    if candidate == root or not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError(f"V2 public artifact escapes public root: {relative}")
    return candidate


def _require_hash(value: Any, label: str) -> None:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"V2 {label} hash is invalid")

