import json
import unittest
from pathlib import Path


class WorkerIncidentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(Path("incident_report.json").read_text(encoding="utf-8"))

    def test_root_cause(self) -> None:
        self.assertGreaterEqual(len(self.report["incident_id"].strip()), 5)
        root_cause = self.report["root_cause"].lower()
        self.assertIn("visibility", root_cause)
        self.assertIn("timeout", root_cause)

    def test_impact(self) -> None:
        self.assertEqual(self.report["impact"], {"duplicated_jobs": 2, "extra_attempts": 2})

    def test_remediation_is_specific(self) -> None:
        text = " ".join(self.report["evidence"]).lower()
        self.assertIn("30", text)
        self.assertTrue("38" in text or "42" in text)
        change = self.report["remediation"]["config_change"].lower()
        self.assertIn("visibility", change)
        self.assertGreaterEqual(len(self.report["remediation"]["verification"]), 20)


if __name__ == "__main__":
    unittest.main()
