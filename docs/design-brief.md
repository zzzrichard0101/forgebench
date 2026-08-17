# ForgeBench Design Brief v0.1

Status: **frozen for Phase 1**  
Date: 2026-08-16

> Phase 1 history remains frozen. The post-baseline research priority and scale
> target are amended by [ADR 0003](adr/0003-adaptive-verification-focus.md):
> adaptive verification is now primary, while meta-harness search and a 50-task
> benchmark are stretch scope.

## 1. Problem

Modern coding agents can write plausible code but often fail on long-horizon work in less visible ways: they stop after partial progress, forget constraints, misuse tools, fail to recover from errors, or declare success without checking the repository state.

A product demo does not reveal these failures reliably. ForgeBench therefore combines:

- a small but auditable agent harness;
- repository-scoped, automatically graded tasks;
- complete execution traces and replay metadata;
- controlled ablations of planning, memory, tool recovery, loop, and verification policies.

The goal is not to build the most feature-rich agent. The goal is to produce defensible evidence about which harness choices improve reliable task completion.

## 2. Primary user and use case

The primary user is an agent engineer who needs to compare harness variants under a fixed model, task set, and budget.

The first supported workflow is:

1. select a task split and harness manifest;
2. create an isolated workspace from a seed repository;
3. let the agent use a constrained set of engineering tools;
4. preserve every model and tool event in an append-only trace;
5. run deterministic graders outside the agent loop;
6. aggregate accuracy, completeness, robustness, efficiency, and safety metrics.

## 3. Research questions

### RQ1 — Completion

Does an explicit completion verifier reduce false completion compared with a minimal tool-use loop?

### RQ2 — Planning

When do structured planning and event-triggered replanning improve success, and when do they only add cost?

### RQ3 — Memory

Can a typed working-memory policy preserve constraints without increasing stale-memory failures?

### RQ4 — Recovery

Do timeout, retry, and stuck-detection policies improve success under injected tool failures?

### RQ5 — Generalization

Do improvements transfer to held-out tasks and a second model under the same execution contract?

### RQ6 — Meta-Harness

Can an outer loop use source, score, and prior traces to propose a harness variant that improves development-set performance without degrading the held-out set?

## 4. System boundary

Included:

- model adapters;
- planning and replanning policies;
- working-memory and context selection;
- typed repository tools;
- loop budgets, stop conditions, and recovery;
- completion verification;
- benchmark runner, graders, trace storage, and reports;
- offline meta-harness optimization.

Excluded from the first release:

- model training or fine-tuning;
- unrestricted host access;
- arbitrary web browsing by the evaluated agent;
- multi-agent orchestration as a goal in itself;
- subjective chat-quality benchmarking;
- a production-grade graphical user interface.

## 5. Initial task population

The target is 50 tasks:

| Family | Count | Representative work |
|---|---:|---|
| Development | 30 | bug fixes, small features, refactors, tests |
| Incident | 10 | logs + code diagnosis, config failures, regressions |
| Adversarial | 10 | prompt injection in files, stale hints, tool failure, forbidden paths |

Difficulty target:

| Difficulty | Count | Expected minimal-loop behavior |
|---|---:|---|
| Easy | 15 | usually solvable in a short, direct sequence |
| Medium | 20 | requires investigation and cross-file validation |
| Hard | 15 | requires replanning, recovery, or multiple constraints |

The public/dev/test split is `10/20/20`. The held-out test set is frozen after Phase 7 and is run at most twice for final reporting.

## 6. Harness variants

The baseline is intentionally small:

```text
observe → reason → call one tool → append observation → repeat or finish
```

Planned cumulative variants:

| ID | Added component |
|---|---|
| H0 | Minimal loop |
| H1 | Structured plan + plan-state tracking |
| H2 | Event-triggered replanning |
| H3 | Independent completion verification |
| H4 | Typed working memory + context selection |
| H5 | Tool timeout/retry + stuck detection |
| H6 | Development-set-selected meta-harness candidate |

Cumulative results will be accompanied by isolated ablations where budget permits.

## 7. Evidence contract

Each run must preserve:

- task ID and immutable task content hash;
- seed-repository revision or content hash;
- model provider, exact model identifier, and inference parameters;
- harness version and full configuration hash;
- system prompt and tool schemas;
- timestamps, token usage, cost estimate, and wall time;
- every model message and tool request/result;
- final workspace diff;
- grader commands, raw output, and final score;
- termination reason and failure labels.

A report without this chain is exploratory and cannot be presented as a final portfolio result.

## 8. Safety boundary

The evaluated agent operates only inside a per-run workspace. Tools resolve and validate target paths before execution. Network access is disabled by default. Secrets are not mounted. Destructive or privilege-changing commands are rejected. Graders run after the agent stops and are not visible to the agent unless a task explicitly exposes public tests.

Adversarial tasks check whether the agent follows untrusted instructions embedded in repository files. Safety failures are reported separately from task correctness and are never averaged away.

## 9. Success criteria for the project

The portfolio project is successful if it produces:

1. a reproducible baseline across at least 30 tasks;
2. a frozen 50-task benchmark with audited graders;
3. at least four controlled harness ablations;
4. a trace-based failure analysis with concrete examples;
5. a held-out comparison and one second-model transfer check;
6. an honest production-readiness report covering cost, latency, recovery, and safety;
7. a five-minute demo and an English executive summary.

The project does not require a positive result for every component. Null or negative results remain valid when the protocol is preserved.

## 10. Phase 1 decisions

The following decisions are frozen until the first baseline is complete:

- Python is the implementation language for runner and graders.
- SQLite plus JSONL is the initial metadata/trace storage.
- Deterministic graders define task success whenever possible.
- The agent cannot read hidden grader files.
- Test tasks are not tuned individually.
- Model and budget changes cannot be attributed to harness improvements.
- A task run is never silently discarded; exclusions require a recorded reason.

Changes require a dated architecture decision record and invalidate comparisons when they alter the evaluation contract.
