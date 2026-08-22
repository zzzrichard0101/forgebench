import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT / "experiments/reports/heldout-private-policy-evaluation-v1.json"
)


class PrivateEvaluationAnalysisTests(unittest.TestCase):
    def test_final_report_preserves_the_negative_result(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "complete_negative_result")
        self.assertEqual(report["population"]["base_hidden_failures"], 30)
        self.assertEqual(report["population"]["base_hidden_successes"], 0)
        for policy in report["policies"].values():
            self.assertEqual(policy["final_hidden_successes"], 0)
        self.assertEqual(
            report["policies"]["risk_hierarchical"][
                "false_completions_recovered"
            ],
            0,
        )
        self.assertEqual(
            report["policies"]["verify_all"]["hard_safety_violations"], 1
        )
        self.assertFalse(report["claim_gate"]["primary_claim_eligible"])

    def test_report_has_frozen_statistics_costs_and_no_trajectory_rows(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["statistics"]["bootstrap_seed"], 1729)
        self.assertEqual(report["statistics"]["bootstrap_samples"], 20_000)
        self.assertEqual(report["risk_prediction"]["recall"], 0.3)
        self.assertEqual(
            report["policies"]["risk_hierarchical"]["usage"]["model_calls"], 9
        )
        self.assertEqual(
            report["policies"]["verify_all"]["usage"]["model_calls"], 30
        )
        serialized = REPORT.read_text(encoding="utf-8")
        self.assertNotIn('"run_id"', serialized)
        self.assertNotIn('"base_id"', serialized)
        self.assertNotIn('"workspace_path"', serialized)
        self.assertFalse(report["privacy"]["private_result_committed"])


if __name__ == "__main__":
    unittest.main()
