# Candidate Skill-Gap Matrix v0.1

This matrix separates evidence already available from evidence ForgeBench must create. Candidate-specific cells remain `TBD` until career information is supplied; no experience is inferred or fabricated.

Scoring rubric:

- `0`: no evidence;
- `1`: learning/demo evidence;
- `2`: independently built and measured;
- `3`: production or research evidence with external verification.

| Hiring signal | Current evidence | Current score | Portfolio target | Planned artifact |
|---|---|---:|---:|---|
| Claude Code/Codex use | TBD | TBD | 2+ | agent instructions, selected transcripts, human-review notes |
| Agent product development | TBD | TBD | 2+ | runnable ForgeBench agent and demo |
| Planning/replanning | TBD | TBD | 2 | H1/H2 implementation and ablation |
| Memory/context engineering | TBD | TBD | 2 | H4 policy, stale-memory tasks, ablation |
| Tool-use engineering | TBD | TBD | 2 | typed gateway, timeout/retry, policy tests |
| Agent loop/completion | TBD | TBD | 2 | H0/H3 comparison, false-completion analysis |
| Benchmark design | TBD | TBD | 2+ | versioned 50-task benchmark and audited graders |
| Evaluation/statistics | TBD | TBD | 2 | paired runs, confidence intervals, raw results |
| Meta-Harness | TBD | TBD | 2 | offline outer-loop prototype and held-out check |
| Open-source agent analysis | TBD | TBD | 2 | KIRA + OpenClaw/Hermes teardown and reproduction |
| Production LLM/Agent | TBD | TBD | 2+ | 100-run/7-day operation, observability, postmortem |
| AX leadership | TBD | TBD | evidence only if real | anonymized adoption case with stakeholder/result evidence |
| Ownership | TBD | TBD | 2+ | milestone history, issue/ADR trail, completed release |
| Communication/English | TBD | TBD | 2 | Korean report, English executive summary, demo talk |
| New-domain adaptation | TBD | TBD | 2 | optional game-production task pack and learning log |

## Candidate information required for calibration

1. Total experience and roles during the last two years.
2. Backend, ML, infrastructure, and frontend stack by proficiency.
3. LLM/agent projects, including users, traffic, latency, cost, and failures if available.
4. Production ownership and incident-response examples.
5. Public repositories, talks, writing, papers, or open-source contributions.
6. Experience with Claude Code, Codex, or similar coding agents.
7. Weekly time, target application date, and model/API budget.

## Interpretation rule

ForgeBench should fill missing evidence, not duplicate strong existing evidence. Once candidate details are known, each row will receive a score and the roadmap scope will be rebalanced toward the weakest job-critical areas.

