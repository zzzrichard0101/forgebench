# Adaptive Verification Development Replay v0.2

Date: 2026-08-17  
Status: **development mechanism gate passed; efficiency gate not established**

## Experiment

Two previously published H1a-lite workspaces were replayed without changing the
source runs:

- `python-plugin-boundary`: known accepted false completion;
- `python-archive-boundary`: known true success and a potential unnecessary
  escalation from the static task-only screen.

The risk policy could inspect only the public task, plan, implementation, and
public tests. Hidden graders ran on preserved pre-escalation and final snapshots
outside the Codex process.

## Recorded v0.1 pilot failure

The first replay (`cd4d96355ad9484697fa266117d4d795`) did not escalate the
plugin task. Policy v0.1 treated any visible negative test as sufficient; the
agent-written containment test therefore masked the untested file-type contract.
No model call occurred and the task remained failed.

The run was preserved. Policy v0.2 replaced binary negative-test detection with
contract-dimension coverage. The revised policy and v0.2 experiment config were
committed before the valid replay.

## v0.2 result

| Task | Public dimension evidence | Route | Before | After | Adaptive input | Time |
|---|---|---:|---:|---:|---:|---:|
| Plugin boundary | containment covered; file type missing | High | Fail | Pass | 97,108 | 53.858 s |
| Archive boundary | containment covered | Low | Pass | Pass | 0 | 0.400 s |

The plugin deep-verification pass added a non-Python entrypoint test and enforced
the `.py` file-type boundary. Existing public checks, the hidden grader, and the
completion verifier then passed. The archive task received no Codex call. Both
source workspaces remained byte-identical under the replay hash contract.

The predeclared functional, routing, preservation, and 250,000-input-token caps
all passed. Total adaptive input was 97,108 tokens.

## Cost interpretation

Selective routing did not yet produce the intended input-token efficiency. On
these same two tasks, using previously published single-run references:

| Metric | H1a | H1a-lite + adaptive replay | Delta |
|---|---:|---:|---:|
| Input tokens | 382,459 | 444,363 | +16.2% |
| Output tokens | 8,309 | 7,833 | -5.7% |
| Wall time | 211.308 s | 208.322 s | -1.4% |

The extra ephemeral Codex process pays for repository rediscovery, making the
risky case expensive even though the passing case is skipped. These references
are not temporally paired, so the table is descriptive rather than causal.

## Decision

Keep the adaptive direction, because the mechanism distinguished missing versus
covered verification dimensions and repaired the observed false completion.
Do not claim a reliability-cost win yet. The next implementation should avoid
full rediscovery by passing a compact evidence packet to a focused verifier or
continuing within an existing model session, then repeat on more development
tasks before freezing held-out policy.

## Limitations

- Both tasks are development cases and the plugin failure was already known.
- Historical workspaces were replayed instead of running a fresh randomized
  comparison.
- Only one deep-verification model call was measured.
- No held-out reliability or general efficiency claim is supported.

