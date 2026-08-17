from __future__ import annotations

from dataclasses import dataclass

from .types import ToolCall, ToolResult


@dataclass(frozen=True)
class RecoveryDecision:
    retry: bool
    reason: str
    tool_call: ToolCall | None = None


class BoundedToolRecoveryPolicy:
    """Retry transient timeouts only; deterministic failures return to the model."""

    def __init__(self, *, max_retries: int = 1, timeout_multiplier: int = 2) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if timeout_multiplier < 1:
            raise ValueError("timeout_multiplier must be positive")
        self.max_retries = max_retries
        self.timeout_multiplier = timeout_multiplier

    def decide(
        self, call: ToolCall, result: ToolResult, retries_used: int
    ) -> RecoveryDecision:
        if result.ok:
            return RecoveryDecision(False, "tool_succeeded")
        if result.metadata.get("error_kind") != "timeout":
            return RecoveryDecision(False, "deterministic_or_unknown_failure")
        if retries_used >= self.max_retries:
            return RecoveryDecision(False, "retry_budget_exhausted")

        arguments = dict(call.arguments)
        if call.name == "run_command":
            timeout = arguments.get("timeout_seconds", 30)
            if isinstance(timeout, int):
                arguments["timeout_seconds"] = min(
                    120, timeout * self.timeout_multiplier
                )
        return RecoveryDecision(
            True,
            "transient_timeout",
            ToolCall(call.name, arguments),
        )
