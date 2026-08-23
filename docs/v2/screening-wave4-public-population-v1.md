# V2 screening wave-4 public population

Status: sealed; awaiting external private evaluation

The frozen `10 tasks × 3 repetitions` Codex run completed without
infrastructure failure:

- 30 frozen slots executed;
- 28 bases passed the public completion gate;
- 2 bases had visible public-test failures;
- 0 infrastructure failures.

The visible failures remain part of the execution record and were neither
rerun nor converted into hidden-failure evidence. All 28 eligible bases were
sealed before any private evaluation under public manifest
`sha256:d5968eeccc597dfc7381a16e0b9d025dd7cbfda0332efcef0adb9de90abaa76c`.
The complete 30-slot execution record is bound by file hash
`sha256:801ee8f24974a9f4cd7546984e66ccf64f2e42ad22241b5a26fe0260c6afc891`.

The frozen run used Codex model `gpt-5.6-sol`, medium reasoning, pinned CLI
`0.147.0`, and the `H1a-lite-bounded-planning` harness. The runner had no
access to private grader source, known-good implementations, or private case
labels.

All ten preregistered mechanisms are represented in the sealed population.
This remains a locally authored `repair_dev` screening population and is not
mechanism-validation evidence. Wave 5 and threshold weakening remain forbidden
under the current protocol.

## Next action

Evaluate all 28 eligible cases with the externally stored sealed development
grader. Publish only aggregate counts and integrity hashes, without committing
private tests, known-good implementations, or case-level labels.
