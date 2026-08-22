import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "experiments" / "reports" / "heldout-model-policy-replay-v1.json"


class HeldoutModelReplayReportTests(unittest.TestCase):
    def test_report_matches_frozen_routing_and_preserves_hidden_boundary(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["counts"]["completed"], 120)
        self.assertEqual(report["counts"]["infrastructure_failure"], 0)
        self.assertEqual(report["usage"]["model_calls"], 57)
        self.assertEqual(report["public_evaluation"]["probe_attempted"], 9)
        self.assertEqual(report["public_evaluation"]["record_hash_failures"], 0)
        self.assertEqual(report["public_evaluation"]["workspace_hash_failures"], 0)
        self.assertEqual(report["public_evaluation"]["completion_passed_before"], 120)
        self.assertEqual(report["public_evaluation"]["completion_passed_after"], 119)
        self.assertEqual(report["evaluation_boundary"]["private_grader_invocations"], 0)
        self.assertFalse(report["evaluation_boundary"]["hidden_labels_read"])
        self.assertEqual(report["evaluation_boundary"]["boundary_failures"], 0)


if __name__ == "__main__":
    unittest.main()
