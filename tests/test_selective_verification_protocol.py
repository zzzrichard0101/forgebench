import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    ROOT / "experiments" / "configs" / "selective-verification-protocol-v1.json"
)


class SelectiveVerificationProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_required_policy_baselines_are_frozen(self) -> None:
        self.assertEqual(
            set(self.protocol["policies"]),
            {
                "accept_all",
                "verify_all",
                "random_k_call_matched",
                "probe_all",
                "risk_model_direct",
                "risk_hierarchical",
                "oracle_k_diagnostic",
            },
        )
        self.assertEqual(self.protocol["primary_policy"], "risk_hierarchical")

    def test_hidden_evidence_is_evaluation_only(self) -> None:
        firewall = self.protocol["hidden_evidence_firewall"]
        self.assertFalse(firewall["risk_features"])
        self.assertFalse(firewall["probe_inputs"])
        self.assertFalse(firewall["model_verification_prompt"])
        self.assertFalse(firewall["routing_runtime"])
        self.assertTrue(firewall["post_routing_evaluation_join_only"])
        self.assertFalse(self.protocol["current_task_id_probe_held_out_eligible"])

    def test_held_out_floor_and_shared_base_completions_are_explicit(self) -> None:
        dataset = self.protocol["minimum_dataset"]
        self.assertGreaterEqual(dataset["development_tasks"], 20)
        self.assertGreaterEqual(dataset["held_out_tasks"], 10)
        self.assertGreaterEqual(dataset["base_trajectories_per_task"], 3)
        self.assertTrue(
            self.protocol["comparison_matching"]["shared_frozen_base_completions"]
        )
        self.assertLessEqual(self.protocol["held_out_execution_limit"], 2)


if __name__ == "__main__":
    unittest.main()
