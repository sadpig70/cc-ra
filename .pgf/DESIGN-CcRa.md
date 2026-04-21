# DESIGN-CcRa.md — Claude Code Rust Analyzer v0.2

> **Post-LLM 시대의 논리·설계 오류 분석 방법론**
> AI(코드 읽는 귀신)라는 새 관찰자가 등장했기에 가능해진 분석 체계. 사람·결정론 툴에 맞춰진 기존 리뷰 방법론을 답습하지 않고, LLM 이 잘 할 수 있는 것(다시각 유지·대규모 심볼릭 추적·구조화 DSL 산출)을 전제로 재설계.

- **Project**: cc-ra v0.2
- **Runtime**: Claude Code CLI (Opus 4.7) + Python 3.10+ helpers
- **Target**: 임의 Rust workspace (1차 검증: MSharp)
- **Previous**: v0.1 (역할 기반 페르소나, 심볼 리뷰) — 빌드 완료, 본 문서로 승격

---

## 1. 7 Core Principles (설계 철학)

| # | 원칙 | 근거 |
|---|------|------|
| ① | **기능별 BFS Gantree** (모듈 아닌) | 한 기능이 여러 모듈에 흩어져 있음. 모듈 기반 분석은 조각만 봄 → 조율 갭 사각지대. 기능 단위가 사용자가 시스템에 약속하는 것. |
| ② | **PG 역공학** — 코드 → Gantree + PPR | LLM 이 이해하는 의도 표기로 변환. Rust 문법에 숨긴 가정·분기·파이프라인이 명시됨 |
| ③ | **코드만 역공학** (설계 문서 차단) | 같은 설계 문서로 구현하고 리뷰하면 설계 자체 오류는 양쪽에서 같은 맹점. Design drift 는 분석 완료 후 별도 phase 에서만 비교 |
| ④ | **공유 분석** (분업 금지) | LLM 은 전체를 받을 수 있음 — 사람 시대의 분업 제약 없음. 모든 포지션이 동일 트리를 본다 |
| ⑤ | **사고 포지션** (역할 아닌) | 역할 경계 = 사각지대. 포지션은 시각·질문 방식만 다름. 영역 제한 없음 |
| ⑥ | **심볼릭 코드 추적** (실행 아님) | 테스터가 코드를 따라 읽듯 단계별 state trace. 상태 전이 버그·feature 상호작용 버그가 자연스럽게 노출 |
| ⑦ | **분석 자체도 PG** (Recursive PG) | 장문 prose 배제. Gantree 노드 + PPR 요약. Divergence 는 일급 노드 (@category/@severity/@confidence/@hazard_point). 스케일 + 기계가독성 |

---

## 2. Non-Goals (의도적 제외)

| 제외 | 이유 |
|------|------|
| Clippy 수준 lint 재구현 | cargo clippy 가 함. cc-ra 는 보조 신호로만 |
| 자동 실행 기반 테스트 | 심볼릭 추적만. 실제 실행은 사용자/CI 영역 |
| 스타일·포맷 | rustfmt 영역 |
| 멀티 언어 | Rust 전용. 다른 언어는 별도 분석기 |
| 자동 fix | v0.3 이연. v0.2 는 탐지·설명·재현경로가 목표 |

---

## 3. 분석 대상 버그 카테고리 (Taxonomy, v0.1 동일 유지)

| Code | Category | 예시 (오늘 MSharp 세션 실제 버그) |
|------|----------|---------------------------------|
| A | Temporal/Frame Ordering | `draw_find` 후 seek 가 다음 프레임에 반영, 휠 vs ensure_cursor_visible 경쟁 |
| B | Implicit Invariant Violation | `recompute` 매 프레임 current 리셋으로 F3 연타 깨짐 |
| C | State Coupling Gap | close 시 matches 만 비우고 cursors 선택 잔존, query/current 기억 비대칭 |
| D | Event Leakage / Layering | Area 팝업 여백 클릭이 에디터 클릭으로 새는 |
| E | Cache/Recompute Aggression | ensure_cursor_visible 매 프레임, 휠 스크롤 봉쇄 |
| F | Architecture / Abstraction Leak | app.rs out=11 — God module |
| G | Domain-specific Hazard | wrap 모드 row_h 고정 가정으로 off-screen 매치 seek 실패 |
| H | Spec ↔ Implementation Drift | AC 선언은 하나 wrap 모드 가정 없음 |

---

## 4. Gantree (v0.2 아키텍처)

