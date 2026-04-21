# Phase 03.5 — Design Drift ★ v0.2 신규

> 설계 문서 (`CLAUDE.md`, `README`, `.pgf/DESIGN-*.md` 등) 의 **명시 주장** ↔ **코드 실제 동작** 간 드리프트를 탐지.
> Phase 3 (Position Analysis) 이 코드-only 로 끝난 뒤 별도 phase.
> **The Auditor 포지션만** 이 phase 에서 설계 문서 접근 허용.

---

## 입력

- `{WORKSPACE}/.cc-ra/_feature_tree.json` (코드 역공학 결과)
- `{WORKSPACE}/.cc-ra/_invariants.json` (Phase 1 에서 추출된 design_claims — 이제 활성화)
- Phase 1 에서 수집된 설계 MD 문서들 (CLAUDE.md, README.md, .pgf/DESIGN-*.md)
- `{WORKSPACE}/.cc-ra/_findings_*.json` (Phase 3 산출, 맥락용)

## 산출

- `{WORKSPACE}/.cc-ra/_drift.json` — H 카테고리 Divergence 통합

---

## 원칙

- Phase 3 의 심볼릭 trace 결과 (`_findings_*`) 는 **코드가 실제로 보장하는 것** 의 증거.
- 이 phase 는 그 증거 ↔ 설계 문서 주장 사이의 **불일치** 를 찾는다.
- 드리프트 방향 2 종:
  - **Under-specified**: 코드가 더 엄격한 동작을 하는데 설계 문서에 명시 없음 → 새 AC 제안
  - **Over-promised**: 설계 문서가 주장하는데 코드가 못 지킴 → H category finding

---

## Step 3.5.1 — Claim Collection

설계 문서에서 주장을 수집:

1. `_invariants.json` 의 `kind: "acceptance_criteria"` (AC-N 형식)
2. `_invariants.json` 의 `kind: "doc"` 중 "must/always/보장" 키워드 단락
3. 주석의 assert!/debug_assert! 메시지 (이미 `_invariants.json` 에 있음)
4. README / DESIGN 의 단축키 표 · 지원 포맷 · 기능 목록

각 claim 에 ID 부여 (`CC-001`, `CC-002`, ...).

## Step 3.5.2 — Claim → Feature 매핑

각 claim 을 `_feature_tree.json` 의 leaf 에 매핑 (AI 추론):

```python
claim_to_feature = AI_map_claims_to_features(claims, feature_tree)
# 예:
# "AC-2: 10k줄 PageDown 즉시" → Navigation::PageJump
# "AC-5: 단일 인스턴스" → OSIntegration::SingleInstance
# "Ctrl+F 누르면..." → FindReplace::OpenFind
```

매핑 실패 (대응 leaf 없음) → claim 자체가 구현 안 됨 / 설계 문서가 stale.

## Step 3.5.3 — Drift Detection

각 (claim, feature) 쌍에 대해:

```python
for claim, feature in claim_to_feature.items():
    actual_ac = feature.inferred_AC   # 코드 역공학 결과
    trace_findings = findings_matching_feature(feature, _findings_*)

    drift = AI_compare_claim_vs_actual(
        claim=claim,
        inferred=actual_ac,
        trace_evidence=trace_findings,
    )
    # 종류:
    #   "match": 일치. 기록 안 함.
    #   "over_promise": claim 이 더 강한 주장. 코드 미지킴.
    #   "under_spec": 코드가 더 엄격. claim 에 명시 없음.
    #   "condition_missing": claim 이 모드 조건 생략 (예: wrap=off 만 성립)
    if drift.type != "match":
        drift_divergences.append(drift)
```

## Step 3.5.4 — Trace 생성 (Auditor 포지션 재호출)

각 drift 에 대해 Auditor 포지션 프롬프트로 trace 작성:

```
Trace_Drift_<id> // (needs-verify) @drift_type:<type>
    Claim_Ref // 설계 문서 출처
    Feature_Location // feature_tree 좌표
    Code_Evidence // 실제 동작 (inferred_AC + trace)
    Divergence
        category: "H"
        claim_type: "over_promise | under_spec | condition_missing"
        severity: ...
        confidence: ...
```

## Step 3.5.5 — _drift.json 저장

```json
[
  {
    "id": "DR-001",
    "drift_type": "condition_missing",
    "design_claim_ref": "CLAUDE.md:205 (AC-2)",
    "design_claim": "10k줄 PageDown 즉시",
    "feature_path": "Navigation::PageJump",
    "inferred_ac": ["wrap=off 에서 O(1) per frame"],
    "actual_behavior": "wrap=on 에서 O(N) per frame",
    "severity": 0.5,
    "likelihood": 0.8,
    "confidence": 0.9,
    "suggested_fix": "AC-2 에 '(wrap=off 기준)' 조건 명시. 또는 wrap 모드 최적화.",
    "trace_file": "_traces_auditor/Drift_001.pg.md"
  }
]
```

---

## 자기 검증

- [ ] 모든 `_invariants.json` 의 `kind: acceptance_criteria` 가 claim_to_feature 에 매핑 시도됨
- [ ] 매핑 실패 claim 은 별도 섹션 ("orphan claims") 에 기록
- [ ] 각 drift 에 severity / confidence / suggested_fix 기입
- [ ] `_drift.json` valid JSON

## 다음 phase

→ `04_triage.md` — Phase 3 + Phase 3.5 의 모든 findings 를 통합하여 triage
