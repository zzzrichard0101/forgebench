import json
import unittest
from pathlib import Path


class ReportShapeTests(unittest.TestCase):
    def test_shape_when_report_exists(self) -> None:
        path = Path("incident_report.json")
        if not path.exists():
            self.skipTest("report not authored")
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(report["incident_id"], str)
        self.assertIsInstance(report["impact"]["duplicated_jobs"], int)
        self.assertGreaterEqual(len(report["evidence"]), 2)


if __name__ == "__main__":
    unittest.main()
