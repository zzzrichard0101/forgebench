# ForgeBench

ForgeBench is a reproducible benchmark and harness laboratory for long-horizon coding and engineering agents.

The project asks one practical question:

> Which harness components make an agent more likely to finish a complex task correctly, rather than merely report partial progress?

## Current status

**Phase 3/10 — deterministic grading and baseline preparation**

- [Design brief](docs/design-brief.md)
- [Metrics and evaluation contract](docs/metrics.md)
- [Task authoring specification](docs/task-schema.md)
- [Candidate skill-gap matrix](docs/skill-gap-matrix.md)
- [Machine-readable task schema](benchmark/schema/task.schema.json)
- [Example benchmark task](benchmark/examples/python-bugfix/task.json)

Phase 2 infrastructure is now present in `src/forgebench`: copy-isolated run
workspaces, a typed tool gateway, a provider-neutral model adapter, and
append-only JSONL traces. It is validated with five end-to-end smoke scenarios.

The first executable benchmark fixture and hidden deterministic grader are also
present. See [Baseline Report v0](docs/baseline-report-v0.md) for what is and is
not yet measured.

No agent result is claimed yet. Baselines and ablations will be added only after the runner and graders are reproducible.

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
