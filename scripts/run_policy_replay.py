"""Replay one sealed base completion under one declared verification policy."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore, PolicyReplayRunner
from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command
from forgebench.grader import DeterministicGrader
from run_codex_baseline import (
    GRADERS,
    MANIFEST_PATH,
    PINNED_CODEX_VERSION,
    ROOT,
    find_local_codex,
    find_local_linux_codex,
    windows_to_wsl,
)


POLICIES = (
    "accept_all",
    "verify_all",
    "random_k_call_matched",
    "probe_all",
    "risk_model_direct",
    "risk_hierarchical",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--base-id", required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--policy-runs-root", type=Path)
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument(
        "--execution-host", choices=["auto", "windows", "wsl"], default="auto"
    )
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--random-selected",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Frozen Random-k selection decision; required only for random_k_call_matched.",
    )
    args = parser.parse_args()

    bundle = BenchmarkCatalog(ROOT, MANIFEST_PATH).get(args.task_id)
    base_root = args.base_root or (args.runs_root / "base-completions")
    policy_runs_root = args.policy_runs_root or (args.runs_root / "policy-replays")
    base = BaseCompletionStore(base_root).load(args.base_id)

    model_required = args.policy in {
        "verify_all",
        "risk_model_direct",
        "risk_hierarchical",
    } or (args.policy == "random_k_call_matched" and args.random_selected is True)
    command_factory = None
    execution_host = args.execution_host
    if model_required:
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
                persist_session=False,
            )
    elif execution_host == "auto":
        execution_host = "not_used"

    result = PolicyReplayRunner(
        policy_runs_root, DeterministicGrader(GRADERS)
    ).run(
        task=bundle.task,
        seed=bundle.seed_path,
        base=base,
        policy=args.policy,
        command_factory=command_factory,
        random_selected=args.random_selected,
        timeout_seconds=args.timeout_seconds,
    )
    output = {
        "schema_version": 1,
        "harness": "policy-replay-v1",
        "run_id": result.run_id,
        "policy": result.policy,
        "base_id": result.base_id,
        "base_workspace_hash": result.base_workspace_hash,
        "task_id": args.task_id,
        "selected": result.selected,
        "provider": "codex-cli" if model_required else None,
        "cli_version": PINNED_CODEX_VERSION if model_required else None,
        "model": args.model if model_required else None,
        "reasoning_effort": args.reasoning_effort if model_required else None,
        "execution_host": execution_host,
        "risk_decision": result.risk_decision.as_dict(),
        "deterministic_probe": (
            result.deterministic_probe.as_dict()
            if result.deterministic_probe is not None
            else None
        ),
        "model_attempted": result.model_attempted,
        "completion_passed_after": result.completion_after.passed,
        "hidden_task_passed_after": result.grade_after.passed,
        "input_tokens": result.input_tokens,
        "cached_input_tokens": result.cached_input_tokens,
        "output_tokens": result.output_tokens,
        "duration_seconds": result.duration_seconds,
        "run_root": str(result.workspace.parent),
    }
    (result.workspace.parent / "run-summary.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
