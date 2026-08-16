"""Run one explicitly approved Claude Code reference baseline.

This script consumes the signed-in Claude subscription or configured provider.
Do not run it implicitly from tests or imports.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.external_agent import ExternalAgentRunner
from forgebench.grader import DeterministicGrader


ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = ROOT / "benchmark" / "examples" / "python-bugfix" / "task.json"
SEED = ROOT / "benchmark" / "fixtures" / "python-cart-rounding"
GRADERS = ROOT / "benchmark" / "graders"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    args = parser.parse_args()

    task = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    prompt = (
        task["instruction"]
        + "\n\nWork autonomously inside this repository. Inspect the code, implement the fix, "
        "run the available tests, and verify completion before stopping. Do not access "
        "files outside the current repository and do not use the network."
    )
    command = [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--safe-mode",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        "Read,Edit,Bash(python *)",
        "--model",
        args.model,
        prompt,
    ]
    runner = ExternalAgentRunner(
        args.runs_root, DeterministicGrader(GRADERS)
    )
    result = runner.run(
        task=task,
        seed=SEED,
        command=command,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "eligible_for_agent_metrics": result.eligible_for_agent_metrics,
                "task_passed": result.grade.passed,
                "run_root": str(result.workspace.parent),
            },
            indent=2,
        )
    )
    return 0 if result.grade.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
