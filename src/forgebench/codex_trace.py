from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CodexTraceSummary:
    event_count: int
    command_count: int
    command_completed: int
    command_failed: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    session_id: str | None = None

    def as_dict(self) -> dict[str, int | str | None]:
        return asdict(self)

    def budget_compliant(self, budgets: dict[str, Any]) -> bool:
        return (
            self.input_tokens <= budgets["max_input_tokens"]
            and self.output_tokens <= budgets["max_output_tokens"]
        )


def summarize_codex_trace(path: Path) -> CodexTraceSummary:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Codex JSONL at line {line_number}") from exc

    commands = [
        event["item"]
        for event in events
        if event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "command_execution"
    ]
    usage: dict[str, int] = {}
    session_id: str | None = None
    for event in events:
        if event.get("type") == "thread.started":
            value = event.get("thread_id")
            if isinstance(value, str) and value:
                session_id = value
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
    return CodexTraceSummary(
        event_count=len(events),
        command_count=len(commands),
        command_completed=sum(item.get("status") == "completed" for item in commands),
        command_failed=sum(item.get("status") == "failed" for item in commands),
        input_tokens=int(usage.get("input_tokens", 0)),
        cached_input_tokens=int(usage.get("cached_input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        reasoning_output_tokens=int(usage.get("reasoning_output_tokens", 0)),
        session_id=session_id,
    )
