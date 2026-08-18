from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_completion import SealedBaseCompletion
from .completion_risk import CompletionRiskPolicy
from .deterministic_probe import DeterministicProbeRunner
from .workspace import WorkspaceError, create_isolated_workspace, hash_workspace


MANIFEST_VERSION = "policy-assignment-v1"
EXECUTABLE_POLICIES = (
    "accept_all",
    "verify_all",
    "random_k_call_matched",
    "probe_all",
    "risk_model_direct",
    "risk_hierarchical",
)


@dataclass(frozen=True)
class ComparisonCandidate:
    base: SealedBaseCompletion
    task: dict[str, Any]


@dataclass(frozen=True)
class ComparisonManifest:
    path: Path
    payload: dict[str, Any]

    @property
    def manifest_id(self) -> str:
        return str(self.payload["manifest_id"])

    @property
    def content_sha256(self) -> str:
        return str(self.payload["content_sha256"])

    def assignment(self, base_id: str) -> dict[str, Any]:
        matches = [item for item in self.payload["bases"] if item["base_id"] == base_id]
        if len(matches) != 1:
            raise KeyError(f"base assignment not found or duplicated: {base_id}")
        return matches[0]


class ComparisonManifestPlanner:
    """Freeze public-only policy assignments for multiple base completions."""

    def __init__(
        self,
        routing_root: Path,
        *,
        risk_policy: CompletionRiskPolicy | None = None,
        probe_runner: DeterministicProbeRunner | None = None,
    ) -> None:
        self.routing_root = routing_root
        self.risk_policy = risk_policy or CompletionRiskPolicy()
        self.probe_runner = probe_runner or DeterministicProbeRunner()

    def plan(
        self,
        *,
        candidates: list[ComparisonCandidate],
        output_path: Path,
        random_seed: int,
        manifest_id: str | None = None,
    ) -> ComparisonManifest:
        if not candidates:
            raise ValueError("comparison manifest requires at least one base")
        manifest_id = manifest_id or uuid.uuid4().hex
        _validate_identifier(manifest_id, "manifest_id")
        base_ids = [candidate.base.base_id for candidate in candidates]
        if len(base_ids) != len(set(base_ids)):
            raise ValueError("comparison manifest contains duplicate base IDs")

        routes = [
            self._route_public(candidate, manifest_id=manifest_id)
            for candidate in sorted(candidates, key=lambda item: item.base.base_id)
        ]
        by_stratum: dict[str, list[dict[str, Any]]] = {}
        for route in routes:
            by_stratum.setdefault(route["stratum"], []).append(route)

        stratum_summary: list[dict[str, Any]] = []
        for stratum, items in sorted(by_stratum.items()):
            target_k = sum(
                item["policies"]["risk_hierarchical"]["model_selected"]
                for item in items
            )
            ranked = sorted(
                items,
                key=lambda item: _random_rank(random_seed, stratum, item["base_id"]),
            )
            selected = {item["base_id"] for item in ranked[:target_k]}
            for item in items:
                item["random_rank"] = _random_rank(
                    random_seed, stratum, item["base_id"]
                )
                item["policies"]["random_k_call_matched"] = {
                    "probe_selected": False,
                    "model_selected": item["base_id"] in selected,
                }
            stratum_summary.append(
                {
                    "stratum": stratum,
                    "eligible_bases": len(items),
                    "risk_hierarchical_model_calls": target_k,
                    "random_k_model_calls": len(selected),
                }
            )

        payload: dict[str, Any] = {
            "schema_version": 1,
            "manifest_version": MANIFEST_VERSION,
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "random_seed": random_seed,
            "random_method": "sha256_rank_within_task_family",
            "stratification": "task_family",
            "policy_order": list(EXECUTABLE_POLICIES),
            "bases": routes,
            "strata": stratum_summary,
        }
        payload["content_sha256"] = _payload_hash(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return ComparisonManifest(output_path, payload)

    def _route_public(
        self,
        candidate: ComparisonCandidate,
        *,
        manifest_id: str,
    ) -> dict[str, Any]:
        base = candidate.base
        task = candidate.task
        if base.task_id != task["id"] or base.task_version != task["version"]:
            raise ValueError("candidate task identity does not match sealed base")
        if not base.eligible:
            raise ValueError("comparison assignments require eligible base completions")
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("sealed base changed before assignment planning")

        route_workspace = create_isolated_workspace(
            base.workspace,
            self.routing_root,
            f"{manifest_id}--{base.base_id}",
            preserve_symlinks=True,
        )
        decision = self.risk_policy.evaluate(
            task=task,
            workspace=route_workspace,
            completion=base.completion,
        )
        probe = (
            self.probe_runner.run(
                task=task,
                workspace=route_workspace,
                decision=decision,
            )
            if decision.escalate
            else None
        )
        hierarchical_model = bool(
            decision.escalate
            and not (probe is not None and probe.supported and probe.passed)
        )
        route = {
            "base_id": base.base_id,
            "source_run_id": base.source_run_id,
            "task_id": base.task_id,
            "task_version": base.task_version,
            "stratum": str(task["family"]),
            "base_workspace_hash": base.workspace_hash,
            "public_completion_eligible": True,
            "risk_decision": decision.as_dict(),
            "probe_route": probe.as_dict() if probe is not None else None,
            "policies": {
                "accept_all": {
                    "probe_selected": False,
                    "model_selected": False,
                },
                "verify_all": {
                    "probe_selected": False,
                    "model_selected": True,
                },
                "probe_all": {
                    "probe_selected": True,
                    "model_selected": False,
                },
                "risk_model_direct": {
                    "probe_selected": False,
                    "model_selected": decision.escalate,
                },
                "risk_hierarchical": {
                    "probe_selected": decision.escalate,
                    "model_selected": hierarchical_model,
                },
            },
        }
        if hash_workspace(base.workspace) != base.workspace_hash:
            raise WorkspaceError("assignment planning mutated the sealed base")
        return route


def load_comparison_manifest(path: Path) -> ComparisonManifest:
    path = path.resolve(strict=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError("unsupported comparison manifest version")
    expected = payload.get("content_sha256")
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    if expected != _payload_hash(unsigned):
        raise ValueError("comparison manifest content hash mismatch")
    return ComparisonManifest(path, payload)


def validate_assignment(
    *,
    manifest: ComparisonManifest,
    base: SealedBaseCompletion,
    task: dict[str, Any],
    policy: str,
) -> dict[str, Any]:
    if policy not in EXECUTABLE_POLICIES:
        raise ValueError(f"policy is not executable from this manifest: {policy}")
    assignment = manifest.assignment(base.base_id)
    if assignment["task_id"] != task["id"]:
        raise ValueError("assignment task does not match replay task")
    if int(assignment["task_version"]) != int(task["version"]):
        raise ValueError("assignment task version does not match replay task")
    if assignment["base_workspace_hash"] != base.workspace_hash:
        raise ValueError("assignment base hash does not match sealed base")
    return assignment["policies"][policy]


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _random_rank(seed: int, stratum: str, base_id: str) -> str:
    value = f"{seed}\0{stratum}\0{base_id}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _validate_identifier(value: str, label: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ValueError(f"{label} must be a simple 1-128 character identifier")
