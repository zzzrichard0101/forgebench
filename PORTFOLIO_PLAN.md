# KRAFTON AI Agent Engineer 지원 포트폴리오 구축 계획

> 목표 포지션: `[AI Research Div.] AI Agent Engineer (2년 이상)`  
> 계획 기준일: 2026-08-16  
> 기본 가정: 주 12~15시간, 10주. 유료 모델 API 예산과 현재 경력은 아직 미확정이다.

## 0. 최종 실행 결과 (2026-08-23)

계획의 핵심 구현·평가 트랙은 종료됐다. ForgeBench는 결과에 맞춰 기준을
바꾸지 않고 두 개의 음성 결론을 봉인했다.

- V1: 30개 held-out base와 120개 policy replay에서 선택적 검증의 신뢰성
  개선 가설이 기각됐다. 0/30 복구, Verify-All hard-safety 위반 1건을 공개했다.
- V2: 네 차례 screening wave의 90개 Codex 슬롯 중 84개를 외부 grader로
  평가했다. 최종 false-completion 다양성은 4개 task cluster와 3개
  mechanism으로, 사전 기준 6개와 4개에 미달했다.
- 종료 결정: Stage B는 활성화하지 않으며 Wave 5와 threshold 완화도 하지
  않는다. 향후 재시도는 별도의 신규 preregistration과 독립 데이터가
  있을 때만 가능하다.
- 공개 품질: 207개 회귀 테스트, content-addressed catalog/corpus/oracle,
  저장소 외부 private grader·label, 결과 기반 재실행 금지를 유지했다.

따라서 남은 작업은 새로운 실험이 아니라 지원 자료, 데모, README와
면접 설명을 이 최종 결과에 맞게 유지하는 것이다.

## 1. 채용공고를 포트폴리오 언어로 번역하기

이 포지션이 확인하려는 핵심은 “LLM API로 에이전트를 만들 수 있는가”가 아니다. **복잡한 과제를 끝까지 수행하는 에이전트의 실패를 측정하고, 하네스를 바꿔 성능을 반복적으로 개선할 수 있는가**다.

| 채용 신호 | 포트폴리오에서 보여줄 증거 |
|---|---|
| Claude Code·Codex 활용 | 실제 개발 로그, 에이전트 지시 파일, 작업 분해 방식, 사람이 개입한 지점과 이유 |
| Agent 제품 개발 | 사용자가 실행 가능한 CLI/웹 데모, 안정적 실행, 실패 복구, 문서와 테스트 |
| Planning | 계획 생성·검증·재계획 정책과 ablation 결과 |
| Memory | 작업 기억/장기 기억의 저장·검색·갱신 정책과 오염·구식 정보 테스트 |
| Tool Use | typed tool schema, 권한 경계, timeout/retry, 관찰 결과 정규화 |
| Loop | 종료 조건, stuck detection, budget 관리, false-completion 방지 |
| Evaluation | 자체 benchmark, 자동 채점기, trace 기반 failure taxonomy, 통계와 회귀 테스트 |
| Meta-Harness | 실행 trace와 score를 이용해 prompt/policy/config 후보를 제안·평가하는 outer loop |
| 오픈소스 분석 | KIRA + OpenClaw 또는 Hermes의 비교 분석, 재현 실험, 작은 upstream 기여 |
| Production | 관측성, 비용·지연, 보안, idempotency, 배포·rollback, 장애 회고 |
| 책임감·소통 | 명확한 milestone, ADR, 실험 보고서, issue/PR 기록, 영어 요약 |

## 2. 포트폴리오의 한 문장

**“저는 에이전트를 데모로 끝내지 않고, 실패를 재현 가능한 benchmark로 바꾸고, trace 기반으로 harness를 개선해 실제 성능 향상을 증명하는 엔지니어입니다.”**

모든 산출물은 이 문장을 증명해야 한다. 프로젝트 수를 늘리는 대신 하나의 flagship 시스템을 깊게 만들고, 오픈소스 분석과 production 운영 기록을 그 시스템에 연결한다.

