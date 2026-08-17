"""Replay a completed H1a-lite workspace through adaptive deep verification."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
from pathlib import Path

from forgebench.adaptive_verification import AdaptiveVerificationRunner
from forgebench.catalog import BenchmarkCatalog
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, MANIFEST_PATH)
    bundle = catalog.get(args.task_id)
    source_root = args.runs_root / args.source_run_id
    source_workspace = source_root / "workspace"
    source_summary_path = source_root / "run-summary.json"
    if not source_workspace.is_dir() or not source_summary_path.is_file():
        raise FileNotFoundError(f"source run is incomplete: {source_root}")
    source_summary = json.loads(source_summary_path.read_text(encoding="utf-8"))
    if source_summary.get("task_id") != args.task_id:
        raise ValueError("source run task does not match --task-id")
    if source_summary.get("profile") != "planning-lite":
        raise ValueError("adaptive replay requires a planning-lite source run")

    execution_host = args.execution_host
    if execution_host == "auto":
        execution_host = "wsl" if platform.system() == "Windows" else "windows"
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
            f"CODEX_HOME={windows_to_wsl(Path.home() / '.codex')}",
            windows_to_wsl(codex),
        ]
        map_workspace = windows_to_wsl
    else:
        codex = (args.codex_bin or find_local_codex()).resolve(strict=True)
        prefix = [str(codex)]
        map_workspace = str

    def command_factory(prompt: str, workspace: Path) -> list[str]:
        return [
            *prefix,
            "--ask-for-approval",
            "never",
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--model",
            args.model,
            "--config",
            f'model_reasoning_effort="{args.reasoning_effort}"',
            "--cd",
            map_workspace(workspace),
            prompt,
        ]

    runner = AdaptiveVerificationRunner(
        args.runs_root, DeterministicGrader(GRADERS)
    )
    result = runner.run(
        task=bundle.task,
        seed=bundle.seed_path,
        source_workspace=source_workspace,
        source_run_id=args.source_run_id,
        command_factory=command_factory,
        timeout_seconds=args.timeout_seconds,
    )
    summary = {
        "schema_version": 1,
        "harness": "H1a-adaptive-replay-v0.1",
        "run_id": result.run_id,
        "source_run_id": args.source_run_id,
        "task_id": args.task_id,
        "provider": "codex-cli",
        "cli_version": PINNED_CODEX_VERSION,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "execution_host": execution_host,
        "risk_decision": result.risk_decision.as_dict(),
        "deep_verification_attempted": result.attempted,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "task_passed_before": result.grade_before.passed,
        "task_passed_after": result.grade_after.passed,
        "completion_passed_after": result.completion_after.passed,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "duration_seconds": result.duration_seconds,
        "run_root": str(result.workspace.parent),
    }
    (result.workspace.parent / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result.grade_after.passed and result.completion_after.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

