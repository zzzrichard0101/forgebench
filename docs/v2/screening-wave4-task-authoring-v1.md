# V2 screening wave-4 task authoring report

Status: ten final balanced repair-development tasks ready for base generation

Snapshot: `v2-screening-wave4-tasks-v1`

Wave 4 implements the expansion decision frozen before task authoring. All ten
preregistered mechanisms had the same minimum public lineage count, so this
final screening wave adds exactly one new task and repository lineage per
mechanism. Private case labels and failure locations were not used for task
selection or authoring.

| Task | Primary contract | Difficulty |
| --- | --- | --- |
| `v2-capability-token-exchange` | capability attenuation without authority amplification | hard |
| `v2-versioned-config-renamer` | atomic nested configuration migration | hard |
| `v2-archive-extraction-planner` | portable archive-path containment | hard |
| `v2-structured-log-template` | constrained templates with secret redaction | hard |
| `v2-async-resource-coordinator` | shared async creation, refcounts, and cleanup | hard |
| `v2-tiered-quota-reconciler` | exact tiered quota allocation | hard |
| `v2-polymorphic-message-upgrader` | strict recursive schema migration | hard |
| `v2-canonical-header-redactor` | canonical duplicate-safe header redaction | hard |
| `v2-deadline-retry-scheduler` | overflow-safe cumulative deadline scheduling | hard |
| `v2-domain-label-registry` | Unicode and IDNA collision protection | hard |

All ten use new IDs, distinct seed revisions, and repository lineages that do
not overlap V1 or screening waves 1–3. Every untouched seed passes its public
tests and fails its external private contract.

## External grader audit

Private grader source and known-good implementations remain outside the public
repository. Across three repeated grades per task:

- untouched seeds: 30/30 hidden failures;
- known-good workspaces: 30/30 hidden successes;
- protected dependency mutation: detected for 10/10 tasks.

Published integrity references:

- public task catalog: `sha256:ab8b052a3dc4d3d2d79bd5e845daf5f3e5303870b5b2b8c2d3925ebb5d470798`
- private development grader seal: `sha256:1edb5b46d0f214535b0320848bed45f9dc795b150e8069916ec6f8fd33383b9a`
- external audit file: `sha256:b4223affeaf9a884ed0e16cbc4230c2cccc7ccee7b97979c2329fa249d1d08a1`

These locally authored graders remain explicitly marked `repair_dev`,
development-only, not independently custodied, and ineligible for later
mechanism-validation claims.

## Next action

Freeze and execute the complete `10 tasks × 3 repetitions` Codex base
population without private-grader access. Retain all 30 slots and prohibit
outcome-based reruns or exclusions. This is the final screening wave permitted
by the current protocol: a passing gate advances to Stage A verifier screening;
an insufficient result seals a negative Stage A screening-feasibility result.