## 3. Flagship 프로젝트 — ForgeBench

### 3.1 문제 정의

`ForgeBench`는 작은 소프트웨어 저장소에서 발생하는 장기 실행 업무를 수행하는 coding/work agent와 그 평가 시스템이다. 단순 코드 생성 대신 다음과 같은 실무형 과제를 다룬다.

- 버그 재현 → 원인 분석 → 수정 → 테스트 → 완료 검증
- 서로 다른 파일에 걸친 기능 추가와 회귀 방지
- 로그/문서/코드를 함께 조사하는 incident triage
- 모호하거나 충돌하는 요구사항 처리
- 오래된 기억, 실패하는 tool, timeout, 부분 성공이 포함된 과제
- 선택 사항: 게임 제작 도메인 pack(밸런스 데이터 검증, asset metadata 정리, gameplay telemetry 분석)

초기 component ablation 이후 핵심 연구 질문을 다음과 같이 좁힌다.

> 모든 작업에 비싼 검증을 적용하지 않고, false completion 위험이 높은
> 완료 시도만 선택적으로 깊게 검증해 reliability와 비용을 함께 개선할
> 수 있는가?

H0 8/10, H1a 10/10, H1a-lite 9/10의 흐름과 H1a-lite에서 실제로 관찰한
completion-acceptance failure를 출발점으로 삼는다. 기존 planning, context,
recovery 결과는 이 질문을 지지하는 구성요소 증거로 유지한다.

### 3.2 시스템 범위

```text
Task Spec
   ↓
Planner ──→ Plan Verifier / Replanner
   ↓
Agent Loop ──→ Tool Gateway ──→ isolated workspace
   ↕                ↕
Working Memory   policy / timeout / retry
   ↓
Completion Verifier
   ↓
Completion Risk Gate
   ├─ Low risk ────────────────┐
   └─ High risk → Deep Verification / Repair
                               ↓
Final Artifact → Trace Store → Hidden Evaluator → Experiment Report
```

MVP에서 반드시 구현할 것:

- Codex model adapter와 고정 가능한 model/config manifest
- filesystem/shell/search/test 도구와 structured result
- step·token·시간·비용 budget
- 계획, 재계획, 종료 및 escalation 정책
- append-only event trace와 replay 가능한 run manifest
- deterministic grader + completion risk gate + selective deep verification
- baseline과 개선 harness 사이의 재현 가능한 실험 runner
- 최소한의 대시보드 또는 정적 HTML report

후순위로 둘 것:

- 화려한 multi-agent orchestration
- 과도한 웹 UI
- vector DB를 사용했다는 사실 자체
- 모델 fine-tuning
- learned risk classifier와 자동 meta-harness search
- 두 번째 model adapter(최종 transfer 예산이 확보되면 추가)

### 3.3 Benchmark 설계

#### Task set

- 최소 30개의 감사된 task: 현재 10개는 development discovery set으로 유지
- boundary, invalid input, unsupported case, protected evidence, incomplete
  verification, hidden generalization 범주를 의도적으로 포함
- 별도 stratified held-out set은 risk rule과 threshold를 동결한 뒤에만 실행
- 각 task는 `task.yaml`, seed repo, setup script, grader, expected invariants를 가진다.
- task 작성자 의도를 숨긴 채 다른 사람이 재실행할 수 있어야 한다.

#### 평가 지표

| 축 | 핵심 지표 |
|---|---|
| 정확성 | task success rate, pass@1, invariant pass rate |
| 완수성 | false-completion rate, unfinished-artifact rate |
| 견고성 | tool failure recovery, timeout recovery, repeated-run variance |
| 효율 | 성공당 token 비용, wall-clock time, tool-call 수 |
| 일반화 | held-out task/model 성능, 난이도별 성능 |
| 안전 | 금지된 파일/명령 접근, 불필요한 변경, secret 노출 시도 차단 |

Adaptive verification에는 `true success`, `accepted false completion`,
`detected failure`, escalation rate, unnecessary escalation rate를 별도로
보고한다. completion gate 통과와 hidden grader 실패를 혼동하지 않는다.

