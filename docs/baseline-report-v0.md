# Baseline Report v0 — Codex CLI

Date: 2026-08-16

Status: **First valid Codex baseline complete**

Sample size: **n = 1**

## Result

Codex fixed the `python-cart-rounding` task and passed every deterministic
grader check. The run is a valid harness sample, but it is **not budget
compliant** because reported input tokens exceeded the task budget.

| Field | Value |
|---|---:|
| Run ID | `0c487e4b25b7447a87bc10d457f2c15c` |
| Codex CLI | `0.147.0` |
| Model | `gpt-5.6-sol` |
| Reasoning effort | `medium` |
| Host / sandbox | WSL2 Ubuntu / `workspace-write` |
| Approximate wall time | 111 seconds |
| Agent exit | 0, no timeout |
| Public tests | 3 / 3 passed |
| Hidden tests | 3 / 3 passed |
| Policy checks | 1 / 1 passed |
| Commands | 8 total: 7 completed, 1 failed then recovered |
| Input tokens | 268,222 (233,216 cached) |
| Output tokens | 3,732 (955 reasoning) |

The failed command exposed Python 3.8 incompatibility with built-in generic
annotations. Codex diagnosed it, added `from __future__ import annotations`,
reran the checks, and completed successfully. The actual defect was fixed by
summing the already rounded line totals, with a regression test covering the
one-cent discrepancy. No third-party dependency was added.

## Budget interpretation

The task budget allows 60,000 input tokens. The CLI reported 268,222 input
tokens, or about 4.47 times the limit. A passing grade therefore means
**functionally correct**, not **efficiently solved**. Future aggregate reports
must publish both raw task success and budget-qualified success.

The unusually high context volume for a tiny repository is now a primary
optimization target. Repeated shell inspection and large cached context suggest
that prompt/context minimization and tighter loop termination should be tested
before scaling the benchmark.

## Harness findings

1. The native Windows Codex sandbox behaved effectively read-only in child
   execution. WSL2 provided a working `workspace-write` boundary without
   disabling the sandbox.
2. The run workspace inherited the enclosing portfolio repository as its Git
   root. The runner now initializes an independent Git baseline inside every
   external-agent workspace to prevent future parent-repository visibility.
3. The agent ran with Python 3.8 in WSL while the deterministic grader used
   Python 3.12 on Windows. The mismatch usefully exposed compatibility handling,
   but runtime versions must be captured explicitly in later reports.
4. The original manifest lacked end-state timing. The runner now records UTC
   start/end times, duration, exit status, timeout status, metric eligibility,
   and grader outcome.

## Reproduction protocol

The runner uses the official non-interactive `codex exec` interface with JSONL
events, an ephemeral session, fixed model and reasoning effort, approval policy
`never`, and the `workspace-write` sandbox. Network search is not enabled and
the sandbox is not bypassed. The ignored `.tools` directory pins the CLI binary;
credentials and raw run artifacts are not committed.

```powershell
$env:PYTHONPATH = "src"
python scripts/run_codex_baseline.py --execution-host wsl
```

See the [official Codex CLI command documentation](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
for the command semantics used by this runner.

## Limits and next experiment

One easy task cannot support a claim about general agent capability. Week 4
should add multiple task families, enforce token budgets in metric eligibility,
capture runtime metadata, and compare at least two harness configurations with
repeated trials.
