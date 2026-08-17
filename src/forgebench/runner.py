from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .context_policy import BoundedContextPolicy, UnboundedContextPolicy
from .model import ModelAdapter
from .recovery import BoundedToolRecoveryPolicy
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
        context_policy: BoundedContextPolicy | None = None,
        recovery_policy: BoundedToolRecoveryPolicy | None = None,
        tool_gateway_factory: Callable[[Path], ToolGateway] | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.command_allowlist = command_allowlist or set()
        self.context_policy = context_policy or UnboundedContextPolicy()
        self.recovery_policy = recovery_policy
        self.tool_gateway_factory = tool_gateway_factory

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
        tools = (
            self.tool_gateway_factory(workspace)
            if self.tool_gateway_factory is not None
            else ToolGateway(workspace, command_allowlist=self.command_allowlist)
        )
        observations: list[ToolResult] = []

        trace.append(
            "run_started",
            {
                "model_id": model.model_id,
                "max_steps": max_steps,
                "task_instruction": task_instruction,
                "workspace": str(workspace),
                "tool_schemas": tools.schemas,
                "context_policy": type(self.context_policy).__name__,
                "recovery_policy": (
                    type(self.recovery_policy).__name__
                    if self.recovery_policy is not None
                    else None
                ),
            },
        )

        for step in range(max_steps):
            snapshot = self.context_policy.select(observations)
            if snapshot.compacted:
                trace.append(
                    "context_compacted",
                    {
                        "step": step,
                        "original_count": snapshot.original_count,
                        "retained_count": len(snapshot.observations),
                        "dropped_count": snapshot.dropped_count,
                        "original_chars": snapshot.original_chars,
                        "retained_chars": snapshot.retained_chars,
                    },
                )
            context = ModelContext(
                task_instruction=task_instruction,
                step=step,
                observations=snapshot.observations,
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
            if self.recovery_policy is not None and not result.ok:
                retries_used = 0
                call = action.tool_call
                while True:
                    decision = self.recovery_policy.decide(call, result, retries_used)
                    trace.append(
                        "recovery_decision",
                        {
                            "step": step,
                            "retry": decision.retry,
                            "reason": decision.reason,
                            "retries_used": retries_used,
                        },
                    )
                    if not decision.retry or decision.tool_call is None:
                        break
                    call = decision.tool_call
                    retries_used += 1
                    result = tools.execute(call)
                    observations.append(result)
                    trace.append(
                        "tool_result",
                        {
                            "step": step,
                            "recovery_attempt": retries_used,
                            "result": asdict(result),
                        },
                    )
                    if result.ok:
                        break

        trace.append("run_finished", {"reason": "step_budget_exhausted", "step": max_steps})
        return RunResult(run_id, workspace, trace_path, "step_budget_exhausted", max_steps, None)
