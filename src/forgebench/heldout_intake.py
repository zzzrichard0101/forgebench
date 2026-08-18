from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import hash_seed, hash_task_catalog
from .deterministic_probe import TRANSFERABLE_ADAPTER
from .policy_freeze import canonical_file_hash, load_policy_freeze


PRIVATE_SEAL_VERSION = "heldout-private-grader-seal-v1"
INTAKE_VERSION = "heldout-intake-v1"
IGNORED_PRIVATE_PARTS = {"__pycache__", ".pytest_cache"}


@dataclass(frozen=True)
class HeldoutIntakeResult:
    snapshot: str
    task_count: int
    family_counts: dict[str, int]
    transferable_probe_tasks: int
    public_catalog_sha256: str
    private_seal_sha256: str
    policy_freeze_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "intake_version": INTAKE_VERSION,
            "snapshot": self.snapshot,
            "task_count": self.task_count,
            "family_counts": self.family_counts,
            "transferable_probe_tasks": self.transferable_probe_tasks,
            "public_catalog_sha256": self.public_catalog_sha256,
            "private_seal_sha256": self.private_seal_sha256,
            "policy_freeze_sha256": self.policy_freeze_sha256,
        }


def create_private_grader_seal(
    grader_root: Path,
    task_ids: list[str],
    *,
    custodian_id: str,
    output_path: Path,
    attest_untouched_seed_fails: bool,
    attest_known_good_outcome_passes: bool,
    attest_protected_mutation_detected: bool,
    attest_three_repeat_grade_deterministic: bool,
) -> dict[str, Any]:
    root = grader_root.resolve(strict=True)
    output = output_path.resolve(strict=False)
    if output == root or output.is_relative_to(root):
        raise ValueError("private seal output must be outside grader root")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", custodian_id):
        raise ValueError("custodian_id must be a simple identifier")
    if len(task_ids) != len(set(task_ids)) or not task_ids:
        raise ValueError("private seal task IDs must be unique and non-empty")
    quality_attestations = {
        "untouched_seed_fails": attest_untouched_seed_fails,
        "known_good_outcome_passes": attest_known_good_outcome_passes,
        "protected_mutation_detected": attest_protected_mutation_detected,
        "three_repeat_grade_deterministic": attest_three_repeat_grade_deterministic,
    }
    if not all(quality_attestations.values()):
        raise ValueError("all private grader quality attestations are required")
    actual = {
        path.name
        for path in root.iterdir()
        if path.is_dir() and path.name not in IGNORED_PRIVATE_PARTS
    }
    if actual != set(task_ids):
        raise ValueError("private grader directories do not match declared task IDs")
    if any(path.is_file() or path.is_symlink() for path in root.iterdir()):
        raise ValueError("private grader root may contain only task directories")
    records = [
        {"task_id": task_id, "grader_sha256": _hash_private_tree(root / task_id)}
        for task_id in sorted(task_ids)
    ]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "seal_version": PRIVATE_SEAL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "custodian_id": custodian_id,
        "attestation": {
            "independent_custodian": True,
            "policy_author_inspected_grader_content": False,
            **quality_attestations,
        },
        "task_graders": records,
    }
    payload["content_sha256"] = _payload_hash(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def load_private_grader_seal(path: Path) -> dict[str, Any]:
    payload = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
    if payload.get("seal_version") != PRIVATE_SEAL_VERSION:
        raise ValueError("unsupported private grader seal version")
    if payload.get("content_sha256") != _payload_hash(payload):
        raise ValueError("private grader seal content hash mismatch")
    attestation = payload.get("attestation", {})
    if attestation.get("independent_custodian") is not True:
        raise ValueError("private grader seal lacks independent custodian attestation")
    if attestation.get("policy_author_inspected_grader_content") is not False:
        raise ValueError("private grader firewall attestation failed")
    required_quality = (
        "untouched_seed_fails",
        "known_good_outcome_passes",
        "protected_mutation_detected",
        "three_repeat_grade_deterministic",
    )
    if any(attestation.get(field) is not True for field in required_quality):
        raise ValueError("private grader quality attestation is incomplete")
    records = payload.get("task_graders")
    if not isinstance(records, list) or not records:
        raise ValueError("private grader seal has no tasks")
    ids = [record.get("task_id") for record in records]
    if (
        len(ids) != len(set(ids))
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None
            for value in ids
        )
        or any(
            re.fullmatch(r"sha256:[0-9a-f]{64}", str(record.get("grader_sha256")))
            is None
            for record in records
        )
    ):
        raise ValueError("private grader seal task IDs are invalid")
    return payload


