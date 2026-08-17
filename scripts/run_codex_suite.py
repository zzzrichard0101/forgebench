"""Run a crash-resilient sequential Codex benchmark suite."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from forgebench.catalog import BenchmarkCatalog
from forgebench.suite import aggregate_suite


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "benchmark" / "manifest.json"
H0_RUNNER = ROOT / "scripts" / "run_codex_baseline.py"
H1_RUNNER = ROOT / "scripts" / "run_codex_h1.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", action="append", dest="task_ids")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--execution-host", choices=["auto", "windows", "wsl"], default="auto")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--harness",
        choices=["h0", "planning", "planning-lite", "verification", "repair"],
        default="h0",
    )
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument(
        "--risk-shadow",
        action="store_true",
        help="Record Completion Risk Gate decisions for H1 profiles.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")
    if args.risk_shadow and args.harness == "h0":
        parser.error("--risk-shadow requires an H1 harness profile")

    catalog = BenchmarkCatalog(ROOT, CATALOG_PATH)
    task_ids = args.task_ids or [bundle.task["id"] for bundle in catalog.list()]
    for task_id in task_ids:
        catalog.get(task_id)
    planned_runs = [
        {"task_id": task_id, "repetition": repetition}
        for task_id in task_ids
        for repetition in range(1, args.repetitions + 1)
    ]
    if args.dry_run:
        print(json.dumps({"planned_runs": planned_runs}, indent=2))
        return 0

    suite_id = uuid.uuid4().hex
    suite_root = args.runs_root / "suites"
    suite_root.mkdir(parents=True, exist_ok=True)
    output_path = suite_root / f"{suite_id}.json"
    suite = {
        "schema_version": 1,
        "suite_id": suite_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "execution_host": args.execution_host,
        "harness": args.harness,
        "risk_mode": "shadow" if args.risk_shadow else "off",
        "planned_runs": planned_runs,
        "results": [],
        "summary": aggregate_suite([]),
    }
    _write(output_path, suite)

    for planned in planned_runs:
        runner = H0_RUNNER if args.harness == "h0" else H1_RUNNER
        command = [
            sys.executable,
            str(runner),
            "--task-id",
            planned["task_id"],
            "--execution-host",
            args.execution_host,
            "--model",
            args.model,
            "--reasoning-effort",
            args.reasoning_effort,
            "--runs-root",
            str(args.runs_root),
        ]
        if args.harness != "h0":
            command.extend(["--profile", args.harness])
            if args.risk_shadow:
                command.append("--risk-shadow")
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        try:
            result = json.loads(completed.stdout)
            result["status"] = "completed"
        except json.JSONDecodeError:
            result = {
                "status": "infrastructure_failure",
                "task_id": planned["task_id"],
                "exit_code": completed.returncode,
                "stderr": completed.stderr[-4000:],
            }
        result["repetition"] = planned["repetition"]
        suite["results"].append(result)
        suite["summary"] = aggregate_suite(suite["results"])
        _write(output_path, suite)

    suite["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write(output_path, suite)
    print(json.dumps({"suite_path": str(output_path), **suite["summary"]}, indent=2))
    return 0 if suite["summary"]["infrastructure_failures"] == 0 else 2


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
