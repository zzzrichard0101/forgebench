# Adaptive Session Reuse Evaluation v0.1

Date: 2026-08-18  
Status: **functional gate passed; total-input efficiency gate failed**

## Result

ForgeBench resumed the original H1a-lite Codex session inside a copied adaptive
workspace. The known accepted false completion changed from hidden fail to pass,
all four public plugin checks passed, and the source workspace hash remained
unchanged.

The predeclared efficiency target did not pass. Codex reports cumulative usage
for resumed sessions, so adaptive usage is calculated as the resumed cumulative
trace minus the source turn usage.

Source run: `3ba463d2bff1464bba1d0a035a39182c`  
Adaptive run: `78c8b3bfe6444cdab0fa60ece621b1e4`

| Metric | Fresh Evidence Packet v0.2 | Resumed session | Delta |
|---|---:|---:|---:|
| Hidden task after verification | Pass | Pass | Preserved |
| Additional input tokens | 64,921 | 94,539 | +45.6% |
| Additional cached input tokens | 56,320 | 87,040 | +54.5% |
| Additional uncached input tokens | 8,601 | 7,499 | -12.8% |
| Output tokens | 1,847 | 1,691 | -8.4% |
| Wall time | 47.224 s | 50.582 s | +7.1% |
| Input cache ratio | 86.8% | 92.1% | +5.3 pp |

The resumed turn used a 2,388-character Evidence Packet and the same
`gpt-5.6-sol` medium-reasoning configuration. It added the required directory
and non-Python regular-file tests, enforced an in-root regular `.py` entrypoint,
and made no unrelated change.

## Interpretation

Session reuse preserved useful context, as shown by fewer uncached input and
output tokens. However, the retained conversation also increased total input
tokens enough to fail the frozen `< 64,921` acceptance criterion. Without a
predeclared price model, the higher cache ratio is not converted into a monetary
cost claim.

## Decision

Do not make session reuse the default adaptive path. Keep the fresh Evidence
Packet v0.2 process as the current reference because it uses fewer total input
tokens and is slightly faster. Retain session reuse as an auditable experimental
mode and move the next optimization to deterministic probe-first routing, where
the model is called only after a generated probe exposes a concrete failure.

## Measurement correction

The first emitted replay summary showed the cumulative session totals (345,044
input and 5,681 output). The correct adaptive increments subtract the source
turn (250,505 input and 3,990 output). The runner now accepts explicit input,
cached-input, and output offsets, records both cumulative trace and delta usage,
and rejects impossible offsets. A regression test covers this behavior.

## Limitations

- This is one known development failure, not held-out evidence.
- Fresh and resumed runs were not a randomized pair.
- Total token counts do not equal billed cost when cached input has a different
  price.
- One run cannot estimate variance.

