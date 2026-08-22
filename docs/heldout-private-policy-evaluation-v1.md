# Held-out Private Policy Evaluation v1

Date: 2026-08-22  
Status: **complete negative result; primary novelty claim rejected**

## Result

The external evaluator validated 30 sealed base outcomes and 120 model-policy
outcomes against the frozen 150-target request. All 30 public-gate-passing base
trajectories failed their hidden grader. No model-backed replay converted any
of those failures into a hidden success.

| Policy | Hidden success | Accepted false completion | Model calls | Probe calls | Input tokens | Hard-safety violation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Accept-All | 0/30 | 30/30 | 0 | 0 | 0 | 0 |
| Verify-All | 0/30 | 29/30 | 30 | 0 | 1,690,849 | 1 |
| Random-k call-matched | 0/30 | 30/30 | 9 | 0 | 348,434 | 0 |
| Probe-All | 0/30 | 30/30 | 0 | 30 | 0 | 0 |
| Risk-Model direct | 0/30 | 30/30 | 9 | 0 | 474,452 | 0 |
| Risk-Hierarchical | 0/30 | 30/30 | 9 | 9 | 504,339 | 0 |

Every policy's task-cluster bootstrap 95% interval for hidden success is
`[0.0, 0.0]`. Each of the ten task clusters scored 0/3 under every policy; the
machine report retains those task-level aggregates without publishing any
individual trajectory row.

Verify-All's lower accepted-false-completion count is not a repair. One replay
modified a protected contract, failed the visible completion gate, and received
a hard-safety violation, while still failing the hidden grader. It therefore
changed one false completion from “accepted” to visibly invalid.

## Risk and intervention

The frozen risk gate escalated 9 of the 30 actual hidden failures:

- precision: `1.0`, because the population contains no hidden successes;
- recall: `0.30`, task-cluster bootstrap 95% CI `[0.0, 0.6]`;
- false-negative rate: `0.70`;
- repair success after escalation: `0/9`.

AUROC, average precision comparison, specificity, and false-positive rate are
undefined because the base population has only one hidden class. Risk routing
identified a subset of failures but the verification action repaired none.

Random-k, Risk-Model direct, and Risk-Hierarchical escalated the same nine
bases. Their independent model calls all failed. The nine hierarchical probes
were unsupported, so P5 had neither an allocation distinction nor a probe
short-circuit advantage in this population.

## Frozen claim gate

| Criterion | Result |
| --- | --- |
| P5 reduces accepted false completion versus P0 by at least one task equivalent | Fail: reduction `0` |
| P5 recovers at least one task equivalent more than P2 at matched calls | Fail: delta `0` |
| P5 cuts Verify-All compute by at least 20% at comparable reliability | Technical pass: `70.17%` fewer input tokens, but both have `0%` reliability |
| P5 gain is not explained by Probe-All | Fail: neither policy has a hidden success |
| No P5 hard-safety regression versus P0 | Pass: both have `0` |

The primary claim requires every criterion, so it is not eligible. The compute
subgate is vacuous: equal zero reliability is not useful reliability, and both
Accept-All and Probe-All dominate every model-backed policy on the observed
reliability-cost plane.

## Statistical and privacy boundary

The task cluster is the independent unit. Confidence intervals use 20,000
cluster-bootstrap samples with frozen seed 1729. Paired trajectory tables and
exact two-sided sign/McNemar calculations are retained as descriptive checks;
repetitions within one task are not treated as independent evidence.

The public machine report contains policy totals and three-repetition task
aggregates only. It binds external result hash
`sha256:42b6bbc576c8aa61a98d44e1cfe69446751b87eb56d8f1032c8d5f2232cc6d2f`.
The private result, grader, sealed labels, known-good artifacts, and individual
trajectory outcomes remain outside Git.

## Portfolio conclusion

ForgeBench does not demonstrate a held-out reliability advantage for selective
verification v1. Its defensible contribution is narrower: a leakage-controlled,
shared-base harness laboratory that makes routing degeneracy, unsupported
probes, ineffective test-time compute, safety regressions, cost, and failed
claims auditable instead of hiding them behind public completion.

A new reliability claim would require a new versioned intervention designed
from development data and a new untouched held-out set. The current held-out
result must not be rerun or tuned into a success claim.
