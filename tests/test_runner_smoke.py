import json
import tempfile
import unittest
from pathlib import Path

from forgebench.context_policy import BoundedContextPolicy
from forgebench.model import ScriptedModelAdapter
from forgebench.recovery import BoundedToolRecoveryPolicy
from forgebench.runner import AgentRunner
from forgebench.types import ModelAction, ToolResult


class RunnerSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.seed = self.root / "seed"
        self.seed.mkdir()
        (self.seed / "note.txt").write_text("alpha\nneedle\nomega\n", encoding="utf-8")
        self.runner = AgentRunner(self.root / "runs")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_smoke_1_read_then_finish(self) -> None:
        result = self._run([
            ModelAction.call("read_file", path="note.txt"),
            ModelAction.finish("read"),
        ])
        self.assertEqual(result.termination_reason, "agent_finished")
        self.assertTraceKinds(result.trace_path, ["run_started", "model_action", "tool_result", "model_action", "run_finished"])

    def test_smoke_2_write_is_confined_to_copy(self) -> None:
        result = self._run([
            ModelAction.call("write_file", path="result.txt", content="done\n"),
            ModelAction.finish("wrote"),
        ])
        self.assertTrue((result.workspace / "result.txt").exists())
        self.assertFalse((self.seed / "result.txt").exists())

    def test_smoke_3_search_returns_observation(self) -> None:
        result = self._run([
            ModelAction.call("search_text", query="needle", path="."),
            ModelAction.finish("found"),
        ])
        events = self.readEvents(result.trace_path)
        tool_event = next(event for event in events if event["kind"] == "tool_result")
        self.assertIn("note.txt:2:needle", tool_event["payload"]["result"]["output"])

    def test_smoke_4_path_escape_is_observed_as_error(self) -> None:
        result = self._run([
            ModelAction.call("read_file", path="../outside.txt"),
            ModelAction.finish("handled"),
        ])
        events = self.readEvents(result.trace_path)
        tool_event = next(event for event in events if event["kind"] == "tool_result")
        self.assertFalse(tool_event["payload"]["result"]["ok"])
        self.assertIn("escapes workspace", tool_event["payload"]["result"]["output"])

    def test_smoke_5_budget_exhaustion_is_explicit(self) -> None:
        result = self._run([ModelAction.call("list_files", path=".")], max_steps=1)
        self.assertEqual(result.termination_reason, "step_budget_exhausted")
        events = self.readEvents(result.trace_path)
        self.assertEqual(events[-1]["payload"]["reason"], "step_budget_exhausted")

    def test_context_compaction_is_visible_in_trace(self) -> None:
        runner = AgentRunner(
            self.root / "bounded-runs",
            context_policy=BoundedContextPolicy(max_observations=1, max_chars=100),
        )
        result = runner.run(
            seed=self.seed,
            task_instruction="Exercise bounded context.",
            model=ScriptedModelAdapter(
                [
                    ModelAction.call("list_files", path="."),
                    ModelAction.call("read_file", path="note.txt"),
                    ModelAction.finish("done"),
                ]
            ),
            max_steps=3,
        )
        compacted = [
            event
            for event in self.readEvents(result.trace_path)
            if event["kind"] == "context_compacted"
        ]
        self.assertEqual(len(compacted), 1)
        self.assertEqual(compacted[0]["payload"]["dropped_count"], 1)

    def test_deterministic_tool_error_is_not_retried(self) -> None:
        runner = AgentRunner(
            self.root / "recovery-runs",
            recovery_policy=BoundedToolRecoveryPolicy(max_retries=1),
        )
        result = runner.run(
            seed=self.seed,
            task_instruction="Exercise recovery classification.",
            model=ScriptedModelAdapter(
                [
                    ModelAction.call("read_file", path="../outside.txt"),
                    ModelAction.finish("done"),
                ]
            ),
            max_steps=2,
        )
        decisions = [
            event
            for event in self.readEvents(result.trace_path)
            if event["kind"] == "recovery_decision"
        ]
        self.assertEqual(len(decisions), 1)
        self.assertFalse(decisions[0]["payload"]["retry"])
        self.assertEqual(
            decisions[0]["payload"]["reason"],
            "deterministic_or_unknown_failure",
        )

    def test_transient_timeout_is_retried_and_recorded(self) -> None:
        class FlakyGateway:
            schemas = ()

            def __init__(self) -> None:
                self.calls = 0

            def execute(self, call):
                self.calls += 1
                if self.calls == 1:
                    return ToolResult(
                        call.name,
                        False,
                        "injected timeout",
                        {"error_kind": "timeout"},
                    )
                return ToolResult(call.name, True, "recovered")

        gateway = FlakyGateway()
        runner = AgentRunner(
            self.root / "transient-runs",
            recovery_policy=BoundedToolRecoveryPolicy(max_retries=1),
            tool_gateway_factory=lambda _workspace: gateway,
        )
        result = runner.run(
            seed=self.seed,
            task_instruction="Recover from a transient failure.",
            model=ScriptedModelAdapter(
                [ModelAction.call("flaky"), ModelAction.finish("done")]
            ),
            max_steps=2,
        )
        events = self.readEvents(result.trace_path)
        tool_results = [event for event in events if event["kind"] == "tool_result"]
        decisions = [event for event in events if event["kind"] == "recovery_decision"]
        self.assertEqual(gateway.calls, 2)
        self.assertEqual(len(tool_results), 2)
        self.assertTrue(decisions[0]["payload"]["retry"])
        self.assertEqual(tool_results[1]["payload"]["recovery_attempt"], 1)

    def _run(self, actions: list[ModelAction], max_steps: int = 5):
        return self.runner.run(
            seed=self.seed,
            task_instruction="Smoke-test the runner.",
            model=ScriptedModelAdapter(actions),
            max_steps=max_steps,
        )

    def readEvents(self, path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def assertTraceKinds(self, path: Path, expected: list[str]) -> None:
        self.assertEqual([event["kind"] for event in self.readEvents(path)], expected)


if __name__ == "__main__":
    unittest.main()
