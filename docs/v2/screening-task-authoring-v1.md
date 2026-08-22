# V2 screening task authoring report

Status: six repair-development tasks ready for base generation  
Snapshot: `v2-screening-tasks-v1`

The first V2 task package contains six new task and repository lineages:

| Task | Mechanism | Difficulty |
| --- | --- | --- |
| `v2-package-member-policy` | containment | medium |
| `v2-converter-command-boundary` | injection | easy |
| `v2-recursive-schema-contract` | schema | hard |
| `v2-canonical-handle-registry` | Unicode normalization | medium |
| `v2-upload-budget-ledger` | numeric/aggregate and replay semantics | medium |
| `v2-retry-after-policy` | temporal/retry | hard |

All tasks use new IDs, distinct seed revisions, and repository lineages that do
not overlap the V1 development or held-out catalogs. Each seed passes its public
tests and fails its external private contract.

## External grader audit

Private grader source and known-good implementations remain outside the public
repository. Across three repeated grades per task:

- untouched seeds: 18/18 hidden failures;
- known-good workspaces: 18/18 hidden successes;
- protected dependency mutation: detected for 6/6 tasks.

Published integrity references:

- public task catalog: `sha256:beda2036bd58a69f06e1579962d61c085df4b97d9852f11497c3e231ee53abca`
- private development grader seal: `sha256:e4df32828bd6eb2575bced7ed671ac4cc668e57a86bb887d52f6d4947ef0dbd6`
- external audit file: `sha256:aed8cddde5738ed27302c2abc370854ce4cf5a0aa8cf312ca8ce96d54aa6980b`

These graders are explicitly marked `repair_dev`, `development_only`, and not
eligible for the later mechanism-validation gate. Independent validation tasks
and graders will be authored only after verifier screening.

## Next action

Generate immutable Codex base completions from every task without access to the
external grader. After public artifacts are sealed, evaluate all eligible bases
externally and classify the complete population; do not select cases by outcome.

