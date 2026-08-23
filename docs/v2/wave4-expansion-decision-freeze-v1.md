# V2 Wave 4 expansion decision freeze

Status: one final balanced screening wave approved before task authoring

The first three immutable screening populations contain 20 task lineages and
60 frozen execution slots. The combined result meets the passing-control gate,
but false-completion diversity remains at four of six required task clusters
and three of four required mechanisms.

## Feasibility assessment

Four of the 20 authored lineages have produced at least one false completion.
Treating that public aggregate as a rough lineage-level yield gives a 0.20
estimate. For ten new lineages, the probability of obtaining at least two new
false-completion clusters is approximately:

- 62.4% under a plug-in binomial estimate;
- 65.0% under a Beta(1,1)-prior posterior predictive estimate;
- 45.6% to 75.6% when the assumed yield varies from 0.15 to 0.25.

The gate also requires at least one previously unrepresented failure mechanism,
which cannot be identified from case-level data without contaminating task
selection. Accounting for that extra condition, the conservative judgmental
probability of a complete gate pass is 40% to 60%. This is a planning estimate,
not a statistical guarantee.

## Frozen selection

After Wave 3, all ten preregistered mechanisms have exactly two public task
lineages. The selection rule therefore adds one new task and repository lineage
for every mechanism. No private case label or failure location chooses a task.

| Mechanism | Planned task |
| --- | --- |
| authorization | `v2-capability-token-exchange` |
| configuration/migration | `v2-versioned-config-renamer` |
| containment | `v2-archive-extraction-planner` |
| injection | `v2-structured-log-template` |
| lifecycle/resource | `v2-async-resource-coordinator` |
| numeric/aggregate | `v2-tiered-quota-reconciler` |
| schema | `v2-polymorphic-message-upgrader` |
| serialization/redaction | `v2-canonical-header-redactor` |
| temporal/retry | `v2-deadline-retry-scheduler` |
| Unicode normalization | `v2-domain-label-registry` |

After authoring and external grader audit, all `10 tasks × 3 repetitions` are
executed and retained. Outcome-based reruns and exclusions remain forbidden.

## Terminal rule

Wave 4 is the final expansion under the current protocol. A passing combined
gate proceeds to Stage A verifier screening. If the gate remains insufficient,
ForgeBench seals a negative Stage A screening-feasibility result instead of
authoring Wave 5 or weakening thresholds. Stage B remains locked in either case
until the complete Stage A activation conditions are satisfied.
