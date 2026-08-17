from __future__ import annotations

import json
from pathlib import Path

from .tools import ToolGateway
from .types import ToolCall, ToolResult


class FirstReadTimeoutGateway:
    """Inject one transient timeout before delegating to the real typed gateway."""

    def __init__(self, gateway: ToolGateway, target: str = "source.json") -> None:
        self.gateway = gateway
        self.target = target
        self.injected = False
        self.calls = 0

    @property
    def schemas(self):
        return self.gateway.schemas

    def execute(self, call: ToolCall) -> ToolResult:
        self.calls += 1
        if (
            not self.injected
            and call.name == "read_file"
            and call.arguments.get("path") in {self.target, f"./{self.target}"}
        ):
            self.injected = True
            return ToolResult(
                call.name,
                False,
                "TimeoutExpired: injected first read timeout",
                {"error_kind": "timeout", "injected": True},
            )
        return self.gateway.execute(call)


def grade_recovery_workspace(workspace: Path, seed: Path) -> dict[str, object]:
    result_path = workspace / "result.json"
    source_path = seed / "source.json"
    source_unchanged = (workspace / "source.json").read_bytes() == source_path.read_bytes()
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        expected = json.loads(source_path.read_text(encoding="utf-8"))
        artifact_correct = result == expected
    except (OSError, json.JSONDecodeError):
        artifact_correct = False
    return {
        "artifact_correct": artifact_correct,
        "source_unchanged": source_unchanged,
        "task_passed": artifact_correct and source_unchanged,
    }