```
CcRa // Claude Code Rust Analyzer (in-progress) @v:0.2
    Inputs // 입력 처리 (done-v0.1)
        WorkspaceDetect, ScopeFilter, ConfigLoad
        SpecIsolate // MD 문서를 design_claims 로 격리 (v0.2 신규 명명)

    ContextBuilder // Phase 1 — 구조적 사실 (done-v0.1)
        ModuleGraph (cargo-modules 통합)
        SymbolIndex (tree-sitter)
        DataFlowMap
        DesignClaims // 별도 artifact. 분석 중 금지. Phase 3.5 전용

    FeatureReverseEngine // Phase 1.5 ★v0.2 신규
        SystemPurposeIdentify // main / pub API / entry points 에서 귀납
        Level2Features // 대 기능 BFS 첫 확장
        BFSRecursiveDecomp // 15분 룰 원자까지
        CodeLocationMap // 각 기능 → code 조각 역인덱스 (cross-cutting)
        PPRSpec // 각 leaf 의 입출력/분기/파이프/추론AC
        InferredAC // 코드가 실제 보장하는 것 (설계 문서 참조 없음)

    ScenarioDerivation // Phase 2.5 ★v0.2 신규
        HappyPath // 각 leaf 의 정상 시퀀스
        BoundaryScenarios // 빈/단일/거대/유니코드
        FeatureInteractionMatrix // 2 leaf 동시 자극
        StateTransitionStress // 상태 머신 edge case

    HypothesisGen // Phase 2 (v0.1 유지, 인풋 확장)
        // 이제는 _feature_tree.json + _scenarios 에서 가설 도출

    PositionAnalysis // Phase 3 ★v0.2 대폭 재설계
        // 8 사고 포지션 병렬 — 분업 아님, 공유
        [parallel]
        Skeptic, Paranoid, Historian, Newcomer,
        Adversary, Holist, Reductionist, Auditor
        [/parallel]
        // 각자 동일 feature_tree + scenarios + 원본 코드 받음
        // 산출: Trace_<id> Gantree + Divergence 노드 (PG 구조)

    DesignDrift // Phase 3.5 ★v0.2 신규
        CollectClaims // design_claims.json 에서 모든 주장 수집
        TraceToCode // 각 주장 → feature_tree 매핑
        FlagDrift // 주장 ↔ 실제 동작 불일치 식별

    Triage // Phase 4 (재설계)
        ClusterByFeaturePath // feature_path × hazard_point 좌표
        ConcurrenceScoring // 동일 좌표를 N 포지션이 플래그 → confidence 주 signal
        Verify // 심볼릭 트레이스 재추적으로 false positive 제거
        PriorityScore // severity × likelihood × blast × concurrence_boost

    Reporting // Phase 5 (템플릿 확장)
        DeepReport // feature_path 좌표 + trace 재현 + 수정 제안
        StatusJson
        SummaryDigest // 5분 요약
```

---

## 5. PPR — 핵심 노드 상세 (v0.2 추가/변경)

### 5.1 FeatureReverseEngine (신규)

```python
def feature_reverse_engine(ctx: CodeContext) -> FeatureTree:
    """코드만 보고 기능별 Gantree + PPR 구축. design_claims 는 접근 금지."""
    # acceptance_criteria (cc-ra self-AC):
    #   - 모든 entry point 가 어떤 L2 feature 에 귀속
    #   - 각 leaf 에 code_locations ≥ 1, inferred_AC ≥ 1
    #   - cross_cutting_modules (여러 모듈에 걸친 기능) 명시
    #   - 15분 룰 원자까지 분해

    purpose = AI_identify_system_purpose(ctx.entry_points, ctx.symbols)
    l2_features = AI_decompose_by_observable_behavior(purpose, ctx)
    queue = list(l2_features)
    tree = FeatureTree(root=purpose, children=l2_features)

    while queue:
        feature = queue.pop(0)
        if is_atomic_by_15min_rule(feature):
            feature.ppr_spec = AI_synthesize_ppr(feature, ctx)
            feature.inferred_AC = AI_infer_ac_from_code(feature.ppr_spec)
            continue
        subs = AI_decompose_feature(feature, ctx)
        feature.children = subs
        queue.extend(subs)

    return tree
```

### 5.2 PositionAnalysis (재설계)

```python
def position_analysis(feature_tree: FeatureTree, scenarios: list, code: CodeContext) -> list[Finding]:
    """8 사고 포지션 병렬 — 분업 아님, 공유."""
    # acceptance_criteria:
    #   - 각 포지션 ≥ 3 trace 산출
    #   - 각 trace 는 PG 구조 (Trace_<id> / Step_N / Divergence_<id>)
    #   - 영역 제한 언어 ("내 영역 아님") 금지
    #   - design_claims 참조 금지 (Phase 3.5 에서만 허용)

    positions = ["skeptic","paranoid","historian","newcomer",
                 "adversary","holist","reductionist","auditor"]
    [parallel via Agent]
    findings_per_position = {
        p: run_position(p, feature_tree, scenarios, code)
        for p in positions
    }
    [/parallel]

    return flatten(findings_per_position)
```

### 5.3 Symbolic Trace 형식 (예시 참조)

```
Trace_<id> // <시나리오 이름> (status)
    Precondition // state setup
    Stimulus // 사용자 액션 시퀀스
    Frame1_<action> // 프레임별 코드 경로 (L3+ 재귀 분해)
        call_<fn>
            # PPR: 입력/동작/출력 요약
        branch_<condition>
        state_change // 관측 state delta
    State_S1 // 스텝 종료 관측
    Frame2_...
    Divergence_<id> // 발견 @category @severity @confidence @hazard_point
        root_cause, suggested_fix, observable_by_positions, replication
```

