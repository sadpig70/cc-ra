# Thinking Position — 공통 스키마 (v0.2)

> 사고 포지션 파일 작성 시 본 구조를 따른다. **역할 기반이 아니라 시각 기반**이다.
> 모든 포지션은 **전체 feature_tree 를 본다**. 영역 분업 없음.

---

## 공통 원칙 (모든 포지션이 따름)

1. **경계 없음** — 너는 전체 기능 트리 전체 코드를 본다. "내 영역 아니다" 라는 표현 금지.
2. **설계 문서 차단** — `CLAUDE.md`, `README.md`, `.pgf/DESIGN-*.md` 같은 설계 문서를 **읽지 않는다**. Phase 3.5 에서만 The Auditor 가 그것을 본다. 너는 코드와 `_feature_tree` 만 본다.
3. **심볼릭 추적** — "이 코드가 이렇게 보인다" 가 아니라 "**이 시나리오를 실행하면 이런 단계 전이가 일어난다**" 로 분석.
4. **PG 구조 산출** — 분석을 **Gantree + PPR** 로 표기한다. Prose 금지.
5. **Divergence 는 일급 노드** — 발견은 trace 내 정식 노드로. 필드 구조화.
6. **Clippy 영역 보고 금지** — unused, redundant clone, missing docs 등 표면적 lint 는 배제.
7. **다른 포지션과 겹쳐도 OK** — 같은 hazard 를 다른 질문 방식으로 건드려도 됨. 그것이 concurrence signal.

---

## 포지션 파일 구조

```markdown
# Position: <이름>

## 시각 (Lens)
이 포지션이 무엇을 본다. 한두 문단. 질문 방식.

## 질문 방식
구체적으로 어떤 종류의 질문을 코드/트리에 던지는가. 3~5 개.

## 주목하는 feature_tree 신호
트리 구조·PPR·inferred_AC 에서 무엇이 발견 단서가 되는가.

## 심볼릭 추적 스타일
이 포지션이 어떻게 코드 경로를 따라가는가. 특이점.

## 산출 형식
Trace_<id> Gantree 로. Divergence 노드 필드 참조.

## 예시 Divergence (참고용)
이 포지션이 산출할 법한 Divergence 노드 하나.
```

---

## 입력 (모든 포지션 공통)

- `{WORKSPACE}/.cc-ra/_feature_tree.json` — 기능 Gantree 통합 인덱스
- `{WORKSPACE}/.cc-ra/decomposition/*.pg.md` — L2 기능별 PG 파일
- `{WORKSPACE}/.cc-ra/_scenarios.json` — Phase 2.5 에서 도출된 시나리오
- `{WORKSPACE}/.cc-ra/_hypotheses.json` — Phase 2 에서 도출된 가설
- 원본 소스 코드 (Read 도구로 직접 접근)
- **금지**: `{WORKSPACE}/.cc-ra/_design_claims.json`, 어떤 `.md` 설계 문서도

---

## 산출 (모든 포지션 공통)

- `{WORKSPACE}/.cc-ra/_traces_<position>/` 폴더 — trace 파일 여러 개 (시나리오 당 1개)
- `{WORKSPACE}/.cc-ra/_findings_<position>.json` — trace 에서 추출된 Divergence 노드 통합

### Trace 파일 형식 (.pg.md)

```
Trace_<id> // <feature_path> :: <scenario_name> (status)
    Precondition
        <state setup>

    Stimulus
        <user actions sequence>

    Frame1_<action> // (in-progress) @dep:stimulus
        call_<fn>
            # PPR: inputs / operation / outputs
            # relevant state reads/writes
        branch_<condition>
        state_change
            <observed state delta>

    State_S1 // frame 종료 상태 snapshot
        <key fields>

    Frame2_...
    State_S2

    ...

    Divergence_<id> // (needs-verify) @hazard_point:<marker>
        category: "A|B|C|D|E|F|G|H"
        severity: 0.0~1.0
        likelihood: 0.0~1.0
        blast_radius: 0.0~1.0
        confidence: 0.0~1.0
        hazard_leaves: [feature_path::leaf, ...]
        root_cause: "한 단락 설명"
        suggested_fix: "코드 패치 또는 설계 변경"
        observable_by_positions: [position_id, ...]   # 예상
        replication:
            minimal_setup: "..."
            steps: [A1, A2, ...]
            observed: "..."
```

### _findings_<position>.json 스키마

```json
[
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
    "hazard_leaves": [...],
    "root_cause": "...",
    "suggested_fix": "...",
    "replication": {...}
  }
]
```

---

## 카테고리 코드 참조 (모든 포지션 공용)

| Code | Category |
|------|----------|
| A | Temporal/Frame Ordering |
| B | Implicit Invariant Violation |
| C | State Coupling Gap |
| D | Event Leakage / Layering |
| E | Cache/Recompute Aggression |
| F | Architecture / Abstraction Leak |
| G | Domain-specific Hazard |
| H | Spec ↔ Implementation Drift (Phase 3.5 전용) |

**H 카테고리**: 포지션 분석 (Phase 3) 에서는 H 를 생성하지 않음. Phase 3.5 Design Drift 가 전담.

---

## 자기 검증 (산출 전)

- [ ] 모든 trace 가 PG 구조 (Gantree + PPR)
- [ ] 모든 Divergence 가 일급 노드로 기록 (필드 완비)
- [ ] design 문서 참조 없음 (grep "CLAUDE.md\|DESIGN-\|README" 0건)
- [ ] 영역 제한 언어 없음 ("내 영역 아니다" 등)
- [ ] clippy 수준 발견 포함 안 됨 (unused, redundant 등)
- [ ] 재현 경로 (replication) 모든 Divergence 에 포함
- [ ] hazard_leaves 가 feature_tree 의 실제 leaf 경로와 매칭

---

## 실패 처리

포지션이 0 trace / invalid JSON 산출 시:
1. 한 번 재시도 (prompt 보강)
2. 두 번째 실패 시 skip, 보고서에 "position_<id>: skipped, reason" 기록
