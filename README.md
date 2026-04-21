<p align="center">
  <img src="assets/banner.svg" alt="cc-ra — Claude Code Rust Analyzer" width="100%"/>
</p>

# cc-ra — Claude Code Rust Analyzer v0.3

> Rust 워크스페이스의 **고난이도 논리·설계 오류**를 8개 사고 포지션의 다관점 AI 분석으로 탐지.
> Clippy 가 잡는 표면적 lint 는 제외. **사람이 코드 리뷰해야만 잡을 수 있는 클래스** 전용.

- **Version**: 0.3
- **Runtime**: Claude Code CLI + Python 3.10+
- **Author**: Jung Wook Yang <sadpig70@gmail.com>
- **Updated**: 2026-04-21

---

## 의존성

### 필수

| 도구 | 최소 버전 | 용도 | 설치 |
|------|---------|------|------|
| **Python** | 3.10+ | 헬퍼 스크립트 실행 (3.11+ 권장) | [python.org](https://python.org) |
| **cargo** | (Rust toolchain) | `cargo metadata`, `cargo check` | `rustup` |
| **tree-sitter** | 0.23+ | Rust AST 파싱 (symbol_index.py) | `pip install -r lib/requirements.txt` |
| **tree-sitter-rust** | 0.23+ | Rust 문법 바인딩 | 위와 동일 |
| **networkx** | 3.0+ | 모듈 그래프 알고리즘 (사이클·위상정렬) | 위와 동일 |

```bash
# Python 의존성 한 번에 설치 (저장소 루트에서)
pip install -r cc-ra/skill/requirements.txt
```

### 권장

| 도구 | 용도 | 설치 |
|------|------|------|
| **cargo-modules** | 정확한 모듈 의존 그래프 (없으면 fallback scan) | `cargo install cargo-modules` |
| **git** | `--since-commit` 모드 (변경 파일만 분석) | 대부분 이미 설치됨 |

### 선택 (Phase 0 보조)

| 도구 | 용도 | 설치 |
|------|------|------|
| **cargo-audit** | 보안 advisory 검사 | `cargo install cargo-audit` |
| **cargo-geiger** | unsafe 사용 집계 | `cargo install cargo-geiger` |

---

## 설치

```bash
# 저장소 루트(cc-ra/ 의 부모)에서 실행

# 1) Python 의존성
pip install -r cc-ra/skill/requirements.txt

# 2) Claude Code Skill 설치
#    cc-ra/skill/ → ~/.claude/skills/cc-ra/  (Windows: %USERPROFILE%\.claude\skills\cc-ra\)
pwsh -NoProfile -ExecutionPolicy Bypass -File cc-ra/install.ps1

# 3) (권장) cargo-modules
cargo install cargo-modules
```

---

## 사용

Claude Code 세션에서:

```
/cc-ra D:/path/to/rust/workspace
```

### 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--scope <glob>` | `src/**/*.rs` | 분석 파일 범위 한정 |
| `--since-commit <ref>` | — | git 변경 파일만 분석 |
| `--positions <list>` | 전체 8개 | 활성 사고 포지션 선택 |
| `--threshold <float>` | `0.4` | confidence cutoff |
| `--no-static` | — | cargo check/clippy 보조 스킵 |
| `--config <path>` | `.cc-ra/config.toml` | 설정 파일 경로 |

---

## 무엇을 탐지하는가

8개 카테고리 — Clippy 가 잡지 못하는 클래스:

| Code | Category | 예시 |
|------|----------|------|
| **A** | Temporal / Frame Ordering | frame N 처리가 frame N+1 에서야 반영 |
| **B** | Implicit Invariant Violation | 암묵 contract 가 특정 경로에서 깨짐 |
| **C** | State Coupling Gap | 함께 변해야 할 필드가 한 경로에서만 갱신 |
| **D** | Event Leakage / Layering | UI 클릭이 의도 외 레이어로 전파 |
| **E** | Cache / Recompute Aggression | stale cache, 매 프레임 재계산으로 사용자 액션 덮어쓰기 |
| **F** | Architecture / Abstraction Leak | God module, 결합도 폭증 |
| **G** | Domain-specific Hazard | UTF 경계, IME 함정, 도메인 특유의 가정 |
| **H** | Spec ↔ Implementation Drift | CLAUDE.md/README 주장 ↔ 코드 불일치 |

**절대 보고하지 않는 것**: clippy lint, 함수 길이, 변수명, 포맷, dead code.

---

## 8 Thinking Positions

모두 동일한 feature_tree 를 본다. 영역 분업 없음. **사고 양식만 다름**.

| Position | 사고 양식 | 핵심 질문 |
|----------|---------|---------|
| **Skeptic** | 모든 주장 의심 | "이 함수가 이름대로 정말 동작하는가?" |
| **Paranoid** | 어떻게 깨질까만 | "이 state 를 깨뜨리는 최소 시퀀스는?" |
| **Historian** | 시간 축·레거시 가정 | "새 기능 추가로 기존 가정이 깨진 곳?" |
| **Newcomer** | 처음 본 시각 | "함수 이름과 몸체가 일치하는가?" |
| **Adversary** | 깨뜨리기 | "최악의 입력은? feature 조합으로 깰 수 있나?" |
| **Holist** | 연결고리·상호작용 | "이 state 를 읽는/쓰는 leaf 의 교집합?" |
| **Reductionist** | 최소 반례 | "이 버그의 minimal repro 는?" |
| **Auditor** | AC 검증 + 전수 패턴 검사 | "inferred_AC 가 모든 경로에서 지켜지나? replace_silent 전수 확인?" |

> **v0.3 Auditor 강화**: `replace_silent` / `buf.insert` / `buf.remove` 전수 grep → undo gap, dirty flag 누락, cache key 누락 패턴 탐지.

---

## 8 Phase 파이프라인

```
[Phase 1  ] Context Build           — Python 헬퍼 4종 실행
[Phase 1.5] Feature Reverse-Eng     — 코드 → Gantree + PPR (설계 문서 금지)
[Phase 2  ] Hypothesis Generation   — 6-Axis 위험 지대 가설 (≥ 20개)
[Phase 2.5] Scenario Derivation     — leaf 마다 5유형 시나리오 합성
[Phase 3  ] Position Analysis       — 8 포지션 (병렬 Agent 또는 inline simulation)
[Phase 3.5] Design Drift            — 설계 문서 ↔ 코드 불일치 탐지
[Phase 4  ] Triage                  — 클러스터링·검증·점수화·Sibling Spread
[Phase 5  ] Report                  — REPORT-{date}.md 생성
```

> **v0.3 dispatch mode**: 코드베이스 규모에 따라 자동 선택
> - `src_lines > 1000` 또는 `hypotheses > 15` → 실제 Agent 병렬 dispatch
> - 소규모 → 현 세션 inline simulation

> **v0.3 Hypothesis Axis 6**: `replace_silent` / `buf.insert` / `buf.remove` 전수 grep → undo/mutation gap 후보 목록화

> **v0.3 Sibling Pattern Spread**: finding 확정 시 동류 패턴의 다른 위치 전수 확인 → `sibling_locations` 필드로 보고

---

## 산출물

`<WORKSPACE>/.cc-ra/` 하위:

| 파일 | Phase | 용도 |
|------|-------|------|
| `_meta.json` | 1 | cargo metadata 슬림 |
| `_module_graph.json` | 1 | 모듈 그래프 + 사이클 |
| `_symbols.json` | 1 | tree-sitter 심볼 인덱스 |
| `_invariants.json` | 1 | design_claims (격리 보관) |
| `_context.json` | 1 | 위 4개 통합 |
| `_feature_tree.json` | 1.5 | 기능별 Gantree |
| `decomposition/*.pg.md` | 1.5 | leaf 단위 PPR + inferred_AC |
| `_hypotheses.json` | 2 | 위험 가설 목록 |
| `_scenarios.json` | 2.5 | 기능별 시나리오 |
| `_traces_<pos>/*.pg.md` | 3 | 포지션별 심볼릭 trace (×8) |
| `_findings_<pos>.json` | 3 | 포지션별 raw findings (×8) |
| `_drift.json` | 3.5 | 설계 드리프트 (H 카테고리) |
| `_findings.json` | 4 | 최종 finding (sibling_locations 포함) |
| `_triage_log.json` | 4 | false positive 폐기 기록 |
| **`REPORT-{date}.md`** | **5** | **사용자용 최종 보고서** |
| `status.json` | 5 | 메타 + 통계 |
| `findings.db.json` | 5 | incremental 비교용 |

---

## 디렉터리 구조

```
cc-ra/
├── README.md                          ← 이 파일
├── cc-ra-technical-specification.md   ← 전체 기술 명세
├── install.ps1                        ← skill 설치 스크립트
├── skill/                             ← Claude Code skill 소스 (install.ps1 이
│   │                                    .claude/skills/cc-ra/ 로 통째로 복사)
│   ├── SKILL.md                       ← 진입점 + phase 오케스트레이션
│   ├── requirements.txt               ← pip 의존성 (tree-sitter, networkx)
│   ├── lib/                           ← Python 헬퍼 (설치 후 skill 과 함께 배포)
│   │   ├── workspace_meta.py          ← cargo metadata 파싱
│   │   ├── module_graph.py            ← cargo-modules + networkx 그래프
│   │   ├── symbol_index.py            ← tree-sitter Rust AST 심볼
│   │   ├── invariant_extract.py       ← 주석/assert/MD invariant 추출
│   │   ├── assemble_context.py        ← Phase 1 산출 통합
│   │   └── render_report.py           ← findings.json → markdown
│   ├── phases/
│   │   ├── 01_context_build.md
│   │   ├── 01_5_feature_reverse.md
│   │   ├── 02_hypothesis.md           ← v0.3: Axis 6 추가
│   │   ├── 02_5_scenario_derive.md
│   │   ├── 03_position_analysis.md    ← v0.3: dispatch mode 분기
│   │   ├── 03_5_design_drift.md
│   │   ├── 04_triage.md               ← v0.3: Sibling Spread + Naive Fix 경고
│   │   └── 05_report.md
│   ├── personas/
│   │   ├── _template.md
│   │   ├── skeptic.md
│   │   ├── paranoid.md
│   │   ├── historian.md
│   │   ├── newcomer.md
│   │   ├── adversary.md
│   │   ├── holist.md
│   │   ├── reductionist.md
│   │   └── auditor.md                 ← v0.3: 전수 패턴 검사 추가
│   └── references/                    ← 번들된 외부 의존 스킬
│       └── pg.md                      ← PG (PPR/Gantree) 표기법 v1.3
└── .pgf/
    ├── DESIGN-CcRa.md
    ├── WORKPLAN-CcRa.md
    └── FINAL-REPORT-CcRa-v0.2.md
```

**설치 후 배포 구조** (`.claude/skills/cc-ra/`):
```
.claude/skills/cc-ra/
├── SKILL.md
├── requirements.txt   ← pip 의존성
├── lib/               ← Python 헬퍼 (CC_RA_LIB 이 이 경로를 가리킴)
│   └── *.py
├── phases/
└── personas/
```

---

## 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|---------|
| **v0.3** | 2026-04-21 | Axis 6 (Undo/Mutation Gap), Auditor 전수 패턴 검사, dispatch mode 분기, Sibling Pattern Spread, Naive Fix 경고 |
| v0.2 | 2026-04-20 | 8 Thinking Positions (역할→사고양식), Feature Gantree 역공학, 시나리오 파생, Design Drift phase, PG 구조 trace |
| v0.1 | 2026-04-20 | 초기 릴리즈 — 8 역할 페르소나, 5-phase 파이프라인 |

---

## 기술 명세

전체 설계 원칙, 아키텍처, 이론적 배경, 렌즈 시스템 계획(v0.4):

→ [cc-ra-technical-specification.md](cc-ra-technical-specification.md)
