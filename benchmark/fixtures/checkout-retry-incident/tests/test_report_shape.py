import json
import unittest
from pathlib import Path


class ReportShapeTests(unittest.TestCase):
    def test_report_has_required_shape_when_present(self) -> None:
        report_path = Path("incident_report.json")
        if not report_path.exists():
            self.skipTest("incident report has not been authored yet")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIsInstance(report["incident_id"], str)
        self.assertIsInstance(report["root_cause"], str)
        self.assertIsInstance(report["impact"]["affected_requests"], int)
        self.assertIsInstance(report["impact"]["total_retry_attempts"], int)
        self.assertGreaterEqual(len(report["evidence"]), 2)
        self.assertIsInstance(report["remediation"]["config_change"], str)
        self.assertIsInstance(report["remediation"]["verification"], str)


if __name__ == "__main__":
    unittest.main()
