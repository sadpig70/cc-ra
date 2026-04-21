# Phase 02.5 — Scenario Derivation ★ v0.2

> 각 leaf 에 대해 **심볼릭 트레이스용 시나리오 목록** 생성.
> Phase 3 (Position Analysis) 의 "입력 재료".

---

## 입력

- `{WORKSPACE}/.cc-ra/_feature_tree.json`
- `{WORKSPACE}/.cc-ra/decomposition/*.pg.md`
- `{WORKSPACE}/.cc-ra/_hypotheses.json` (Phase 2 산출)

## 산출

- `{WORKSPACE}/.cc-ra/_scenarios.json`

---

## 시나리오 타입 (5 유형)

각 leaf 에 최소 3 시나리오, 가능하면 5:

### Type 1 — Happy Path
정상 사용 시퀀스. sanity check. 이 시나리오에서 문제가 있으면 기본 버그.

### Type 2 — Boundary
극단 입력:
- 빈 입력 (empty string, zero count, None)
- 단일 원소 (len=1, 첫/끝 위치)
- 최대 입력 (huge string, 많은 라인)
- 유니코드 특이 (emoji, surrogate, 결합 마크)
- 특수 문자 (null byte, EOL, BOM)

### Type 3 — State Transition
상태 A → B → A 순환. 여러 번 반복. idempotency 확인.

### Type 4 — Feature Interaction
2개 feature 동시 활성화 또는 순차 조합:
- Find + Edit
- Wrap + ScrollBar
- MultiCursor + Replace
- Tab Drag + Close

### Type 5 — Error / Adversarial
비정상:
- 외부 자원 실패 (파일 없음, 권한 거부)
- 빠른 연속 입력 (프레임보다 빠른)
- 설정 변경 중 액션
- ReDoS 패턴, 거대 regex

---

## _scenarios.json 스키마

```json
{
  "by_feature_path": {
    "FindReplace::ComputeMatches::RestoreCurrent": [
      {
        "id": "SC-RC-1",
        "type": "happy",
        "name": "F3 연타 기본",
        "setup": "문서 'foo bar foo baz foo'. 커서 0.",
        "sequence": ["Ctrl+F", "F3", "F3"],
        "expected": "current = 0 → 1 → 2"
      },
      {
        "id": "SC-RC-2",
        "type": "state_transition",
        "name": "편집 후 재진입 시 위치 기억 상실",
        "setup": "...",
        "sequence": [...],
        "expected": "..."
      }
    ],
    "FindReplace::SeekMatch": [...],
    ...
  }
}
```

---

## Step 2.5.1 — 각 leaf 순회

각 leaf 에 대해:
1. PPR spec 의 branches 를 읽어 각 분기마다 최소 시나리오 1개 (branch coverage)
2. inferred_AC 각각에 대해 위반 가능 시나리오 추가
3. Type 1~5 중 적용 가능한 것 모두 합성
4. `_hypotheses.json` 에 해당 leaf 와 연결된 가설이 있으면 그 가설을 커버하는 시나리오 추가

## Step 2.5.2 — Cross-leaf 시나리오

Type 4 (Feature Interaction) 는 단일 leaf 에 속하지 않음. 별도 섹션:

```json
{
  "cross_feature": [
    {
      "id": "CF-1",
      "name": "Find open + 외부 파일 변경",
      "features": ["FindReplace::OpenFind", "FileLifecycle::ExternalChangeDetect"],
      "setup": "Find 팝업 열린 상태, 외부 툴이 파일 수정",
      "sequence": [...],
      "expected": "matches 재계산 여부"
    }
  ]
}
```

## Step 2.5.3 — Hypothesis 커버리지 체크

각 `_hypotheses.json` 항목이 최소 1 개 시나리오로 커버되어야 함. 누락 있으면 시나리오 추가.

---

## 자기 검증

- [ ] 모든 leaf 에 ≥ 3 시나리오
- [ ] 모든 Type (1~5) 에 ≥ 1 시나리오 (전체 합계)
- [ ] `cross_feature` ≥ 5 시나리오
- [ ] `_hypotheses.json` 의 100% 가 어떤 시나리오에 커버됨
- [ ] 각 시나리오에 setup, sequence, expected 모두 기입

## 다음 phase

→ `03_position_analysis.md`
