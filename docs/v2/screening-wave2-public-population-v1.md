# V2 screening wave-2 public population

Status: sealed; awaiting external private evaluation

The frozen `6 tasks × 3 repetitions` Codex run completed without infrastructure
failure:

- 18 frozen slots executed;
- 17 bases passed the public completion gate;
- 1 base had a visible public-test failure;
- 0 infrastructure failures.

The visible failure remains part of the execution record and was neither rerun
nor converted into hidden-failure evidence. All 17 eligible bases were sealed
before any private evaluation under public manifest
`sha256:6d2db02a015a16a107445d3b2582591ed9a15acbdafd22d368ff0ce889f5aaab`.

The frozen run used Codex model `gpt-5.6-sol`, medium reasoning, pinned CLI
`0.147.0`, and the same bounded-planning harness as screening wave 1. The runner
had no access to private grader source or known-good implementations.

## Next action

Evaluate all 17 eligible cases with the externally stored sealed development
grader. Publish only aggregate cohort and mechanism counts, then combine those
counts with the immutable wave-1 population to decide whether verifier
screening has enough coverage to begin.