def validate_heldout_intake(
    *,
    public_root: Path,
    heldout_manifest_path: Path,
    development_manifest_path: Path,
    private_seal_path: Path,
    policy_freeze_path: Path,
    policy_repository_root: Path,
) -> HeldoutIntakeResult:
    root = public_root.resolve(strict=True)
    manifest = json.loads(
        heldout_manifest_path.resolve(strict=True).read_text(encoding="utf-8")
    )
    records = manifest.get("tasks")
    if manifest.get("frozen") is not True or not isinstance(records, list):
        raise ValueError("held-out public manifest must be frozen")
    freeze = load_policy_freeze(policy_freeze_path, policy_repository_root)
    required_tasks = int(freeze.payload["dataset"]["held_out_tasks_required"])
    if len(records) != required_tasks:
        raise ValueError(f"held-out snapshot requires exactly {required_tasks} tasks")
    actual_catalog_hash = hash_task_catalog(root, records)
    if manifest.get("catalog_sha256") != actual_catalog_hash:
        raise ValueError("held-out public task catalog hash mismatch")

    tasks: list[dict[str, Any]] = []
    for record in records:
        task = json.loads((root / record["task_path"]).read_text(encoding="utf-8"))
        for field in ("id", "version", "family", "difficulty", "split"):
            if record.get(field) != task.get(field):
                raise ValueError(f"held-out manifest mismatch: {record.get('id')} {field}")
        if task.get("split") != "test":
            raise ValueError("held-out tasks must use the test split")
        seed = (root / task["seed_repo"]["source"]).resolve(strict=True)
        if seed != root and not seed.is_relative_to(root):
            raise ValueError(f"held-out seed escapes public root: {task['id']}")
        if task["seed_repo"]["revision"] != hash_seed(seed):
            raise ValueError(f"held-out seed hash mismatch: {task['id']}")
        tasks.append(task)

    development = json.loads(
        development_manifest_path.resolve(strict=True).read_text(encoding="utf-8")
    )
    frozen_development_hash = next(
        artifact["sha256"]
        for artifact in freeze.payload["artifacts"]
        if artifact["path"] == "benchmark/manifest.json"
    )
    if canonical_file_hash(development_manifest_path) != frozen_development_hash:
        raise ValueError("development manifest differs from the policy freeze")
    development_ids = {record["id"] for record in development["tasks"]}
    heldout_ids = {task["id"] for task in tasks}
    overlap = heldout_ids & development_ids
    if overlap:
        raise ValueError(f"held-out task IDs overlap development: {sorted(overlap)}")
    development_revisions = {
        json.loads(
            (policy_repository_root / record["task_path"]).read_text(encoding="utf-8")
        )["seed_repo"]["revision"]
        for record in development["tasks"]
    }
    heldout_revisions = {task["seed_repo"]["revision"] for task in tasks}
    if development_revisions & heldout_revisions:
        raise ValueError("held-out seed revision overlaps development")

    family_counts = Counter(task["family"] for task in tasks)
    if set(family_counts) != {"development", "incident", "adversarial"}:
        raise ValueError("held-out snapshot must cover all three task families")
    transferable = sum(
        task.get("probe_contract", {}).get("adapter") == TRANSFERABLE_ADAPTER
        for task in tasks
    )
    minimum_transferable = int(
        freeze.payload["dataset"]["minimum_transferable_probe_contract_tasks"]
    )
    if transferable < minimum_transferable:
        raise ValueError(
            f"held-out snapshot requires at least {minimum_transferable} transferable probe tasks"
        )

    private_seal = load_private_grader_seal(private_seal_path)
    private_ids = {record["task_id"] for record in private_seal["task_graders"]}
    if private_ids != heldout_ids:
        raise ValueError("private grader seal IDs do not match held-out public tasks")
    return HeldoutIntakeResult(
        snapshot=str(manifest["snapshot"]),
        task_count=len(tasks),
        family_counts=dict(sorted(family_counts.items())),
        transferable_probe_tasks=transferable,
        public_catalog_sha256=actual_catalog_hash,
        private_seal_sha256=str(private_seal["content_sha256"]),
        policy_freeze_sha256=freeze.content_sha256,
    )


def _hash_private_tree(root: Path) -> str:
    root = root.resolve(strict=True)
    digest = hashlib.sha256()
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("private grader trees cannot contain symlinks")
        if path.is_file() and not (
            set(path.relative_to(root).parts) & IGNORED_PRIVATE_PARTS
        ):
            files.append(path)
    if not files:
        raise ValueError("private grader task directory is empty")
    for path in sorted(files):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        file_hash = canonical_file_hash(path).encode("ascii")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(file_hash)
    return "sha256:" + digest.hexdigest()


def _payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
