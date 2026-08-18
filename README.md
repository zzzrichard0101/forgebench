# ForgeBench

ForgeBench is a reproducible benchmark and harness laboratory for long-horizon coding and engineering agents.

The project asks one practical question:

> Which harness components make an agent more likely to finish a complex task correctly, rather than merely report partial progress?

## Current status

**Phase 8 benchmark expansion in progress — 14/20 development tasks complete**

- [Design brief](docs/design-brief.md)
- [Metrics and evaluation contract](docs/metrics.md)
- [Task authoring specification](docs/task-schema.md)
- [Candidate skill-gap matrix](docs/skill-gap-matrix.md)
- [Dataset card](benchmark/dataset-card.md)
- [Failure taxonomy and labeling guide](docs/failure-taxonomy.md)
- [Machine-readable task schema](benchmark/schema/task.schema.json)
- [Benchmark snapshot manifest](benchmark/manifest.json)
- [Example benchmark task](benchmark/examples/python-bugfix/task.json)
- [Benchmark expansion v0.4](docs/benchmark-expansion-v0.4.md)

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
The follow-up [component split](docs/ablation-report-h1-components-v0.2.md)
showed planning-only also passed 2/2; no real run activated verifier repair, so
its incremental success benefit remains unproven.

The first full-suite planning ablation passed 10/10 tasks versus the adjudicated
H0 result of 8/10, with protected-evidence violations falling from two to zero.
Aggregate input-token overhead was 19.9% and wall-time overhead was 23.3%, but
all runs still exceeded their token budgets and only one repetition exists.
See [Full-suite Planning Ablation v0.3](docs/ablation-report-planning-full-v0.3.md).

A cost-capped paired replication then reran the two discriminating incident
tasks. H0 again failed 0/2 by mutating protected evidence, while planning passed
2/2 without mutation. The four runs consumed 849,735 input tokens against a
1,000,000-token cap. See [Paired Confirmation v0.4](docs/paired-confirmation-v0.4.md).

The first H1a-lite optimization retained 2/2 success and zero protected-file
violations while using 23.0% fewer input tokens and 18.8% less wall time than
the recent structured-planning runs on the same scope. It remains a targeted
single-repetition result. See [H1a-lite Ablation v0.5](docs/ablation-report-planning-lite-v0.5.md).

The targeted [H1a-lite replication](docs/planning-lite-replication-v0.6.md)
again passed 2/2 with no protected-file mutation. Across two lite rounds the
profile is 4/4, and mean input tokens were 18.8% below the recent H1a reference.
The next gate is one complete ten-task lite suite with no reliability regression.

That [full-suite lite evaluation](docs/planning-lite-full-suite-v0.7.md) scored
9/10. It cut input tokens by 20.3% and wall time by 25.7% versus H1a, but missed
one hidden plugin boundary despite passing public completion checks. H1a-lite
therefore remains a cost profile rather than replacing the 10/10 H1a default.

Phase 6 now has explicit [context and recovery policies](docs/context-recovery-design-v0.1.md):
failed observations are prioritized inside a bounded context window, transient
timeouts receive at most one capped retry, deterministic failures are not
retried, and every compaction or recovery decision is trace-visible.

The first [H2 fault-injection report](docs/fault-injection-report-h2-v0.1.md)
passed its deterministic mechanism gate: transient recovery improved from 0/3
to 3/3, deterministic failures triggered zero retries, and decisive failure
evidence was retained while context text fell from 40,105 to 12,000 characters.
This is harness evidence, not yet a model-quality benchmark claim.

The first [model-backed recovery smoke](docs/model-backed-recovery-smoke-v0.1.md)
then placed Codex behind the typed tool loop. Both control and H2 produced the
correct artifact, while H2's same-step timeout recovery reduced model calls
from four to three, input tokens by 26.2%, and wall time by 25.2%. This is one
paired synthetic smoke run, not a general performance claim.

The next primary question is now [adaptive verification](docs/adaptive-verification-design-v0.1.md).
H1a-lite exposed one accepted false completion: public completion evidence
passed while a hidden plugin boundary failed. ForgeBench will compare a
predeclared `H1a-adaptive` risk gate against H0, H1a, and H1a-lite, escalating
only completion attempts with trace-visible risk signals. The observed failure
is development evidence and cannot count as held-out proof. This change is
recorded in [ADR 0003](docs/adr/0003-adaptive-verification-focus.md).

The first [Completion Risk Gate shadow screen](docs/completion-risk-shadow-v0.1.md)
now records deterministic rule IDs, weights, evidence, and escalation decisions
without changing execution. On the ten development tasks it marked 2/10 high
risk: the known plugin false completion and one previously successful archive
boundary task. This is a leakage-controlled routing plausibility check, not a
held-out accuracy result.

The first [adaptive development replay](docs/adaptive-replay-report-v0.2.md)
then routed the known plugin false completion to one Codex deep-verification
pass and routed a passing archive task directly to finish. The plugin changed
from hidden fail to pass; the archive stayed passing with zero additional model
tokens. However, the extra ephemeral process pushed two-task aggregate input
16.2% above the historical H1a reference. The mechanism gate passed, but a
general reliability-cost claim has not.

The follow-up [Evidence Packet v0.2 evaluation](docs/adaptive-evidence-packet-v0.2.md)
reduced the focused verification input from 97,108 to 64,921 tokens (-33.1%)
while preserving the plugin repair. A recorded v0.1 packet saved tokens but
misinterpreted the missing file-type dimension and failed; v0.2 requires a
minimum probe set per dimension. End-to-end input on the two development tasks
is still 7.8% above the historical H1a reference, so the main cost target remains
open.

