import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "benchmark" / "manifest.json"
AUDIT_PATH = ROOT / "experiments" / "reports" / "dev-grader-audit-v0.5.json"
PROTOCOL_PATH = ROOT / "experiments" / "configs" / "selective-verification-protocol-v1.json"
PROBE_SOURCE = ROOT / "src" / "forgebench" / "deterministic_probe.py"


class DevelopmentFreezeGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.dev_records = [
            record for record in self.manifest["tasks"] if record["split"] == "dev"
        ]

    def test_audit_scope_and_distribution_match_the_frozen_snapshot(self) -> None:
        self.assertEqual(self.manifest["snapshot"], self.audit["dataset_snapshot"])
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

    def test_policy_freeze_remains_blocked_until_probe_is_transferable(self) -> None:
        protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        probe_source = PROBE_SOURCE.read_text(encoding="utf-8")
        self.assertFalse(protocol["current_task_id_probe_held_out_eligible"])
        self.assertIn('task.get("id") != "python-plugin-boundary"', probe_source)
        self.assertEqual(self.audit["decision"]["policy_freeze"], "blocked")
        self.assertFalse(self.audit["decision"]["held_out_authoring_allowed"])
        self.assertEqual(self.audit["decision"]["blocking_finding"], "F001")


if __name__ == "__main__":
    unittest.main()
