# Phase 03 — Position Analysis (Multi-Position Parallel) ★ v0.2 재작성

> 8 사고 포지션이 **동일한 feature_tree + scenarios + 원본 코드** 를 각자 분석.
> **분업 아님. 공유.** 전원이 전체를 본다. 경계 없음.

---

## 입력

- `{WORKSPACE}/.cc-ra/_feature_tree.json`
- `{WORKSPACE}/.cc-ra/decomposition/*.pg.md`
- `{WORKSPACE}/.cc-ra/_scenarios.json`
- `{WORKSPACE}/.cc-ra/_hypotheses.json`
- 원본 소스 코드

**금지**: `{WORKSPACE}/.cc-ra/_design_claims.json`, 어떤 설계 MD 문서도.

## 산출 (각 포지션마다)

- `{WORKSPACE}/.cc-ra/_traces_<position>/` — trace 파일 폴더 (각 trace 가 .pg.md)
- `{WORKSPACE}/.cc-ra/_findings_<position>.json` — Divergence 노드 통합 추출

8 포지션 ID:
- `skeptic`, `paranoid`, `historian`, `newcomer`
- `adversary`, `holist`, `reductionist`, `auditor`

---

## Step 3.1 — Parallel Dispatch (8 포지션)

**단일 메시지로 8 Agent tool use block** 병렬 spawn:

```
Agent({
  description: "Position analysis: {position_id}",
  subagent_type: "general-purpose",
  prompt: """
    너는 cc-ra 의 {position_id} 사고 포지션이다.

    ## 역할 정의
    {personas/{position_id}.md 의 전체 내용}

    ## 공통 원칙 (모든 포지션 공통)
    {personas/_template.md 의 "공통 원칙" 섹션}

    ## 컨텍스트 파일
    - Feature tree: {WORKSPACE}/.cc-ra/_feature_tree.json
    - Decomposition: {WORKSPACE}/.cc-ra/decomposition/*.pg.md (폴더 전체 Read)
    - Scenarios: {WORKSPACE}/.cc-ra/_scenarios.json
    - Hypotheses: {WORKSPACE}/.cc-ra/_hypotheses.json
    - 원본 코드: Read 도구로 직접 접근

    ## 금지
    - {WORKSPACE}/.cc-ra/_design_claims.json 접근 금지
    - CLAUDE.md, README.md, .pgf/DESIGN-*.md 읽기 금지
    - "내 영역 아니다" 류 경계 표현 금지
    - Clippy 수준 lint 보고 금지

    ## 작업
    1. feature_tree 전체를 본다. 특정 모듈/기능에 한정하지 않는다.
    2. _scenarios.json 에서 트리거될 수 있는 시나리오 선택 (최소 5개).
    3. 각 시나리오에 대해 심볼릭 코드 추적 수행.
       - 원본 코드 Read 로 함수 본문 확인
       - 단계별 state 변화 기록
       - PPR spec 의 inferred_AC 위반 여부 확인
    4. 각 trace 를 PG 구조 (.pg.md) 로 저장:
       {WORKSPACE}/.cc-ra/_traces_{position_id}/<trace_id>.pg.md
    5. Divergence 발견은 trace 내 일급 노드로.
    6. 모든 trace 완료 후 Divergence 노드들을 JSON 으로 통합:
       {WORKSPACE}/.cc-ra/_findings_{position_id}.json

    ## 출력 보고 (메시지 마지막)
    "DONE: {position_id} | traces={N} | divergences={M} | top:{short_claim}"
  """,
  run_in_background: false
})
```

**중요**: 단일 메시지에 Agent 호출 8개를 모두 포함 → 병렬 실행.

## Step 3.2 — 결과 집계

각 Agent 의 마지막 "DONE:" 줄 파싱하여 진단 출력:

```text
[CC-RA Phase 3] Position analysis complete
  skeptic:       4 traces, 6 divergences  (top: close state asymmetry)
  paranoid:      6 traces, 9 divergences  (top: wrap scroll desync)
  historian:     4 traces, 5 divergences  (top: find session memory partial)
  newcomer:      3 traces, 4 divergences  (top: replace_silent naming)
  adversary:     5 traces, 7 divergences  (top: replace all no undo)
  holist:        6 traces, 8 divergences  (top: ensure_cursor vs wheel)
  reductionist:  N/A (refined 3 divergences to minimal repro)
  auditor:       4 traces, 4 divergences  (top: compute_matches idempotence)
  TOTAL raw: 43 divergences (pre-triage)
```

## Step 3.3 — 실패 처리

포지션 Agent 이 다음 실패 시:
- Invalid JSON 산출
- 0 divergence (너무 방어적일 가능성 — 드문 포지션)
- design 문서 참조 감지

→ 한 번 재시도 (prompt 보강 with "반드시 PG 구조, 설계 문서 참조 금지 확인")
→ 두 번째도 실패 시 skip, 보고서에 "position_<id>: skipped, reason" 기록

## Step 3.4 — Concurrence 예비 계산

모든 `_findings_<position>.json` 을 스캔하여 **동일 `hazard_point`** 을 플래그한 포지션 수를 임시 계산. Phase 4 triage 의 입력.

---

## 중요 가이드 (포지션 프롬프트 재확인)

각 포지션 프롬프트에 **필수 포함** 어구:
- "너는 전체 feature_tree 를 본다. 영역 제한 없다."
- "이 시스템의 모든 코드에 대해 너의 시각을 적용하라."
- "설계 문서를 절대 읽지 마라. code + feature_tree + scenarios 만 본다."
- "분석은 PG 구조 trace 로. prose 장문 금지."

---

## 자기 검증

- [ ] 8개 `_findings_<position>.json` 모두 존재 (skip 없이)
- [ ] 각 파일 valid JSON
- [ ] 각 포지션 ≥ 3 divergence
- [ ] 모든 trace .pg.md 파일이 PG 구조 준수
- [ ] grep 설계 문서 참조 → 0 건
- [ ] concurrence 예비 계산 완료 (hazard_point 별 포지션 수)

## 다음 phase

→ `03_5_design_drift.md` (별도)
→ `04_triage.md`
