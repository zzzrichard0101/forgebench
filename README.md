# ForgeBench

ForgeBench is a reproducible benchmark and harness laboratory for long-horizon coding and engineering agents.

The project asks one practical question:

> Which harness components make an agent more likely to finish a complex task correctly, rather than merely report partial progress?

## Current status

**Phase 3/10 complete — first Codex baseline measured**

- [Design brief](docs/design-brief.md)
- [Metrics and evaluation contract](docs/metrics.md)
- [Task authoring specification](docs/task-schema.md)
- [Candidate skill-gap matrix](docs/skill-gap-matrix.md)
- [Machine-readable task schema](benchmark/schema/task.schema.json)
- [Example benchmark task](benchmark/examples/python-bugfix/task.json)

Phase 2 infrastructure is now present in `src/forgebench`: copy-isolated run
workspaces, a typed tool gateway, a provider-neutral model adapter, and
append-only JSONL traces. It is validated with five end-to-end smoke scenarios.

The first executable benchmark fixture, hidden deterministic grader, and Codex
CLI reference runner are present. The first valid run passed all 7 checks, but
exceeded its input-token budget; both facts are reported instead of collapsing
them into one success number. See [Baseline Report v0](docs/baseline-report-v0.md)
for the result, limitations, and next experiment.

## Local verification

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/validate_task.py benchmark/examples/python-bugfix/task.json
python scripts/run_codex_baseline.py --execution-host wsl
```

The baseline runner uses Codex, not Claude. Raw run artifacts and pinned local
tool binaries stay untracked; the public report contains only sanitized,
reproducible summary data.

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
