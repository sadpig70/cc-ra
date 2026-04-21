# WORKPLAN-CcRa.md (v0.2)

> [DESIGN-CcRa.md](DESIGN-CcRa.md) 의 v0.2 Gantree 를 빌드·실행 작업 단위로 변환.
> v0.1 은 `FINAL-REPORT-CcRa-v0.1.md` 로 보존됨. 본 WORKPLAN 은 v0.2 빌드 + 실행 절차.

---

## POLICY

```toml
[execution]
max_parallel_positions = 8
fork_context_per_position = true   # 각 포지션 격리 컨텍스트
max_verify_cycles = 2
fail_fast = false
incremental = true

[principles]
# 분석 중 반드시 준수
code_only_reverse = true           # Phase 1.5~3 에서 design_claims 접근 금지
no_persona_boundaries = true       # 포지션 프롬프트에 "너의 영역" 금지
pg_structured_trace = true         # 모든 trace 는 Gantree + PPR
shared_artifact = true             # 분업 없음. 전 포지션 동일 트리 받음
```

---

## Build Phases (v0.2 빌드 절차)

```
WP // cc-ra v0.2 build (in-progress)
    P0_Setup // (done) v0.1 에서 완료 — 디렉터리, 의존, Python 검증

    P1_DesignDoc // DESIGN v0.2 (done)
        DESIGN-CcRa.md // 7 원칙 + v0.2 Gantree + AC

    P2_WorkplanDoc // 본 문서 (in-progress)

    P3_SkillRewrite // v0.2 skill 재작성 (designing)
        PersonaTemplate // _template.md — 사고 포지션 공통 스키마
        Positions8 // 8 사고 포지션 .md
            [parallel]
            Skeptic, Paranoid, Historian, Newcomer,
            Adversary, Holist, Reductionist, Auditor
            [/parallel]
        Phases5_7 // 5 phase → 7 phase 확장
            Phase01_ContextBuild // 소폭 업데이트 (DesignClaims 격리)
            Phase01_5_FeatureReverse // ★신규
            Phase02_Hypothesis // 입력 확장 (feature_tree 기반)
            Phase02_5_ScenarioDerive // ★신규
            Phase03_PositionAnalysis // 재작성 (포지션 + 심볼릭 트레이스)
            Phase03_5_DesignDrift // ★신규
            Phase04_Triage // ConcurrenceScoring 추가
            Phase05_Report // feature_path 좌표 + trace 재현 포맷
        SKILL_md // v0.2 flow 반영

    P4_Install // .claude/skills/cc-ra/ 재설치 (designing) @dep:P3_SkillRewrite

    P5_TechnicalDocument // cc-ra-technical-specification.md (designing)
        // standalone 기술서 — 철학·아키텍처·사용·한계 총집

    P6_FinalReport // FINAL-REPORT-CcRa-v0.2.md + status 갱신 (designing) @dep:P4,P5

    P7_Execute // 실제 분석 실행 (사용자 invocation 대기)
        // /cc-ra D:/Tools/MSharp → 12 L2 feature decomposition + 8 position analysis
```

---

## 각 노드 → 산출 파일

| Node | File |
|------|------|
| DESIGN-CcRa | `cc-ra/.pgf/DESIGN-CcRa.md` |
| WORKPLAN | `cc-ra/.pgf/WORKPLAN-CcRa.md` |
| PersonaTemplate | `cc-ra/skill/personas/_template.md` |
| Positions8 | `cc-ra/skill/personas/{skeptic,paranoid,historian,newcomer,adversary,holist,reductionist,auditor}.md` |
| Phase01_ContextBuild | `cc-ra/skill/phases/01_context_build.md` |
| Phase01_5_FeatureReverse | `cc-ra/skill/phases/01_5_feature_reverse.md` |
| Phase02_Hypothesis | `cc-ra/skill/phases/02_hypothesis.md` |
| Phase02_5_ScenarioDerive | `cc-ra/skill/phases/02_5_scenario_derive.md` |
| Phase03_PositionAnalysis | `cc-ra/skill/phases/03_position_analysis.md` |
| Phase03_5_DesignDrift | `cc-ra/skill/phases/03_5_design_drift.md` |
| Phase04_Triage | `cc-ra/skill/phases/04_triage.md` |
| Phase05_Report | `cc-ra/skill/phases/05_report.md` |
| SKILL_md | `cc-ra/skill/SKILL.md` |
| Install | `cc-ra/install.ps1` (기존 재실행) |
| TechnicalDocument | `cc-ra/cc-ra-technical-specification.md` |
| FinalReport | `cc-ra/.pgf/FINAL-REPORT-CcRa-v0.2.md` |

**참고**: v0.1 페르소나 파일 (`architect.md`, `invariant_hunter.md` 등 8개) 은 rewrite 후 **교체됨**. 파일명은 유지하는 것이 아니라 새 포지션 이름으로 재생성. 기존 파일은 v0.1 FINAL-REPORT 에 참조로만 남음.

---

## 실행 순서

1. **P1 DESIGN** — 이미 완료됨
2. **P2 WORKPLAN** — 본 문서, 작성 중
3. **P3 Skill Rewrite** — 순서:
   a. `_template.md` (포지션 공통 스키마 먼저)
   b. 8 포지션 파일 (template 을 따라 작성)
   c. Phase 프롬프트 7개 (`01`→`05`, `01_5`/`02_5`/`03_5` 신규)
   d. `SKILL.md` (마지막 — 위 전부 참조)
4. **P4 Install** — `install.ps1` 재실행
5. **P5 Technical Document** — 독립 기술서
6. **P6 Final Report** — v0.2 빌드 완료 보고서
7. **P7** — 사용자의 `/cc-ra D:/Tools/MSharp` invocation 대기

---

## 이전 산출 (v0.1) 보존

- `cc-ra/.pgf/FINAL-REPORT-CcRa-v0.1.md` — v0.1 빌드 결과 유지
- `cc-ra/.pgf/status-CcRa.json` — v0.2 로 갱신되나 v0.1 빌드 결과는 `build_artifacts` 에 남음
- `.cc-ra/decomposition/05_FindReplace.pg.md` — 파일럿 산출물. v0.2 결과의 일부로 인정

---

**Status**: P1 완료, P2 본 문서, P3~P6 순차 진행
