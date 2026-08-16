from __future__ import annotations

import json
import unittest
from pathlib import Path


class IncidentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(
            Path("incident_report.json").read_text(encoding="utf-8")
        )

    def test_identity_and_root_cause(self) -> None:
        self.assertEqual(
            self.report["incident_id"], "checkout-retry-storm-2026-08-15"
        )
        self.assertEqual(
            self.report["root_cause"], "retry_on_non_transient_400"
        )

    def test_impact_is_counted_from_events(self) -> None:
        self.assertEqual(self.report["impact"]["affected_requests"], 3)
        self.assertEqual(self.report["impact"]["total_retry_attempts"], 9)

    def test_evidence_and_remediation_are_specific(self) -> None:
        evidence = " ".join(self.report["evidence"]).lower()
        self.assertIn("400", evidence)
        self.assertTrue("retry" in evidence or "attempt" in evidence)
        change = self.report["remediation"]["config_change"].lower()
        self.assertIn("400", change)
        self.assertTrue("remove" in change or "exclude" in change)
        verification = self.report["remediation"]["verification"].strip()
        self.assertGreaterEqual(len(verification), 20)


if __name__ == "__main__":
    unittest.main()
