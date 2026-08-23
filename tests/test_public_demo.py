from __future__ import annotations

import unittest
from pathlib import Path

from forgebench.public_demo import format_public_demo, run_public_demo


ROOT = Path(__file__).resolve().parents[1]


class PublicDemoTests(unittest.TestCase):
    def test_public_demo_exposes_block_then_probe_verified_remediation(self) -> None:
        result = run_public_demo(ROOT)
        first, second = result["attempts"]

        self.assertTrue(first["completion_passed"])
        self.assertEqual(first["risk_level"], "high")
        self.assertFalse(first["probe_passed"])
        self.assertEqual(first["disposition"], "blocked_for_repair")
        self.assertIn("plugin_non_python_regular_file", first["failing_probe_cases"])

        self.assertTrue(second["completion_passed"])
        self.assertEqual(second["risk_level"], "high")
        self.assertTrue(second["probe_passed"])
        self.assertEqual(
            second["disposition"], "accepted_after_deterministic_probe"
        )

    def test_public_demo_is_deterministic_and_discloses_its_boundary(self) -> None:
        first = run_public_demo(ROOT)
        second = run_public_demo(ROOT)

        self.assertEqual(first, second)
        self.assertFalse(first["private_artifacts_accessed"])
        self.assertEqual(first["model_calls"], 0)
        self.assertIn("scripted", first["disclosure"].lower())
        rendered = format_public_demo(first)
        self.assertIn("NO PRIVATE GRADER", rendered)
        self.assertIn(first["evidence_hash"], rendered)


if __name__ == "__main__":
    unittest.main()
