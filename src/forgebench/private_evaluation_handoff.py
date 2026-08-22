from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .heldout_public_replay import payload_hash
from .workspace import hash_workspace


def build_private_evaluation_request(
    *,
    assignment_path: Path,
    execution_path: Path,
    base_root: Path,
    replay_runs_root: Path,
    repo_root: Path,
    public_result_freeze_path: Path,
) -> dict[str, Any]:
    """Build a hash-bound request without reading a label or private grader."""

    repo_root = repo_root.resolve(strict=True)
    assignment = _read_json(assignment_path)
    execution = _read_json(execution_path)
    result_freeze = _read_json(public_result_freeze_path)
    if result_freeze["status"] != "frozen_before_private_label_join":
        raise ValueError("public replay result is not frozen for private joining")
    if any(slot["status"] != "completed" for slot in execution["slots"]):
        raise ValueError("all replay slots must be complete before handoff")

    base_targets = []
    for base in assignment["bases"]:
        workspace = base_root / str(base["base_id"]) / "workspace"
        actual_hash = hash_workspace(workspace)
        if actual_hash != base["base_workspace_hash"]:
            raise ValueError(f"base workspace hash mismatch: {base['base_id']}")
        base_targets.append(
            {
                "base_id": base["base_id"],
                "task_id": base["task_id"],
                "task_version": int(base["task_version"]),
                "stratum": base["stratum"],
                "workspace_path": _relative(workspace, repo_root),
                "workspace_sha256": actual_hash,
            }
        )

    replay_targets = []
    for slot in execution["slots"]:
        run_root = replay_runs_root / str(slot["run_id"])
        record = _read_json(run_root / "model-policy-replay.json")
        if payload_hash(record) != record["content_sha256"]:
            raise ValueError(f"replay record content hash mismatch: {slot['run_id']}")
        if record["content_sha256"] != slot["record_sha256"]:
            raise ValueError(f"execution record hash mismatch: {slot['run_id']}")
        workspace = run_root / "workspace"
        actual_hash = hash_workspace(workspace)
        if actual_hash != record["replay_workspace_hash"]:
            raise ValueError(f"replay workspace hash mismatch: {slot['run_id']}")
        replay_targets.append(
            {
                "run_id": slot["run_id"],
                "policy": slot["policy"],
                "base_id": slot["base_id"],
                "task_id": slot["task_id"],
                "record_path": _relative(
                    run_root / "model-policy-replay.json", repo_root
                ),
                "record_sha256": record["content_sha256"],
                "workspace_path": _relative(workspace, repo_root),
                "workspace_sha256": actual_hash,
            }
        )

    targets = {
        "bases": sorted(base_targets, key=lambda item: item["base_id"]),
        "replays": sorted(replay_targets, key=lambda item: item["run_id"]),
    }
    encoded_targets = json.dumps(
        targets, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    request = {
        "schema_version": 1,
        "request_version": "heldout-private-evaluation-request-v1",
        "request_id": "heldout-v1-private-evaluation-v1",
        "public_result_freeze_sha256": result_freeze["content_sha256"],
        "replay_record_catalog_sha256": result_freeze[
            "replay_record_catalog_sha256"
        ],
        "base_catalog_sha256": result_freeze["base_catalog_sha256"],
        "sealed_label_catalog_sha256": result_freeze[
            "sealed_label_catalog_sha256"
        ],
        "private_grader_seal_sha256": result_freeze[
            "private_grader_seal_sha256"
        ],
        "target_catalog_sha256": "sha256:"
        + hashlib.sha256(encoded_targets).hexdigest(),
        "counts": {"base_targets": len(base_targets), "replay_targets": len(replay_targets)},
        "targets": targets,
        "evaluation_contract": {
            "same_private_grader_version_for_every_target": True,
            "grade_base_targets_or_join_the_existing_sealed_base_labels": True,
            "grade_every_replay_workspace": True,
            "repeatability_and_integrity_checks_required": True,
            "do_not_modify_target_workspaces": True,
            "do_not_return_grader_source_known_good_artifacts_or_hidden_values": True,
            "private_inputs_and_outcomes_must_remain_outside_public_repository": True,
            "accept_all_outcome_source": "matching sealed base outcome",
            "probe_all_outcome_source": "matching sealed base outcome; replay made no workspace change",
        },
        "required_result_fields": {
            "base_outcome": [
                "base_id",
                "workspace_sha256",
                "hidden_task_passed",
                "hard_safety_violation",
            ],
            "replay_outcome": [
                "run_id",
                "record_sha256",
                "workspace_sha256",
                "hidden_task_passed",
                "hard_safety_violation",
            ],
        },
        "hidden_inputs_read_by_request_builder": False,
    }
    request["content_sha256"] = payload_hash(request)
    return request


def validate_private_evaluation_result(
    *, request: dict[str, Any], result: dict[str, Any]
) -> dict[str, int]:
    """Validate an external result envelope without needing grader source."""

    if result.get("schema_version") != 1:
        raise ValueError("unsupported private evaluation result schema")
    if result.get("result_version") != "heldout-private-evaluation-result-v1":
        raise ValueError("unsupported private evaluation result version")
    if result.get("content_sha256") != payload_hash(result):
        raise ValueError("private evaluation result content hash mismatch")
    bindings = {
        "request_sha256": request["content_sha256"],
        "target_catalog_sha256": request["target_catalog_sha256"],
        "sealed_label_catalog_sha256": request["sealed_label_catalog_sha256"],
        "private_grader_seal_sha256": request["private_grader_seal_sha256"],
    }
    for field, expected in bindings.items():
        if result.get(field) != expected:
            raise ValueError(f"private evaluation binding mismatch: {field}")

    expected_bases = {
        item["base_id"]: item for item in request["targets"]["bases"]
    }
    expected_replays = {
        item["run_id"]: item for item in request["targets"]["replays"]
    }
    observed_bases = _unique_map(result.get("base_outcomes"), "base_id")
    observed_replays = _unique_map(result.get("replay_outcomes"), "run_id")
    if set(observed_bases) != set(expected_bases):
        raise ValueError("private base outcome IDs do not match request")
    if set(observed_replays) != set(expected_replays):
        raise ValueError("private replay outcome IDs do not match request")
    for base_id, outcome in observed_bases.items():
        expected = expected_bases[base_id]
        _require_outcome_booleans(outcome, base_id)
        if outcome.get("workspace_sha256") != expected["workspace_sha256"]:
            raise ValueError(f"private base workspace binding mismatch: {base_id}")
    for run_id, outcome in observed_replays.items():
        expected = expected_replays[run_id]
        _require_outcome_booleans(outcome, run_id)
        if outcome.get("record_sha256") != expected["record_sha256"]:
            raise ValueError(f"private replay record binding mismatch: {run_id}")
        if outcome.get("workspace_sha256") != expected["workspace_sha256"]:
            raise ValueError(f"private replay workspace binding mismatch: {run_id}")

    integrity = result.get("integrity")
    if not isinstance(integrity, dict) or not all(
        integrity.get(field) is True
        for field in (
            "target_hashes_verified",
            "grader_version_unchanged",
            "repeatability_checks_passed",
            "private_artifacts_retained_external",
        )
    ):
        raise ValueError("private evaluation integrity attestations are incomplete")
    return {"base_outcomes": len(observed_bases), "replay_outcomes": len(observed_replays)}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))


def _relative(path: Path, root: Path) -> str:
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError(f"evaluation target is outside repository root: {resolved}")
    return resolved.relative_to(root).as_posix()


def _unique_map(value: Any, key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"private evaluation field must be a list: {key}")
    mapped: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get(key), str):
            raise ValueError(f"invalid private evaluation item: {key}")
        identifier = item[key]
        if identifier in mapped:
            raise ValueError(f"duplicate private evaluation item: {identifier}")
        mapped[identifier] = item
    return mapped


def _require_outcome_booleans(outcome: dict[str, Any], identifier: str) -> None:
    for field in ("hidden_task_passed", "hard_safety_violation"):
        if not isinstance(outcome.get(field), bool):
            raise ValueError(f"private outcome lacks boolean {field}: {identifier}")
