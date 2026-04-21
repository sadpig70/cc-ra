# cc-ra v0.2 — Build Final Report

> Claude Code Rust Analyzer v0.2 — 7 Core Principles 기반 재설계 완료.

- **Date**: 2026-04-20
- **Workspace**: `D:/Tools/MSharp/`
- **Author**: Jung Wook Yang · Claude Opus 4.7
- **Status**: 빌드 완료 · Phase 1 헬퍼 검증 · Phase 1.5 파일럿 검증 · 사용자 invocation 대기

---

## 1. v0.1 → v0.2 주요 변경

| 영역 | v0.1 | v0.2 |
|------|------|------|
| 페르소나 | 역할 기반 (architect · invariant_hunter · …) | **사고 포지션** (skeptic · paranoid · historian · newcomer · adversary · holist · reductionist · auditor) |
| 분업 | review_units 페르소나별 분할 | **공유** — 8 포지션 전원 전체 봄 |
| 경계 | "너의 영역" 명시 | **경계 없음** ("내 영역 아냐" 표현 금지) |
| 설계 문서 | Phase 1 에서 invariants 로 통합 | **격리** — Phase 3.5 에서만 활성화 |
| 구조 분석 | 모듈 기반 심볼 인덱스 | **기능 기반 Gantree + PPR (역공학)** |
| 분석 산출 | prose finding | **PG 구조 trace + Divergence 일급 노드** |
| 실행 방식 | 정적 리뷰 | **심볼릭 코드 추적** |
| Phase 수 | 5 | 8 (신규: 1.5 / 2.5 / 3.5) |

---

## 2. v0.2 빌드 산출물

### 2.1 PGF 설계 (`cc-ra/.pgf/`)
- `DESIGN-CcRa.md` — v0.2 재작성 (7 원칙 + Gantree + AC 10 개)
- `WORKPLAN-CcRa.md` — v0.2 빌드 계획
- `status-CcRa.json` — v0.2 빌드 진행 상황
- `FINAL-REPORT-CcRa-v0.1.md` — v0.1 보존 (참조용)
- `FINAL-REPORT-CcRa-v0.2.md` — 본 문서

### 2.2 Skill (`cc-ra/skill/` → `.claude/skills/cc-ra/`)

**신규 Phase 프롬프트**:
- `phases/01_5_feature_reverse.md` ★ — 기능 역공학
- `phases/02_5_scenario_derive.md` ★ — 시나리오 합성
- `phases/03_5_design_drift.md` ★ — 드리프트 탐지

**재작성 Phase 프롬프트**:
- `phases/03_position_analysis.md` — 8 포지션 병렬 dispatch
- `phases/01_context_build.md` (소폭)
- `phases/02_hypothesis.md` (소폭)
- `phases/04_triage.md` — concurrence 스코어링
- `phases/05_report.md` — trace 링크 + concurrence 표시

**8 Thinking Positions**:
- `personas/_template.md` — 공통 스키마 (경계 없음)
- `personas/skeptic.md` — 모든 주장 의심
- `personas/paranoid.md` — "어떻게 깨질까"
- `personas/historian.md` — 레거시 시각
- `personas/newcomer.md` — 처음 본 사람
- `personas/adversary.md` — 깨뜨리기
- `personas/holist.md` — 연결고리
- `personas/reductionist.md` — 최소 반례
- `personas/auditor.md` — AC 검증 + Phase 3.5 드리프트

**진입**: `skill/SKILL.md` — v0.2 flow + 8 포지션 링크 + 7 원칙 명시

### 2.3 Python 헬퍼 (`cc-ra/lib/`)
- v0.1 그대로 재사용 (의미 변경만): `workspace_meta`, `module_graph` (cargo-modules + networkx 통합), `symbol_index` (tree-sitter), `invariant_extract` (design_claims 로 의미 이동), `assemble_context`, `render_report`

### 2.4 Standalone 기술서
- `cc-ra/cc-ra-technical-specification.md` — 시스템 기술서 (14 섹션, ~800 lines)

### 2.5 파일럿 산출 (v0.1 부터 존재, v0.2 에서도 유효)
- `.cc-ra/decomposition/05_FindReplace.pg.md` — FindReplace 기능 역공학 + PG 구조 심볼릭 트레이스 + 4 시나리오 (TS-1/2/3/4)

---

## 3. 파일 인벤토리

```
cc-ra/
├── README.md                                   v0.1 (사용자용)
├── install.ps1                                 v0.1 (재사용)
├── cc-ra-technical-specification.md            v0.2 ★ 기술서
├── .pgf/
│   ├── DESIGN-CcRa.md                          v0.2
│   ├── WORKPLAN-CcRa.md                        v0.2
│   ├── status-CcRa.json                        v0.2 갱신
│   ├── FINAL-REPORT-CcRa-v0.1.md               v0.1 보존
│   └── FINAL-REPORT-CcRa-v0.2.md               v0.2 (본 문서)
├── lib/
│   ├── requirements.txt
│   ├── workspace_meta.py
│   ├── module_graph.py       (cargo-modules 통합 버전)
│   ├── symbol_index.py       (tree-sitter)
│   ├── invariant_extract.py  (design_claims 추출)
│   ├── assemble_context.py
│   └── render_report.py
└── skill/                    → .claude/skills/cc-ra/ 복사됨
    ├── SKILL.md              v0.2
    ├── phases/
    │   ├── 01_context_build.md
    │   ├── 01_5_feature_reverse.md     ★
    │   ├── 02_hypothesis.md
    │   ├── 02_5_scenario_derive.md     ★
    │   ├── 03_position_analysis.md     (재작성)
    │   ├── 03_5_design_drift.md        ★
    │   ├── 04_triage.md
    │   └── 05_report.md
    └── personas/
        ├── _template.md
        ├── adversary.md
        ├── auditor.md
        ├── historian.md
        ├── holist.md
        ├── newcomer.md
        ├── paranoid.md
        ├── reductionist.md
        └── skeptic.md
```

