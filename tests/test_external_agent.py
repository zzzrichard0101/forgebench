import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.external_agent import ExternalAgentRunner
from forgebench.grader import DeterministicGrader


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "examples" / "python-bugfix" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-cart-rounding"
GRADERS = ROOT / "benchmark" / "graders"


class ExternalAgentTests(unittest.TestCase):
    def test_external_process_is_captured_and_graded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = ExternalAgentRunner(
                Path(temp) / "runs", DeterministicGrader(GRADERS)
            )
            result = runner.run(
                task=TASK,
                seed=SEED,
                command=[sys.executable, "-c", "print('trace-event')"],
                timeout_seconds=30,
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(result.eligible_for_agent_metrics)
            self.assertIn("trace-event", result.raw_trace_path.read_text(encoding="utf-8"))
            self.assertFalse(result.grade.passed)
            self.assertTrue((result.workspace.parent / "external-manifest.json").exists())
            self.assertTrue((result.workspace.parent / "grader-result.json").exists())

    def test_nonzero_external_exit_is_not_an_agent_metric_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runner = ExternalAgentRunner(
                Path(temp) / "runs", DeterministicGrader(GRADERS)
            )
            result = runner.run(
                task=TASK,
                seed=SEED,
                command=[sys.executable, "-c", "raise SystemExit(7)"],
                timeout_seconds=30,
            )
            self.assertEqual(result.exit_code, 7)
            self.assertFalse(result.eligible_for_agent_metrics)


if __name__ == "__main__":
    unittest.main()
