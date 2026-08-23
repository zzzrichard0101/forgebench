# V2 screening wave-4 base-generation freeze

Status: frozen before model execution

The final Wave 4 matrix is fixed at ten tasks and three repetitions per task,
for 30 Codex base-generation slots. Task order, seed content, runner source,
model, reasoning effort, harness, and private-grader seal are content-addressed
before the first slot executes.

The run uses Codex `gpt-5.6-sol`, medium reasoning, CLI `0.147.0`, and the
`H1a-lite-bounded-planning` public harness. Network access is disabled. The
runner cannot receive private grader source, known-good implementations, or
private labels.

All 30 frozen slots must be retained. Selective execution, outcome-based
reruns, and outcome-based exclusions are forbidden. A public-test failure
remains a visible failure in the execution record; an infrastructure failure
blocks corpus sealing instead of being silently replaced.

After execution, every publicly eligible base will be sealed into one public
Wave 4 corpus before external private evaluation begins. Wave 5 and threshold
weakening are prohibited under the current protocol.
