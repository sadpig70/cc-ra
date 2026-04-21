# cc-ra — Claude Code Rust Analyzer
## Technical Specification v0.3

> **Post-LLM 시대의 논리·설계 오류 분석 방법론을 구현한 시스템**

- **Project Name**: cc-ra
- **Version**: 0.3
- **Runtime**: Claude Code CLI (Opus 4.7+) + Python 3.10+
- **Target**: Rust workspace (Cargo)
- **Author**: Jung Wook Yang <sadpig70@gmail.com>
- **Date**: 2026-04-21
- **License**: Private (사용자 지정)

---

## 목차

1. [개요와 동기](#1-개요와-동기)
2. [7 Core Principles (설계 철학)](#2-7-core-principles-설계-철학)
3. [버그 카테고리 분류 (Taxonomy)](#3-버그-카테고리-분류-taxonomy)
4. [아키텍처](#4-아키텍처)
5. [8 Phase 파이프라인](#5-8-phase-파이프라인)
6. [8 Thinking Positions](#6-8-thinking-positions)
7. [PG 구조화 Symbolic Trace](#7-pg-구조화-symbolic-trace)
8. [Python 헬퍼 계층](#8-python-헬퍼-계층)
9. [산출물 명세](#9-산출물-명세)
10. [사용법](#10-사용법)
11. [렌즈 시스템 (v0.4 설계)](#11-렌즈-시스템-v04-설계)
12. [이론적 배경과 선행 연구 매핑](#12-이론적-배경과-선행-연구-매핑)
13. [한계와 경계 조건](#13-한계와-경계-조건)
14. [로드맵](#14-로드맵)
15. [Appendix — 파일럿 실증 사례](#15-appendix--파일럿-실증-사례)

---

## 1. 개요와 동기

### 1.1 문제 정의

Rust 워크스페이스의 **고난이도 논리·설계 오류** 탐지. 여기서 "고난이도"는:

- Clippy · cargo check · rust-analyzer 같은 결정론적 툴이 잡을 수 없는 클래스
- 사람이 코드 리뷰 해야만 발견 가능한 **의미론·시간 순서·상호작용** 버그
- **설계 자체에서 유래된** 오류 (구현의 실수가 아니라 설계가 암묵 가정한 것이 현실에서 깨지는 경우)

### 1.2 기존 접근의 한계

| 기존 접근 | 한계 |
|----------|------|
| **사람 코드 리뷰** (Fagan Inspection 등) | 느림 · 편향 · 피로 · 컨텍스트 제한 · 역할 분업의 사각지대 |
| **결정론적 정적 툴** (clippy, sonarqube) | 패턴 매칭 · 표면적 lint · 의미론 이해 부재 |
| **기존 LLM 코드 리뷰 툴** (CodeGuru 등) | 역할 기반 페르소나 답습 · prose 산출 · 구조화 부재 |
| **Symbolic Execution** (KLEE 등) | 자동화 툴 한정 · 복잡한 엔진 필요 · 인간/LLM 활용 어려움 |

### 1.3 cc-ra 의 입장

**"AI 라는 새 관찰자 (코드 읽는 귀신) 에 맞춰 재설계된 방법론"**.

기존 방법을 LLM 에 옮겨 쓰는 것이 아니라, LLM 이 잘 할 수 있는 것을 **전제로** 설계 결정.

LLM 이 잘 하는 것:
1. 대용량 코드베이스 전체를 피로 없이 읽음
2. 의미론 이해
3. 다중 시각 동시 유지
4. 구조화된 DSL 산출

이 네 가지 능력이 cc-ra 의 7 원칙을 가능케 함.

---

## 2. 7 Core Principles (설계 철학)

### ① 기능별 BFS Gantree (모듈 아닌)

**원칙**: 시스템을 "무엇을 하는가" 기준으로 분해. 모듈 구조가 아닌 feature 구조.

**근거**: 한 기능이 여러 모듈에 걸쳐 구현됨 (cross-cutting). 모듈 기반 분석은 조각만 봄 → 조율 갭이 사각지대.

**예시**: MSharp 의 `Find` 기능은 `find.rs` + `app.rs` + `editor.rs` + `keys.rs` 4 파일에 분산. 모듈 리뷰로는 파일별 독립 관찰, 기능 리뷰는 책임 전체를 한 노드로.

### ② PG 역공학 (코드 → Gantree + PPR)

**원칙**: Rust 코드를 PG (Gantree + PPR) 표기로 변환. 이 표기가 후속 분석의 공유 아티팩트.

**근거**: Rust 문법이 숨기는 가정·분기·파이프라인·invariant 가 PPR 로 펼쳐지면 명시됨. LLM 이 이해하는 의도 표기법.

### ③ 코드만 역공학 (설계 문서 차단)

**원칙**: Phase 1.5 ~ Phase 3 에서 `CLAUDE.md`, `README`, `DESIGN-*.md` 접근 금지. Phase 3.5 에서만 비교용으로 활성화.

**근거**: **Bias amplification 문제** — 같은 설계 문서로 구현하고 리뷰하면 설계 자체 오류는 양쪽에서 같은 맹점. 독립 역공학으로 설계 오류를 분석 관찰자 입장에서 발견 가능.

### ④ 공유 분석 (분업 금지)

**원칙**: 8 포지션이 동일한 feature_tree + 동일한 시나리오를 받음. 영역 분할 없음.

**근거**: 사람 시대의 분업은 컨텍스트 제한 때문이었음. LLM 은 전체를 받을 수 있음 → 분업 제약 없음. 분업하면 경계 사각지대.

### ⑤ 사고 포지션 (역할 아닌, 경계 없음)

**원칙**: "architect / invariant_hunter" 같은 역할 페르소나가 아니라 "Skeptic / Paranoid / Historian" 같은 **사고 양식** 기반 포지션. 영역 제한 없음.

**근거**: 역할 경계 = 사각지대. 경계가 있으면 "이건 다른 페르소나 영역" 하고 넘김. 모두 전체를 보되 **질문 방식** 만 다름.

### ⑥ 심볼릭 코드 추적 (실행 아님)

**원칙**: 테스터가 시스템을 테스트 하듯 각 기능 시나리오를 **코드 레벨에서 단계별 추적**. 실제 실행은 아님 — 코드를 읽어가며 상태 전이 기록.

**근거**: 상태 전이 버그, feature × feature 상호작용, race 조건은 정적 리뷰로 거의 못 잡음. 시나리오 시뮬레이션이 자연스럽게 노출.

### ⑦ 분석 자체도 PG 구조 (Recursive PG)

**원칙**: 분석 과정 · 결과 를 분석 대상 (코드) 과 **같은 DSL (PG)** 로 표기. 장문 prose 배제.

**근거**: 스케일 (60+ leaf × 시나리오 × 8 포지션 = 수백 trace) · 기계 가독성 · 주소지정 · Divergence 를 일급 노드로 만들어 triage 자동화.

---

## 3. 버그 카테고리 분류 (Taxonomy)

cc-ra 는 8 카테고리만 본다. Clippy 가 잡는 것은 제외.

| Code | Category | 예시 |
|------|----------|------|
| **A** | **Temporal / Frame Ordering** | frame N 의 처리가 frame N+1 에서야 반영, 호출 순서 의존 |
| **B** | **Implicit Invariant Violation** | 주석·암묵 contract 가 특정 경로에서 깨짐 |
| **C** | **State Coupling Gap** | 함께 변해야 할 필드가 한 경로에서만 갱신 |
| **D** | **Event Leakage / Layering** | UI 레이어 클릭이 도메인 레이어로 새는 등 추상화 누수 |
| **E** | **Cache / Recompute Aggression** | 매 프레임 재계산으로 사용자 액션 덮어쓰기, stale cache |
| **F** | **Architecture / Abstraction Leak** | God module, 결합도 폭증, 도메인 경계 붕괴 |
| **G** | **Domain-specific Hazard** | 도메인 특유의 함정 (텍스트 에디터의 UTF 경계, IME 등) |
| **H** | **Spec ↔ Implementation Drift** | 설계 문서 주장과 코드 동작 불일치 (Phase 3.5 전용) |

---

## 4. 아키텍처

### 4.1 실행 환경

- **런타임**: Claude Code CLI (LLM as runtime)
- **헬퍼**: Python 3.10+ 스크립트 (결정론적 구조 추출)
- **진입**: `/cc-ra <workspace>` 슬래시 커맨드

### 4.2 레이어

```
┌─────────────────────────────────────────────────────────┐
│ User Invocation (/cc-ra)                                │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│ Claude Code (SKILL.md orchestrator)                     │
│   - 8 phase 순차 실행                                   │
│   - dispatch mode 결정 (parallel_agents / inline_sim)   │
│   - Agent dispatch (8 포지션 병렬)                       │
│   - PG artifact I/O                                     │
└─────────────────────────────────────────────────────────┘
              │                         │
┌─────────────────────┐   ┌─────────────────────────────┐
│ Python Helpers      │   │ 8 Thinking Positions        │
│ (결정론적)          │   │ (LLM sub-agents)            │
│   - workspace_meta  │   │   - skeptic, paranoid,      │
│   - module_graph    │   │     historian, newcomer,    │
│   - symbol_index    │   │     adversary, holist,      │
│   - invariant_ex    │   │     reductionist, auditor   │
│   - assemble_ctx    │   │                             │
│   - render_report   │   │                             │
└─────────────────────┘   └─────────────────────────────┘
              │                         │
              └────────────┬────────────┘
                           │
              ┌──────────────────────┐
              │ Artifacts (.cc-ra/)   │
              │   JSON + PG .md       │
              └──────────────────────┘
```

### 4.3 데이터 흐름

```
Phase 1    ─→  _context.json (symbols, module_graph, files)
            ╲
             → _invariants.json → (격리 — design_claims)

Phase 1.5  ─→  _feature_tree.json + decomposition/*.pg.md

Phase 2    ─→  _hypotheses.json  (★ v0.3: Axis 6 Undo/Mutation Gap Survey 포함)

Phase 2.5  ─→  _scenarios.json

Phase 3    ─→  _traces_<pos>/*.pg.md (×8)
                _findings_<pos>.json   (×8)
                [dispatch mode: parallel_agents or inline_simulation]

Phase 3.5  ─→  _drift.json  ← design_claims 활성화

Phase 4    ─→  _findings.json (triaged) + _triage_log.json
                [★ v0.3: sibling_locations 필드, Naive Fix 경고 포함]

Phase 5    ─→  REPORT-{date}.md + status.json
```

---

## 5. 8 Phase 파이프라인

### Phase 1 — Context Build
**입력**: workspace 경로
**산출**: `_context.json`
**주요**: Python 헬퍼 4개 + assemble 실행. symbols / module_graph / files / invariants(design_claims 로 격리).

### Phase 1.5 — Feature Reverse-Engineering ★
**입력**: `_context.json` + 원본 코드 (설계 문서 **금지**)
**산출**: `_feature_tree.json`, `decomposition/*.pg.md`
**주요**: BFS 로 L2 대 기능 → 원자까지 분해. 각 leaf 에 PPR def + inferred_AC.

### Phase 2 — Hypothesis Generation
**입력**: `_feature_tree.json`
**산출**: `_hypotheses.json` (≥ 20)
**주요**: 위험 지대 가설. 6-Axis:
- Axis 1: State Machine Hazards
- Axis 2: Temporal/Frame Ordering
- Axis 3: Invariant Candidates
- Axis 4: Feature Interaction Matrix
- Axis 5: Error Path Survey
- **Axis 6 (★ v0.3): Undo/Mutation Gap Survey** — `replace_silent` / `buf.insert` / `buf.remove` 전수 grep → undo gap 후보 목록화

### Phase 2.5 — Scenario Derivation ★
**입력**: feature_tree + hypotheses
**산출**: `_scenarios.json`
**주요**: 각 leaf 에 5 유형 시나리오 (happy / boundary / state-transition / interaction / adversarial).

### Phase 3 — Position Analysis (8 병렬) ★
**입력**: feature_tree + scenarios + 원본 코드
**산출**: `_traces_<pos>/*.pg.md` (×8), `_findings_<pos>.json` (×8)
**주요 (★ v0.3 dispatch mode 분기)**:
```python
if agent_tool_available and (src_lines > 1000 or hypotheses > 15):
    → parallel_agents   # Agent tool 8개 병렬 dispatch
else:
    → inline_simulation # 현 세션 포지션 순차 시뮬레이션
```
8 포지션이 **동일한 전체**를 자기 시각으로 분석. 심볼릭 trace → PG 구조. Divergence 일급 노드.

**★ v0.3 Auditor 전수 패턴 검사**:
- Undo Bypass 패턴 전수 grep
- Dirty Flag 누락 패턴
- Cache Key 누락 패턴

### Phase 3.5 — Design Drift ★
**입력**: `_findings_*` + `_invariants.json` (design_claims 활성화) + 설계 MD 문서
**산출**: `_drift.json`
**주요**: Auditor 재호출. 설계 주장 ↔ 실제 동작 불일치 식별. Category H finding.

### Phase 4 — Triage
**입력**: `_findings_*` + `_drift.json`
**산출**: `_findings.json` (final)
**주요**: `feature_path × hazard_point` 클러스터링. **concurrence_count** 가 confidence 주 신호. `priority = severity × likelihood × blast × concurrence_boost`.

**★ v0.3 Sibling Pattern Spread**: Finding 확정 시마다 동일 패턴의 다른 발생 위치 전수 확인. 동류 finding 은 `F003a`, `F003b` 형태로 부모와 연결. `suggested_fix` 에 `sibling_locations` 필드 추가.

**★ v0.3 Naive Fix 경고**: suggested_fix 작성 시 한 위치만 수정하고 sibling 을 남기는 패턴, 호출 지점 대신 함수 내부 수정으로 미래 호출도 보호하는 방법 등을 명시.

### Phase 5 — Report
**입력**: `_findings.json` + `_context.json`
**산출**: `REPORT-{date}.md`, `status.json`
**주요**: 5분 요약 + 포지션/카테고리 분포 + finding 본문 (각 finding 에 PG trace 링크).

---

## 6. 8 Thinking Positions

| Position | 사고 양식 | 대표 질문 |
|----------|---------|---------|
| **Skeptic** | 모든 주장 의심 | "이 함수 이름이 의미하는 것을 정말 수행하는가?" |
| **Paranoid** | "어떻게 깨질까" 만 | "이 state 를 깨뜨릴 수 있는 최소 시퀀스는?" |
| **Historian** | 시간 축. 레거시 가정 | "새 feature 추가로 기존 가정이 깨진 곳?" |
| **Newcomer** | 처음 본 시각 | "이 함수 이름이 몸체와 일치하나?" |
| **Adversary** | 깨뜨리기 | "최악의 입력은? Feature 조합으로 깰 수 있나?" |
| **Holist** | 연결고리 · 상호작용 | "이 state 를 읽는/쓰는 leaf 의 교집합?" |
| **Reductionist** | 최소 반례 | "이 버그의 minimal repro 는?" |
| **Auditor** | AC 검증 + 전수 패턴 검사 | "inferred_AC 가 모든 경로에서? replace_silent 전수 확인?" |

### 8 포지션 설계 원칙

**포지션은 인식론적 스타일(How to think)이지, 도메인 역할(What to know)이 아니다.**

역할 경계 페르소나 → 경계 사각지대. 인식론적 포지션 → 전체를 보되 질문 방식만 다름.
의료 소프트웨어든 게임 엔진이든 "Skeptic 시각" 자체는 도메인 무관하게 작동한다.

→ v0.4 에서 도입할 렌즈 시스템은 포지션을 대체하지 않고, 포지션이 착용하는 **도메인 컨텍스트 레이어**로 추가된다.

### 공통 원칙 (8 포지션 모두 적용)

1. 경계 없음 — 전체 feature_tree 와 전체 코드 접근
2. 설계 문서 차단 (Auditor 의 Phase 3.5 재호출 제외)
3. 심볼릭 추적 스타일 분석
4. PG 구조 산출 (Gantree + PPR + Divergence 일급 노드)
5. Clippy 영역 배제
6. 다른 포지션과 겹쳐도 OK (concurrence = signal)

---

## 7. PG 구조화 Symbolic Trace

### 7.1 Trace 파일 구조

```
Trace_<id> // <feature_path> :: <scenario_name> (status)
    Precondition // state setup
        <doc/config/cursor/scroll 등>

    Stimulus // 사용자 액션 시퀀스
        <A1, A2, ...>

    Frame<N>_<action>
        call_<fn>
            # PPR: inputs → operation → outputs
        branch_<condition>
        state_change
            <관측 delta>

    State_S<N> // 스텝 종료 snapshot

    Divergence_<id> // @hazard_point:<marker>
        category, severity, likelihood, blast_radius, confidence
        hazard_leaves, root_cause, suggested_fix
        sibling_locations        // ★ v0.3 신규
        observable_by_positions, replication
```

### 7.2 Divergence 노드 스키마

```json
{
  "id": "D001",
  "position": "skeptic",
  "trace_file": "_traces_skeptic/TS-3.pg.md",
  "feature_path": "FindReplace::SeekMatch::ComputeLineY",
  "category": "G",
  "severity": 0.85,
  "likelihood": 0.7,
  "blast_radius": 0.5,
  "confidence": 0.90,
  "hazard_point": "HAZARD_POINT_ALPHA",
  "hazard_leaves": ["SeekMatch::ComputeLineY", "ensure_cursor_visible"],
  "root_cause": "...",
  "suggested_fix": "...",
  "sibling_locations": ["src/keys.rs:fn_a", "src/editor.rs:fn_b"],
  "observable_by_positions": ["adversary", "holist", "reductionist"],
  "replication": {
    "minimal_setup": "...",
    "steps": [],
    "observed": "..."
  }
}
```

### 7.3 이점

- **주소지정**: `Trace_TS3::Frame2::seek_match_call` 로 경로 참조
- **Hazard 마커**: 같은 `@hazard_point` 로 여러 trace·divergence 연결
- **Triage 자동화**: Divergence 가 일급 노드라 JSON 으로 집계 용이
- **Concurrence 측정**: 같은 hazard_point 를 플래그한 포지션 수
- **재현성**: 각 Divergence 에 minimal replication
- **Sibling 추적**: `sibling_locations` 로 동류 버그 전파 범위 즉시 가시화

---

## 8. Python 헬퍼 계층

| Helper | 용도 | 외부 의존 |
|--------|------|----------|
| `workspace_meta.py` | `cargo metadata --no-deps` 슬림 변환 | cargo |
| `module_graph.py` | `cargo-modules dependencies` + DOT 파싱 + networkx. `orphans` 통합 | cargo-modules (옵션, fallback 있음), networkx |
| `symbol_index.py` | tree-sitter Rust AST 심볼 인덱스 | tree-sitter, tree-sitter-rust |
| `invariant_extract.py` | 주석 · assert · MD 에서 invariant 후보 | 없음 |
| `assemble_context.py` | Phase 1 산출 통합 | 없음 |
| `render_report.py` | findings.json → markdown | 없음 |

**설치**: `pip install -r cc-ra/lib/requirements.txt`

**의존성 총 3개**: tree-sitter, tree-sitter-rust, networkx.

---

## 9. 산출물 명세

```
<WORKSPACE>/.cc-ra/
├── _meta.json                      Phase 1 — cargo metadata 슬림
├── _module_graph.json              Phase 1 — nodes/owns/uses/cycles/orphans/metrics
├── _symbols.json                   Phase 1 — tree-sitter 심볼
├── _invariants.json                Phase 1 — design_claims (격리)
├── _context.json                   Phase 1 — 통합
├── _feature_tree.json              Phase 1.5 ★
├── decomposition/
│   ├── 00_root.pg.md
│   ├── 01_FileLifecycle.pg.md
│   ├── …
│   └── 12_UserCommands.pg.md
├── _hypotheses.json                Phase 2 (★ v0.3: Axis 6 포함)
├── _scenarios.json                 Phase 2.5 ★
├── _traces_skeptic/*.pg.md         Phase 3 ★
├── _traces_paranoid/*.pg.md
├── _traces_historian/*.pg.md
├── _traces_newcomer/*.pg.md
├── _traces_adversary/*.pg.md
├── _traces_holist/*.pg.md
├── _traces_reductionist/*.pg.md
├── _traces_auditor/*.pg.md
├── _findings_<position>.json       Phase 3 (×8)
├── _drift.json                     Phase 3.5 ★
├── _findings.json                  Phase 4 — final (★ v0.3: sibling_locations 포함)
├── _triage_log.json                Phase 4
├── REPORT-{ISO_DATE}.md            Phase 5 — 사용자용
├── status.json                     Phase 5 — 메타
└── findings.db.json                Phase 5 — incremental 비교용
```

---

## 10. 사용법

### 10.1 설치

```bash
# Python deps (3개)
pip install -r D:/Tools/MSharp/cc-ra/lib/requirements.txt

# Skill 설치 (cc-ra/skill/ → .claude/skills/cc-ra/)
"D:/Tools/PS7/7/pwsh.exe" -NoProfile -ExecutionPolicy Bypass -File \
    D:/Tools/MSharp/cc-ra/install.ps1

# (권장) cargo-modules — 모듈 그래프 정확도 ↑
cargo install cargo-modules
```

### 10.2 실행

Claude Code 세션에서:

```
/cc-ra D:/path/to/rust/workspace
```

### 10.3 옵션

| 옵션 | 기본 | 설명 |
|------|------|------|
| `--scope <glob>` | `src/**/*.rs` | 분석 범위 |
| `--since-commit <ref>` | — | git 변경 파일만 |
| `--positions <list>` | 8 all | 활성 포지션 |
| `--threshold <float>` | 0.4 | confidence cutoff |
| `--no-static` | — | cargo check/clippy 스킵 |
| `--config <path>` | `.cc-ra/config.toml` | config |

### 10.4 결과 해석

`REPORT-{date}.md` 의 섹션:
1. **5분 요약** — 상위 5 critical (priority ≥ 0.5)
2. **포지션별 발견 요약** — unique finding count 차별성 지표
3. **카테고리 분포** — A ~ H 개수
4. **Findings (Priority 순)** — 각 finding 상세 + trace 링크 + sibling_locations
5. **Low Confidence** — confidence < threshold
6. **Hypotheses Not Verified** — Phase 2 에서 제기됐으나 finding 전환 실패
7. **Design Drifts** (H 전용) — Phase 3.5 산출

---

## 11. 렌즈 시스템 (v0.4 설계)

> **현재 상태**: 설계 완료, 구현 예정 (v0.4).
> 이 섹션은 아키텍처 결정 기록 + 구현 스펙이다.

### 11.1 동기 — 포지션 시스템의 남은 맹점

8 포지션은 **인식론적 스타일** 축을 커버한다. 그러나 한 가지 축이 더 있다:

> **도메인 특유의 위험 패턴** — 의료 소프트웨어의 환자 데이터 동기화 위험, 임베디드의 실시간 데드라인, 금융의 정합성 보장.

이것은 코드를 열심히 읽어도 그 도메인의 **known failure mode** 를 모르면 보이지 않는 클래스다.

### 11.2 설계 원칙 — 포지션과 렌즈는 다른 축

```
분석 관찰자 = 사고 포지션 × 도메인 렌즈
               (how to think)   (what to watch for)
```

렌즈는 포지션을 대체하지 않는다. 포지션이 **착용하는 컨텍스트 레이어**다.
렌즈 없이도 8 포지션은 온전히 작동한다. 렌즈는 도메인 특유의 blind spot 을 보완한다.

### 11.3 실행 모드

```
기본 run:          8 포지션, 렌즈 없음
기본 + 렌즈 run:   동일 8 포지션 + 도메인 렌즈 컨텍스트 주입
Delta analysis:    두 run 의 finding 차이 = 렌즈 기여분
```

### 11.4 Phase 0.5 — Lens Research (신규 phase)

```python
def lens_research(feature_tree: dict) -> LensKnowledge:
    """
    feature_tree 에서 도메인 키워드 추출 → WebSearch × 3~5 →
    도메인 known failure modes, 관련 표준, 최근 사례 수집 →
    _lens_knowledge.md 로 저장
    """
    # Step 1: 도메인 자동 감지
    domain_keywords = AI_extract_domain(feature_tree)
    # e.g., "텍스트 에디터" → ["text_editor", "UTF handling", "undo semantics"]

    # Step 2: 병렬 WebSearch (단일 Agent, 중앙화)
    queries = [
        f"{domain} software known failure modes",
        f"{domain} safety or audit checklist",
        f"{domain} recent CVE or incident patterns",
    ]
    raw_results = [WebSearch(q) for q in queries]  # parallel

    # Step 3: 정제 → _lens_knowledge.md
    knowledge = AI_distill(raw_results, max_items=20)
    return knowledge  # 각 항목: pattern, source, relevance_score
```

**중앙화의 이유**: 8 포지션이 각자 검색하면 동일 쿼리 8번 중복. 연구는 1회, 결과는 전원 공유.

### 11.5 포지션 프롬프트에 렌즈 주입 방식

```
[LENS CONTEXT — treat as hypothesis hints, NOT ground truth]
Domain: {detected_domain}
Known failure patterns in this domain:
  - {pattern_1}: {brief_description}
  - {pattern_2}: {brief_description}
  ...
Relevant standards/checklists:
  - {standard_1}

⚠ 위 정보는 탐지 힌트다. 실제 코드 trace 로 검증 후에만 finding 으로 보고할 것.
  검색 결과를 코드보다 신뢰하지 말 것.
```

**가설 힌트로 명시하는 이유**: 검색 결과를 사실로 주입하면 없는 버그를 "발견"하는 역전이 발생한다. 포지션은 렌즈 컨텍스트를 힌트로 받아, **코드 trace 로 검증된 경우에만** finding 으로 승격한다.

### 11.6 렌즈 종류

#### Auto-Lens (기본 경로)

Phase 1.5 의 feature_tree 분석 후 자동 생성:

| feature_tree 신호 | 자동 생성 렌즈 |
|------------------|--------------|
| lock/mutex/RwLock 다수 | concurrency-safety lens |
| 외부 API 호출 / HTTP 다수 | fault-tolerance lens |
| 파일 I/O + 사용자 데이터 | data-integrity lens |
| 실시간 타이머 / 인터럽트 | realtime-constraint lens |
| 사용자 인증 / 세션 | auth-security lens |

#### Domain-Lens (사용자 지정)

```
/cc-ra D:/workspace --lens medical
/cc-ra D:/workspace --lens embedded
/cc-ra D:/workspace --lens financial
/cc-ra D:/workspace --lens ai-pipeline
```

#### Wild-Lens (의도적 이방인 시각)

```
/cc-ra D:/workspace --lens wild
```

**목적**: 엉뚱한 도메인 렌즈를 의도적으로 적용. 정상 도메인 렌즈가 당연하게 넘기는 것을 이방인 시각이 잡아낼 수 있다. "항공 안전 감사" 렌즈로 텍스트 에디터를 보면 — undo 실패 = 데이터 유실 = crash에 준하는 중요도로 재해석.

### 11.7 도메인 지식 캐시

`_lens_knowledge.md` 는 저장되어 **동일 도메인 재분석 시 재사용**된다.

```
<WORKSPACE>/.cc-ra/
└── _lens_knowledge.md   # auto-generated or user-specified lens + search results
```

만료 정책: 7일 (config 조정 가능). 만료 후 재검색.

### 11.8 Delta Analysis

기본 run + 기본+렌즈 run 을 모두 실행한 경우, Phase 4 triage 에서 두 run 의 finding 을 비교:

```
Delta findings = (기본+렌즈 findings) - (기본 findings)
```

- Delta 에만 있는 finding → 렌즈 기여분 (도메인 specific)
- 양쪽에 있는 finding → 도메인 무관 구조적 버그 (더 신뢰도 높음)
- 기본에만 있는 finding → 렌즈 적용 후 기각 (reconsider)

Delta finding 은 보고서에 `[LENS]` 태그로 별도 표시.

### 11.9 Sharpening Loop (반복 심화)

1차 기본 run → high-uncertainty finding 목록 추출 → 해당 영역에 특화된 날카로운 렌즈 자동 생성 → 2차 run. 넓게 본 후 의심 지점을 집중 파고드는 iterative 방식.

```python
if first_run.uncertain_findings > 5:
    sharp_lens = AI_generate_targeted_lens(first_run.uncertain_findings)
    second_run = run_with_lens(sharp_lens)
```

---

## 12. 이론적 배경과 선행 연구 매핑

cc-ra 의 각 원칙별 선행:

| 원칙 | 가장 가까운 선행 | 차이 |
|------|----------------|------|
| ① 기능별 BFS | FMEA · Feature-Oriented Programming · Attack Trees | 이것들은 제조/보안 · 설계 분야. 코드 역공학 + 리뷰 통합 드묾 |
| ② PG 역공학 | Hoare Logic · Design by Contract · TLA+ · Alloy | 선행은 수학적 · 형식적. PG 는 LLM-native 완화 표기 |
| ③ 코드만 역공학 | 독립 리뷰 원칙 · Fresh eyes technique | 설계 문서 차단을 **정책으로 강제** 하는 것은 드묾 |
| ④ 공유 분석 | — | 대부분 Multi-Agent 연구가 분업. "분업 금지" 는 LLM-native 관찰 |
| ⑤ 사고 포지션 | Six Thinking Hats · Red Team / Blue Team | de Bono 는 회의용. 코드 리뷰 적용 드묾 |
| ⑥ 심볼릭 추적 | Symbolic Execution (King 1976) · Model Checking (TLA+, SPIN) | 선행은 자동화 툴. 인간/LLM 심볼릭은 드문 적용 |
| ⑦ 재귀 PG | CEGAR · Structured Log | "분석 결과를 분석 대상과 동일 DSL" 재귀 구조화는 선행 미확인 |
| 렌즈 시스템 | Threat Intelligence · Domain-specific testing | 포지션과 도메인 컨텍스트를 **두 축으로 분리** + 검색 기반 동적 생성 |

**학문적 최근접**: **STPA** (Nancy Leveson, MIT) — 시스템을 제어 액션으로 계층 분해 + hazard marking. 도메인은 안전-critical 시스템.

**cc-ra 가 진짜 새로운 부분**:
1. **재귀 PG** — 코드 표기 DSL 이 분석 표기 DSL 과 동일
2. **"분업 금지 + 경계 없음 + 문서 차단" 삼중 적용**
3. **LLM-runtime 전제** — 설계 자체가 Post-LLM 가능
4. **포지션 × 렌즈 이축 모델** — 인식론적 스타일과 도메인 컨텍스트를 분리 관리

---

## 13. 한계와 경계 조건

### 13.1 현재 한계

- **비결정성** — LLM 런타임이라 같은 입력에 다른 결과 가능. 보고서 품질의 lower bound 보장 어려움
- **비용** — 8 포지션 × 전체 코드 병렬 분석은 토큰 비용 큼 (user: "비용 감안 안 함" 정책)
- **시간** — medium workspace 60분 내외 예상. 대형 (100+ 파일) 은 3시간+ 가능
- **Incremental 미지원** — full run. mtime 캐시는 v0.4 예정
- **Rust 전용** — 다른 언어는 별도 분석기 (v0.4 Multi-language 예정)

### 13.2 작동 잘 안 되는 경우

- **매크로 집약** 코드 — tree-sitter 는 매크로 확장 불가. feature_tree 에 누락 가능. `cargo expand` 통합 미지원 (v0.4 예정)
- **극히 큰 crate** (500+ 파일) — Phase 1 의 symbol_index 생성 자체가 느림
- **Unsafe 집약** — cc-ra 는 주로 high-level 논리. unsafe 세부는 cargo-geiger 등 보조 툴 의존
- **생성 코드** (build.rs 로 쓰여지는 코드) — 역공학 대상 아님

### 13.3 렌즈 시스템 한계 (v0.4 예정)

- **도메인 오탐지** — feature_tree 에서 도메인 자동 감지가 틀릴 경우 엉뚱한 렌즈 생성
- **검색 노이즈** — WebSearch 결과가 무관하거나 오래된 정보일 수 있음. 가설 힌트 명시로 완화
- **렌즈 깊이의 한계** — 검색으로 얻는 도메인 지식이 실제 전문가 수준에 미치지 못할 수 있음

### 13.4 False Positive / False Negative

- **False positive 예상 ~ 30%** — 심볼릭 추적이 암묵 invariant 를 과도하게 의심할 수 있음
- **False negative** — 런타임 동작에만 나타나는 버그 (실제 실행 필요) 는 잡지 못함. cc-ra 는 정적/심볼릭 분석.

---

## 14. 로드맵

### v0.3 (완료 — 2026-04-21)

- [x] **Axis 6 Undo/Mutation Gap Survey** — `replace_silent`/`buf.insert` 전수 grep
- [x] **Auditor 전수 패턴 검사** — Undo Bypass / Dirty Flag / Cache Key 3종
- [x] **Phase 3 dispatch mode** — 코드베이스 규모 기반 parallel_agents / inline_simulation 분기
- [x] **Sibling Pattern Spread** — finding 확정 시 동류 패턴 위치 전수 확인
- [x] **Naive Fix 경고** — `suggested_fix` 에 sibling_locations 필드 + 함정 명시

### v0.4 (단기 — 렌즈 시스템)

- [ ] **Phase 0.5 Lens Research** — feature_tree → 도메인 감지 → WebSearch → `_lens_knowledge.md`
- [ ] **Auto-Lens 생성** — feature_tree 신호 기반 렌즈 자동 추천
- [ ] **Domain-Lens CLI 옵션** — `--lens <domain>`
- [ ] **Wild-Lens 모드** — `--lens wild`
- [ ] **Delta Analysis** — 기본 run vs 기본+렌즈 run 비교
- [ ] **렌즈 지식 캐시** — `_lens_knowledge.md` 7일 만료 재사용
- [ ] **Sharpening Loop** — uncertain finding → 특화 렌즈 → 2차 run
- [ ] **cargo expand 통합** — proc-macro 확장 코드 분석 포함
- [ ] **Incremental 캐시** — mtime + content hash 기반 변경 파일만 재분석

### v0.5 (중기)

- [ ] **Multi-language** — Python / TypeScript (동일 방법론, 다른 tree-sitter grammar)
- [ ] **HTML 보고서** — 인터랙티브 코드 인용 + trace 트리 접기
- [ ] **Watch 모드** — 파일 변경 감시 백그라운드

### v0.6+ (장기)

- [ ] **시간순 회귀 분석** — git blame × finding → "언제 들어온 버그"
- [ ] **LSP (rust-analyzer) 통합** — 타입 해석이 필요한 특정 phase 에 lazy 호출
- [ ] **CI 연동** — PR 마다 자동 실행 + finding 을 comment 로
- [ ] **AutoFix 모드** — 안전한 패치 자동 적용 + `cargo check` 회귀 검증

---

## 15. Appendix — 파일럿 실증 사례

### 15.1 대상

MSharp (Rust + eframe/egui 텍스트 에디터, ~1700 lines)

### 15.2 파일럿 실행 결과

- **Phase 1 헬퍼** — 16 files, 319 symbols, 77 invariant candidates, 16 modules, 21 use edges, 0 cycles (전부 smoke test 통과)
- **Phase 1.5 파일럿** — `FindReplace` 기능 역공학 → `.cc-ra/decomposition/05_FindReplace.pg.md`
- **Symbolic Trace 파일럿** — TS-1 happy / TS-2 session memory / TS-3 wrap scroll / TS-4 replace-all undo

### 15.3 cc-ra v0.2 → v0.3 수정 기여 Findings

cc-ra 분석 후 MSharp 에 실제 적용된 수정 목록:

| Finding | 카테고리 | 수정 내용 |
|---------|---------|---------|
| F-01: word-wrap hit_test 불일치 | G | 렌더 루프(누적 height) ↔ hit_test(고정 row_h) 통일 |
| F-02: Replace All undo 불가 | C | `push_undo_snapshot` 추가 |
| F-03: line_duplicate 외 5개 함수 undo 누락 | C | `push_undo_snapshot` 일괄 추가 |
| F-04: newline_with_indent ins_len 버그 | B | extra indent 미포함 계산 수정 |
| F-05: external_change_dialog stale index | C | `usize` → `PathBuf` 로 탭 재배열 내성 확보 |
| F-06: FindState 캐시 키 취약성 | E | `recompute_cache_key` 도입, `invalidate_cache` 추가 |
| F-07: primary_cursor() 문서 오류 | H | `cursors[0]` → `cursors.last()` 로 CLAUDE.md 정정 |
| F-08: status bar 버전 하드코딩 | F | `env!("CARGO_PKG_VERSION")` 으로 동적 표시 |

**cc-ra v0.3 (Auditor 전수 패턴 검사) 추가 발견**:

| Finding | 발견 방식 | 수정 여부 |
|---------|---------|---------|
| line_delete undo 누락 (F-03 sibling) | Axis 6 전수 grep | ✓ 수정됨 |

### 15.4 파일럿 산출물

- [cc-ra/.pgf/DESIGN-CcRa.md](cc-ra/.pgf/DESIGN-CcRa.md) — 시스템 설계 (Gantree + PPR + AC)
- [cc-ra/.pgf/WORKPLAN-CcRa.md](cc-ra/.pgf/WORKPLAN-CcRa.md) — 빌드 작업 계획
- [cc-ra/.pgf/FINAL-REPORT-CcRa-v0.1.md](cc-ra/.pgf/FINAL-REPORT-CcRa-v0.1.md) — v0.1 빌드 결과
- [cc-ra/.pgf/FINAL-REPORT-CcRa-v0.2.md](cc-ra/.pgf/FINAL-REPORT-CcRa-v0.2.md) — v0.2 전환 결과
- [.cc-ra/decomposition/05_FindReplace.pg.md](.cc-ra/decomposition/05_FindReplace.pg.md) — 기능 역공학 + PG 트레이스 파일럿

---

## Signed

**Author**: Jung Wook Yang <sadpig70@gmail.com>
**Runtime**: Claude Sonnet 4.6 (Claude Code CLI)
**Framework**: PG v1.3 · PGF v2.5
**Date**: 2026-04-21
**Workspace**: `D:/Tools/MSharp/`

---

_End of Technical Specification v0.3_
