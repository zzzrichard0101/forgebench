# ForgeBench V1 preservation boundary

Status: frozen historical evidence  
V2 decision date: 2026-08-23

ForgeBench V1 ended with a valid negative result. All 30 public-gate-passing
base completions failed private evaluation, none of 57 model-backed verifier
calls repaired a hidden failure, and Verify-All introduced one hard-safety
violation. The published report remains the authority for those results:
`experiments/reports/heldout-private-policy-evaluation-v1.json`.

V2 is a new experiment. It does not revise, extend, or re-score V1.

## Immutable V1 evidence

The following are excluded from V2 development, prompt design, feature design,
threshold selection, and task authoring:

- V1 held-out task contents and repository lineages;
- individual V1 hidden labels and private grader source;
- V1 held-out base completions and policy replays;
- V1 probe outcomes, policy assignments, thresholds, and random selections;
- V1 private result details beyond the already published aggregate report.

V2 code may read the public V1 aggregate report only to enforce this boundary
and to state the motivating negative result. It may not use individual V1
outcomes as training or development examples.

## Namespace rule

All V2 artifacts use a `v2` namespace in their file name or parent directory.
No V2 command may overwrite a V1 configuration, report, seal, manifest, or
artifact. A needed correction creates a new version and preserves the old one.

## Contamination rule

Any V2 run that gains early access to V1 private material or to its own
validation/held-out labels is marked `contaminated` and is ineligible for a
confirmatory claim. The run is retained for audit rather than deleted.