---

## 6. Acceptance Criteria (v0.2)

| # | 기준 | 검증 |
|---|------|------|
| AC-1 | MSharp 에 대해 기능 Gantree 12 L2 레벨 생성 | `.cc-ra/decomposition/*.pg.md` 12개 |
| AC-2 | v0.1 의 자동 페르소나 finding 대비 의미적 finding ≥ 2배 | 수동 카운트 |
| AC-3 | 오늘 세션의 실제 버그 (find/wrap/replace 등) 중 ≥ 5개 retro-detect | git revert → 분석 |
| AC-4 | 각 finding 에 PG 구조 trace + replication | REPORT 검수 |
| AC-5 | 8 포지션 모두 ≥ 1 unique finding | 포지션별 count |
| AC-6 | clippy 가 잡을 수 있는 finding 0% (모두 고난이도) | 표본 검수 |
| AC-7 | design_claims 참조 없이 코드 분석 완료 검증 | phase 3 산출물 grep |
| AC-8 | Phase 3.5 drift detection ≥ 1 (CLAUDE.md vs 실제 동작) | REPORT 섹션 |
| AC-9 | 전체 실행 시간 ≤ 60분 (medium 워크스페이스) | wall-clock |
| AC-10 | confidence < 0.4 는 Low Confidence 섹션 분리 | 보고서 구조 |

---

## 7. 산출물 위치

```
.cc-ra/
├── _meta.json, _module_graph.json, _symbols.json, _invariants.json
├── _context.json
├── _feature_tree.json          ★v0.2 — 기능별 Gantree 통합 인덱스
├── decomposition/              ★v0.2 — 기능별 PG 파일
│   ├── 00_root.pg.md
│   ├── 01_FileLifecycle.pg.md
│   ├── …                       (12 L2 features)
│   └── 12_UserCommands.pg.md
├── _scenarios.json             ★v0.2 — leaf 별 시나리오
├── _hypotheses.json
├── _traces_{position}/         ★v0.2 — 포지션별 PG 트레이스 (폴더)
├── _findings_{position}.json   ★v0.2 — 포지션별 Divergence 노드 추출
├── _findings.json              Triage 후 final
├── _drift.json                 ★v0.2 — Phase 3.5 산출
├── REPORT-{date}.md            사용자용 최종
├── status.json
└── findings.db.json            incremental 비교용
```

---

## 8. Phase 순서 (v0.2)

| Phase | 이름 | 입력 | 산출 |
|-------|------|------|------|
| 1 | Context Build | workspace | _context.json |
| 1.5 ★ | Feature Reverse Engine | _context.json (코드만) | _feature_tree, decomposition/*.pg.md |
| 2 | Hypothesis | feature_tree | _hypotheses |
| 2.5 ★ | Scenario Derivation | feature_tree + hypotheses | _scenarios |
| 3 | Position Analysis (8 병렬) | feature_tree + scenarios + code | _traces_{p}, _findings_{p} |
| 3.5 ★ | Design Drift | _findings_* + _design_claims | _drift |
| 4 | Triage | _findings_* + _drift | _findings (final) |
| 5 | Report | _findings + _context | REPORT, status.json |

★ = v0.2 신규 phase

---

## 9. 외부 도구 (v0.1 동일)

- `cargo` (필수), `cargo-modules` (권장, 설치 확인 완료)
- Python 3.11.9, tree-sitter 0.23+, tree-sitter-rust, networkx
- `cargo-audit`, `cargo-geiger`, `cargo expand` (옵션)
- 제외: rust-analyzer, syn (ROI 부족)

---

## 10. 구현 상태

| Phase / Artifact | 상태 |
|------------------|------|
| Python helpers (workspace_meta, module_graph, symbol_index, invariant_extract, assemble_context, render_report) | ✓ v0.1 에서 이미 동작, v0.2 에서 의미 변경 (design_claims 격리) |
| skill/SKILL.md | v0.1 → v0.2 업데이트 필요 |
| skill/personas/ (8개) | v0.1 역할 페르소나 → v0.2 사고 포지션으로 rewrite 필요 |
| skill/phases/ | 01/02/04/05 업데이트, 01.5/02.5/03.5 신규, 03 재작성 |
| decomposition/05_FindReplace.pg.md | ✓ 파일럿 존재, 나머지 11개 미작성 (실제 /cc-ra 실행 시 생성) |

---

## 11. v0.3+ 로드맵

- AutoFix (안전한 패치 자동 + cargo check 회귀)
- Multi-language (Python, TypeScript)
- Watch 모드 (mtime 기반 incremental)
- HTML interactive 보고서
- 시간순 회귀 분석 (git blame × finding)
- LSP (rust-analyzer) — ROI 재평가 후

---

**Signed**: Jung Wook Yang <sadpig70@gmail.com> · Claude Opus 4.7 · 2026-04-20
