import json
import unittest
from pathlib import Path


class AuthClockSkewIncidentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(Path("incident_report.json").read_text(encoding="utf-8"))

    def test_root_cause(self) -> None:
        self.assertGreaterEqual(len(self.report["incident_id"].strip()), 5)
        root = self.report["root_cause"].lower()
        self.assertIn("clock", root)
        self.assertTrue("skew" in root or "tolerance" in root)

    def test_impact(self) -> None:
        self.assertEqual(self.report["impact"], {"false_rejections": 3, "affected_clients": 2})

    def test_remediation_is_evidence_based(self) -> None:
        evidence = " ".join(self.report["evidence"]).lower()
        self.assertIn("0", evidence)
        self.assertTrue(any(value in evidence for value in ("1", "2", "3")))
        change = self.report["remediation"]["config_change"].lower()
        self.assertTrue("skew" in change or "tolerance" in change)
        self.assertGreaterEqual(len(self.report["remediation"]["verification"]), 20)


if __name__ == "__main__":
    unittest.main()