LLM judge만으로 성공을 판정하지 않는다. 가능한 항목은 테스트, 파일 상태, schema, command exit code 등의 deterministic grader로 평가하고, 품질처럼 기계 판정이 어려운 항목만 사전 정의 rubric을 가진 judge로 보완한다.

#### 실험 규칙

- Baseline: 최소 ReAct loop + 동일 모델 + 동일 도구
- 모든 비교에서 model/version, temperature, task set, budget 고정
- stochastic run은 task당 최소 3회 반복
- 평균만 쓰지 않고 bootstrap 95% CI 또는 paired 결과 제시
- 비교 정책: `H0`, `H1a`, `H1a-lite`, `H1a-adaptive`
- H1a-adaptive risk rule, threshold, escalation action은 held-out 실행 전에 동결
- 실패 trace를 최소 6개 범주로 라벨링: planning, context/memory, tool, verification, recovery, budget
- test set은 설계 완료 후 동결하고 최종 2회만 실행

### 3.4 목표 결과(사전에 선언하되 조작하지 않기)

- H1a-lite 대비 accepted false completion 감소
- H1a에 실질적으로 가까운 held-out reliability
- H1a 대비 aggregate token과 wall time의 유의미한 절감
- tool 장애 주입 task의 recovery success `70% 이상`
- 적어도 한 개선이 두 번째 모델에서도 방향성 재현

목표 미달도 숨기지 않는다. 개선되지 않은 실험은 “무엇이 왜 통하지 않았는가”를 보여주는 강한 연구·엔지니어링 증거다.

## 4. 보조 산출물 2개

### A. Open-source Agent Harness Teardown

KIRA를 중심으로 OpenClaw 또는 Hermes 하나를 더 골라 비교한다.

- 동일 task subset과 동일 모델 예산에서 재현
- loop, context policy, completion check, tool interface, recovery 정책 비교
- 핵심 코드 경로를 architecture map으로 설명
- 관찰한 실패 10건 이상을 trace와 함께 분류
- 한 가지 개선을 fork에서 구현하고 전후 수치 제시
- 가능하면 문서·테스트·bug fix 형태의 upstream PR 1건

최종 산출물: 한국어 기술 글 1편, 영어 executive summary 1편, 재현 스크립트, 결과 CSV.

### B. Production Readiness Case Study

ForgeBench를 작은 서비스로 운영하며 production 기준을 증명한다.

- queue 기반 비동기 실행과 idempotency key
- sandbox/allowlist, secret redaction, destructive action gate
- retry/backoff, timeout, cancellation, checkpoint/resume
- trace/span, 비용·latency·success dashboard
- prompt/model/config versioning과 rollback
- 장애 주입 3종 및 postmortem 1편
- 7일 이상 지속 실행 또는 100회 이상의 누적 run 결과

실사용자가 없다면 “사용자 수”를 꾸미지 말고, 재현 가능한 load/failure test와 운영 의사결정을 증거로 쓴다.

## 5. 10주 실행 로드맵

| 주차 | 빌드 | 검증과 공개 산출물 | 통과 조건 |
|---|---|---|---|
| 1 | 공고·연구 정리, 문제/metric/task schema 확정 | 2쪽 design brief, skill-gap matrix | 프로젝트 한 문장과 평가 지표가 고정됨 |
| 2 | isolated runner, tool gateway, model adapter, trace schema | architecture diagram, ADR 2개 | 예제 task 5개가 end-to-end 실행됨 |
| 3 | 최소 loop와 deterministic grader | baseline report v0 | 동일 run을 재현하고 원인을 추적 가능 |
| 4 | benchmark 30개, failure taxonomy | dataset card, labeling guide | grader mutation test 통과, dev/test 분리 |
| 5 | planning·replanning·completion verifier | ablation report 1 | false completion 전후 수치 확보 |
| 6 | memory·context policy·tool recovery | ablation report 2 | 장애 주입 결과와 비용 trade-off 확보 |
| 7 | Completion Risk Gate와 selective deep verification | adaptive design + ablation report | risk decision과 escalation이 trace로 재현됨 |
| 8 | 최소 30개 completion-risk benchmark 완성 | frozen held-out manifest | rule/threshold 동결, 데이터 누수 점검 |
| 9 | service화, 관측성, 안전·복구 | demo URL/영상, postmortem | 100-run 또는 7-day 운영 증거 |
| 10 | 최종 held-out 평가와 지원 패키지 | report, README, 5분 demo, 1-page PDF | 제3자가 15분 내 재현 시작 가능 |

