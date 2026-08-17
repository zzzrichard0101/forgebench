"""Run one cost-capped, model-backed H2-off versus H2-on recovery smoke pair."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import time
import uuid
from pathlib import Path

from forgebench.codex_model import CodexCliModelAdapter
from forgebench.context_policy import BoundedContextPolicy
from forgebench.model_recovery import FirstReadTimeoutGateway, grade_recovery_workspace
from forgebench.recovery import BoundedToolRecoveryPolicy
from forgebench.runner import AgentRunner
from forgebench.tools import ToolGateway
from run_codex_baseline import (
    PINNED_CODEX_VERSION,
    ROOT,
    find_local_codex,
    find_local_linux_codex,
    windows_to_wsl,
)


DEFAULT_CONFIG = ROOT / "experiments" / "configs" / "model-recovery-smoke-v0.1.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--codex-bin", type=Path)
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))

    execution_host = args.execution_host
    if execution_host == "auto":
        execution_host = "wsl" if platform.system() == "Windows" else "windows"
    prefix, path_mapper = _codex_prefix(execution_host, args.codex_bin)

    experiment_id = uuid.uuid4().hex
    experiment_root = args.runs_root / "model-recovery" / experiment_id
    seed = experiment_root / "seed"
    controller = experiment_root / "controller"
    seed.mkdir(parents=True, exist_ok=True)
    controller.mkdir(parents=True, exist_ok=True)
    (seed / "source.json").write_text(
        json.dumps(
            {"incident_id":"recover-17","status":"ready","attempts":3},
            separators=(",", ":"),
        ) + "\n",
        encoding="utf-8",
    )

    ledger = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "config_id": config["experiment_id"],
        "cli_version": PINNED_CODEX_VERSION,
        "execution_host": execution_host,
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        "results": [],
        "status": "running",
    }
    output_path = experiment_root / "result.json"
    _write(output_path, ledger)

    for variant in ("control", "treatment"):
        if _total_input(ledger) >= int(config["max_total_input_tokens"]):
            ledger["status"] = "stopped_input_cap"
            break
        trace_root = experiment_root / "model-traces" / variant

        def command_factory(prompt: str) -> list[str]:
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
                "read-only",
                "--model",
                config["model"],
                "--config",
                f'model_reasoning_effort="{config["reasoning_effort"]}"',
                "--cd",
                path_mapper(controller),
                prompt,
            ]

        adapter = CodexCliModelAdapter(
            model_id=config["model"],
            command_factory=command_factory,
            process_cwd=ROOT,
            trace_root=trace_root,
            timeout_seconds=180,
        )
        gateways: list[FirstReadTimeoutGateway] = []

        def gateway_factory(workspace: Path) -> FirstReadTimeoutGateway:
            gateway = FirstReadTimeoutGateway(ToolGateway(workspace))
            gateways.append(gateway)
            return gateway

        runner = AgentRunner(
            experiment_root / "agent-runs" / variant,
            context_policy=(
                BoundedContextPolicy() if variant == "treatment" else None
            ),
            recovery_policy=(
                BoundedToolRecoveryPolicy(max_retries=1)
                if variant == "treatment"
                else None
            ),
            tool_gateway_factory=gateway_factory,
        )
        started = time.perf_counter()
        try:
            run = runner.run(
                seed=seed,
                task_instruction=config["task"],
                model=adapter,
                max_steps=int(config["max_model_steps"]),
            )
            grade = grade_recovery_workspace(run.workspace, seed)
            result = {
                "variant": variant,
                "status": "completed",
                "run_id": run.run_id,
                "termination_reason": run.termination_reason,
                "model_steps": run.steps,
                "gateway_calls": gateways[0].calls,
                "timeout_injected": gateways[0].injected,
                "duration_seconds": round(time.perf_counter() - started, 3),
                "grade": grade,
                "usage": adapter.usage(),
            }
        except Exception as exc:
            result = {
                "variant": variant,
                "status": "infrastructure_failure",
                "error": f"{type(exc).__name__}: {exc}",
                "duration_seconds": round(time.perf_counter() - started, 3),
                "usage": adapter.usage(),
            }
        ledger["results"].append(result)
        _write(output_path, ledger)
    else:
        ledger["status"] = "completed"

    ledger["summary"] = _summary(ledger, config)
    _write(output_path, ledger)
    print(
        json.dumps(
            {"result_path":str(output_path),"status":ledger["status"],**ledger["summary"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ledger["summary"]["smoke_acceptance_passed"] else 1


def _codex_prefix(execution_host: str, codex_bin: Path | None):
    if execution_host == "wsl":
        codex = (codex_bin or find_local_linux_codex()).resolve(strict=True)
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        if wsl is None:
            raise FileNotFoundError("WSL executable not found")
        return [
            wsl,
            "-d",
            "Ubuntu",
            "--",
            "env",
            f"CODEX_HOME={windows_to_wsl(Path.home() / '.codex')}",
            windows_to_wsl(codex),
        ], windows_to_wsl
    codex = (codex_bin or find_local_codex()).resolve(strict=True)
    return [str(codex)], str


def _total_input(ledger: dict) -> int:
    return sum(int(item["usage"]["input_tokens"]) for item in ledger["results"])


def _summary(ledger: dict, config: dict) -> dict:
    by_variant = {item["variant"]: item for item in ledger["results"]}
    control = by_variant.get("control")
    treatment = by_variant.get("treatment")
    accepted = bool(
        control
        and treatment
        and treatment["status"] == "completed"
        and treatment["grade"]["task_passed"]
        and treatment["grade"]["source_unchanged"]
        and (
            treatment["usage"]["model_calls"] <= control["usage"]["model_calls"]
            if control["status"] == "completed"
            else False
        )
    )
    return {
        "control_task_passed": (
            control.get("grade", {}).get("task_passed") if control else None
        ),
        "treatment_task_passed": (
            treatment.get("grade", {}).get("task_passed") if treatment else None
        ),
        "control_model_calls": (
            control.get("usage", {}).get("model_calls") if control else None
        ),
        "treatment_model_calls": (
            treatment.get("usage", {}).get("model_calls") if treatment else None
        ),
        "total_input_tokens": _total_input(ledger),
        "input_cap": int(config["max_total_input_tokens"]),
        "smoke_acceptance_passed": accepted,
    }


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
