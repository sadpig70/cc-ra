---
name: cc-ra
description: |
  Claude Code Rust Analyzer v0.2 — Rust 워크스페이스의 고난이도 논리·설계 오류를
  다관점 AI 분석으로 탐지. Clippy 가 잡는 표면적 lint 는 보조 신호로만 사용.

  7 Core Principles:
    ① 기능별 BFS Gantree (모듈 아닌)
    ② PG 역공학 (코드 → Gantree + PPR)
    ③ 코드만 역공학 (설계 문서 차단)
    ④ 공유 분석 (분업 금지)
    ⑤ 사고 포지션 (역할 아닌, 경계 없음)
    ⑥ 심볼릭 코드 추적 (실행 아님)
    ⑦ 분석 자체도 PG 구조

  8 Thinking Positions: Skeptic / Paranoid / Historian / Newcomer /
                       Adversary / Holist / Reductionist / Auditor.
  모두 동일한 feature_tree 를 본다. 영역 분업 없음.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - TaskCreate
  - TaskUpdate
  - TaskList
---

# cc-ra — Claude Code Rust Analyzer v0.2

---

## 진입

```
/cc-ra <workspace-path> [옵션]
```

### 옵션
- `--scope <glob>` — 분석 범위 한정
- `--since-commit <ref>` — git 변경 파일만
- `--positions <list>` — 활성 포지션 (기본: 8개 전부)
- `--config <path>` — config 경로 (기본: `<workspace>/.cc-ra/config.toml`)
- `--threshold <float>` — confidence cutoff (기본: 0.4)
- `--no-static` — cargo check/clippy 스킵

### 입력 없으면
`/cc-ra` 만 — 현재 working directory 가정.

---

## 실행 흐름 (8 Phases)

```
[Phase 0]   환경 점검 + .cc-ra/ 준비
[Phase 1]   Context Build          → phases/01_context_build.md
[Phase 1.5] Feature Reverse-Engineering ★ → phases/01_5_feature_reverse.md
[Phase 2]   Hypothesis Generation  → phases/02_hypothesis.md
[Phase 2.5] Scenario Derivation ★  → phases/02_5_scenario_derive.md
[Phase 3]   Position Analysis (8 병렬) ★ → phases/03_position_analysis.md
[Phase 3.5] Design Drift ★         → phases/03_5_design_drift.md
[Phase 4]   Triage                 → phases/04_triage.md
[Phase 5]   Report                 → phases/05_report.md
```

★ = v0.2 신규 phase

---

## Bundled References

cc-ra 는 외부 스킬 설치 여부와 무관하게 자급자족 실행되도록 필요한 레퍼런스를 번들한다.

| Reference | File | 언제 읽나 |
|-----------|------|---------|
| **PG (PPR/Gantree) notation** | [references/pg.md](references/pg.md) | Phase 1.5 (feature_tree 생성), Phase 3 (symbolic trace 작성), Phase 5 (report 내 PG 인용) 전에 **반드시 선독**. Gantree 문법, PPR `def` 블록, `AI_` 함수, `→` 파이프라인, `(status)` 코드, `@dep:`, `[parallel]`, acceptance_criteria 의미를 이 파일이 정의. |

**규칙**: PG 아티팩트를 생성/해석하는 phase 진입 시 `references/pg.md` 를 먼저 읽는다. 이 레퍼런스가 없으면 cc-ra 의 산출물 (feature_tree.json, `*.pg.md` trace) 문법이 붕괴한다.

---

## Phase 0 — 환경 준비

```bash
cargo --version
python --version
cargo modules --version 2>/dev/null || echo "(권장: cargo install cargo-modules)"
mkdir -p "<WORKSPACE>/.cc-ra"
```

`CC_RA_LIB` 환경 변수: 이 SKILL 디렉터리의 `../lib` (또는 설치 시 hardcode).

---

## Phase 1 — Context Build

→ [phases/01_context_build.md](phases/01_context_build.md)

요약: Python 헬퍼 4개 (workspace_meta, module_graph, symbol_index, invariant_extract) + assemble_context 실행. `_context.json` 생성. **주의**: invariant_extract 산출 (`_invariants.json`) 은 **design_claims 로 격리**. Phase 1.5~3 접근 금지, Phase 3.5 에서만 활성.

---

## Phase 1.5 — Feature Reverse-Engineering ★ v0.2

→ [phases/01_5_feature_reverse.md](phases/01_5_feature_reverse.md)

요약: **코드만 보고** 기능별 Gantree 역공학. 모듈 구조 아닌 "시스템이 하는 일" 관점. BFS 로 15분 룰 원자까지 분해. 각 leaf 에 PPR def (입출력·분기·파이프·inferred_AC). 설계 문서 참조 금지.

산출: `_feature_tree.json` + `decomposition/NN_<Name>.pg.md`

---

## Phase 2 — Hypothesis Generation

→ [phases/02_hypothesis.md](phases/02_hypothesis.md)

요약: feature_tree 에서 위험 지대 가설 ≥ 20 개 도출. 분업 아닌 힌트.

---

## Phase 2.5 — Scenario Derivation ★ v0.2

→ [phases/02_5_scenario_derive.md](phases/02_5_scenario_derive.md)

요약: 각 leaf 에 심볼릭 트레이스용 시나리오 5 유형 (happy/boundary/state/interaction/adversarial) 합성. Phase 3 입력 재료.

산출: `_scenarios.json`