주당 권장 리듬:

- 60% 구현 및 테스트
- 20% benchmark/실험
- 10% trace review와 실패 라벨링
- 10% 문서·영상·영어 요약

## 6. 저장소와 공개 결과물 구조

```text
forgebench/
├─ README.md                 # 30초 요약, 핵심 숫자, 5분 quickstart
├─ docs/
│  ├─ architecture.md
│  ├─ experiment-protocol.md
│  ├─ failure-taxonomy.md
│  ├─ production-readiness.md
│  └─ adr/
├─ agent/
│  ├─ loop/
│  ├─ planning/
│  ├─ memory/
│  ├─ tools/
│  └─ verification/
├─ benchmark/
│  ├─ tasks/
│  ├─ graders/
│  └─ dataset-card.md
├─ experiments/
│  ├─ manifests/
│  ├─ ablations/
│  └─ reports/
├─ meta_harness/
├─ tests/
├─ demo/
├─ SECURITY.md
└─ Makefile
```

공개 저장소 첫 화면에 반드시 보일 것:

1. 해결한 문제와 왜 어려운지
2. baseline → best harness 핵심 수치 표
3. 60~90초 GIF 또는 5분 이하 영상
4. architecture 그림
5. 재현 명령 3개 이하
6. 대표 실패 사례와 개선 전후 trace
7. 한계, 비용, 재현 조건, 다음 실험

## 7. 지원 패키지

### GitHub pinned 구성

1. `forgebench`: flagship code + benchmark + report
2. `agent-harness-teardown`: KIRA/OpenClaw 또는 Hermes 분석과 재현
3. 기존 실서비스 프로젝트 중 가장 강한 1개. 없다면 ForgeBench 운영 case study를 별도 문서로 강조

### 포트폴리오 문서 목차(8~12쪽)

1. 1쪽 — 지원자 소개와 핵심 성과 숫자 3개
2. 2쪽 — 문제와 왜 기존 agent loop가 실패했는지
3. 2쪽 — architecture와 주요 설계 결정
4. 2쪽 — benchmark, grader, 실험 프로토콜
5. 2쪽 — ablation 결과와 실패 분석
6. 1쪽 — production·안전·비용
7. 1쪽 — 오픈소스 분석/기여와 배운 점
8. 1쪽 — 한계와 크래프톤에서 이어갈 연구 질문

### 이력서 bullet 공식

`문제/규모 + 본인의 구체적 설계·행동 + 검증 방법 + 수치 결과 + production 영향`

예시(실제 수치로 교체):

> 30개 completion-risk coding task와 deterministic hidden grader를 설계하고,
> 저비용 policy의 false completion을 선택적으로 탐지하는 adaptive verification
> gate를 구현해 동일 Codex·budget 조건에서 reliability-cost trade-off를 개선함.

### 면접 대비 질문

- 왜 이 benchmark가 실제 업무를 대표하는가?
- grader 자체의 오류는 어떻게 검증했는가?
- 가장 효과가 없었던 harness 변경과 그 이유는?
- 모델 성능 향상과 harness 향상을 어떻게 분리했는가?
- memory가 도움이 된 경우와 해가 된 경우는?
- agent가 “완료했다”고 거짓 판단하는 것을 어떻게 탐지했는가?
- 비용을 두 배 쓰면 얻는 성능과 production에서의 선택은?
- Risk Gate가 관찰한 plugin failure나 dev set에 과적합되지 않았다는 증거는?
- 악의적 repo/task가 tool을 통해 할 수 있는 피해를 어떻게 제한했는가?
- Claude Code/Codex를 개발에 사용했을 때 사람이 맡은 판단은 무엇인가?

