# V2 screening wave-2 task authoring report

Status: six additional repair-development tasks ready for base generation  
Snapshot: `v2-screening-wave2-tasks-v1`

The first frozen screening population produced too few false completions. This
second package therefore adds six new task and repository lineages without
changing, deleting, or selectively rerunning any wave-1 result.

| Task | Primary contract | Difficulty |
| --- | --- | --- |
| `v2-access-rule-resolver` | authorization and deny precedence | hard |
| `v2-config-layer-transaction` | deep configuration merge and atomicity | hard |
| `v2-query-pair-encoder` | ordered canonical serialization | medium |
| `v2-shared-lease-pool` | lifecycle and reference counting | hard |
| `v2-stream-secret-redactor` | streaming boundaries and bounded state | hard |
| `v2-webhook-replay-gate` | authentication, time windows, and replay | hard |

All six use new IDs, distinct seed revisions, and lineages that do not overlap
V1 or screening wave 1. Every untouched seed passes its public tests and fails
its external private contract.

## External grader audit

Private grader source and known-good implementations remain outside the public
repository. Across three repeated grades per task:

- untouched seeds: 18/18 hidden failures;
- known-good workspaces: 18/18 hidden successes;
- protected dependency mutation: detected for 6/6 tasks.

Published integrity references:

- public task catalog: `sha256:0a30356af3e339afc19f75b1cece13c8850f64588d815b76f35191c0f871c855`
- private development grader seal: `sha256:2023e8b322de9a59a8ad4171c0cf0e3231c26ca3facb54e525defdb4b3c30875`
- external audit file: `sha256:3d9d0458367f9fbfb9d9089fab8e87c84ddd29ca5e570732fc6b7d576add786a`

These locally authored graders remain explicitly marked `repair_dev`,
development-only, not independently custodied, and ineligible for the later
mechanism-validation gate.

## Next action

Freeze and run `6 tasks × 3 repetitions` of Codex base completions without
private-grader access. Seal all public artifacts before external grading, then
classify the complete eligible population without outcome-based selection.
