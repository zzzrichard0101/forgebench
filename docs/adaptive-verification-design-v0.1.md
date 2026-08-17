# Adaptive Verification Design v0.1

Date: 2026-08-17  
Status: **pre-implementation design; freeze before held-out evaluation**

## 1. Why this is the next step

Broad harness benchmarking and automatic harness evolution are now established
research directions. Harness-Bench evaluates 106 sandboxed tasks and 5,194
trajectories; Agentic Harness Engineering and Meta-Harness optimize harness
components or code in an outer loop. ForgeBench should not claim novelty merely
from comparing planning, recovery, or context policies.

ForgeBench has a narrower empirical starting point. H1a-lite reduced input
tokens by 20.3% and wall time by 25.7% versus H1a, but one run passed the public
completion policy and failed its hidden contract. This creates a concrete
reliability-cost question rather than another general harness leaderboard.

Relevant research:

- [Harness-Bench](https://arxiv.org/abs/2605.27922)
- [Agentic Harness Engineering](https://arxiv.org/abs/2604.25850)
- [Meta-Harness](https://arxiv.org/abs/2603.28052)
- [Code as Agent Harness](https://arxiv.org/abs/2605.18747)
- [One Recipe, Many Harnesses](https://arxiv.org/abs/2608.10178)
- [VerifiAgent](https://arxiv.org/abs/2504.00406)
- [FACTOR](https://arxiv.org/abs/2606.22474)
- [The Verification Horizon](https://arxiv.org/abs/2606.26300)

Adaptive verification itself is not a new general idea: prior work allocates
verification by reasoning type, uncertainty, or factual-claim risk. The scoped
contribution here is different: traceable, predeclared escalation for coding
agent completion under a public-evidence/hidden-contract gap. The project must
not market the generic phrase "adaptive verification" as algorithmic novelty.

## 2. Operational definition

ForgeBench uses **accepted false completion** for a run where:

1. the agent terminates normally;
2. the harness-visible completion policy accepts the artifact; and
3. the independent hidden grader fails at least one required invariant.

This definition does not assume access to private model reasoning. The evidence
comes from termination state, completion-policy output, artifact state, and
hidden-grader output.

## 3. Research question

> Without running expensive verification on every task, can a predeclared risk
> gate selectively escalate uncertain completions and approach H1a reliability
> at a cost closer to H1a-lite?

The first experiment tests a rule-based policy. A learned classifier is not
needed until there is enough development data to justify one.

## 4. Candidate policies

| Policy | Execution | Purpose |
|---|---|---|
| H0 | Minimal loop | Low-cost baseline |
| H1a | Structured planning and stronger verification | Reliability reference |
| H1a-lite | Bounded planning and public completion checks | Efficiency reference |
| H1a-adaptive | H1a-lite + risk gate + selective deep verification | Proposed policy |

```text
Task -> H1a-lite -> public completion checks -> Completion Risk Gate
                                                  | low risk  -> finish
                                                  | high risk -> deep verification
                                                               -> repair or finish
```

## 5. Risk signals available before hidden grading

Version 0.1 may use only deterministic, traceable rules:

- the requested behavior introduces or changes an input-domain boundary;
- public checks exercise only successful or positive paths;
- changed behavior has more supported input categories than the checks cover;
- the implementation adds dispatch, plugin, parser, path, schema, permission,
  or fallback logic without a corresponding negative test;
- the agent records an assumption that is not resolved by repository evidence;
- changed production branches have no matching executed verification evidence;
- a protected-evidence or tool-recovery event makes the final evidence stale.

Each firing rule records its ID, evidence references, score contribution, and
the resulting decision. No rule may name a held-out task or encode its hidden
expected answer.

## 6. Selective escalation actions

The first implementation keeps escalation bounded and auditable:

1. generate or identify one negative/boundary case for each fired risk family;
2. execute the focused check in the isolated workspace;
3. if it fails, allow one bounded repair pass and rerun the focused and public
   checks;
4. refuse completion if evidence remains missing or stale.

Deep verification cannot read hidden grader files. It derives checks from the
task statement, public repository interfaces, the diff, and execution trace.

## 7. Outcome matrix and metrics

| Completion decision | Hidden grader | Outcome |
|---|---|---|
| Accept | Pass | `true_success` |
| Accept | Fail | `accepted_false_completion` |
| Reject/escalate | Fail | `detected_failure` |
| Reject/escalate | Pass | `unnecessary_escalation` candidate |

Primary metrics:

- true-success rate;
- accepted-false-completion rate;
- false-completion detection recall;
- escalation rate and unnecessary-escalation rate;
- protected-evidence violations;
- input/output tokens, wall time, model calls, and tool calls;
- successful-run and true-success cost.

An escalation is not automatically unnecessary merely because the original
artifact would have passed. It is unnecessary only when the pre-escalation
artifact passes the frozen grader and the escalation discovers no additional
declared risk evidence.

## 8. Benchmark and leakage controls

- Build at least 30 audited tasks across boundary conditions, invalid inputs,
  unsupported cases, protected evidence, incomplete verification, and hidden
  generalization.
- Treat the current ten-task suite, including `python-plugin-boundary`, as
  development evidence.
- Preserve a pre-escalation workspace snapshot so counterfactual H1a-lite
  outcomes and unnecessary escalation can be graded without reconstructing
  state after repair.
- Freeze a separate stratified held-out set before tuning thresholds.
- Freeze risk-rule IDs, weights, threshold, escalation budget, model settings,
  and grader versions before held-out execution.
- Preserve every attempted run; do not replace failures with reruns.
- Repeat stochastic comparisons where the token budget permits and report raw
  paired outcomes even when confidence intervals are wide.

## 9. Acceptance gate

H1a-adaptive advances only if the predeclared held-out comparison shows:

1. fewer accepted false completions than H1a-lite;
2. no hard-safety regression;
3. true success statistically and practically compatible with H1a; and
4. aggregate input tokens and wall time materially below H1a.

Exact tolerances will be declared after the development set is complete and
before the held-out set is run. Until then, no result is described as proving
the policy generally works.

## 10. Scope boundary

The portfolio novelty claim is not a new universal verification algorithm. It
is a reproducible engineering contribution: an explicit completion-risk policy,
traceable escalation decisions, a benchmark designed to expose false
completion, and an honest reliability-cost evaluation under hidden feedback.
