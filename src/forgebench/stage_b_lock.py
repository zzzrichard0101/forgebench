from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .v2_corpus import payload_hash


FORBIDDEN_GATE_FIELDS = {
    "case_labels",
    "grader_output",
    "grader_results",
    "hidden_outcomes",
    "labels",
    "known_good",
}


class StageBActivationError(ValueError):
    pass


@dataclass(frozen=True)
class StageBActivation:
    allowed: bool
    stage_a_version: str
    gate_report_sha256: str


def verify_stage_b_activation(
    *, preregistration: dict[str, Any], gate_report: dict[str, Any] | None
) -> StageBActivation:
    """Accept only a complete, uncontaminated public aggregate Stage A pass."""

    if preregistration.get("stage_b_locked_until_gate_passes") is not True:
        raise StageBActivationError("Stage B lock is not enabled in the preregistration")
    if gate_report is None:
        raise StageBActivationError("Stage B remains locked without a Stage A gate report")
    if _contains_forbidden_fields(gate_report):
        raise StageBActivationError("Stage B activation input contains private case material")
    if gate_report.get("content_sha256") != payload_hash(gate_report):
        raise StageBActivationError("Stage A gate report hash is invalid")
    if gate_report.get("status") != "stage_a_gate_passed":
        raise StageBActivationError("Stage A gate has not passed")
    if gate_report.get("contaminated") is not False:
        raise StageBActivationError("contaminated Stage A evidence cannot unlock Stage B")

    observed = gate_report.get("mechanism_validation")
    if not isinstance(observed, dict):
        raise StageBActivationError("mechanism-validation aggregate is missing")
    required = preregistration["mechanism_validation"]
    minimums = {
        "false_completion_task_clusters": required["false_completion_clusters_min"],
        "passing_control_task_clusters": required["passing_control_clusters_min"],
        "hidden_repairs": required["hidden_repairs_min"],
        "repaired_mechanisms": required["repaired_mechanisms_min"],
        "repair_delta_vs_generic_review": required["repair_delta_vs_generic_review_min"],
        "passing_controls_retained": required["passing_controls_retained_min"],
    }
    for field, minimum in minimums.items():
        value = observed.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
            raise StageBActivationError(f"Stage A gate minimum not met: {field}")
    violations = observed.get("hard_safety_violations")
    if isinstance(violations, bool) or not isinstance(violations, int):
        raise StageBActivationError("hard-safety aggregate is missing")
    if violations > required["hard_safety_violations_max"]:
        raise StageBActivationError("hard-safety limit exceeded")
    share = observed.get("single_mechanism_repair_share")
    if isinstance(share, bool) or not isinstance(share, (int, float)):
        raise StageBActivationError("mechanism concentration aggregate is missing")
    if share > required["single_mechanism_repair_share_max"]:
        raise StageBActivationError("single-mechanism repair share is too high")
    if observed.get("complete_audit_manifest") is not True:
        raise StageBActivationError("complete audit manifest is required")
    version = gate_report.get("stage_a_version")
    if not isinstance(version, str) or not version.strip():
        raise StageBActivationError("Stage A version is missing")
    return StageBActivation(True, version, gate_report["content_sha256"])


def _contains_forbidden_fields(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in FORBIDDEN_GATE_FIELDS or _contains_forbidden_fields(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_fields(item) for item in value)
    return False
