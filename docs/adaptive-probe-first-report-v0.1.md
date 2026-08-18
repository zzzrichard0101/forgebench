# Adaptive Probe-First Report v0.1

Date: 2026-08-18  
Status: **predeclared development replay passed**

## Outcome

Run `cafb3099562141ac9601c71c35560931` replayed the known false completion from
source run `3ba463d2bff1464bba1d0a035a39182c` in a fresh isolated workspace. The
Completion Risk Gate routed it high. The public-contract probe then rejected a
directory entrypoint but exposed that a regular non-Python file was still
accepted. This happened before the model call and took 0.094 seconds.

Codex received Evidence Packet v0.2 plus that probe result. One bounded fresh
turn added the missing regular-file and `.py` checks. The public completion
contract and hidden task grader both passed afterward. The source workspace hash
remained `sha256:1157d7a2891f93aef5bb12cf519736a33ce4b07e0db6dbc6c0147c650b5d4062`.

## Comparison

| Metric | Fresh packet reference | Probe-first | Change |
| --- | ---: | ---: | ---: |
| Total input tokens | 64,921 | 47,847 | -26.3% |
| Cached input tokens | 56,320 | 35,072 | -37.7% |
| Uncached input tokens | 8,601 | 12,775 | +48.5% |
| Output tokens | 1,847 | 1,133 | -38.7% |
| Duration | 47.224s | 39.863s | -15.6% |
| Final hidden task | pass | pass | unchanged |

Every frozen acceptance condition in
`experiments/configs/adaptive-probe-first-v0.1.json` passed. A separate
deterministic mechanism test confirms that a correct high-risk workspace makes
both probes pass and skips model construction entirely, recording zero model
tokens.

## Interpretation and limits

This result supports the mechanism claim: a harness can turn a public missing
contract dimension into an executable observation before asking an agent to
repair it, and can avoid the agent call when those probes pass. It also reduced
total context and latency in this replay.

It does not establish a general benchmark improvement. This is one development
task whose failure was known while the adapter was built. The higher uncached
input also means the token totals alone do not justify a price-weighted cost
claim. The next credible step is a frozen multi-task evaluation with adapters
derived only from public contracts and reported separately on development and
held-out tasks.