---

## Phase 3 — Position Analysis (병렬) ★ v0.2 재작성

→ [phases/03_position_analysis.md](phases/03_position_analysis.md)

요약: Agent 도구로 **8 사고 포지션 병렬 dispatch**. 모두 동일한 feature_tree + scenarios + 원본 코드 받음. **분업 아님, 공유**. 각자 심볼릭 trace 를 PG 구조 (.pg.md) 로 산출 + Divergence 일급 노드.

포지션 ID:
- [skeptic](personas/skeptic.md) — 모든 주장 의심
- [paranoid](personas/paranoid.md) — "어떻게 깨질까" 만 묻기
- [historian](personas/historian.md) — 시간 축. 레거시 가정
- [newcomer](personas/newcomer.md) — 처음 본 사람 시각
- [adversary](personas/adversary.md) — 깨뜨리기
- [holist](personas/holist.md) — 연결고리·상호작용
- [reductionist](personas/reductionist.md) — 최소 반례
- [auditor](personas/auditor.md) — AC 검증

---

## Phase 3.5 — Design Drift ★ v0.2 신규

→ [phases/03_5_design_drift.md](phases/03_5_design_drift.md)

요약: 설계 문서 (`CLAUDE.md`, `README`, `.pgf/DESIGN-*.md`) 의 명시 주장 ↔ 코드 실제 동작 드리프트 탐지. Auditor 포지션 재호출 (이 phase 에서만 설계 문서 접근 허용). 카테고리 "H" finding 산출.

---

## Phase 4 — Triage

→ [phases/04_triage.md](phases/04_triage.md)

요약: `_findings_<position>.json` × 8 + `_drift.json` 통합. `feature_path × hazard_point` 좌표로 클러스터링. **concurrence_count** 가 confidence 핵심 신호. `severity × likelihood × blast × concurrence_boost` 로 priority_score.

---

## Phase 5 — Report

→ [phases/05_report.md](phases/05_report.md)

요약: `render_report.py` 또는 직접 Write 로 markdown 보고서. 각 finding 에 PG trace 링크 + concurrence + observing_positions + replication.

---

## 진단 출력 (각 phase 끝)

```text
[CC-RA] Phase 1 done    | files=16 symbols=319 claims_extracted=77
[CC-RA] Phase 1.5 done  | features=12 leaves=~70
[CC-RA] Phase 2 done    | hypotheses=28
[CC-RA] Phase 2.5 done  | scenarios=~200
[CC-RA] Phase 3 done    | positions=8 traces=~40 divergences=~50
[CC-RA] Phase 3.5 done  | drifts=~6
[CC-RA] Phase 4 done    | unique=~25 critical=~5
[CC-RA] Phase 5 done    | report=.cc-ra/REPORT-2026-04-20.md
[CC-RA] === Complete ===
```

---

## 산출물 위치 (v0.2)

```
<WORKSPACE>/.cc-ra/
├── _meta.json, _module_graph.json, _symbols.json, _invariants.json,
├── _context.json                           Phase 1
├── _feature_tree.json                      Phase 1.5 ★
├── decomposition/*.pg.md                   Phase 1.5 ★
├── _hypotheses.json                        Phase 2
├── _scenarios.json                         Phase 2.5 ★
├── _traces_<position>/*.pg.md              Phase 3 ★ (8 폴더)
├── _findings_<position>.json               Phase 3 ★ (8 파일)
├── _drift.json                             Phase 3.5 ★
├── _findings.json, _triage_log.json        Phase 4
├── REPORT-{date}.md                        Phase 5 — 사용자용 최종
├── status.json
└── findings.db.json
```

---

## 카테고리 코드 (분석자·보고서 공용)

| Code | Category |
|------|----------|
| A | Temporal / Frame Ordering |
| B | Implicit Invariant Violation |
| C | State Coupling Gap |
| D | Event Leakage / Layering |
| E | Cache / Recompute Aggression |
| F | Architecture / Abstraction Leak |
| G | Domain-specific Hazard |
| H | Spec ↔ Implementation Drift *(Phase 3.5 전용)* |

---

## 절대 보고하지 않는 것

- Clippy / cargo check 가 잡을 수 있는 lint
- 함수 길이, 변수 이름, 들여쓰기
- 단순 unwrap → expect 권고
- 미사용 import, dead code (clippy 영역)
- Format (rustfmt 영역)

cc-ra 는 **사람이 코드 리뷰해야 잡을 수 있는 클래스** 가 목표.

---

## v0.1 과의 차이 요약

| 영역 | v0.1 | v0.2 |
|------|------|------|
| 페르소나 | 역할 기반 (architect, invariant_hunter, ...) | **사고 포지션** (skeptic, paranoid, ...) |
| 분업 | review_units 페르소나별 분할 | **공유** — 전원 전체 본다 |
| 경계 | "너의 영역" 명시 | **경계 없음** |
| 설계 문서 | Phase 1 에서 invariants 로 mixed | **격리** — Phase 3.5 전용 |
| 분해 | 모듈 기반 심볼 인덱스 | **기능 기반 Gantree + PPR** |
| 분석 산출 | prose finding | **PG 구조 trace + Divergence 일급 노드** |
| 실행 | 정적 리뷰 | **심볼릭 코드 추적** |

v0.1 의 Python 헬퍼는 재사용 (workspace_meta, module_graph, symbol_index, invariant_extract, assemble_context, render_report).
