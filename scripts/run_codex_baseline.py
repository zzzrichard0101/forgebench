"""Run one explicitly requested Codex CLI reference baseline.

The runner uses a pinned local npm installation when the Windows Store app
binary is not executable from a child process. It never bypasses the Codex
sandbox and does not enable network search.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog
from forgebench.codex_trace import summarize_codex_trace
from forgebench.external_agent import ExternalAgentRunner
from forgebench.grader import DeterministicGrader


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "benchmark" / "manifest.json"
GRADERS = ROOT / "benchmark" / "graders"
PINNED_CODEX_VERSION = "0.147.0"


def find_local_codex() -> Path:
    """Locate the pinned native binary installed under the ignored .tools dir."""

    architecture = "win32-x64" if platform.machine().lower() in {"amd64", "x86_64"} else "win32-arm64"
    pattern = (
        f"node_modules/.pnpm/@openai+codex@*-{architecture}/node_modules/"
        "@openai/codex/vendor/*/bin/codex.exe"
    )
    matches = sorted((ROOT / ".tools" / "codex").glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(
            "Pinned Codex CLI not found. Run: "
            "New-Item -ItemType Directory -Path .tools\\codex -Force; "
            "pnpm add --dir .tools/codex @openai/codex@0.147.0 --save-exact"
        )
    return matches[0].resolve()


def find_local_linux_codex() -> Path:
    pattern = (
        "node_modules/.pnpm/@openai+codex@*-linux-x64/node_modules/"
        "@openai/codex/vendor/x86_64-unknown-linux-musl/bin/codex"
    )
    matches = sorted((ROOT / ".tools" / "codex-linux").glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(
            "Pinned Linux Codex CLI not found. Run: "
            "New-Item -ItemType Directory -Path .tools\\codex-linux -Force; "
            "pnpm add --dir .tools/codex-linux "
            "'@openai/codex-linux-x64@npm:@openai/codex@0.147.0-linux-x64' --save-exact"
        )
    return matches[0].resolve()


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{tail}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--task-id", default="python-cart-rounding")
    parser.add_argument("--list-tasks", action="store_true")
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout-seconds", type=int)
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, MANIFEST_PATH)
    if args.list_tasks:
        for bundle in catalog.list():
            task = bundle.task
            print(
                f"{task['id']}\t{task['family']}\t{task['difficulty']}\t{task['split']}"
            )
        return 0
    bundle = catalog.get(args.task_id)
    task = bundle.task
    timeout_seconds = args.timeout_seconds or task["budgets"]["max_seconds"]
    prompt = (
        task["instruction"]
        + "\n\nWork autonomously inside this repository. Inspect the code, implement the fix, "
        "run the available tests, and verify completion before stopping. Do not access "
        "files outside the current repository and do not use the network."
    )
    execution_host = args.execution_host
    if execution_host == "auto":
        execution_host = "wsl" if platform.system() == "Windows" else "windows"

    workspace_mapper = str
    if execution_host == "wsl":
        codex = (args.codex_bin or find_local_linux_codex()).resolve(strict=True)
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        if wsl is None:
            raise FileNotFoundError("WSL executable not found")
        codex_prefix = [
            wsl,
            "-d",
            "Ubuntu",
            "--",
            "env",
            f"CODEX_HOME={windows_to_wsl(Path.home() / '.codex')}",
            windows_to_wsl(codex),
        ]
        workspace_mapper = windows_to_wsl
    else:
        codex = (args.codex_bin or find_local_codex()).resolve(strict=True)
        codex_prefix = [str(codex)]

    command = [
        *codex_prefix,
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
        "{workspace}",
        prompt,
    ]
    runner = ExternalAgentRunner(
        args.runs_root, DeterministicGrader(GRADERS)
    )
    result = runner.run(
        task=task,
        seed=bundle.seed_path,
        command=command,
        timeout_seconds=timeout_seconds,
        workspace_path_mapper=workspace_mapper,
    )
    trace_summary = summarize_codex_trace(result.raw_trace_path)
    external_manifest = json.loads(
        (result.workspace.parent / "external-manifest.json").read_text(encoding="utf-8")
    )
    token_budget_compliant = trace_summary.budget_compliant(task["budgets"])
    time_budget_compliant = (
        external_manifest["duration_seconds"] <= task["budgets"]["max_seconds"]
    )
    # A known token/time violation is enough to reject qualification. When both
    # pass, the result remains unknown until Codex exposes an enforceable step
    # count equivalent to the task contract.
    budget_qualified_success = (
        False
        if (
            not result.grade.passed
            or not token_budget_compliant
            or not time_budget_compliant
        )
        else None
    )
    summary = {
        "schema_version": 1,
        "run_id": result.run_id,
        "task_id": task["id"],
        "task_version": task["version"],
        "provider": "codex-cli",
        "cli_version": PINNED_CODEX_VERSION,
        "execution_host": execution_host,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "eligible_for_agent_metrics": result.eligible_for_agent_metrics,
        "task_passed": result.grade.passed,
        "token_budget_compliant": token_budget_compliant,
        "time_budget_compliant": time_budget_compliant,
        "step_budget_enforced": False,
        "budget_qualification_complete": False,
        "budget_qualified_success": budget_qualified_success,
        "duration_seconds": external_manifest["duration_seconds"],
        "trace": trace_summary.as_dict(),
        "run_root": str(result.workspace.parent),
    }
    (result.workspace.parent / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result.grade.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
