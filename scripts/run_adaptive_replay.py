"""Replay a completed H1a-lite workspace through adaptive deep verification."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path

from forgebench.adaptive_verification import AdaptiveVerificationRunner
from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_command import build_exec_command, build_resume_command
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
    parser.add_argument(
        "--codex-home",
        type=Path,
        help="Override CODEX_HOME; must match the persisted source session home.",
    )
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--evidence-mode",
        choices=["full", "packet", "probe-packet"],
        default="full",
    )
    parser.add_argument("--evidence-max-chars", type=int, default=24000)
    parser.add_argument(
        "--resume-source-session",
        action="store_true",
        help="Resume the persisted source Codex session in the isolated replay workspace.",
    )
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
    source_session_id = source_summary.get("session_id")
    if args.resume_source_session and not source_session_id:
        raise ValueError("source run does not contain a persisted session_id")
    if args.resume_source_session and source_summary.get("attempts") != 1:
        raise ValueError("session replay currently requires a one-attempt source run")
    input_token_offset = (
        int(source_summary.get("input_tokens", 0)) if args.resume_source_session else 0
    )
    source_manifest = json.loads(
        (source_root / "h1-manifest.json").read_text(encoding="utf-8")
    )
    cached_input_token_offset = (
        int(source_manifest["attempts"][0]["trace"].get("cached_input_tokens", 0))
        if args.resume_source_session
        else 0
    )
    output_token_offset = (
        int(source_summary.get("output_tokens", 0)) if args.resume_source_session else 0
    )

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
        if args.resume_source_session:
            return build_resume_command(
                prefix=prefix,
                session_id=source_session_id,
                prompt=prompt,
                workspace=map_workspace(workspace),
                model=args.model,
                reasoning_effort=args.reasoning_effort,
            )
        return build_exec_command(
            prefix=prefix,
            prompt=prompt,
            workspace=map_workspace(workspace),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            persist_session=False,
        )

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
        evidence_mode=args.evidence_mode,
        evidence_max_chars=args.evidence_max_chars,
        input_token_offset=input_token_offset,
        cached_input_token_offset=cached_input_token_offset,
        output_token_offset=output_token_offset,
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
        "evidence_mode": args.evidence_mode,
        "session_mode": "resumed" if args.resume_source_session else "fresh",
        "source_session_id": source_session_id if args.resume_source_session else None,
        "usage_offset": {
            "input_tokens": input_token_offset,
            "cached_input_tokens": cached_input_token_offset,
            "output_tokens": output_token_offset,
        },
        "evidence_packet": (
            {
                "packet_version": result.evidence_packet.packet_version,
                "content_sha256": result.evidence_packet.content_sha256,
                "total_chars": result.evidence_packet.total_chars,
            }
            if result.evidence_packet is not None
            else None
        ),
        "deterministic_probe": (
            result.deterministic_probe.as_dict()
            if result.deterministic_probe is not None
            else None
        ),
        "risk_decision": result.risk_decision.as_dict(),
        "deep_verification_attempted": result.attempted,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "task_passed_before": result.grade_before.passed,
        "task_passed_after": result.grade_after.passed,
        "completion_passed_after": result.completion_after.passed,
        "input_tokens": result.input_tokens,
        "cached_input_tokens": result.cached_input_tokens,
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
