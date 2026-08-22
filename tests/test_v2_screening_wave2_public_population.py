import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "experiments" / "reports" / "v2-screening-wave2-public-population-v1.json"


class V2ScreeningWave2PublicPopulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_frozen_execution_is_preserved(self) -> None:
        execution = self.report["execution"]
        self.assertEqual(execution["frozen_slots"], 18)
        self.assertEqual(execution["eligible_public"], 17)
        self.assertEqual(execution["visible_failure"], 1)
        self.assertEqual(execution["infrastructure_failure"], 0)
        self.assertEqual(sum(execution[key] for key in ("eligible_public", "visible_failure", "infrastructure_failure")), 18)

    def test_selection_and_privacy_boundary_are_explicit(self) -> None:
        self.assertTrue(self.report["selection"]["all_frozen_slots_executed"])
        self.assertTrue(self.report["selection"]["all_publicly_eligible_cases_sealed"])
        self.assertFalse(self.report["selection"]["visible_failure_rerun"])
        self.assertFalse(self.report["selection"]["outcome_based_exclusion"])
        self.assertFalse(self.report["privacy"]["private_evaluation_performed"])
        rendered = json.dumps(self.report)
        self.assertNotIn("case_id", rendered)
        self.assertNotIn("C:\\\\Users", rendered)


if __name__ == "__main__":
    unittest.main()
