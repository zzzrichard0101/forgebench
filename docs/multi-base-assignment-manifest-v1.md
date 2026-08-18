# Multi-Base Policy Assignment Manifest v1

Date: 2026-08-18  
Status: **mechanism implemented and CLI-smoke verified**

## Purpose

The shared-base runner guarantees a fair artifact for one replay. This layer
freezes which actions each policy will take across a collection before any
hidden label is joined.

For every eligible base completion, the manifest records:

- task identity, family stratum, source run, and immutable base hash;
- the public Completion Risk Gate decision;
- the deterministic probe route used by the hierarchical policy;
- whether each policy is assigned a probe and/or model call;
- a deterministic Random-k rank.

The manifest is content-hashed. Replays can accept the manifest path and refuse
execution when the base hash, task version, Random-k bit, or observed routing
differs from the frozen assignment.

## Random-k matching

Within each task-family stratum, Risk-Hierarchical first determines its expected
model-call count from public evidence:

```text
high risk AND NOT(all supported probes pass)
```

Random-k receives exactly that many model calls. Candidates are ordered by:

```text
sha256(random_seed, task_family, base_id)
```

and the first `k` are selected. This avoids runtime randomness and is stable for
a fixed seed and base collection. Actual tokens and latency are still reported
because equal call count does not imply equal cost.

## Leakage and mutation controls

- Planning accepts only public-gate-passing sealed bases.
- Risk and probe routing run in copied workspaces.
- Canonical base hashes are checked before and after planning.
- No hidden grader result or label path is read or written by the planner.
- Oracle-k remains outside this deployable manifest.
- Any content edit invalidates the manifest hash.

## Verification

A deterministic two-base test uses one known false completion and one correct
completion from the same task family. Risk-Hierarchical assigns one model call;
Random-k also assigns exactly one. Repeating with the same seed produces the
same Random-k assignment, and both canonical bases remain unchanged.

The real CLI smoke froze `dev-one-base-assignment-v1` from the existing plugin
development base:

- manifest hash:
  `sha256:28ab50c8880655c4800b1c8e1c253ba5e827fc7d129bb6afc3d0ca692ca10847`;
- Risk-Hierarchical expected model calls: 1;
- Random-k model calls: 1;
- Accept-All and Probe-All replays validated the manifest reference and base
  hash before running.

This one-base smoke tests wiring, not Random-k effectiveness.

## Commands

```powershell
$env:PYTHONPATH = "src"
python scripts/plan_policy_comparison.py `
  --entry python-plugin-boundary=<base-id> `
  --manifest-id <manifest-id> `
  --random-seed 1729

python scripts/run_policy_replay.py `
  --task-id python-plugin-boundary `
  --base-id <base-id> `
  --policy probe_all `
  --assignment-manifest runs/comparison-manifests/<manifest-id>.json
```

## Remaining work

The next phase expands the development task set and authors an untouched
held-out set. A later aggregation layer will join replay results with separately
stored labels and compute risk-coverage and reliability-cost metrics.
