# Selective Verification Policy Freeze v1

## Outcome

The development policy is frozen before held-out task authoring. The freeze
records the complete policy comparison set, risk rules and threshold, probe
selection contract, model and timeout, evidence budget, Random-k seed, practical
claim margins, and SHA-256 hashes of every execution-critical artifact.
The `dev-v0.6` dataset manifest also binds the full content of every task
document through one catalog hash.

The machine-readable manifest is
`experiments/configs/selective-verification-policy-freeze-v1.json`. Loading it
fails if the manifest content or any referenced artifact changes.

## Transferable probe gate

`deterministic-probe-v0.2` selects the
`python_manifest_file_loader` interface contract from public task metadata. The
contract declares a module, callable, manifest key, accepted suffix, and
contract dimensions. It does not branch on a task ID. A regression test changes
only the task ID to an unseen held-out-style name and obtains the same adapter
and probe outcome.

This resolves grader-audit finding F001 without claiming universal probe
coverage. Unsupported contracts conservatively route high-risk completions to
one bounded model verification. At least three of the ten held-out tasks must
independently expose a transferable probe contract so P5 remains operationally
distinct from P4.

## Frozen primary settings

- primary policy: `risk_hierarchical`;
- risk policy: `completion-risk-v0.2`, threshold 3;
- probe: `deterministic-probe-v0.2`;
- model: `gpt-5.6-sol`, medium reasoning, one 300-second attempt;
- evidence packet: v0.2, 24,000 characters;
- Random-k seed: 1729, stratified by task family;
- held-out execution limit: two attempts.

Any change creates a new freeze version. It cannot silently replace this
manifest or reuse its held-out result.
