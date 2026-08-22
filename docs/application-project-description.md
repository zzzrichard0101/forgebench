# ForgeBench application project description

## 30-second introduction

ForgeBench is a reproducible harness and benchmark laboratory for long-horizon
coding agents. I implemented planning and completion contracts, an isolated
tool loop, bounded recovery, deterministic probes, risk-based model escalation,
hash-bound replay, and an external hidden-evaluation firewall. The final
held-out hypothesis failed: 120 model-policy replays recovered no hidden
failure, and Verify-All introduced one hard-safety regression. I froze and
published that negative result rather than tuning against the test set.

## Resume bullets

- Built a Codex-based agent harness laboratory with isolated workspaces, typed
  tool execution, append-only traces, deterministic completion checks, bounded
  recovery, and selective model-verification policies; maintained 130 automated
  regression tests at the final held-out checkpoint.
- Designed a leakage-controlled shared-base experiment covering 30 base
  trajectories and 120 model-policy replays, binding 150 evaluation targets by
  SHA-256 before joining external hidden outcomes.
- Rejected the predeclared selective-verification claim after task-clustered
  analysis showed 0/30 P5 recoveries despite 9 model calls and 504,339 input
  tokens; disclosed one Verify-All hard-safety regression and preserved private
  graders and trajectory outcomes outside Git.

## Korean project summary

ForgeBench는 coding agent가 “완료했다”고 판단한 뒤 어떤 작업에 추가 검증
비용을 배분해야 하는지를 연구하는 Agent Harness 실험실입니다. 동일한 base
workspace를 여러 정책에 재사용하고, 모델/도구/예산을 고정하며, planning,
tool use, completion loop, recovery, deterministic probe, risk routing의 영향을
추적합니다. 공개 completion gate와 외부 hidden grader를 분리하고 모든 정책과
평가 대상을 결과 확인 전에 hash로 동결했습니다.

최종 held-out 결과는 가설을 지지하지 않았습니다. 공개 gate를 통과한 base
30개가 모두 hidden failure였고, 120개 model-policy replay 중 성공은 0건이었습니다.
Risk-Hierarchical은 실제 실패 9개를 escalation했지만 하나도 복구하지 못했고,
Verify-All은 추가 비용과 hard-safety 위반 1건만 만들었습니다. 이 결과를 통해
agent evaluation에서 더 많은 test-time compute가 곧 reliability를 의미하지
않으며, probe coverage와 repair action 자체의 품질을 별도로 검증해야 함을
확인했습니다.

## English executive summary

ForgeBench is a reproducible harness laboratory for deciding when a coding
agent's apparent completion warrants additional verification. It holds the
model, tools, budgets, and base workspaces constant while comparing completion,
probe, risk-routing, and model-verification policies. The held-out result was
negative: all 30 public-gate-passing bases failed hidden evaluation, and none of
120 model-policy replays recovered a failure. The project therefore contributes
an auditable evaluation and replay system, not a reliability-improvement claim.

## Role-fit evidence

| Job signal | Evidence in ForgeBench |
| --- | --- |
| Coding-agent proficiency | Codex CLI runner, frozen model manifests, trace and token accounting |
| Planning and loop | structured plan contracts, completion gates, bounded repair and termination |
| Tool use and safety | isolated workspaces, typed tool boundary, protected-file detection |
| Evaluation | deterministic/public gates, external hidden grader, shared-base paired design |
| Benchmark engineering | 10 held-out tasks x 3 trajectories, immutable catalogs, repeated integrity checks |
| Meta-harness thinking | policy candidates evaluated from common traces and artifacts with frozen claim gates |
| Communication and ownership | failed hypothesis, infrastructure recovery, limitations, and cost disclosed in ADR-style reports |

## Interview answers

### What is the strongest result?

The strongest result is methodological rather than a score improvement: 150
evaluation targets remained bound across policy development, model replay, and
external grading, and the system rejected its own primary claim without hidden
data entering routing code.

### Why did the proposed policy fail?

The held-out population was entirely false completion, risk routing covered
only 9/30 failures, the transferable probe supported none of its nine selected
routes, and the model-verification action repaired 0/57 attempted cases across
all model-backed policies. Selection quality alone could not compensate for an
ineffective intervention.

### Why is this still portfolio-worthy?

Agent engineering requires knowing whether a harness actually improves the
system. ForgeBench demonstrates experiment isolation, evaluation firewalls,
traceability, failure preservation, statistical reporting, and the judgment to
stop an unsupported claim. Those capabilities transfer directly to benchmark,
evaluation, and production harness work.

### What would you do next?

Keep this held-out set closed. On development data, first establish a repair
action that succeeds on diverse failure mechanisms and broaden probe adapters
by public contract rather than task ID. Freeze a v2 policy only after mechanism
gates pass, then evaluate it on a new independently authored held-out set.
