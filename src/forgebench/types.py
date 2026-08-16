from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelAction:
    kind: Literal["tool", "finish"]
    tool_call: ToolCall | None = None
    final_answer: str | None = None

    @classmethod
    def call(cls, name: str, **arguments: Any) -> "ModelAction":
        return cls(kind="tool", tool_call=ToolCall(name=name, arguments=arguments))

    @classmethod
    def finish(cls, answer: str) -> "ModelAction":
        return cls(kind="finish", final_answer=answer)


@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelContext:
    task_instruction: str
    step: int
    observations: tuple[ToolResult, ...]
    tool_schemas: tuple[dict[str, Any], ...]

