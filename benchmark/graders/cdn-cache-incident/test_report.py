import json
import unittest
from pathlib import Path


class CacheIncidentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(Path("incident_report.json").read_text(encoding="utf-8"))

    def test_root_cause(self) -> None:
        self.assertEqual(self.report["incident_id"], "cdn-cache-2026-08-15")
        self.assertEqual(self.report["root_cause"], "cache_ttl_regression")

    def test_impact(self) -> None:
        self.assertEqual(self.report["impact"]["stale_responses"], 499)
        self.assertEqual(
            sorted(self.report["impact"]["affected_regions"]),
            ["ap-northeast-2", "us-west-2"],
        )

    def test_remediation_is_specific(self) -> None:
        evidence = " ".join(self.report["evidence"]).lower()
        self.assertIn("3600", evidence)
        change = self.report["remediation"]["config_change"].lower()
        self.assertTrue("60" in change or "rollback" in change)
        self.assertGreaterEqual(len(self.report["remediation"]["verification"]), 20)


if __name__ == "__main__":
    unittest.main()