## 8. 품질 기준과 피해야 할 포트폴리오

### 제출 기준

- 새 환경에서 quickstart와 핵심 실험이 재현된다.
- 모든 표가 raw result와 run manifest까지 추적된다.
- cherry-picking 없이 실패 run과 결측치를 설명한다.
- secrets, 라이선스, 데이터 출처, 모델·비용이 공개된다.
- README의 주장은 test 또는 trace로 연결된다.
- AI coding agent 사용 내역은 숨기지 않고, 검증·리뷰 과정을 설명한다.

### 피할 것

- LangChain/LangGraph를 연결한 챗봇을 “agent engineering”으로 포장
- benchmark 없이 “정확도가 좋아졌다”고 주장
- 같은 task를 보며 prompt를 반복 수정한 뒤 test 성능으로 제시
- 모델과 budget을 바꾸고 harness 개선으로 해석
- LLM judge 하나만으로 자기 agent를 평가
- multi-agent라는 구조 자체를 성과로 제시
- 화면은 화려하지만 실패 복구, trace, test가 없는 데모
- 공개할 수 없는 회사 경험을 근거 없이 큰 숫자로만 서술

## 9. 범위 조정 규칙

- 주 8시간 이하: task 30개, model 1종, meta-harness는 offline prototype으로 축소
- API 예산이 작음: 소형 모델로 개발하고, 최종 test subset만 frontier model로 실행
- production 경험이 충분함: 보조 B를 줄이고 기존 경력의 architecture·incident·metric을 익명화해 연결
- 연구 경험이 충분함: 구현보다 benchmark validity와 통계 검증을 강화
- 지원 마감이 4주 이내: 1~3주에 baseline/benchmark 20개/핵심 개선 하나, 4주에 report와 demo 완성

## 10. 시작 전에 채워야 할 개인 정보

아래 정보에 따라 난이도와 강조점을 다시 산정한다.

- 총 경력과 최근 2년의 역할/기술 스택
- 실제 LLM/Agent 프로젝트와 production 운영 경험
- 공개 가능한 코드·성과·문서
- Python/backend/infra/ML research 역량의 상대적 강약
- 영어 기술 글쓰기와 논문 재현 경험
- 주당 투자 시간, 지원 목표일, API/GPU 예산
- 선호 방향: coding agent / 업무 자동화 agent / game·multimodal agent

## 11. 참고한 KRAFTON AI 공개 신호

- Terminus-KIRA: 최소 terminal harness의 실패를 trace로 분석하고 completion check, replanning, interface를 고쳐 약 10%p 성능 향상을 보고  
  https://www.krafton.ai/blog/posts/2026-02-20-terminus_kira/terminus-en.html
- Meta-Harness: 이전 후보의 source, score, trace 전체를 사용해 harness code를 outer-loop에서 최적화  
  https://www.krafton.ai/portfolio/meta-harness-end-to-end-optimization-of-model-harnesses/
- Orak: MCP 기반 plug-and-play game-agent benchmark와 agentic module 분석  
  https://krafton.ai/portfolio/orak-a-foundational-benchmark-for-training-and-evaluating-llm-agents-on-diverse-video-games-2/
- OAKS: 지속적으로 변하는 지식에서 memory/adaptation 실패를 측정  
  https://www.krafton.ai/portfolio/can-large-language-models-keep-up-benchmarking-online-adaptation-to-continual-knowledge-streams/
- Prompt-to-Policy: write → train → judge → revise loop, experiment lineage, dual judge와 guardrail  
  https://www.krafton.ai/blog/posts/2026-04-03-prompt-to-policy/prompt-to-policy_en.html
- Online Agent-as-a-Judge: 수동 평가가 놓치는 행동을 상황 생성 evaluator로 유도하고 trajectory evidence로 평가  
  https://krafton.ai/portfolio/online-agent-as-a-judge-situation-generating-evaluation-for-interactive-agents/
