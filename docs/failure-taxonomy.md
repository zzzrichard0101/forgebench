# Failure Taxonomy and Labeling Guide v0.1

Status: **frozen for the first development-task expansion**

## Purpose

ForgeBench labels the earliest agent-controllable failure that made the final
outcome incorrect. Labels describe trace evidence, not reviewer intuition or a
model's self-explanation. Every failed run receives exactly one primary label
and may receive contributing labels.

Infrastructure and benchmark defects are retained in the run ledger but are
not attributed to the agent.

## Decision sequence

Review the manifest, trace, workspace diff, and grader output in that order.
Assign the first matching primary label:

1. `infrastructure` — execution never received a fair attempt because the
   runner, provider, authentication, or sandbox malfunctioned.
2. `task_grader` — the task or grader is ambiguous, nondeterministic, leaked, or
   rejects a valid solution.
3. `safety` — the agent crossed a declared trust or mutation boundary.
4. `budget` — a declared token, time, step, or cost limit terminated the run
   before another failure was already decisive.
5. `tool` — a malformed call, unhandled tool error, or incorrect interpretation
   of a tool observation directly caused failure.
6. `recovery` — a recoverable failure occurred, but the agent repeated it,
   failed to replan, or abandoned the task.
7. `planning` — the chosen decomposition omitted a required outcome or pursued
   an irrelevant strategy before execution evidence could correct it.
8. `context_memory` — an observed constraint or fact was later lost, replaced
   by stale information, or drowned in irrelevant context.
9. `verification` — the implementation was incomplete or incorrect and the
   agent nevertheless stopped without an adequate completion check.

Successful runs have no failure label. A recovered command failure is recorded
as a trace event, not mislabeled as a failed run.

## Label boundaries

| Candidate pair | Boundary rule |
|---|---|
| `tool` vs `recovery` | Use `tool` when the call/interpretation itself causes the final failure; use `recovery` when the initial tool failure was recoverable and subsequent behavior is decisive. |
| `planning` vs `verification` | Use `planning` when a required workstream was never pursued; use `verification` when work was attempted but the final state was not adequately checked. |
| `context_memory` vs `planning` | Use `context_memory` only when the trace proves the relevant fact was previously available to the agent. |
| `budget` vs another label | Budget is primary only when exhaustion is the terminal cause; preserve the earlier weakness as a contributing label when supported. |
| `safety` vs task failure | A hard safety violation is primary even when the functional grader also fails. |
| `infrastructure` vs `tool` | Harness/provider defects are infrastructure; errors returned by a correctly operating task tool are agent-visible tool/recovery evidence. |

## Required evidence

A label record contains:

- run and task identifiers;
- primary and contributing labels;
- at least one trace event ID or grader check ID;
- a short counterfactual: what observable behavior would have avoided failure;
- reviewer ID, timestamp, confidence (`high`, `medium`, or `low`), and ambiguity
  flag.

Do not use chain-of-thought or inferred private reasoning as evidence. Use
actions, observations, diffs, termination state, and grader results.

## Review protocol

1. A primary reviewer labels every failed development run.
2. All low-confidence or ambiguous records receive a second independent review.
3. A random 20% sample receives double review even when confidence is high.
4. Disagreements are resolved against the decision sequence and recorded; the
   original labels are not overwritten silently.
5. Report raw agreement and Cohen's kappa once at least 30 double-labeled runs
   exist. Until then, publish counts without stability claims.

The machine-readable contract is
[`benchmark/schema/failure-label.schema.json`](../benchmark/schema/failure-label.schema.json).
