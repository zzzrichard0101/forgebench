# Baseline Report v0 — Infrastructure Readiness

Date: 2026-08-16  
Status: **first invocation excluded; authentication refresh required**

## What is validated

- copy-isolated workspaces preserve the seed repository;
- typed read/write/list/search tools emit append-only events;
- path escape attempts are rejected and recorded;
- step-budget exhaustion has an explicit termination reason;
- the intentionally defective cart fixture fails its hidden invariant;
- the known-good fix passes public, hidden, and workspace-policy checks;
- mutating the protected dependency file fails independently of code correctness;
- external agent stdout/stderr, command manifest, workspace, and grade are retained.

The current local suite contains 16 dependency-free tests. This report does not
claim agent performance because the scripted adapter and known-good fixture are
infrastructure controls, not evaluated models.

## Reference baseline protocol

The first real run will use the installed Claude Code CLI against the public
`python-cart-rounding` task. The invocation is non-interactive, disables session
persistence and customizations, constrains tools, copies the seed into a unique
workspace, and runs hidden graders only after the CLI exits.

The project also reserves a Codex reference path. Official OpenAI documentation
defines `codex exec` as the stable non-interactive command, supports JSONL events,
an ephemeral session, an explicit workspace root, and the `workspace-write`
sandbox. It also warns against bypassing approvals and sandboxing except inside
an externally hardened environment:

https://learn.chatgpt.com/docs/developer-commands?surface=cli

The installed Windows-app Codex executable is currently visible but cannot be
started from this managed shell (`Access denied`). This is recorded as an
environment constraint, not a model failure.

## Next measurement

### Attempt 0 — infrastructure failure

| Field | Value |
|---|---|
| Run ID | `cedd8696e4004e3585c963a30d60e5e7` |
| Requested alias | `sonnet` |
| Resolved model reported at init | `claude-sonnet-5` |
| Claude Code version | `2.1.206` |
| Outcome | OAuth session expired; refresh failed before inference |
| API/model turns | 0 |
| Reported cost | USD 0 |
| Metric eligibility | excluded — authentication infrastructure failure |
| Grader outcome | expected seed failure; workspace was unchanged |

This attempt proves that `auth status: loggedIn` is not sufficient readiness
evidence: a stale OAuth session may still fail on the first request. Future run
preflight must perform an authenticated no-op or classify this terminal reason
before adding the run to an agent-performance denominator.

After the user refreshes Claude authentication:

1. run one `sonnet` smoke baseline;
2. retain the exact model identifier reported in stream JSON;
3. grade without revealing hidden checks;
4. inspect trace completeness and permissions;
5. decide whether the CLI path is suitable for the 30-task baseline or whether
   an API adapter is required for tighter harness ablations.