The next optimization, [Adaptive Session Reuse v0.1](docs/adaptive-session-reuse-report-v0.1.md),
resumed the source agent inside a copied workspace and repaired the hidden
failure, but failed its total-input efficiency gate: the adaptive increment was
94,539 tokens versus 64,921 for a fresh packet process (+45.6%). Uncached input
fell 12.8% and output fell 8.4%, but no price-weighted cost claim is made. Fresh
Evidence Packet v0.2 remains the reference path; session reuse stays an
experimental mode.

The [Probe-First result](docs/adaptive-probe-first-report-v0.1.md) adds a
public-contract adapter before adaptive repair. In the first predeclared
development replay, the adapter exposed the omitted non-Python-file case before
the model call and one fresh Codex turn repaired it. Total input fell from 64,921
to 47,847 tokens (26.3%) and duration fell from 47.224s to 39.863s (15.6%) versus
the fresh Evidence Packet reference. Uncached input rose from 8,601 to 12,775,
so this is a total-context and latency result, not a price-weighted cost claim.
The deterministic correct-workspace test also verifies the zero-model-token
short-circuit. This remains development evidence, not a held-out benchmark.

The next-stage [Selective Verification Research Protocol v1](docs/selective-verification-research-protocol-v1.md)
now defines the paper-level test: reuse identical frozen base completions and
compare Accept-All, Verify-All, Random-k, Probe-All, direct risk routing, and the
hierarchical risk policy. The primary novelty claim is gated on a held-out
reliability-cost advantage, not on false completion or probing alone.

The first [shared base-completion runner](docs/base-completion-policy-runner-v1.md)
now seals one public-gate-passing artifact and replays each policy from an
identical hash-checked copy. Public records and hidden labels are stored
separately. A real development smoke confirmed that Accept-All and Probe-All
shared the same known false completion while only Probe-All exposed the missing
non-Python boundary at zero model tokens.

The [multi-base assignment manifest](docs/multi-base-assignment-manifest-v1.md)
now freezes public-only routing across a base collection. Random-k receives the
same number of model calls as Risk-Hierarchical within each task-family stratum,
using a deterministic seed-derived rank. Each replay validates the manifest
hash, task version, base hash, and expected probe/model routing.

## Local verification

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/validate_task.py benchmark/examples/python-bugfix/task.json
python scripts/run_codex_baseline.py --list-tasks
python scripts/run_codex_baseline.py --task-id python-config-precedence --execution-host wsl
python scripts/run_codex_suite.py --dry-run --repetitions 3
python scripts/run_codex_suite.py --harness planning --repetitions 1
python scripts/run_codex_h1.py --task-id checkout-retry-incident --execution-host wsl
python scripts/run_codex_h1.py --task-id checkout-retry-incident --profile planning --execution-host wsl
python scripts/run_codex_h1.py --task-id checkout-retry-incident --profile planning-lite --execution-host wsl
python scripts/run_codex_h1.py --task-id python-plugin-boundary --profile planning-lite --risk-shadow --execution-host wsl
python scripts/run_codex_h1.py --task-id python-plugin-boundary --profile planning-lite --risk-shadow --persist-session --execution-host wsl
python scripts/run_paired_codex_experiment.py --task-id checkout-retry-incident --task-id worker-visibility-incident
python scripts/run_fault_injection.py
python scripts/run_model_recovery_smoke.py --execution-host wsl
python scripts/run_adaptive_replay.py --task-id python-plugin-boundary --source-run-id <planning-lite-run-id> --execution-host wsl
python scripts/run_adaptive_replay.py --task-id python-plugin-boundary --source-run-id <planning-lite-run-id> --evidence-mode packet --execution-host wsl
python scripts/run_adaptive_replay.py --task-id python-plugin-boundary --source-run-id <persisted-planning-lite-run-id> --evidence-mode packet --resume-source-session --execution-host wsl
python scripts/run_adaptive_replay.py --task-id python-plugin-boundary --source-run-id <planning-lite-run-id> --evidence-mode probe-packet --execution-host wsl
python scripts/seal_base_completion.py --task-id python-plugin-boundary --source-run-id <planning-lite-run-id> --base-id <base-id>
python scripts/run_policy_replay.py --task-id python-plugin-boundary --base-id <base-id> --policy probe_all
python scripts/plan_policy_comparison.py --entry python-plugin-boundary=<base-id> --manifest-id <manifest-id> --random-seed 1729
```

Both persisted-session commands must use the same `--codex-home` when session
storage is isolated from the default Codex home.

The paired experiment command is a dry-run by default. It counterbalances H0
and planning order, estimates input-token use from published runs with a 25%
safety margin, and requires `--execute` plus an explicit cap-compliant plan
before it starts model calls.

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
4. Build and freeze an adaptive completion-risk policy on development tasks.
5. Compare H0, H1a, H1a-lite, and H1a-adaptive on a frozen held-out set.
6. Check whether the result transfers to a second model.

## Reproducibility principle

Every reported number must resolve to:

```text
report row → run manifest → agent trace → workspace diff → grader output
```

## Scope

ForgeBench evaluates repository-scoped engineering work such as bug fixing, feature implementation, incident triage, and adversarial reliability tasks. It does not attempt to train or fine-tune a foundation model.

## Roadmap

See [PORTFOLIO_PLAN.md](PORTFOLIO_PLAN.md) for the ten-week portfolio plan.
