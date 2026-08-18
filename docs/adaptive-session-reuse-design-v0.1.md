# Adaptive Session Reuse Design v0.1

Date: 2026-08-18  
Status: **implementation complete; live cost result pending**

## Problem

Evidence Packet v0.2 reduced the adaptive pass from 97,108 to 64,921 input
tokens, but the second Codex process still had to reconstruct repository context.
The earlier source runs used `--ephemeral`, so their session rollout files were
not persisted and cannot be resumed.

## Mechanism

The H1 runner now has an opt-in `--persist-session` mode. It omits
`--ephemeral`, extracts the `thread.started` identifier from the JSONL trace,
and records that ID in both the H1 manifest and normalized run summary.

The adaptive runner has an opt-in `--resume-source-session` mode. A high-risk
attempt still receives a copied, isolated workspace and the bounded Evidence
Packet v0.2, but the verification command uses `codex exec resume` with:

- the recorded source session ID;
- an explicit `--cd` pointing to the copied adaptive workspace;
- the same model and reasoning effort;
- the existing one-pass timeout and leakage controls.

The default remains ephemeral, so historical runner behavior does not change.
Both commands can share an explicit `--codex-home` for isolated session storage.

## Predeclared development check

The frozen configuration is
`experiments/configs/adaptive-session-reuse-v0.1.json`. On a fresh
`python-plugin-boundary` H1a-lite run, the resumed adaptive pass must:

1. record and resolve the source session ID;
2. route the completion as high risk;
3. perform exactly one deep-verification pass;
4. pass completion and the hidden task grader;
5. leave the source workspace unchanged;
6. use fewer than 64,921 additional input tokens.

This remains development evidence and cannot support a held-out claim.

## Verification status

All 68 deterministic repository tests pass, including command construction,
ephemeral-default preservation, session-ID propagation, and explicit replay
workspace selection. A live run in the current managed environment created and
recorded a session ID, then failed before sampling because outbound Codex model
connections were denied. It consumed zero model tokens and is excluded from
agent-quality and cost results. The live acceptance check remains pending in a
network-enabled execution environment.

