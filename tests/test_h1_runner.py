import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.grader import DeterministicGrader
from forgebench.h1_runner import H1Runner


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "worker-visibility-incident" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "worker-visibility-incident"
GRADERS = ROOT / "benchmark" / "graders"


class H1RunnerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
