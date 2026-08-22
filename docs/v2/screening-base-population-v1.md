# V2 screening base population v1

Status: sealed; insufficient for verifier screening

The frozen `6 tasks × 3 repetitions` Codex run completed without infrastructure
failure:

- 18 frozen slots;
- 16 public-gate-eligible bases;
- 2 visible failures;
- 0 infrastructure failures.

Only after the 16 eligible bases were sealed under public manifest
`sha256:3a2211a6737e0632bd1da69c9c6ceab3eb48fe935d02917886349609f58c7bdc`
were all bases evaluated by the external development grader.

Aggregate private result:

- 2 false completions;
- 14 passing controls;
- false completions cover 1 task cluster and 1 mechanism;
- passing controls cover 5 task clusters.

The screening preregistration requires at least six false-completion clusters,
six passing-control clusters, and four false-completion mechanisms. This
population therefore remains immutable but is not sufficient to start verifier
screening. No case was removed or rerun based on its private outcome.

Next, author additional new repair-development lineages. Do not weaken graders,
reuse V1 tasks, convert passing outcomes into injected failures, or treat the 14
controls as false-completion evidence.

