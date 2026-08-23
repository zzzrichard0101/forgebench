# V2 screening wave-3 authoring freeze

Status: frozen before task authoring

Wave 3 uses only the public distribution of task and repository lineages to
select mechanisms. No private case label is a selection feature.

After waves 1 and 2, temporal/retry and serialization/redaction each have two
public development lineages. The other eight preregistered mechanisms each have
one. The frozen rule selects all mechanisms tied at the minimum public count and
adds exactly one new task and repository lineage for each:

| Mechanism | Planned task |
| --- | --- |
| authorization | `v2-delegated-scope-checker` |
| configuration/migration | `v2-typed-env-loader` |
| containment | `v2-sandbox-path-mapper` |
| injection | `v2-subprocess-request-builder` |
| lifecycle/resource | `v2-callback-shutdown-stack` |
| numeric/aggregate | `v2-credit-reservation-ledger` |
| schema | `v2-tagged-event-decoder` |
| Unicode normalization | `v2-unicode-namespace-map` |

This produces eight new lineages. After authoring and external grader audit, the
entire `8 tasks × 3 repetitions` matrix will be frozen and executed. All 24
slots are retained; outcome-based reruns and exclusions are forbidden.

These tasks and locally authored graders remain `repair_dev`, development-only,
and ineligible for mechanism-validation claims. The two prior screening
populations remain immutable.
