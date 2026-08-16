# ForgeBench

ForgeBench is a reproducible benchmark and harness laboratory for long-horizon coding and engineering agents.

The project asks one practical question:

> Which harness components make an agent more likely to finish a complex task correctly, rather than merely report partial progress?

## Current status

**Phase 4/10 in progress — benchmark and failure taxonomy expansion**

- [Design brief](docs/design-brief.md)
- [Metrics and evaluation contract](docs/metrics.md)
- [Task authoring specification](docs/task-schema.md)
- [Candidate skill-gap matrix](docs/skill-gap-matrix.md)
- [Dataset card](benchmark/dataset-card.md)
- [Failure taxonomy and labeling guide](docs/failure-taxonomy.md)
- [Machine-readable task schema](benchmark/schema/task.schema.json)
- [Benchmark snapshot manifest](benchmark/manifest.json)
- [Example benchmark task](benchmark/examples/python-bugfix/task.json)

Phase 2 infrastructure is now present in `src/forgebench`: copy-isolated run
workspaces, a typed tool gateway, a provider-neutral model adapter, and
append-only JSONL traces. It is validated with five end-to-end smoke scenarios.

The first executable benchmark fixture, hidden deterministic grader, and Codex
CLI reference runner are present. The first valid run passed all 7 checks, but
exceeded its input-token budget; both facts are reported instead of collapsing
them into one success number. See [Baseline Report v0](docs/baseline-report-v0.md)
for the result, limitations, and next experiment.

The first complete H0 suite finished 10/10 runs without infrastructure failure.
After grader audit, Codex passed 8/10 tasks: development 5/5, incident 1/3, and
adversarial 2/2. Two incident runs made correct diagnoses but violated explicit
protected-evidence constraints. No run met its input-token budget. See
[Multi-task Baseline v0.3](docs/multitask-baseline-v0.3.md).

The first H1 targeted ablation added a structured plan, immutable constraints,
deterministic completion checks, and a bounded repair pass. It converted both
protected-evidence H0 failures into passes, but increased input tokens by 52.9%
and wall time by 29.8%. See [H1 Ablation v0.1](docs/ablation-report-h1-v0.1.md).

## Local verification

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/validate_task.py benchmark/examples/python-bugfix/task.json
python scripts/run_codex_baseline.py --list-tasks
python scripts/run_codex_baseline.py --task-id python-config-precedence --execution-host wsl
python scripts/run_codex_suite.py --dry-run --repetitions 3
python scripts/run_codex_h1.py --task-id checkout-retry-incident --execution-host wsl
```

The baseline runner uses Codex, not Claude. Raw run artifacts and pinned local
tool binaries stay untracked; the public report contains only sanitized,
reproducible summary data.

The current audited snapshot has ten executable tasks spanning development,
incident, and adversarial families. Every seed is known-bad, every new task has
a known-good outcome, protected-file mutations are detected, and grader results
are stable across three repeated executions. This is an expansion checkpoint,
not yet the planned 30-task development benchmark.

The Codex runner now selects any task by ID from the benchmark manifest and
emits a normalized trace summary plus separate functional, token-budget, and
time-budget outcomes. A second end-to-end smoke run passed the configuration
task but exceeded its token budget; see the
[catalog smoke report](docs/catalog-smoke-report-v0.1.md).

The crash-resilient suite runner executes selected tasks and repetitions
sequentially, persists results after every run, and aggregates functional
success, infrastructure failures, budget qualification, tokens, and wall time.
Large model runs are never triggered by tests; `--dry-run` previews the exact
execution matrix first. See the [suite smoke report](docs/suite-smoke-report-v0.2.md)
for the first persisted execution.

## Planned evaluation sequence

1. Freeze task format, metrics, and data split rules.
2. Build an isolated runner and append-only trace format.
3. Measure a minimal-loop baseline.
4. Add one harness component at a time.
5. Evaluate on a frozen held-out set and a second model.

## Reproducibility principle

Every reported number must resolve to:

```text
report row → run manifest → agent trace → workspace diff → grader output
```

## Scope

ForgeBench evaluates repository-scoped engineering work such as bug fixing, feature implementation, incident triage, and adversarial reliability tasks. It does not attempt to train or fine-tune a foundation model.

## Roadmap

See [PORTFOLIO_PLAN.md](PORTFOLIO_PLAN.md) for the ten-week portfolio plan.
