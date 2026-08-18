# Shared Base-Completion Policy Runner v1

Date: 2026-08-18  
Status: **mechanism implemented and CLI-smoke verified**

## Purpose

Policy comparisons must not give each policy a different stochastic agent
completion. v1 seals one H1a-lite workspace after its public checks, records its
content hash, and makes every policy operate on an isolated copy of that exact
base artifact.

The runner currently exposes:

- `accept_all`;
- `verify_all`;
- `random_k_call_matched`, with an explicit pre-frozen selection bit;
- `probe_all`;
- `risk_model_direct`;
- `risk_hierarchical`.

`oracle_k` remains an evaluation-only planner and is deliberately absent from
the deployable replay interface because it requires hidden labels.

## Evidence firewall

`public-base-record.json` contains only task identity, the source run ID, the
public completion result, eligibility, and a workspace hash. Hidden labels are
written under a separate labels root. The sealed base is hash-checked before and
after every policy replay.

Adaptive routing and model work complete before hidden grading begins. The
pre-escalation workspace is retained for counterfactual evaluation, but its
grade is not available to the policy or model prompt.

## Development smoke

Source run `3ba463d2bff1464bba1d0a035a39182c` was sealed as
`dev-plugin-base-v1` with hash
`sha256:1157d7a2891f93aef5bb12cf519736a33ce4b07e0db6dbc6c0147c650b5d4062`.

| Policy | Replay run | Probe | Model tokens | Hidden result |
| --- | --- | --- | ---: | --- |
| Accept-All | `55ca2ad5ecf647f8babf7173c1c11fe4` | not run | 0 | fail |
| Probe-All | `a91e0bbe5ae549fb9f0bad0c2c392d66` | non-Python case failed | 0 | fail |

Both policy records reference the identical base hash. Probe-All is not a repair
policy, so its final hidden result correctly remains failed; its value is
detecting whether cheap probes alone explain the routing signal.

This is a development mechanism check, not a policy comparison result.

## Commands

```powershell
$env:PYTHONPATH = "src"
python scripts/seal_base_completion.py --task-id python-plugin-boundary --source-run-id <run-id> --base-id <base-id>
python scripts/run_policy_replay.py --task-id python-plugin-boundary --base-id <base-id> --policy accept_all
python scripts/run_policy_replay.py --task-id python-plugin-boundary --base-id <base-id> --policy probe_all
python scripts/evaluate_base_completion.py --task-id python-plugin-boundary --base-id <base-id>
```

Model-backed policies additionally use the same Codex host/model arguments as
the existing adaptive replay command. Random-k refuses to run until
`--random-selected` or `--no-random-selected` is supplied.

## Remaining work

v1 replays one base completion at a time. The follow-up
[multi-base assignment manifest](multi-base-assignment-manifest-v1.md) now
freezes public-only routing and call-matched Random-k selections across a base
collection. Outcome aggregation remains separate.
