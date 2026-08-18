import json
import unittest
from pathlib import Path


class ConnectionLeakIncidentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(Path("incident_report.json").read_text(encoding="utf-8"))

    def test_root_cause(self) -> None:
        self.assertGreaterEqual(len(self.report["incident_id"].strip()), 5)
        root = self.report["root_cause"].lower()
        self.assertIn("connection", root)
        self.assertTrue("release" in root or "leak" in root)
        self.assertTrue("error" in root or "exception" in root)

    def test_impact(self) -> None:
        self.assertEqual(self.report["impact"], {"leaked_connections": 3, "timed_out_requests": 3})

    def test_remediation_is_specific(self) -> None:
        evidence = " ".join(self.report["evidence"]).lower()
        self.assertIn("3", evidence)
        change = self.report["remediation"]["code_change"].lower()
        self.assertIn("release", change)
        self.assertTrue("finally" in change or "context" in change or "error" in change)
        self.assertGreaterEqual(len(self.report["remediation"]["verification"]), 20)


if __name__ == "__main__":
    unittest.main()
