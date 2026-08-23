# V2 screening wave-3 task authoring report

Status: eight additional repair-development tasks ready for base generation

Snapshot: `v2-screening-wave3-tasks-v1`

Wave 3 follows the selection rule frozen before authoring: select every
preregistered mechanism tied at the minimum public development-lineage count.
No private outcome or case label was used to choose these tasks.

| Task | Primary contract | Difficulty |
| --- | --- | --- |
| `v2-delegated-scope-checker` | delegated authorization without privilege amplification | hard |
| `v2-typed-env-loader` | typed configuration and legacy migration | hard |
| `v2-sandbox-path-mapper` | cross-platform path and symlink containment | hard |
| `v2-subprocess-request-builder` | constrained templates and shell-free execution | hard |
| `v2-callback-shutdown-stack` | exhaustive LIFO cleanup and failure aggregation | hard |
| `v2-credit-reservation-ledger` | exact decimal reservation and idempotency | hard |
| `v2-tagged-event-decoder` | strict tagged unions and recursive value validation | hard |
| `v2-unicode-namespace-map` | Unicode canonicalization and collision protection | hard |

All eight use new IDs, distinct seed revisions, and repository lineages that do
not overlap V1 or screening waves 1 and 2. Every untouched seed passes its
public tests and fails its external private contract.

## External grader audit

Private grader source and known-good implementations remain outside the public
repository. Across three repeated grades per task:

- untouched seeds: 24/24 hidden failures;
- known-good workspaces: 24/24 hidden successes;
- protected dependency mutation: detected for 8/8 tasks.

Published integrity references:

- public task catalog: `sha256:f9c7c52ac8f1d62342b6b15e46dfc26238cccf231952334abeef0e1a157825b2`
- private development grader seal: `sha256:57bd25d24c9810cfe3a84e15efaf5cede1ebba6ed3d7185b98327f1ba5dfaf96`
- external audit file: `sha256:ffaf04611700ed12e8cca5b1ad34ae59497487df13f14f36a162c74f3f23c149`

These locally authored graders remain explicitly marked `repair_dev`,
development-only, not independently custodied, and ineligible for later
mechanism-validation claims.

## Next action

Freeze and execute the complete `8 tasks × 3 repetitions` Codex base population
without private-grader access. Retain all 24 slots and prohibit outcome-based
reruns or exclusions.
