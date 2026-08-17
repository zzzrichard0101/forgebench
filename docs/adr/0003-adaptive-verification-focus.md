# ADR 0003: Focus the next evaluation on adaptive verification

Date: 2026-08-17  
Status: Accepted

## Context

The original plan treated planning, verification, context, recovery, and a
meta-harness as a mostly cumulative component sequence. That sequence produced
useful engineering evidence, but recent work now covers broad harness
comparison and automated harness evolution at much larger scale.

ForgeBench also produced a more specific failure worth pursuing. H1a-lite
passed its public completion checks on `python-plugin-boundary`, yet the hidden
grader rejected the artifact because a non-Python entrypoint boundary was
missing. This is an observed completion-acceptance failure, not merely a
hypothetical motivation.

## Decision

The next primary question is:

> Can a harness preserve low-cost completion for low-risk runs while escalating
> only high-risk runs to deeper verification, reducing false completion without
> paying the full verification cost on every task?

ForgeBench will add `H1a-adaptive`: H1a-lite followed by a rule-based Completion
Risk Gate and selective deep verification. The risk policy and escalation
actions must use only information available to the agent and harness before the
hidden grader runs.

The observed `python-plugin-boundary` failure becomes a development discovery
case. It cannot count as held-out proof for the adaptive policy. Risk rules will
be frozen before final held-out evaluation.

Context compaction and bounded recovery remain implemented harness capabilities
and supporting evidence. They are no longer the main portfolio research claim.
Automated meta-harness search, learned risk prediction, multi-agent
orchestration, and a 50-task scale target move to stretch scope.

## Consequences

- The target benchmark becomes at least 30 audited tasks weighted toward
  completion-risk distinctions rather than 50 tasks optimized for breadth.
- Evaluation separates true success, accepted false completion, detected
  failure, safety violations, escalation rate, and unnecessary escalation.
- H0, H1a, H1a-lite, and H1a-adaptive are compared under the same model, tasks,
  tools, budgets, and grader versions.
- A one-case improvement is a smoke result only. Portfolio claims require a
  frozen held-out comparison and repeated runs within the available budget.
- Hidden grader content is never supplied to the risk gate or deep verifier.

