# Phase 04 — Triage (v0.2)

> 8 포지션의 raw findings + Phase 3.5 design_drift 를 통합·검증·우선순위화.
> **v0.2 핵심 변경**: 클러스터 키가 `feature_path × hazard_point`. Concurrence (동의한 포지션 수) 가 confidence 주 신호.

---

## 입력

- `{WORKSPACE}/.cc-ra/_context.json`
- 8개 `_findings_{persona}.json`

## 산출

- `{WORKSPACE}/.cc-ra/_findings.json` — 검증/통합된 최종 Finding 배열

```json
[
  {
    "id": "F001",
    "category": "B",
    "title": "한 줄 요약 (보고서 헤더용)",
    "personas": ["invariant_hunter", "stateful_analyst"],
    "personas_concur": true,           // 둘 이상 페르소나가 같은 결론?
    "location": "src/find.rs:67-119",
    "claim": "...",
    "scenario": "...",
    "evidence": ["..."],
    "root_cause": "한 단락 — 왜 이 버그가 생기는가",
    "suggested_fix": "...",
    "severity": 0.85,
    "likelihood": 0.6,
    "blast_radius": 0.4,
    "confidence": 0.78,
    "priority_score": 0.85 * 0.6 * 0.4 = 0.204,
    "verification_trace": "... 코드 재추적 인용 ...",
    "raw_finding_ids": ["arch-3", "inv-2"]
  }
]
```

## Step 4.1 — Load & Tag

8 `_findings_<position>.json` + `_drift.json` 모두 읽어 통합. 각 finding 에 origin position 태그.

## Step 4.2 — Cluster (v0.2 — feature_path × hazard_point)

클러스터 키가 feature_path + hazard_point 로 강화됨:

```python
clusters = defaultdict(list)
for f in raw:
    key = (f["feature_path"], f.get("hazard_point"))
    clusters[key].append(f)
```

- 같은 leaf 의 같은 hazard 를 여러 포지션이 플래그 → 자동 concurrence
- 다른 category 라도 같은 hazard_point 면 동일 클러스터 (다관점 = 신뢰도↑)

클러스터 내 포지션 수 = `concurrence_count`.

## Step 4.3 — Verify (False Positive 제거)

각 클러스터에 대해:
1. **Re-Read evidence 인용 코드** — 정말 그렇게 동작하나?
2. **반증 시도** — claim 이 틀렸다면 어떤 코드 경로가 반증할 수 있는가?
3. **컨텍스트 재확인** — 주변 코드/주석/이미 적용된 수정이 그 버그를 막고 있는가?

검증 실패 (false positive) → cluster 폐기, `_triage_log.json` 에 기록 (디버깅용).

## Step 4.4 — Synthesize Root Cause

클러스터 내 raw findings 의 perspectives 를 종합:
- 왜 이 버그가 생기는가 (한 단락)
- 같은 root cause 에서 파생되는 다른 버그가 있나 (덧붙임)

## Step 4.5 — Reproduction Scenario

각 cluster 에 대해 재현 가능한 시나리오 작성:
- 사용자 액션 sequence (구체적)
- 또는 코드 path 추적 (사용자 시나리오 없을 시)
- 가능하면 단위 테스트 outline

## Step 4.6 — Score

각 finding 에 4 점수 부여 (0~1):

**severity** — 발생 시 영향
- 데이터 유실/crash → 0.9~1.0
- UX 깨짐 (사용자 혼란) → 0.5~0.8
- 미세한 부정확 → 0.2~0.5
- 미관/성능 (크리티컬 아님) → 0.0~0.2

**likelihood** — 실제 발생 빈도
- 흔한 사용 시나리오 → 0.7~1.0
- 특정 feature 조합 → 0.3~0.7
- 극단/악의적 입력 → 0.0~0.3

**blast_radius** — 영향 범위
- 전 시스템 → 0.8~1.0
- 한 모듈 → 0.4~0.7
- 한 기능 한정 → 0.0~0.3

**confidence** — finding 자체의 신뢰도
- 코드로 명확 증명 → 0.8~1.0
- 강한 추론 → 0.5~0.8
- 약한 추측 → 0.0~0.5

**priority_score** = severity × likelihood × blast_radius × concurrence_boost

**concurrence_boost**:
- 1 포지션: 1.0
- 2 포지션: 1.2
- 3 포지션: 1.5
- 4+ 포지션: 1.8 (cap)

다관점 독립 관찰은 우연이 아니므로 boost 정당화. Auditor + Adversary 같은 상반된 시각이 같은 hazard 에 동의하면 특히 신뢰도↑.

## Step 4.7 — Suggested Fix

각 finding 마다 다음 중 하나:
- **명확한 코드 패치** — 작은 수정 (5~30 줄)
- **설계 변경 제안** — 구조적 변경 필요 (어떤 추상화 도입 등)
- **명세 명확화 권고** — 스펙 갭이 원인이면 명세부터 정리

## Step 4.8 — Filter by Confidence

- `confidence ≥ 0.4` (config 의 `confidence_threshold`) → 본 보고서
- `confidence < 0.4` → "Low Confidence" 별도 섹션

## Step 4.9 — Sort & ID Assign

- 정렬: priority_score 내림차순
- ID 부여: F001, F002, ...
- Low confidence: L001, L002, ...

## 자기 검증

- [ ] 모든 finding 의 evidence 가 실제 코드와 일치 (랜덤 샘플 3개 검증)
- [ ] priority_score 계산이 severity × likelihood × blast_radius 와 일치
- [ ] 동일 cluster 가 둘 이상 finding 으로 남지 않음 (중복 검사)
- [ ] confidence < 0.4 가 모두 Low Confidence 섹션
- [ ] suggested_fix 가 actionable

## 진단 출력

```text
[CC-RA Phase 4] Triage complete
  Raw findings:     71
  After clustering: 38 unique
  After verify:     27 (44 false positives or weak)
  Critical (>0.5):  4
  High (0.3~0.5):   8
  Medium (0.1~0.3): 11
  Low (<0.1):       4
  Low confidence:   12 (separate section)
```

## 다음 phase

→ `05_report.md`
