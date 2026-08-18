import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.grader import DeterministicGrader
from forgebench.h1_runner import H1Runner, build_h1_prompt
from forgebench.completion_risk import CompletionRiskPolicy


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "worker-visibility-incident" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "worker-visibility-incident"
GRADERS = ROOT / "benchmark" / "graders"


class H1RunnerTests(unittest.TestCase):
    def test_trace_session_id_is_propagated_to_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = H1Runner(Path(temp) / "runs", DeterministicGrader(GRADERS))
            session_id = "01a00b3b-7a93-7eb1-8329-c683c8034510"

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                plan = {
                    "objective": "Diagnose duplicate jobs without changing evidence.",
                    "steps": [
                        {"action": "Analyze", "verification": "Recount attempts"},
                        {"action": "Report", "verification": "Validate JSON"},
                    ],
                    "immutable_paths": ["worker_config.json", "job_events.jsonl"],
                    "completion_checks": ["report exists", "evidence unchanged"],
                }
                report = {
                    "incident_id": "worker-duplicate",
                    "root_cause": "Visibility timeout is below job runtime",
                    "impact": {"duplicated_jobs": 2, "extra_attempts": 2},
                    "evidence": ["Timeout is 30 seconds", "Jobs exceed timeout"],
                    "remediation": {
                        "config_change": "Raise visibility timeout",
                        "verification": "Confirm jobs complete exactly once",
                    },
                }
                script = (
                    "import json; from pathlib import Path; "
                    f"print(json.dumps({{'type':'thread.started','thread_id':{session_id!r}}})); "
                    f"print(json.dumps({{'type':'turn.completed','usage':{{'input_tokens':3,'output_tokens':2}}}})); "
                    "root=Path.cwd(); (root/'.forgebench').mkdir(exist_ok=True); "
                    f"(root/'.forgebench'/'plan.json').write_text({json.dumps(json.dumps(plan))}, encoding='utf-8'); "
                    f"(root/'incident_report.json').write_text({json.dumps(json.dumps(report))}, encoding='utf-8')"
                )
                return [sys.executable, "-c", script]

            result = runner.run(
                task=TASK,
                seed=SEED,
                command_factory=command_factory,
                max_repair_attempts=0,
            )
            manifest = json.loads(
                (result.workspace.parent / "h1-manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(result.session_id, session_id)
            self.assertEqual(manifest["session_id"], session_id)

    def test_lite_prompt_keeps_schema_and_immutable_contract_concise(self) -> None:
        prompt = build_h1_prompt(TASK, style="lite")
        self.assertIn("2-4 steps", prompt)
        self.assertIn("worker_config.json", prompt)
        self.assertIn("job_events.jsonl", prompt)
        self.assertIn("read-only", prompt)
        self.assertLess(len(prompt), len(build_h1_prompt(TASK)))

    def test_failed_completion_check_triggers_repair_in_same_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = H1Runner(Path(temp) / "runs", DeterministicGrader(GRADERS))
            invocations = 0

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                nonlocal invocations
                invocations += 1
                is_repair = invocations > 1
                plan = {
                    "objective": "Diagnose duplicate jobs without changing evidence.",
                    "steps": [
                        {"action": "Analyze", "verification": "Recount attempts"},
                        {"action": "Report", "verification": "Validate JSON"},
                    ],
                    "immutable_paths": ["worker_config.json", "job_events.jsonl"],
                    "completion_checks": ["report exists", "evidence unchanged"],
                }
                report = {
                    "incident_id": "worker-duplicate",
                    "root_cause": "Visibility timeout is below job runtime",
                    "impact": {"duplicated_jobs": 2, "extra_attempts": 2},
                    "evidence": ["Timeout is 30 seconds", "Jobs take 38 to 42 seconds"],
                    "remediation": {
                        "config_change": "Raise the visibility timeout above runtime.",
                        "verification": "Confirm every long-running job completes exactly once.",
                    },
                }
                config = (
                    (SEED / "worker_config.json").read_bytes()
                    if is_repair
                    else b'{"visibility_timeout_seconds": 60, "max_attempts": 3}\n'
                )
                script = (
                    "import json; from pathlib import Path; root=Path.cwd(); "
                    "(root/'.forgebench').mkdir(exist_ok=True); "
                    f"(root/'.forgebench'/'plan.json').write_text({json.dumps(json.dumps(plan))}, encoding='utf-8'); "
                    f"(root/'incident_report.json').write_text({json.dumps(json.dumps(report))}, encoding='utf-8'); "
                    f"(root/'worker_config.json').write_bytes({config!r})"
                )
                return [sys.executable, "-c", script]

            result = runner.run(
                task=TASK,
                seed=SEED,
                command_factory=command_factory,
                max_repair_attempts=1,
            )
            manifest = json.loads(
                (result.workspace.parent / "h1-manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(result.attempts, 2)
            self.assertEqual(
                (result.workspace / "worker_config.json").read_bytes(),
                (SEED / "worker_config.json").read_bytes(),
            )
            self.assertTrue(result.completion.passed, manifest)
            self.assertTrue(result.grade.passed)
            self.assertFalse(manifest["attempts"][0]["completion"]["passed"])
            self.assertTrue(manifest["attempts"][1]["completion"]["passed"])

    def test_planning_profile_records_but_does_not_repair_completion_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = H1Runner(Path(temp) / "runs", DeterministicGrader(GRADERS))

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                script = (
                    "from pathlib import Path; "
                    "Path('worker_config.json').write_text('{}', encoding='utf-8')"
                )
                return [sys.executable, "-c", script]

            result = runner.run(
                task=TASK,
                seed=SEED,
                command_factory=command_factory,
                harness_name="H1a-structured-planning",
                completion_gate=False,
                max_repair_attempts=0,
            )

            self.assertEqual(result.attempts, 1)
            self.assertFalse(result.completion.passed)
            self.assertFalse(result.grade.passed)
            manifest = json.loads(
                (result.workspace.parent / "h1-manifest.json").read_text(encoding="utf-8")
            )
            self.assertFalse(manifest["completion_gate"])

    def test_risk_shadow_mode_records_manifest_and_trace_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = H1Runner(Path(temp) / "runs", DeterministicGrader(GRADERS))

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                plan = {
                    "objective": "Diagnose duplicate jobs without changing evidence.",
                    "steps": [
                        {"action": "Analyze", "verification": "Recount attempts"},
                        {"action": "Report", "verification": "Validate JSON"},
                    ],
                    "immutable_paths": ["worker_config.json", "job_events.jsonl"],
                    "completion_checks": ["report exists", "evidence unchanged"],
                }
                report = {
                    "incident_id": "worker-duplicate",
                    "root_cause": "Visibility timeout is below job runtime",
                    "impact": {"duplicated_jobs": 2, "extra_attempts": 2},
                    "evidence": ["Timeout is 30 seconds", "Jobs exceed timeout"],
                    "remediation": {
                        "config_change": "Raise visibility timeout",
                        "verification": "Confirm jobs complete exactly once",
                    },
                }
                script = (
                    "import json; from pathlib import Path; root=Path.cwd(); "
                    "(root/'.forgebench').mkdir(exist_ok=True); "
                    f"(root/'.forgebench'/'plan.json').write_text({json.dumps(json.dumps(plan))}, encoding='utf-8'); "
                    f"(root/'incident_report.json').write_text({json.dumps(json.dumps(report))}, encoding='utf-8')"
                )
                return [sys.executable, "-c", script]

            result = runner.run(
                task=TASK,
                seed=SEED,
                command_factory=command_factory,
                max_repair_attempts=0,
                risk_policy=CompletionRiskPolicy(),
            )
            run_root = result.workspace.parent
            manifest = json.loads(
                (run_root / "h1-manifest.json").read_text(encoding="utf-8")
            )
            event = json.loads(
                (run_root / "harness-trace.jsonl").read_text(encoding="utf-8")
            )

            self.assertEqual(manifest["risk_mode"], "shadow")
            self.assertEqual(manifest["risk_decision"]["level"], "low")
            self.assertEqual(event["kind"], "completion_risk_decision")
            self.assertEqual(event["payload"], manifest["risk_decision"])
            self.assertEqual(result.risk_decision.level, "low")


if __name__ == "__main__":
    unittest.main()
