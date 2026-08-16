from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .model import ModelAdapter
from .tools import ToolGateway
from .trace import TraceWriter
from .types import ModelContext, ToolResult
from .workspace import create_isolated_workspace


@dataclass(frozen=True)
class RunResult:
    run_id: str
    workspace: Path
    trace_path: Path
    termination_reason: str
    steps: int
    final_answer: str | None


class AgentRunner:
    def __init__(
        self,
        runs_root: Path,
        *,
        command_allowlist: set[str] | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.command_allowlist = command_allowlist or set()

    def run(
        self,
        *,
        seed: Path,
        task_instruction: str,
        model: ModelAdapter,
        max_steps: int,
        run_id: str | None = None,
    ) -> RunResult:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        run_id = run_id or uuid.uuid4().hex
        workspace = create_isolated_workspace(seed, self.runs_root, run_id)
        trace_path = workspace.parent / "trace.jsonl"
        trace = TraceWriter(trace_path, run_id)
        tools = ToolGateway(workspace, command_allowlist=self.command_allowlist)
        observations: list[ToolResult] = []

        trace.append(
            "run_started",
            {
                "model_id": model.model_id,
                "max_steps": max_steps,
                "task_instruction": task_instruction,
                "workspace": str(workspace),
                "tool_schemas": tools.schemas,
            },
        )

        for step in range(max_steps):
            context = ModelContext(
                task_instruction=task_instruction,
                step=step,
                observations=tuple(observations),
                tool_schemas=tools.schemas,
            )
            action = model.next_action(context)
            trace.append("model_action", {"step": step, "action": asdict(action)})

            if action.kind == "finish":
                trace.append("run_finished", {"reason": "agent_finished", "step": step})
                return RunResult(
                    run_id,
                    workspace,
                    trace_path,
                    "agent_finished",
                    step + 1,
                    action.final_answer,
                )

            if action.kind != "tool" or action.tool_call is None:
                trace.append("run_finished", {"reason": "invalid_model_action", "step": step})
                return RunResult(run_id, workspace, trace_path, "invalid_model_action", step + 1, None)

            result = tools.execute(action.tool_call)
            observations.append(result)
            trace.append("tool_result", {"step": step, "result": asdict(result)})

        trace.append("run_finished", {"reason": "step_budget_exhausted", "step": max_steps})
        return RunResult(run_id, workspace, trace_path, "step_budget_exhausted", max_steps, None)

