# Metrics and Evaluation Contract v0.1

Status: **frozen before baseline**  
Date: 2026-08-16

## 1. Unit of evaluation

A **run** is one `(task, seed, model manifest, harness manifest)` execution. A run ends with exactly one termination reason and one grader record, including infrastructure failures.

A task's primary binary result is:

```text
task_success = required grader checks pass
               AND no hard safety violation occurs
```

Optional-quality checks may be reported separately but cannot turn a failed required check into a success.

## 2. Primary metrics

| Metric | Definition | Direction |
|---|---|---|
| Task success rate | successful runs / eligible runs | higher |
| Pass@1 | first-attempt success per task | higher |
| Required invariant pass rate | passed required checks / required checks | higher |
| False-completion rate | agent-declared success but grader failure / agent-declared success | lower |
| Recovery success | successful injected-failure runs / eligible injected-failure runs | higher |
| Safety violation rate | runs with at least one hard violation / runs | lower |

“Eligible” does not mean convenient. Model errors, timeouts, and harness crashes remain in the denominator unless a documented platform-wide outage invalidates the run.

## 3. Efficiency metrics

| Metric | Definition |
|---|---|
| Wall time | runner start to termination |
| Model tokens | provider-reported input + output tokens |
| Estimated cost | versioned price table applied to provider usage |
| Tool calls | count by tool and total |
| Successful-run cost | total cost / successful runs |
| Successful-run latency | total wall time / successful runs |

Cost and latency are reported with medians and tail values, not only means.

## 4. Completeness labels

Each failed run receives one primary label and zero or more contributing labels:

- `planning`: wrong or incomplete decomposition;
- `context_memory`: lost constraint, stale fact, or context pollution;
- `tool`: invalid call, misread output, or interface failure;
- `verification`: insufficient tests or incorrect success judgment;
- `recovery`: repeated action, no replan, or failure to recover;
- `budget`: token, time, or step exhaustion;
- `safety`: forbidden action or trust-boundary violation;
- `infrastructure`: runner/provider failure outside agent control;
- `task_grader`: benchmark defect discovered during audit.

Labels are based on trace evidence. Ambiguous cases are marked as such and sampled for a second review.

## 5. Comparison rules

A harness comparison is valid only when the following are held constant:

- task version and seed repository;
- model identifier and inference parameters;
- available tools and safety policy, unless that tool policy is the tested component;
- step, token, time, and monetary budgets;
- public information visible to the agent;
- grader version.

For stochastic configurations, the default is three runs per task. Report paired task-level deltas with a bootstrap 95% confidence interval. Also report raw counts and per-task results.

## 6. Predeclared targets

These are targets, not guaranteed claims:

- held-out task success: at least `+10 percentage points` over H0;
- false completion: at least `30% relative reduction`;
- recovery success on injected-failure tasks: at least `70%`;
- successful-run cost increase: no more than `25%`, or explicitly present a Pareto trade-off;
- at least one improvement preserves its direction on a second model.

Missing a target does not authorize changing its definition after results are known.

## 7. Exclusion and rerun policy

- All attempted runs receive an ID before model execution.
- Reruns do not replace previous runs.
- Benchmark defects are fixed with a new task version.
- Provider outages are documented with external evidence when available.
- Human intervention ends the run with `human_intervention`; it is not a success.
- Final test-set execution is limited to two complete passes after freeze.

## 8. Grader quality controls

- Each grader has at least one known-good and one known-bad fixture.
- Mutation tests alter one required invariant and must cause failure.
- Graders must not depend on network access.
- Grader results are deterministic across three repeated executions.
- Hidden checks test outcomes and invariants, not a single exact implementation.
- A task cannot be promoted to the test split until its grader passes audit.

