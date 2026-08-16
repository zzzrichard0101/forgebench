"""Plan or run a token-capped paired H0 versus planning experiment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog
from forgebench.experiment import estimate_input_tokens, paired_plan


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "benchmark" / "manifest.json"
H0_REPORT = ROOT / "experiments" / "reports" / "multitask-baseline-v0.3.json"
H1_REPORT = ROOT / "experiments" / "reports" / "ablation-planning-full-v0.3.json"
RUNNERS = {
    "h0": ROOT / "scripts" / "run_codex_baseline.py",
    "planning": ROOT / "scripts" / "run_codex_h1.py",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", action="append", dest="task_ids")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--start-repetition", type=int, default=2)
    parser.add_argument("--estimate-margin", type=float, default=1.25)
    parser.add_argument("--max-estimated-input-tokens", type=int, default=1_000_000)
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if args.max_estimated_input_tokens < 1:
        parser.error("--max-estimated-input-tokens must be positive")

    catalog = BenchmarkCatalog(ROOT, CATALOG_PATH)
    task_ids = args.task_ids or [bundle.task["id"] for bundle in catalog.list()]
    for task_id in task_ids:
        catalog.get(task_id)

    try:
        plan = paired_plan(task_ids, args.repetitions, args.start_repetition)
        reference = _reference_tokens(H0_REPORT, H1_REPORT)
        estimate = estimate_input_tokens(plan, reference, args.estimate_margin)
    except (ValueError, KeyError) as error:
        parser.error(str(error))

    preview = {
        "mode": "execute" if args.execute else "dry-run",
        "planned_runs": len(plan),
        "planned_pairs": len(plan) // 2,
        "estimate_margin": args.estimate_margin,
        "estimated_input_tokens": estimate,
        "max_estimated_input_tokens": args.max_estimated_input_tokens,
        "within_cap": estimate <= args.max_estimated_input_tokens,
        "plan": plan,
    }
    if not args.execute:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0 if preview["within_cap"] else 2
    if estimate > args.max_estimated_input_tokens:
        parser.error(
            f"estimated input tokens {estimate} exceed cap "
            f"{args.max_estimated_input_tokens}; reduce scope or raise the explicit cap"
        )

    experiment_id = uuid.uuid4().hex
    output_root = args.runs_root / "paired"
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / f"{experiment_id}.json"
    ledger = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        **preview,
        "results": [],
        "observed_input_tokens": 0,
        "status": "running",
    }
    _write(output_path, ledger)

    for item in plan:
        if ledger["observed_input_tokens"] >= args.max_estimated_input_tokens:
            ledger["status"] = "stopped_observed_cap"
            break
        command = [
            sys.executable,
            str(RUNNERS[item["harness"]]),
            "--task-id",
            item["task_id"],
            "--execution-host",
            args.execution_host,
            "--model",
            args.model,
            "--reasoning-effort",
            args.reasoning_effort,
            "--runs-root",
            str(args.runs_root),
        ]
        if item["harness"] == "planning":
            command.extend(["--profile", "planning"])
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, shell=False, check=False
        )
        try:
            result = json.loads(completed.stdout)
            result["status"] = "completed"
            ledger["observed_input_tokens"] += _input_tokens(result)
        except json.JSONDecodeError:
            result = {
                "status": "infrastructure_failure",
                "exit_code": completed.returncode,
                "stderr": completed.stderr[-4000:],
            }
        result.update(item)
        ledger["results"].append(result)
        _write(output_path, ledger)
    else:
        ledger["status"] = "completed"

    ledger["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write(output_path, ledger)
    print(
        json.dumps(
            {
                "experiment_path": str(output_path),
                "status": ledger["status"],
                "completed_runs": len(ledger["results"]),
                "observed_input_tokens": ledger["observed_input_tokens"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ledger["status"] == "completed" else 2


def _reference_tokens(h0_path: Path, h1_path: Path) -> dict[tuple[str, str], int]:
    h0 = json.loads(h0_path.read_text(encoding="utf-8"))
    h1 = json.loads(h1_path.read_text(encoding="utf-8"))
    reference = {
        (run["task_id"], "h0"): int(run["input_tokens"])
        for run in h0["runs"]
    }
    reference.update(
        {
            (run["task_id"], "planning"): int(run["input_tokens"])
            for run in h1["h1a_planning"]["runs"]
        }
    )
    return reference


def _input_tokens(result: dict) -> int:
    if "input_tokens" in result:
        return int(result["input_tokens"])
    return int(result.get("trace", {}).get("input_tokens", 0))


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
