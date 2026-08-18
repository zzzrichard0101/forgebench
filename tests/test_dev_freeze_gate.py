import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "benchmark" / "manifest.json"
AUDIT_PATH = ROOT / "experiments" / "reports" / "dev-grader-audit-v0.5.json"


class DevelopmentFreezeGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.dev_records = [
            record for record in self.manifest["tasks"] if record["split"] == "dev"
        ]

    def test_audit_scope_and_distribution_match_the_frozen_snapshot(self) -> None:
        self.assertEqual(self.audit["dataset_snapshot"], "dev-v0.5")
        self.assertEqual(self.manifest["snapshot"], "dev-v0.6")
        self.assertEqual(len(self.dev_records), 20)
        self.assertEqual(
            [record["id"] for record in self.dev_records],
            self.audit["scope"]["audited_task_ids"],
        )
        self.assertEqual(
            dict(Counter(record["family"] for record in self.dev_records)),
            self.audit["distribution"]["family"],
        )
        self.assertEqual(
            dict(Counter(record["difficulty"] for record in self.dev_records)),
            self.audit["distribution"]["difficulty"],
        )

    def test_graders_do_not_inspect_implementation_source(self) -> None:
        prohibited = ("inspect.getsource", "ast.parse", ".read_bytes(")
        for record in self.dev_records:
            task = json.loads((ROOT / record["task_path"]).read_text(encoding="utf-8"))
            grader_scripts = [
                value.removeprefix("{grader_root}/")
                for check in task["grader"]["checks"]
                for value in check.get("argv", [])
                if value.startswith("{grader_root}/") and value.endswith(".py")
            ]
            self.assertTrue(grader_scripts, task["id"])
            for relative in grader_scripts:
                source = (ROOT / "benchmark" / "graders" / relative).read_text(
                    encoding="utf-8"
                )
                for marker in prohibited:
                    self.assertNotIn(marker, source, f"{task['id']}: {marker}")
                if task["family"] != "incident":
                    self.assertNotIn(".read_text(", source, task["id"])
                else:
                    self.assertIn('Path("incident_report.json").read_text', source)

    def test_audit_preserves_the_original_freeze_blocker(self) -> None:
        self.assertEqual(self.audit["decision"]["policy_freeze"], "blocked")
        self.assertFalse(self.audit["decision"]["held_out_authoring_allowed"])
        self.assertEqual(self.audit["decision"]["blocking_finding"], "F001")


if __name__ == "__main__":
    unittest.main()