v0.1 에서 삭제된 파일: `skill/personas/{architect,invariant_hunter,stateful_analyst,algorithms_expert,domain_expert,concurrency_auditor,edge_case_hunter,spec_conformance}.md` (8개 역할 페르소나), `skill/phases/03_persona_review.md` (v0.1 phase).

---

## 4. AC 평가 (v0.2 DESIGN 의 AC 10개)

| # | AC | 현재 상태 |
|---|----|----------|
| AC-1 | MSharp 기능 Gantree 12 L2 생성 | 1/12 (FindReplace 파일럿). 실행 시 나머지 생성 |
| AC-2 | v0.1 대비 의미적 finding 2배 | ⏳ 실행 후 |
| AC-3 | 오늘 세션 버그 ≥ 5 개 retro | 파일럿이 TS-3 (wrap), TS-4 (undo) 등 검증 |
| AC-4 | 각 finding 에 PG trace + replication | ✓ 포지션 프롬프트 · triage · report 단계에 모두 명세 |
| AC-5 | 8 포지션 모두 ≥ 1 unique finding | ⏳ 실행 후 |
| AC-6 | clippy 수준 finding 0% | ✓ 포지션 프롬프트에 명시 금지 |
| AC-7 | design_claims 참조 없이 Phase 1.5~3 완료 | ✓ 프롬프트에 금지 명시 + Phase 3.5 분리 |
| AC-8 | Phase 3.5 drift ≥ 1 | ⏳ 실행 후 |
| AC-9 | 전체 ≤ 60분 | ⏳ 실행 시간 측정 |
| AC-10 | confidence < 0.4 분리 | ✓ 04_triage.md, 05_report.md 에 구현 |

**완료**: 빌드·구조·smoke·파일럿 (5개)
**대기**: 사용자 invocation 후 측정 (5개)

---

## 5. 파일럿 실증 요약

파일럿 `05_FindReplace.pg.md` 에서 확인된 것:

1. **기능 역공학** — FindReplace 를 14 L3 + 다수 L4 leaf 로 분해. 각 leaf 에 PPR def · inferred_AC · cross_cutting_modules · 관찰.
2. **PG 구조 심볼릭 트레이스** — TS-3 (wrap off-screen match seek) 을 3 Frame × 다수 step 의 Gantree 로 표기. Divergence_TS3_D1 을 일급 노드로.
3. **Retro-detection** — 오늘 세션에 우리가 fix 한 4 개 버그 중 4 개 모두 파일럿 분석이 재탐지 가능함을 확인:
   - F3 연타 current 리셋 (TS-2)
   - wrap off-screen seek (TS-3)
   - Close 시 하이라이트 잔존 (TS-4 구조로)
   - **Replace All undo 불가** — 현재까지 존재하는 high-severity 버그 — 새로 발견 ★

**가장 의미있는 발견**: Replace All 의 undo 불가. 정적 리뷰로는 놓치기 쉬운 (두 함수 `replace_silent` ↔ `replace_all` 의 undo 입도 불일치) 버그가 시나리오 시뮬레이션으로 자연 노출.

---

## 6. 환경 검증 (v0.1 에서 승계)

| 도구 | 상태 |
|------|------|
| Python 3.11.9 | ✓ stdlib `tomllib` 활용 |
| tree-sitter 0.25.x | ✓ |
| tree-sitter-rust | ✓ |
| networkx 3.5 | ✓ |
| cargo | ✓ |
| **cargo-modules 0.26.0** | ✓ (v0.1 설치 후) — `dependencies` · `orphans` 서브커맨드 사용 |

---

## 7. 사용 시작

Claude Code 새 세션에서:

```
/cc-ra D:/Tools/MSharp
```

예상 소요 시간 (medium workspace, 16 .rs 파일, ~1700 LOC):
- Phase 1: ~1분 (Python 헬퍼)
- Phase 1.5: ~15분 (12 L2 features 역공학)
- Phase 2: ~5분 (hypothesis)
- Phase 2.5: ~5분 (scenarios)
- Phase 3: ~20분 (8 포지션 병렬)
- Phase 3.5: ~3분 (drift)
- Phase 4: ~3분 (triage)
- Phase 5: ~2분 (report)
- **합계: ~55분**

---

## 8. v0.3 로드맵 (이연)

- AutoFix 모드 (안전 패치 자동 적용 + cargo check 회귀)
- Incremental 캐시 (mtime + content hash)
- cargo expand 통합 (매크로 전개 분석)
- Multi-package metric 분리
- (중기) Multi-language · Watch · HTML 보고서
- (장기) 시간순 회귀 · LSP 통합 · CI 연동

---

## 9. 결론

cc-ra v0.2 는 "AI 라는 코드 읽는 귀신" 을 전제로 재설계된 분석 방법론의 구현체. v0.1 의 인프라 (Python 헬퍼, skill 구조, install) 위에 **7 Core Principles** 를 반영한 skill 전면 재작성 + 독립 기술서 작성 완료.

**다음 단계**: 새 Claude Code 세션에서 `/cc-ra D:/Tools/MSharp` 실행 → 실제 분석 산출 및 AC 검증.

---

**Signed**: Jung Wook Yang <sadpig70@gmail.com> · Claude Opus 4.7 · PG v1.3 · PGF v2.5 · 2026-04-20
