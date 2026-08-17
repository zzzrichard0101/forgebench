from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from .external_agent import decode_process_output
from .types import ModelAction, ModelContext, ToolCall


CommandFactory = Callable[[str], list[str]]


class CodexModelError(RuntimeError):
    pass


class CodexCliModelAdapter:
    """Use one non-interactive Codex JSONL turn for each harness action."""

    def __init__(
        self,
        *,
        model_id: str,
        command_factory: CommandFactory,
        process_cwd: Path,
        trace_root: Path,
        timeout_seconds: int = 180,
    ) -> None:
        self._model_id = model_id
        self.command_factory = command_factory
        self.process_cwd = process_cwd
        self.trace_root = trace_root
        self.timeout_seconds = timeout_seconds
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.reasoning_output_tokens = 0

    @property
    def model_id(self) -> str:
        return self._model_id

    def next_action(self, context: ModelContext) -> ModelAction:
        self.calls += 1
        prompt = build_action_prompt(context)
        completed = subprocess.run(
            self.command_factory(prompt),
            cwd=self.process_cwd,
            capture_output=True,
            text=False,
            timeout=self.timeout_seconds,
            shell=False,
            check=False,
        )
        stdout = decode_process_output(completed.stdout)
        stderr = decode_process_output(completed.stderr)
        self.trace_root.mkdir(parents=True, exist_ok=True)
        (self.trace_root / f"turn-{self.calls}.jsonl").write_text(
            stdout, encoding="utf-8"
        )
        (self.trace_root / f"turn-{self.calls}.stderr.txt").write_text(
            stderr, encoding="utf-8"
        )
        if completed.returncode != 0:
            raise CodexModelError(
                f"Codex action turn {self.calls} exited {completed.returncode}: "
                f"{stderr[-1000:]}"
            )

        message, usage = parse_codex_jsonl(stdout)
        self.input_tokens += int(usage.get("input_tokens", 0))
        self.output_tokens += int(usage.get("output_tokens", 0))
        self.reasoning_output_tokens += int(usage.get("reasoning_output_tokens", 0))
        return parse_model_action(message)

    def usage(self) -> dict[str, int]:
        return {
            "model_calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_output_tokens": self.reasoning_output_tokens,
        }


def build_action_prompt(context: ModelContext) -> str:
    observations = [
        {
            "name": item.name,
            "ok": item.ok,
            "output": item.output,
            "metadata": item.metadata,
        }
        for item in context.observations
    ]
    examples = [
        {
            "kind": "tool",
            "tool_call": {"name": "<tool name>", "arguments": {}},
        },
        {"kind": "finish", "final_answer": "<short result>"},
    ]
    return f"""You are the decision component inside a typed agent harness.
Do not inspect the filesystem, run shell commands, or use built-in tools. Decide exactly one next action using only the task, tool schemas, and observations below.
Return exactly one JSON object with no markdown, explanation, or wrapper key. Use one of these two direct object shapes:
{json.dumps(examples, ensure_ascii=False)}

Task:
{context.task_instruction}

Step: {context.step}
Tool schemas:
{json.dumps(context.tool_schemas, ensure_ascii=False)}

Observations:
{json.dumps(observations, ensure_ascii=False)}
"""


def parse_codex_jsonl(value: str) -> tuple[str, dict[str, int]]:
    messages: list[str] = []
    usage: dict[str, int] = {}
    for line_number, line in enumerate(value.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexModelError(f"invalid Codex JSONL at line {line_number}") from exc
        item = event.get("item", {})
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "agent_message"
        ):
            messages.append(str(item.get("text", "")))
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
    if not messages:
        raise CodexModelError("Codex JSONL contained no completed agent message")
    return messages[-1], usage


def parse_model_action(value: str) -> ModelAction:
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CodexModelError(f"Codex action is not valid JSON: {text[:500]}") from exc
    if isinstance(payload, dict) and len(payload) == 1:
        wrapped = payload.get("tool_action") or payload.get("finish_action")
        if isinstance(wrapped, dict):
            payload = wrapped
    if payload.get("kind") == "finish" and isinstance(
        payload.get("final_answer"), str
    ):
        return ModelAction.finish(payload["final_answer"])
    if payload.get("kind") == "tool":
        call = payload.get("tool_call")
        if (
            isinstance(call, dict)
            and isinstance(call.get("name"), str)
            and isinstance(call.get("arguments"), dict)
        ):
            return ModelAction(
                kind="tool",
                tool_call=ToolCall(call["name"], call["arguments"]),
            )
    raise CodexModelError("Codex action does not match the typed action schema")
