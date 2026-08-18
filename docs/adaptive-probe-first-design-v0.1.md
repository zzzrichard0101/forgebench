# Adaptive Probe-First Design v0.1

Date: 2026-08-18  
Status: **mechanism implemented; live development replay reported**

## Question

Can ForgeBench replace model-led boundary rediscovery with deterministic public
probes, then allocate a model turn only when a probe exposes a concrete defect?

## Flow

1. The existing Completion Risk Gate evaluates public completion evidence.
2. A high-risk attempt is copied into an isolated adaptive workspace.
3. A task adapter runs deterministic probes derived from the public contract.
4. If every supported probe passes, adaptive verification short-circuits with
   zero model tokens.
5. If a probe fails or errors, Codex receives Evidence Packet v0.2 plus the
   bounded probe result and gets one repair attempt.
6. Unsupported tasks fall back to the existing packet path.

## v0.1 scope

The first adapter covers the public `python-plugin-boundary` file-type contract.
It checks two generic cases already frozen by Evidence Packet v0.2:

- a directory used as a `.py` entrypoint;
- a regular non-Python file used as an entrypoint.

A process exit of `3` means the invalid input was accepted and is reported as a
probe failure. Other nonzero exits are probe infrastructure errors and are not
presented as proof of a product defect. Probe output is capped, trace-visible,
and executed with a 15-second timeout.

This adapter executes trusted benchmark code in a subprocess. It is not yet a
general untrusted-repository sandbox and must not be marketed as one.

## Frozen evaluation

The predeclared configuration is
`experiments/configs/adaptive-probe-first-v0.1.json`. The known development
false completion must produce a failing non-Python-file probe before the model
call, then pass the hidden task after at most one repair. Additional input must
be below the fresh Evidence Packet reference of 64,921 tokens.

A separate deterministic mechanism test uses a correct implementation whose
public tests still omit the file-type cases. The risk gate remains high, both
probes pass, and the model call must be skipped with zero model tokens.

## Leakage boundary

The adapter uses the public task ID, public `load_plugin` API, and the public
contract dimensions. It does not read hidden graders, author metadata, secrets,
or protected-file contents. Because the adapter was developed using a known dev
failure, neither its routing accuracy nor repair result can count as held-out
evidence.

The observed outcome is recorded separately in
`docs/adaptive-probe-first-report-v0.1.md`; the frozen criteria above remain
unchanged.
