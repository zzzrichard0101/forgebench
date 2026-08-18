# ForgeBench Dataset Card v0.4

## Snapshot

This is an early development snapshot, not the frozen evaluation set.

| Dimension | Current count |
|---|---:|
| Total executable tasks | 15 |
| Public examples | 1 |
| Development tasks | 14 |
| Held-out test tasks | 0 |
| Development / incident / adversarial | 10 / 3 / 2 |
| Easy / medium / hard | 3 / 12 / 0 |

The current tasks cover monetary rounding, configuration precedence, cursor
pagination, event idempotency, rolling time boundaries, three evidence-driven
incident investigations, two path-boundary tasks with untrusted repository
instructions, and five additional API-contract boundaries: header
normalization, state replay, boolean schema input, URL host matching, and batch
termination.

## Intended use

ForgeBench evaluates repository-scoped agent harnesses on completion,
verification, recovery, efficiency, and safety. This snapshot exists to test
the task contract and grader-audit process before scaling to 20 development
tasks and freezing policy assignments for an independently produced held-out
set. It must not be used to claim broad model rankings: fifteen authored tasks
are still small and all development graders are public.

## Task construction

Each task contains a versioned instruction, immutable seed path and revision,
budgets, safety policy, public diagnostics, deterministic required checks, and
author metadata describing intended capabilities and likely failures.

Every task must demonstrate:

1. the untouched seed fails at least one required invariant;
2. at least one implementation-independent known-good outcome passes;
3. mutating a protected artifact is detected;
4. three repeated grades of the same workspace are identical;
5. no grader requires network access.

These controls run in `tests/test_benchmark_catalog.py`.

## Split and leakage policy

- `public` tasks may include graders and worked analysis.
- `dev` tasks expose public diagnostics; their required graders are available
  during harness development in this repository snapshot.
- Future `test` task instructions and immutable seed revisions will be listed in
  a frozen manifest, while private grader material remains outside the agent
  workspace and outside prompt context.
- Looking at a test grader, manually repairing a test run, or tuning against a
  test trace invalidates that final evaluation pass.
- Task changes create a new version; failed historical runs remain attached to
  their original version.

## Known limitations

- Current tasks use Python and small repositories, so language and scale
  diversity are absent.
- Incident grading checks evidence-derived invariants but cannot fully measure
  report quality.
- Adversarial coverage currently tests filesystem trust boundaries and prompt
  conflict, not network or secret-manager integrations.
- Difficulty labels are author estimates until repeated baseline evidence is
  available.

## Version history

- `dev-v0.4`: five API-contract tasks were added as the first expansion tranche.
  Every seed has a deterministic failure, implementation-independent hidden
  cases, a known-good solution, and protected dependency metadata.
- `dev-v0.3`: incident tasks moved to v2 after the first 10-task baseline found
  that v1 graders required undisclosed exact identifiers and root-cause labels.
  Version 2 accepts semantically equivalent identifiers and explanations while
  retaining evidence, impact, remediation, and protected-file invariants.

## Expansion gate

The next snapshot adds six tasks with incident and adversarial emphasis to reach
20 development tasks. Promotion requires grader mutation coverage, family
balance, and label agreement. Harness policy is then frozen before held-out
task material is generated or inspected.
