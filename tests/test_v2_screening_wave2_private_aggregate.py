import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "experiments" / "reports" / "v2-screening-wave2-private-aggregate-v1.json"


class V2ScreeningWave2PrivateAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_wave2_population_is_aggregated(self) -> None:
        execution = self.report["wave2_execution"]
        self.assertEqual(execution["frozen_slots"], 18)
        self.assertEqual(execution["eligible_public"], 17)
        self.assertEqual(execution["visible_failure"], 1)
        aggregate = self.report["wave2_private_aggregate"]
        self.assertEqual(aggregate["false_completions"], 5)
        self.assertEqual(aggregate["passing_controls"], 12)
        self.assertEqual(aggregate["false_completions"] + aggregate["passing_controls"], 17)

    def test_combined_gate_uses_clusters_and_remains_blocked(self) -> None:
        observed = self.report["combined_screening_aggregate"]
        minimum = self.report["screening_minimum"]
        self.assertGreaterEqual(observed["passing_control_task_clusters"], minimum["passing_control_task_clusters"])
        self.assertLess(observed["false_completion_task_clusters"], minimum["false_completion_task_clusters"])
        self.assertLess(observed["false_completion_mechanisms"], minimum["false_completion_mechanisms"])
        self.assertFalse(self.report["screening_population_ready"])
        self.assertFalse(self.report["decision"]["run_verifier_screening"])

    def test_repeatability_and_privacy_are_recorded(self) -> None:
        self.assertEqual(self.report["integrity"]["repeatability_checks"], 3)
        self.assertTrue(self.report["integrity"]["repeatability_passed"])
        rendered = json.dumps(self.report)
        self.assertFalse(self.report["privacy"]["case_labels_committed"])
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)


if __name__ == "__main__":
    unittest.main()
