# Model-backed Recovery Smoke v0.1

Date: 2026-08-17

Status: **one paired Codex smoke run complete; repetitions pending**

## Question

Can ForgeBench own the tool loop, inject the same first-read timeout, and let
Codex complete a graded artifact with fewer model turns when bounded recovery is
enabled?

Codex was connected through `CodexCliModelAdapter`. Each model turn used
non-interactive `codex exec --json`; Codex returned one typed `tool` or `finish`
action, while ForgeBench executed the tool and supplied the next observation.
This follows the official Codex CLI contract that `--json` emits JSONL events
for non-interactive runs: <https://developers.openai.com/codex/cli/reference>.

## Frozen task and injection

- Read `source.json` through the typed gateway.
- Copy the exact JSON object to `result.json`.
- Never modify `source.json`.
- The first `read_file("source.json")` returns an injected timeout.
- Control: unbounded context, no harness recovery.
- Treatment: bounded context plus one typed transient retry.

The smoke configuration was written before the valid run at
`experiments/configs/model-recovery-smoke-v0.1.json`.

## Valid paired result

Experiment ID: `56db25da77dc4db5aeb9d52dea3cd0aa`

| Metric | H2 off | H2 on | Change |
|---|---:|---:|---:|
| Task passed | yes | yes | no regression |
| Source unchanged | yes | yes | no regression |
| Model calls / steps | 4 | 3 | -25.0% |
| Gateway calls | 3 | 3 | no change |
| Input tokens | 57,088 | 42,119 | -26.2% |
| Output tokens | 113 | 96 | -15.0% |
| Wall time | 26.946 s | 20.159 s | -25.2% |

Control required Codex to observe the timeout and choose the same read again on
the next model turn. Treatment classified the timeout and retried inside the
same harness step, so Codex next saw both the failure and successful observation
and proceeded directly to `write_file`.

No context compaction occurred in this short task, so the comparison isolates
the recovery component rather than claiming a bounded-memory benefit.

## Preserved infrastructure failure

Pilot experiment `89edcda31f2642f0a608486cdeef2a99` is retained as an
infrastructure failure. Codex selected the correct action but wrapped it in the
example label `tool_action`; the first parser version rejected that valid intent.
Both pilot cells stopped after one model call and consumed 28,422 input tokens.
They are excluded from agent metrics, not deleted or replaced.

The parser now requests a direct object and tolerates a single example wrapper;
both forms have unit coverage.

## Interpretation

This run crosses the important boundary from deterministic policy tests to an
actual Codex-controlled decision loop. It shows a plausible benefit: typed
harness recovery removed one model round trip while preserving correctness and
safety.

It is still a one-pair smoke result on a synthetic task. The adapter starts an
ephemeral Codex process for every decision, which is deliberately simple and
expensive. Repeated tasks, additional failure types, and a persistent session or
API adapter are required before making a general recovery-success or production
efficiency claim.
