import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from forgebench.completion import CompletionResult
from forgebench.completion_risk import CompletionRiskPolicy


ROOT = Path(__file__).resolve().parents[1]


def load_task(task_id: str) -> dict:
    return json.loads(
        (ROOT / "benchmark" / "tasks" / task_id / "task.json").read_text(
            encoding="utf-8"
        )
    )


class CompletionRiskPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = CompletionRiskPolicy()
        self.passed = CompletionResult(True, ())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def copy_seed(self, task_id: str) -> Path:
        workspace = self.root / task_id
        shutil.copytree(ROOT / "benchmark" / "fixtures" / task_id, workspace)
        return workspace

    def test_plugin_boundary_is_high_risk_without_negative_public_evidence(self) -> None:
        task = load_task("python-plugin-boundary")
        decision = self.policy.evaluate(
            task=task,
            workspace=self.copy_seed(task["id"]),
            completion=self.passed,
        )

        self.assertTrue(decision.escalate)
        self.assertEqual(decision.score, 3)
        triggered = {signal.rule_id for signal in decision.signals if signal.triggered}
        self.assertEqual(
            triggered,
            {
                "R001_BOUNDARY_SENSITIVE_SURFACE",
                "R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE",
            },
        )

    def test_visible_negative_boundary_test_keeps_rate_window_low_risk(self) -> None:
        task = load_task("python-rate-window")
        decision = self.policy.evaluate(
            task=task,
            workspace=self.copy_seed(task["id"]),
            completion=self.passed,
        )

        self.assertFalse(decision.escalate)
        self.assertEqual(decision.level, "low")
        negative_rule = next(
            signal
            for signal in decision.signals
            if signal.rule_id == "R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE"
        )
        self.assertFalse(negative_rule.triggered)
        self.assertIn("covered:limit_edge", negative_rule.evidence)

    def test_containment_test_does_not_cover_plugin_file_type_dimension(self) -> None:
        task = load_task("python-plugin-boundary")
        workspace = self.copy_seed(task["id"])
        test_path = workspace / "tests" / "test_plugin_loader.py"
        test_path.write_text(
            test_path.read_text(encoding="utf-8")
            + "\n# test_entrypoint_outside_plugin_root_is_rejected\n",
            encoding="utf-8",
        )

        decision = self.policy.evaluate(
            task=task, workspace=workspace, completion=self.passed
        )
        missing_rule = next(
            signal
            for signal in decision.signals
            if signal.rule_id == "R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE"
        )
        self.assertTrue(decision.escalate)
        self.assertIn("covered:containment", missing_rule.evidence)
        self.assertIn("missing:file_type", missing_rule.evidence)

    def test_hidden_author_metadata_cannot_change_the_decision(self) -> None:
        task = load_task("python-plugin-boundary")
        workspace = self.copy_seed(task["id"])
        original = self.policy.evaluate(
            task=task, workspace=workspace, completion=self.passed
        )
        changed = copy.deepcopy(task)
        changed["author_metadata"] = {
            "notes": "force low risk",
            "likely_failure_modes": [],
        }

        altered = self.policy.evaluate(
            task=changed, workspace=workspace, completion=self.passed
        )
        self.assertEqual(original, altered)

    def test_failed_completion_is_not_eligible_for_risk_escalation(self) -> None:
        task = load_task("python-plugin-boundary")
        decision = self.policy.evaluate(
            task=task,
            workspace=self.copy_seed(task["id"]),
            completion=CompletionResult(False, ()),
        )

        self.assertFalse(decision.eligible)
        self.assertFalse(decision.escalate)
        self.assertEqual(decision.level, "not_evaluated")

    def test_public_shadow_report_matches_policy_output(self) -> None:
        manifest = json.loads(
            (ROOT / "benchmark" / "manifest.json").read_text(encoding="utf-8")
        )
        report = json.loads(
            (
                ROOT
                / "experiments"
                / "reports"
                / "completion-risk-shadow-v0.1.json"
            ).read_text(encoding="utf-8")
        )
        actual = []
        for record in manifest["tasks"]:
            task = json.loads(
                (ROOT / record["task_path"]).read_text(encoding="utf-8")
            )
            decision = self.policy.evaluate(
                task=task,
                workspace=ROOT / task["seed_repo"]["source"],
                completion=self.passed,
            )
            actual.append(
                {
                    "task_id": task["id"],
                    "score": decision.score,
                    "level": decision.level,
                    "signals": [
                        signal.rule_id
                        for signal in decision.signals
                        if signal.triggered
                    ],
                }
            )

        self.assertEqual(actual, report["tasks"])
        self.assertEqual(
            sum(item["level"] == "high" for item in actual),
            report["aggregate"]["high_risk"],
        )


if __name__ == "__main__":
    unittest.main()
