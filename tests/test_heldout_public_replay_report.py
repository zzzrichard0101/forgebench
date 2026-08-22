import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "experiments"
    / "reports"
    / "heldout-public-policy-replay-v1.json"
)


class HeldoutPublicReplayReportTests(unittest.TestCase):
    def test_report_preserves_public_only_boundary_and_probe_limitation(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["counts"]["completed"], 60)
        self.assertEqual(report["counts"]["infrastructure_failure"], 0)
        self.assertEqual(report["public_evaluation"]["completion_passed_after"], 60)
        self.assertEqual(report["public_evaluation"]["probe_attempted"], 30)
        self.assertEqual(report["public_evaluation"]["probe_supported"], 0)
        self.assertEqual(report["usage"]["model_calls"], 0)
        self.assertEqual(
            report["evaluation_boundary"]["private_grader_invocations"], 0
        )
        self.assertFalse(report["evaluation_boundary"]["hidden_labels_read"])


if __name__ == "__main__":
    unittest.main()
