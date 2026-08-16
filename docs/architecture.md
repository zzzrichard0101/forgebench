# Architecture v0.1

```text
Seed repository ──copy──> run workspace
                              ↑
Task instruction → AgentRunner → ModelAdapter
                         ↓            ↑
                    ToolGateway ──────┘
                         ↓
                 append-only TraceWriter
```

## Trust boundaries

- `ModelAdapter` receives only the task, prior bounded tool observations, and tool schemas.
- `ToolGateway` resolves every path against the copied run workspace.
- Commands use an argument array with `shell=False` and an explicit executable allowlist.
- The seed repository is never modified; each run owns a new copy.
- The append-only trace lives beside, not inside, the model-visible workspace.
- Hidden graders are intentionally absent until Phase 3.

## Replaceable boundaries

`ModelAdapter` isolates provider APIs from harness logic. The deterministic
`ScriptedModelAdapter` exists for infrastructure tests only and cannot produce a
benchmark claim. Provider adapters added later must expose an exact model ID and
usage metadata.

`ToolGateway` is intentionally small. New tools require a typed schema, bounded
output, workspace-policy tests, and a trace representation before they can be
enabled for evaluated runs.

