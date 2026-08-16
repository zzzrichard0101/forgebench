import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "planning",
    "context_memory",
    "tool",
    "verification",
    "recovery",
    "budget",
    "safety",
    "infrastructure",
    "task_grader",
}


class FailureLabelTests(unittest.TestCase):
    def test_public_label_records_follow_the_contract(self) -> None:
        paths = sorted((ROOT / "experiments" / "labels").glob("*.json"))
        self.assertEqual(len(paths), 3)
        for path in paths:
            with self.subTest(path=path):
                label = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(label["schema_version"], 1)
                self.assertEqual(label["run_id"], path.stem)
                self.assertIn(label["primary_label"], LABELS)
                self.assertTrue(set(label["contributing_labels"]) <= LABELS)
                self.assertTrue(label["evidence"])
                for evidence in label["evidence"]:
                    self.assertIn(
                        evidence["source"],
                        {"trace", "grader", "manifest", "workspace_diff"},
                    )
                    self.assertGreaterEqual(len(evidence["observation"]), 10)
                self.assertIn(label["confidence"], {"high", "medium", "low"})
                self.assertIsInstance(label["ambiguous"], bool)


if __name__ == "__main__":
    unittest.main()
