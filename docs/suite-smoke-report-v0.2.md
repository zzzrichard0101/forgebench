# Suite Smoke Report v0.2

Date: 2026-08-16

Status: **10-task catalog audited; suite execution path validated**

## Catalog checkpoint

The development snapshot now contains 10 executable tasks: five development,
three incident, and two adversarial tasks. All task documents and seed hashes
validate. The audit confirms known-bad seeds, known-good outcomes for every dev
task, protected-file mutation detection, and stable grading across three runs.

## Suite smoke result

The crash-resilient suite runner executed one newly added task,
`python-rate-window`, using Codex `gpt-5.6-sol` at medium reasoning.

| Metric | Result |
|---|---:|
| Attempted / completed | 1 / 1 |
| Infrastructure failures | 0 |
| Functional passes | 1 |
| Wall time | 53.009 seconds |
| Input / output tokens | 149,255 / 1,520 |
| Input-token budget | 50,000 |
| Token-budget compliant | no |

The runner persisted its suite ledger before execution and after every result,
then aggregated functional outcome, infrastructure status, budget qualification,
tokens, and duration. Raw artifacts remain untracked; the sanitized result is
stored in `experiments/reports/suite-smoke-v0.2.json`.

## Interpretation

This validates orchestration, not model quality. Three different small Codex
tasks have now passed functionally while exceeding their input-token budgets.
The repeated observation motivates a controlled context/loop efficiency
experiment. It is not yet a statistical comparison because repetitions and the
full catalog have not been run.
