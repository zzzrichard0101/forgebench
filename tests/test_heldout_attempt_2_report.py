import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "experiments"
    / "reports"
    / "heldout-base-generation-attempt-2.json"
)


class HeldoutAttempt2ReportTests(unittest.TestCase):
    def test_complete_population_is_ready_without_hidden_grader_claim(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["attempt_id"], "heldout-v1-attempt-2")
        self.assertEqual(
            report["audited_counts"],
            {
                "eligible_public": 30,
                "visible_failure": 0,
                "infrastructure_failure": 0,
                "incomplete": 0,
            },
        )
        self.assertEqual(report["base_record_count"], 30)
        self.assertTrue(report["decision"]["primary_comparison_ready"])
        self.assertEqual(report["decision"]["heldout_attempts_remaining"], 0)
        self.assertFalse(report["recovery"]["private_grader_invoked"])
        self.assertFalse(report["recovery"]["trace_free_interrupted_output_selected"])
        self.assertEqual(report["usage"]["unmetered_interrupted_calls"], 1)


if __name__ == "__main__":
    unittest.main()
