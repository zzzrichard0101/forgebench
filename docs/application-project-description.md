# ForgeBench application project description

## 30-second introduction

ForgeBench is a reproducible harness and benchmark laboratory for long-horizon
coding agents. I built planning and completion contracts, an isolated tool
loop, bounded recovery, deterministic probes, hash-bound replay, and an
external hidden-evaluation firewall. I ran two preregistered research tracks.
The V1 selective-verification claim failed, and the V2 90-slot screening
population did not reach its diversity gate. I sealed both negative results
instead of tuning policies, datasets, or thresholds against private outcomes.

## Resume bullets

- Built a Codex-based agent harness laboratory with isolated workspaces, typed
  tool execution, append-only traces, deterministic completion checks, bounded
  recovery, and selective model-verification policies; maintained 207 automated
  regression tests at the final checkpoint.
- Designed two leakage-controlled evaluation programs: V1 bound 30 held-out
  bases and 120 policy replays, while V2 executed 90 frozen Codex slots and
  externally graded all 84 publicly eligible bases across 30 task lineages.
- Rejected the V1 reliability claim after 0/30 recoveries and one Verify-All
  hard-safety regression; later stopped V2 before Stage B when the immutable
  population reached only 4/6 false-completion clusters and 3/4 mechanisms.

## Korean project summary

ForgeBench는 coding agent의 planning, tool use, completion loop, recovery와
추가 검증 정책을 재현 가능하게 비교하는 Agent Harness 실험실입니다. 동일한
base workspace를 정책 간 공유하고, 모델·도구·예산을 고정하며, 공개 completion
gate와 저장소 외부 hidden grader를 분리합니다. 모든 catalog, 실행 계획,
workspace, grader와 결과 envelope는 SHA-256으로 결합됩니다.

V1에서는 공개 gate를 통과한 base 30개와 model-policy replay 120개를
평가했지만 hidden success는 하나도 만들지 못했습니다. Risk-Hierarchical은
실패 9개를 선택했지만 0/30 복구였고, Verify-All은 hard-safety 위반 1건을
추가했습니다. 선택적 검증의 신뢰성 개선 가설을 기각했습니다.

V2에서는 repair-development population의 실행가능성을 먼저 검증했습니다.
네 차례 wave에서 90개 Codex 슬롯을 고정 실행했고, 공개 기준을 통과한 84개를
외부 grader로 평가했습니다. 최종 population은 passing-control cluster 27개를
확보했지만 false-completion cluster 4개와 mechanism 3개에 머물러 사전 기준
6개와 4개를 충족하지 못했습니다. 마지막 Wave 4의 28개 base는 hidden
grader에서도 모두 성공했습니다. 결과를 보고 Wave 5를 만들거나 기준을
낮추지 않고 Stage B를 차단했습니다.

이 프로젝트의 주장은 특정 harness가 더 우수하다는 것이 아닙니다. 모델 실행,
공개 판정, 비공개 평가와 연구 의사결정을 분리해 지원되지 않는 주장을 실제로
거부할 수 있는 시스템을 구현했다는 것입니다.

## English executive summary

ForgeBench is a reproducible laboratory for coding-agent harness research. It
holds models, tools, budgets, and base workspaces constant while making
planning, completion, recovery, probes, routing, and evaluation traceable. V1
rejected a selective-verification claim after zero recoveries across 30
held-out failures. V2 then executed 90 frozen screening slots and externally
graded 84 eligible bases, but reached only four false-completion clusters and
three failure mechanisms against preregistered minima of six and four. The
project contributes an auditable system that can stop unsupported research,
not a post-hoc reliability-improvement claim.

## Role-fit evidence

| Job signal | Evidence in ForgeBench |
| --- | --- |
| Coding-agent proficiency | Codex CLI runner, frozen model manifests, 90-slot V2 execution, trace and token accounting |
| Planning and loop | structured plan contracts, completion gates, bounded repair and termination |
| Tool use and safety | isolated workspaces, typed tool boundary, protected-file detection and safety regression reporting |
| Evaluation | deterministic public gates, external hidden graders, three-repeat audits, immutable decision gates |
| Benchmark engineering | 30 V2 task lineages, 84 external grades, catalog/corpus/oracle content hashes |
| Meta-harness thinking | common-base policy replay, routing analysis, and explicit separation of selection from intervention quality |
| Communication and ownership | two rejected claims, preserved failures, terminal stop rule, limitations and costs disclosed |

## Interview answers

### What is the strongest result?

The strongest result is methodological: ForgeBench enforced boundaries strong
enough to reject its own claims twice. V1 kept 150 evaluation targets bound
through replay and private grading. V2 retained all 90 frozen slots and stopped
before Stage B when the development population failed the preregistered
diversity gate.

### Why did the V1 policy fail?

The held-out population was entirely false completion, risk routing covered
only 9/30 failures, transferable probes supported none of those selected
routes, and model verification repaired 0/57 attempted cases across the
model-backed policies. Selection quality could not compensate for an
ineffective intervention.

### Why did the V2 feasibility gate fail?

The missing quantity was diverse false completion, not passing controls. After
Wave 3 the population still lacked two false-completion clusters and one
mechanism. A final balanced ten-task Wave 4 produced 28 publicly eligible bases,
and all 28 also passed private grading. Combined diversity therefore stayed at
4/6 clusters and 3/4 mechanisms. That is evidence that the proposed Stage B
experiment was not supportable with this development population.

### Why is this still portfolio-worthy?

Agent engineering requires knowing whether a harness or benchmark supports a
claim. ForgeBench demonstrates isolation, evaluation firewalls, task and
grader audits, crash-resilient execution, traceability, failure preservation,
and the judgment to stop. These capabilities transfer directly to agent
benchmark, evaluation, meta-harness, and production reliability work.

### What would you do next?

Do not add Wave 5 or weaken the current thresholds. Preserve this protocol as
closed. A future attempt should begin with a new preregistration, independently
authored tasks and graders, and an explicit strategy for sourcing naturally
occurring diverse completion failures before allocating model verification.
