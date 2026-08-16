import json
import shutil
import tempfile
import unittest
from pathlib import Path

from forgebench.completion import CompletionVerifier


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "worker-visibility-incident" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "worker-visibility-incident"


class CompletionVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / "workspace"
        shutil.copytree(SEED, self.workspace)
        self.verifier = CompletionVerifier()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_missing_plan_and_artifact_block_completion(self) -> None:
        result = self.verifier.verify(TASK, self.workspace, SEED)
        self.assertFalse(result.passed)
        failed = {item.check_id for item in result.findings if not item.passed}
        self.assertIn("structured_plan", failed)
        self.assertIn("artifact:incident_report.json", failed)

    def test_protected_mutation_is_actionable(self) -> None:
        (self.workspace / "worker_config.json").write_text("{}\n", encoding="utf-8")
        result = self.verifier.verify(TASK, self.workspace, SEED)
        finding = next(
            item for item in result.findings if item.check_id == "protected:worker_config.json"
        )
        self.assertFalse(finding.passed)
        self.assertIn("Restore worker_config.json", finding.repair_instruction)

    def test_valid_plan_report_and_unchanged_evidence_pass(self) -> None:
        plan = {
            "objective": "Diagnose duplicate jobs and write only the report.",
            "steps": [
                {"action": "Analyze events", "verification": "Recount job IDs"},
                {"action": "Write report", "verification": "Validate JSON shape"},
            ],
            "immutable_paths": ["worker_config.json", "job_events.jsonl"],
            "completion_checks": ["report exists", "evidence unchanged"],
        }
        plan_path = self.workspace / ".forgebench" / "plan.json"
        plan_path.parent.mkdir()
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        report = {
            "incident_id": "worker-duplicate",
            "root_cause": "visibility timeout",
            "impact": {"duplicated_jobs": 2, "extra_attempts": 2},
            "evidence": ["timeout is 30", "jobs exceed timeout"],
            "remediation": {"config_change": "raise timeout", "verification": "monitor retries"},
        }
        (self.workspace / "incident_report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        result = self.verifier.verify(TASK, self.workspace, SEED)
        self.assertTrue(result.passed, result)


if __name__ == "__main__":
    unittest.main()
