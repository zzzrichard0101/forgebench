# Completion Risk Gate Shadow Screen v0.1

Date: 2026-08-17  
Status: **mechanism and static development screen complete; no adaptive claim**

## What was implemented

`CompletionRiskPolicy` is a deterministic, public-evidence-only gate. It emits
the policy version, eligibility, score, threshold, risk level, escalation
decision, and every rule's evidence. When enabled in `H1Runner`, the decision is
stored in both the run manifest and an append-only `harness-trace.jsonl` event.

Version 0.1 is shadow-only. A high-risk decision does not yet call a model,
change the workspace, or read the hidden grader.

## Rules

| Rule | Weight | Trigger |
|---|---:|---|
| `R001_BOUNDARY_SENSITIVE_SURFACE` | 1 | Public task text describes a boundary-sensitive surface |
| `R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE` | 2 | Boundary-sensitive task lacks a visible negative-case marker in public checks |
| `R003_UNRESOLVED_PLAN_ASSUMPTION` | 2 | Public plan contains an unresolved-assumption marker |

The threshold is 3. Rule IDs, weights, and evidence are recorded rather than
collapsed into an unexplained label.

## Static development screen

The ten audited development tasks were screened using their public task text and
public test sources. Completion was treated as counterfactually eligible so the
screen measures routing only; it is not a model-backed run.

| Result | Count |
|---|---:|
| High risk | 2 / 10 |
| Low risk | 8 / 10 |

High-risk tasks:

- `python-plugin-boundary`: boundary-sensitive with no visible negative test;
- `python-archive-boundary`: boundary-sensitive with no visible negative test.

Retrospectively, this flags the one known H1a-lite accepted false completion and
also flags one H1a-lite success. The latter is a potential unnecessary
escalation and is intentionally preserved. The current result is therefore a
plausibility check, not an accuracy estimate.

`python-rate-window` remains low risk because its public tests visibly exercise
the at-limit rejection boundary. This is the intended distinction between a
boundary-sensitive task and a boundary-sensitive task with missing negative
evidence.

## Leakage controls

- `author_metadata` is excluded and covered by a test proving it cannot change
  the decision.
- Hidden grader definitions and outputs are not policy inputs.
- The known plugin failure remains development evidence only.
- The policy is observation-only until false-positive behavior is measured on
  additional development tasks.

## Next gate

Implement a bounded deep-verification action for high-risk runs, preserve a
pre-escalation workspace snapshot, and compare shadow decisions with actual
grader outcomes. Do not tune rule weights on the future held-out set.

