# H2 Fault-injection Report v0.1

Date: 2026-08-17

Status: **deterministic mechanism evaluation complete; model-backed evaluation pending**

## Question

Do bounded context selection and typed recovery rules behave correctly under
controlled tool failures without retrying deterministic errors or weakening the
workspace safety boundary?

The experiment was frozen in
`experiments/configs/h2-fault-injection-v0.1.json` before execution. It contains
three injections, control and treatment cells, and three repetitions per cell.

## Results

| Injection | Control | H2 treatment | Acceptance |
|---|---:|---:|---:|
| First-attempt timeout recovery | 0 / 3 | 3 / 3 | pass: ≥70% |
| Deterministic invalid-call retries | 0 | 0 | pass: exactly 0 |
| Decisive failure retained under context pressure | 3 / 3 | 3 / 3 | pass |
| Mean retained context characters | 40,105 | 12,000 | pass: ≤12,000 |
| Safety regressions | 0 | 0 | pass |

The transient treatment used six tool calls for three runs: one injected failure
and one successful retry per run. The control used three calls and never
recovered. Deterministic failures used one call per run in both configurations;
H2 correctly refused to spend its retry budget on them.

The bounded context policy reduced retained observation text by 70.1% while
preserving the decisive failed observation in all three repetitions.

## Interpretation

The predeclared mechanism acceptance gate passed. The result proves that the
harness can distinguish injected transient timeouts from deterministic errors,
apply a bounded retry, enforce its context limit, and expose each decision in
the trace.

It does **not** prove that an LLM agent solves more repository tasks. The probe
uses a deterministic model adapter so that harness behavior is isolated from
model variance. Per the project evaluation contract, these runs are mechanism
evidence and cannot be reported as benchmark task success.

## Next experiment

Add model-visible recovery tasks in which Codex must use the post-retry
observation to complete a graded repository artifact. Compare H2-off and H2-on
with the same task, model, budgets, and injected tool schedule. The primary
outcome remains recovery success; token, tool-call, and wall-time overhead are
secondary outcomes.
