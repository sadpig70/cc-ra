# Phase 02 — Hypothesis Generation (v0.2)

> "어디에 버그가 숨었을 가능성이 높은가?" — Phase 1.5 의 **feature_tree** 를 기반으로
> 기능별 위험 지대를 가설로 추론한다.
> 포지션 분석 (Phase 3) 의 힌트 역할이지, 영역 할당 아님. 모든 포지션이 이 가설을 공유.

---

## 입력

- `{WORKSPACE}/.cc-ra/_context.json`
- `{WORKSPACE}/.cc-ra/_feature_tree.json` (v0.2)
- `{WORKSPACE}/.cc-ra/decomposition/*.pg.md` (v0.2)

## 산출

- `{WORKSPACE}/.cc-ra/_hypotheses.json`

```json
[
  {
    "id": "H001",
    "category": "B|C|...|H",
    "claim": "한 줄 가설 — 어떤 종류의 버그가 어디에 있을 수 있다",
    "location_hint": "src/foo.rs:Bar struct or src/baz.rs:fn quux",
    "rationale": "왜 이렇게 의심하는가 (구조적 근거)",
    "risk_score": 0.0,
    "personas_to_check": ["invariant_hunter", "stateful_analyst"]
  }
]
```

## 가설 생성 5축 (병렬 분석)

### Axis 1 — State Machine Hazards

`data_flow` 와 `symbols` 를 보고:
- 같은 struct의 여러 mut 메서드가 동일한 필드 묶음을 항상 함께 갱신하나?
- 한 메서드만 한 필드를 빼먹는다면 → 가설
- enum 변형이 추가됐는데 match 모든 곳에서 처리되나? (exhaustive 일 것이나, `_ => ` 캐치-올이 의심)

### Axis 2 — Temporal/Frame Ordering

`entry_points` 의 frame loop 함수 본문 흐름을 본다:
- 같은 프레임 안에 호출 순서가 결과에 영향을 주는 호출들 — 의도된 순서인가
- 사용자 입력 처리 → 상태 변경 → 렌더 의 순서가 한 프레임 안에서 일관된가
- 한 프레임에 발생한 변경이 다음 프레임에야 반영되는 함수 (deferred effect)
- 이번 세션의 `seek_match` 가 editor::show 후에 일어나는 패턴 — 같은 프로젝트에 또 있나?

### Axis 3 — Invariant Candidates

`invariants` 에서 추출된 명시 invariant + 다음 패턴의 암묵 invariant:
- `Vec[0]` 인덱싱 → "비어있지 않음" invariant
- `Option::unwrap` → "이 시점엔 Some" invariant
- `&str[..i]` → "i 가 char boundary" invariant
- 두 필드 비교 (`a == b.len()`) → "동기화 invariant"

각 invariant 가 모든 mutation 경로에서 유지되는지는 페르소나가 확인할 것 — 너는 후보 등록만.

### Axis 4 — Feature Interaction Matrix

`symbols` + `module_graph` 에서 추출되는 feature 식별:
- `pub` API 그룹화 (예: find/replace, multi-cursor, undo, file IO, IPC)
- 각 feature 가 사용하는 핵심 struct/필드
- 두 feature 가 같은 struct/필드 만지면 → 충돌 가능성
- 그 조합이 하나의 frame 안에서 동시 활성화될 수 있는가?

### Axis 5 — Error Path Survey

`symbols` 에서 다음 grep:
- `Result` 를 반환하는데 호출 site 에서 `let _ =` 로 무시하는 패턴
- `Option` 에서 `unwrap_or_default` — default 가 invariant 위반?
- `expect("...")` 메시지가 의미 있는 invariant 가정?
- panic-able 코드 (`[i]`, `unwrap`) 가 user-input-driven 함수 안에 있는가?

## 절차

1. 각 axis 에 대해 위 패턴을 코드/그래프에 적용 → 의심 후보 식별
2. 각 후보를 가설 형식으로 변환:
   - id 부여 (H001, H002, ...)
   - category 코드 (A~H 중)
   - location_hint
   - rationale (왜 의심)
   - risk_score (0~1) — 다음 휴리스틱:
     * 핵심 entry point 또는 frame loop → +0.3
     * 여러 페르소나가 관심을 가질 만한 영역 → +0.2
     * 명시 invariant 와 연관 → +0.2
     * 사용자 입력에 직접 노출 → +0.2
     * 캐시/derived state 포함 → +0.1
   - `personas_to_check` — 어느 페르소나가 검증할지 (1~3개)
3. **최소 20개 가설** (medium 워크스페이스). 부족하면 risk_score 낮은 것도 포함.
4. JSON 으로 직렬화 → `_hypotheses.json`

## 자기 검증

- [ ] `_hypotheses.json` valid JSON
- [ ] ≥ 20 가설 (medium 워크스페이스)
- [ ] 각 가설의 location_hint 가 _symbols 에 매핑 가능
- [ ] 각 가설에 personas_to_check 1개 이상
- [ ] risk_score 분포가 다양 (모두 0.5 등 무성의 X)

## 다음 phase

→ `02_5_scenario_derive.md` (v0.2 신규)
→ `03_position_analysis.md` (v0.2)
