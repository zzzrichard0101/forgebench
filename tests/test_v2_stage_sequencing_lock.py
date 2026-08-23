import json
import unittest
from copy import deepcopy
from pathlib import Path

from forgebench.completion_risk import DEFAULT_THRESHOLD, POLICY_VERSION
from forgebench.policy_freeze import canonical_file_hash
from forgebench.stage_b_lock import StageBActivationError, verify_stage_b_activation
from forgebench.v2_corpus import payload_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "experiments" / "configs" / "v2-stage-sequencing-freeze-v1.json"
PREREG_PATH = ROOT / "experiments" / "configs" / "v2-stage-a-preregistration-v1.json"


def passing_gate_report() -> dict:
    report = {
        "schema_version": 1,
        "status": "stage_a_gate_passed",
        "stage_a_version": "synthetic-stage-a-v1",
        "contaminated": False,
        "mechanism_validation": {
            "false_completion_task_clusters": 15,
            "passing_control_task_clusters": 15,
            "hidden_repairs": 6,
            "repaired_mechanisms": 3,
            "repair_delta_vs_generic_review": 3,
            "passing_controls_retained": 14,
            "hard_safety_violations": 0,
            "single_mechanism_repair_share": 0.5,
            "complete_audit_manifest": True,
        },
    }
    report["content_sha256"] = payload_hash(report)
    return report


class V2StageSequencingLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_freeze_is_content_addressed_and_wave3_is_next(self) -> None:
        self.assertEqual(self.freeze["content_sha256"], payload_hash(self.freeze))
        self.assertEqual(self.freeze["current_stage"], "stage_a_screening_population_wave3")
        self.assertEqual(self.freeze["ordered_stages"][-1], "stage_b_public_evidence_activation")

    def test_historical_baseline_and_sealed_artifacts_are_unchanged(self) -> None:
        self.assertEqual(POLICY_VERSION, "completion-risk-v0.2")
        self.assertEqual(DEFAULT_THRESHOLD, 3)
        for artifact in self.freeze["protected_artifacts"]:
            self.assertEqual(canonical_file_hash(ROOT / artifact["path"]), artifact["sha256"])

    def test_stage_b_is_locked_without_a_complete_gate_pass(self) -> None:
        with self.assertRaises(StageBActivationError):
            verify_stage_b_activation(preregistration=self.prereg, gate_report=None)
        failed = passing_gate_report()
        failed["mechanism_validation"]["hidden_repairs"] = 5
        failed["content_sha256"] = payload_hash(failed)
        with self.assertRaises(StageBActivationError):
            verify_stage_b_activation(preregistration=self.prereg, gate_report=failed)

    def test_only_uncontaminated_aggregate_can_unlock_stage_b(self) -> None:
        report = passing_gate_report()
        activation = verify_stage_b_activation(preregistration=self.prereg, gate_report=report)
        self.assertTrue(activation.allowed)
        contaminated = deepcopy(report)
        contaminated["case_labels"] = ["private"]
        contaminated["content_sha256"] = payload_hash(contaminated)
        with self.assertRaises(StageBActivationError):
            verify_stage_b_activation(preregistration=self.prereg, gate_report=contaminated)

    def test_stage_b_policy_is_reserved_but_not_active(self) -> None:
        design = self.freeze["reserved_stage_b_design"]
        self.assertEqual(design["version"], "stage-b-public-evidence-v0.1")
        self.assertEqual(design["decision_policy_status"], "not_frozen_not_active")
        self.assertFalse(design["unknown_defaults_to_low"])
        self.assertIn("risk_fitting", self.freeze["stage_b_before_gate"]["forbidden"])


if __name__ == "__main__":
    unittest.main()
