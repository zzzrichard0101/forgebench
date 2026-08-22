import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "experiments" / "reports" / "v2-screening-base-population-v1.json"


class V2ScreeningBasePopulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_execution_is_preserved(self) -> None:
        execution = self.report["execution"]
        self.assertEqual(execution["frozen_slots"], 18)
        self.assertEqual(execution["eligible_public"], 16)
        self.assertEqual(execution["visible_failure"], 2)
        self.assertEqual(execution["infrastructure_failure"], 0)

    def test_population_gate_blocks_verifier_screening(self) -> None:
        observed = self.report["private_aggregate"]
        minimum = self.report["screening_minimum"]
        self.assertLess(observed["false_completion_task_clusters"], minimum["false_completion_task_clusters"])
        self.assertLess(observed["passing_control_task_clusters"], minimum["passing_control_task_clusters"])
        self.assertFalse(self.report["screening_population_ready"])
        self.assertFalse(self.report["decision"]["run_verifier_screening"])

    def test_public_report_contains_no_case_labels_or_external_paths(self) -> None:
        rendered = json.dumps(self.report)
        self.assertFalse(self.report["privacy"]["case_labels_committed"])
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)


if __name__ == "__main__":
    unittest.main()
