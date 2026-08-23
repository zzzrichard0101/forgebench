import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "experiments"
    / "reports"
    / "v2-screening-wave3-private-aggregate-v1.json"
)


class V2ScreeningWave3PrivateAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_wave3_population_is_aggregated(self) -> None:
        execution = self.report["wave3_execution"]
        self.assertEqual(execution["frozen_slots"], 24)
        self.assertEqual(execution["eligible_public"], 23)
        self.assertEqual(execution["visible_failure"], 1)
        aggregate = self.report["wave3_private_aggregate"]
        self.assertEqual(aggregate["false_completions"], 3)
        self.assertEqual(aggregate["passing_controls"], 20)
        self.assertEqual(
            aggregate["false_completions"] + aggregate["passing_controls"],
            23,
        )

    def test_combined_population_arithmetic_and_gate(self) -> None:
        observed = self.report["combined_screening_aggregate"]
        minimum = self.report["screening_minimum"]
        self.assertEqual(observed["frozen_slots"], 60)
        self.assertEqual(observed["eligible_public"], 56)
        self.assertEqual(observed["visible_failure"], 4)
        self.assertEqual(
            observed["false_completions"] + observed["passing_controls"],
            observed["eligible_public"],
        )
        self.assertGreaterEqual(
            observed["passing_control_task_clusters"],
            minimum["passing_control_task_clusters"],
        )
        self.assertLess(
            observed["false_completion_task_clusters"],
            minimum["false_completion_task_clusters"],
        )
        self.assertLess(
            observed["false_completion_mechanisms"],
            minimum["false_completion_mechanisms"],
        )
        self.assertFalse(self.report["screening_population_ready"])
        self.assertFalse(self.report["decision"]["run_verifier_screening"])
        self.assertFalse(self.report["decision"]["stage_b_activation_allowed"])

    def test_repeatability_integrity_and_privacy_are_recorded(self) -> None:
        integrity = self.report["integrity"]
        self.assertEqual(integrity["repeatability_checks"], 3)
        self.assertTrue(integrity["repeatability_passed"])
        self.assertTrue(integrity["grader_files_match_seal"])
        self.assertTrue(integrity["target_hashes_verified"])
        rendered = json.dumps(self.report)
        self.assertFalse(self.report["privacy"]["case_labels_committed"])
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)
        self.assertNotIn("test_contract.py", rendered)


if __name__ == "__main__":
    unittest.main()
