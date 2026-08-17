import subprocess
import tempfile
import unittest
from pathlib import Path

from forgebench.context_policy import BoundedContextPolicy
from forgebench.recovery import BoundedToolRecoveryPolicy
from forgebench.tools import ToolGateway
from forgebench.types import ToolCall, ToolResult


class ContextPolicyTests(unittest.TestCase):
    def test_failures_are_prioritized_over_old_successes(self) -> None:
        observations = [
            ToolResult("read_file", True, "old success"),
            ToolResult("run_command", False, "important failure"),
            ToolResult("read_file", True, "new success"),
        ]
        snapshot = BoundedContextPolicy(max_observations=2, max_chars=100).select(
            observations
        )
        self.assertEqual(
            [item.output for item in snapshot.observations],
            ["important failure", "new success"],
        )
        self.assertEqual(snapshot.dropped_count, 1)

    def test_large_outputs_are_truncated_under_budget(self) -> None:
        snapshot = BoundedContextPolicy(
            max_observations=2, max_chars=40, max_item_chars=40
        ).select([ToolResult("read_file", True, "x" * 100)])
        self.assertTrue(snapshot.compacted)
        self.assertTrue(snapshot.observations[0].metadata["context_truncated"])
        self.assertIn("context truncated", snapshot.observations[0].output)
        self.assertLessEqual(snapshot.retained_chars, 40)


class RecoveryPolicyTests(unittest.TestCase):
    def test_gateway_normalizes_timeout_as_transient_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            gateway = ToolGateway(Path(temp))

            def timeout(_arguments):
                raise subprocess.TimeoutExpired(["test"], 3)

            gateway._handlers["injected_timeout"] = timeout
            result = gateway.execute(ToolCall("injected_timeout", {}))
            self.assertFalse(result.ok)
            self.assertEqual(result.metadata["error_kind"], "timeout")

    def test_timeout_is_retried_once_with_bounded_timeout(self) -> None:
        policy = BoundedToolRecoveryPolicy(max_retries=1, timeout_multiplier=2)
        call = ToolCall("run_command", {"argv": ["python", "test.py"], "timeout_seconds": 70})
        failure = ToolResult("run_command", False, "timeout", {"error_kind": "timeout"})
        first = policy.decide(call, failure, retries_used=0)
        second = policy.decide(call, failure, retries_used=1)
        self.assertTrue(first.retry)
        self.assertEqual(first.tool_call.arguments["timeout_seconds"], 120)
        self.assertFalse(second.retry)
        self.assertEqual(second.reason, "retry_budget_exhausted")

    def test_deterministic_failure_is_not_retried(self) -> None:
        decision = BoundedToolRecoveryPolicy().decide(
            ToolCall("read_file", {"path": "missing"}),
            ToolResult("read_file", False, "missing", {"error_kind": "deterministic"}),
            retries_used=0,
        )
        self.assertFalse(decision.retry)
        self.assertEqual(decision.reason, "deterministic_or_unknown_failure")


if __name__ == "__main__":
    unittest.main()
