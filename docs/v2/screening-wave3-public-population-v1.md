# V2 screening wave-3 public population

Status: sealed; awaiting external private evaluation

The frozen `8 tasks × 3 repetitions` Codex run completed without
infrastructure failure:

- 24 frozen slots executed;
- 23 bases passed the public completion gate;
- 1 base had a visible public-test failure;
- 0 infrastructure failures.

The visible failure remains part of the execution record and was neither rerun
nor converted into hidden-failure evidence. All 23 eligible bases were sealed
before any private evaluation under public manifest
`sha256:0a637f8158176abfbfb0cddab9f411185dc3aefc06ff88b54b4f2760ae8bcd86`.
The complete 24-slot execution record is bound by file hash
`sha256:f5e4b6b4a1357e5c6b11df8dc1cfad8de6fce18270fc092c3d676d2e441d41b8`.

The frozen run used Codex model `gpt-5.6-sol`, medium reasoning, pinned CLI
`0.147.0`, and the `H1a-lite-bounded-planning` harness. The runner had no access
to private grader source, known-good implementations, or private case labels.

All eight mechanisms selected by the public-lineage balancing rule are
represented in the sealed population. This remains a locally authored
`repair_dev` screening population and is not mechanism-validation evidence.

## Next action

Evaluate all 23 eligible cases with the externally stored sealed development
grader. Publish only aggregate counts and integrity hashes, without committing
private tests, known-good implementations, or case-level labels.
