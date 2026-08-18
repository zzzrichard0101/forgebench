"""Run the H1 planning, completion-verification, and repair harness."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command
from forgebench.completion_risk import CompletionRiskPolicy
from forgebench.grader import DeterministicGrader
from forgebench.h1_runner import H1Runner
from run_codex_baseline import (
    GRADERS,
    MANIFEST_PATH,
    PINNED_CODEX_VERSION,
    ROOT,
    find_local_codex,
    find_local_linux_codex,
    windows_to_wsl,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument(
        "--codex-home",
        type=Path,
        help="Override CODEX_HOME (use the same directory when resuming a session).",
    )
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--risk-shadow",
        action="store_true",
        help="Record Completion Risk Gate decisions without changing execution.",
    )
    parser.add_argument(
        "--persist-session",
        action="store_true",
        help="Persist the Codex session so a later adaptive pass can resume it.",
    )
    parser.add_argument(
        "--profile",
        choices=["planning", "planning-lite", "verification", "repair"],
        default="repair",
    )
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, MANIFEST_PATH)
    bundle = catalog.get(args.task_id)
    execution_host = args.execution_host
    if execution_host == "auto":
        execution_host = "wsl" if platform.system() == "Windows" else "windows"
    codex_home = (args.codex_home or (Path.home() / ".codex")).resolve(strict=True)
    os.environ["CODEX_HOME"] = str(codex_home)

    if execution_host == "wsl":
        codex = (args.codex_bin or find_local_linux_codex()).resolve(strict=True)
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        if wsl is None:
            raise FileNotFoundError("WSL executable not found")
        prefix = [
            wsl,
            "-d",
            "Ubuntu",
            "--",
            "env",
            f"CODEX_HOME={windows_to_wsl(codex_home)}",
            windows_to_wsl(codex),
        ]
        map_workspace = windows_to_wsl
    else:
        codex = (args.codex_bin or find_local_codex()).resolve(strict=True)
        prefix = [str(codex)]
        map_workspace = str

    def command_factory(prompt: str, workspace: Path) -> list[str]:
        return build_exec_command(
            prefix=prefix,
            prompt=prompt,
            workspace=map_workspace(workspace),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            persist_session=args.persist_session,
        )

    runner = H1Runner(args.runs_root, DeterministicGrader(GRADERS))
    profiles = {
        "planning": ("H1a-structured-planning", "structured", False, 0),
        "planning-lite": ("H1a-lite-bounded-planning", "lite", False, 0),
        "verification": ("H1b-planning-completion", "structured", True, 0),
        "repair": ("H1c-planning-completion-repair", "structured", True, 1),
    }
    harness_name, prompt_style, completion_gate, max_repair_attempts = profiles[args.profile]
    result = runner.run(
        task=bundle.task,
        seed=bundle.seed_path,
        command_factory=command_factory,
        harness_name=harness_name,
        prompt_style=prompt_style,
        completion_gate=completion_gate,
        max_repair_attempts=max_repair_attempts,
        risk_policy=CompletionRiskPolicy() if args.risk_shadow else None,
    )
    token_budget_compliant = (
        result.input_tokens <= bundle.task["budgets"]["max_input_tokens"]
        and result.output_tokens <= bundle.task["budgets"]["max_output_tokens"]
    )
    time_budget_compliant = (
        result.duration_seconds <= bundle.task["budgets"]["max_seconds"]
    )
    completion_accepted = result.completion.passed or not completion_gate
    budget_qualified_success = (
        False
        if not (
            result.grade.passed
            and completion_accepted
            and token_budget_compliant
            and time_budget_compliant
        )
        else None
    )
    summary = {
        "schema_version": 1,
        "harness": harness_name,
        "profile": args.profile,
        "run_id": result.run_id,
        "task_id": bundle.task["id"],
        "task_version": bundle.task["version"],
        "provider": "codex-cli",
        "cli_version": PINNED_CODEX_VERSION,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "execution_host": execution_host,
        "attempts": result.attempts,
        "completion_passed": result.completion.passed,
        "risk_mode": "shadow" if args.risk_shadow else "off",
        "session_persistence": "persisted" if args.persist_session else "ephemeral",
        "session_id": result.session_id,
        "risk_decision": (
            result.risk_decision.as_dict() if result.risk_decision is not None else None
        ),
        "task_passed": result.grade.passed,
        "duration_seconds": result.duration_seconds,
        "input_tokens": result.input_tokens,
        "cached_input_tokens": result.cached_input_tokens,
        "output_tokens": result.output_tokens,
        "token_budget_compliant": token_budget_compliant,
        "time_budget_compliant": time_budget_compliant,
        "step_budget_enforced": False,
        "budget_qualification_complete": False,
        "budget_qualified_success": budget_qualified_success,
        "run_root": str(result.workspace.parent),
    }
    (result.workspace.parent / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result.grade.passed and completion_accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
