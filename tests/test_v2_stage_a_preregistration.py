import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiments" / "configs" / "v2-stage-a-preregistration-v1.json"
V1_REPORT_PATH = ROOT / "experiments" / "reports" / "heldout-private-policy-evaluation-v1.json"


class V2StageAPreregistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.v1_report = json.loads(V1_REPORT_PATH.read_text(encoding="utf-8"))

    def test_v1_motivation_matches_the_frozen_public_report(self) -> None:
        self.assertEqual(self.v1_report["population"]["base_trajectories"], 30)
        self.assertEqual(self.v1_report["population"]["base_hidden_failures"], 30)
        self.assertEqual(
            sum(
                policy["usage"]["model_calls"]
                for policy in self.v1_report["policies"].values()
            ),
            57,
        )
        self.assertEqual(
            sum(
                policy["false_completions_recovered"]
                for policy in self.v1_report["policies"].values()
            ),
            0,
        )

    def test_v2_preserves_v1_and_keeps_stage_b_locked(self) -> None:
        boundary = self.config["v1_boundary"]
        self.assertFalse(boundary["v1_heldout_reuse_allowed"])
        self.assertFalse(boundary["v1_private_material_access_allowed"])
        self.assertFalse(boundary["overwrite_v1_artifacts_allowed"])
        self.assertTrue(self.config["stage_b_locked_until_gate_passes"])

    def test_validation_measures_repair_and_safe_abstention(self) -> None:
        gate = self.config["mechanism_validation"]
        self.assertGreaterEqual(gate["false_completion_clusters_min"], 15)
        self.assertGreaterEqual(gate["passing_control_clusters_min"], 15)
        self.assertGreaterEqual(gate["hidden_repairs_min"], 6)
        self.assertGreaterEqual(gate["repaired_mechanisms_min"], 3)
        self.assertGreaterEqual(gate["repair_delta_vs_generic_review_min"], 3)
        self.assertEqual(gate["hard_safety_violations_max"], 0)
        self.assertLess(gate["single_mechanism_repair_share_max"], 1.0)

    def test_hidden_oracle_never_becomes_verifier_input(self) -> None:
        self.assertFalse(self.config["hidden_oracle_is_verifier_input"])
        self.assertTrue(
            self.config["diagnosis_accuracy_requires_independent_blinded_labels"]
        )


if __name__ == "__main__":
    unittest.main()
