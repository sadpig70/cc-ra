# Phase 01.5 — Feature Reverse-Engineering ★ v0.2

> **코드만 보고** 기능별 Gantree + PPR 를 역공학. 설계 문서 참조 **금지**.
> 모듈 구조가 아닌 "시스템이 하는 일" 관점으로 BFS 분해.

---

## 입력

- `{WORKSPACE}/.cc-ra/_context.json` (Phase 1 산출)
- 원본 소스 코드 (Read 로 직접 접근)
- **금지**: `{WORKSPACE}/.cc-ra/_design_claims.json`, `CLAUDE.md`, `README.md`, `DESIGN-*.md`

## 산출

- `{WORKSPACE}/.cc-ra/_feature_tree.json` — 통합 인덱스
- `{WORKSPACE}/.cc-ra/decomposition/*.pg.md` — 기능별 PG 파일

---

## Step 1.5.1 — System Purpose 식별

`_context.json` 의 entry points + 최상위 pub API 에서 **시스템이 무엇을 하는가** 한 문장으로 추출.

예: "Windows 용 경량 코드 에디터 — Rust 텍스트 편집 · 탭 관리 · 세션 복원"

주의: 이 추출은 코드 증거 (main 함수, pub API 이름, event handler 이름) 에 근거. 설계 문서의 선언 문장 참조 금지.

## Step 1.5.2 — Level 2 대 기능 목록화 (BFS 첫 확장)

다음 코드 증거에서 L2 기능을 귀납:
- **Entry points**: `main`, event handler, `impl App { fn update }` 같은 frame loop
- **키바인딩 / 메뉴 / 팔레트**: 사용자가 트리거할 수 있는 모든 액션
- **pub API**: 라이브러리면 public interface
- **IPC / 외부 진입**: `start_server`, 파일 연결 등

각 L2 = "사용자가 이 시스템으로 할 수 있는 한 종류의 일".

예 (MSharp):
- FileLifecycle, TextEditing, Navigation, Selection, FindReplace, TabManagement,
  WindowChrome, ViewPresentation, SyntaxHighlighting, SessionPersistence,
  OSIntegration, UserCommands

## Step 1.5.3 — BFS 재귀 분해 (원자까지)

각 feature 에 대해:

```python
while queue:
    f = queue.pop(0)
    if atomic(f):          # 15분 룰
        f.ppr_spec = synthesize_ppr(f, code)
        f.inferred_AC = infer_ac_from_code(f.ppr_spec)
        continue
    subs = decompose(f)
    f.children = subs
    queue.extend(subs)
```

**원자성 기준 (PG 스킬의 15분 룰 준용)**:
- 함수 시그니처로 표현 가능
- 한 문장으로 설명 가능
- 50줄 이내 단일 함수 / 단일 분기 / 단일 파이프 단계

## Step 1.5.4 — 각 leaf 에 첨부

```
<Leaf> // <한 문장 설명>
    code_locations: [file:line-range, ...]
    cross_cutting_modules: [mod1, mod2, ...]
    ppr_spec:
        inputs: [(name, type), ...]
        outputs: [(name, type), ...]
        branches: [(condition, action), ...]
        pipelines: [step1 → step2 → ...]
        state_read: [field, ...]
        state_write: [field, ...]
        inferred_AC: [문장, ...]
    observations: [   # 역공학 시 떠오른 의문·위험 후보
        "관찰 1",
        ...
    ]
```

## Step 1.5.5 — 각 L2 기능을 파일로

`{WORKSPACE}/.cc-ra/decomposition/NN_<Name>.pg.md` 형식.

예시 구조:
```markdown
# Feature: <Name>

> 코드 역공학 산출. 설계 문서 참조 없음.

## Gantree (BFS)
```gantree
...
```

## PPR Specs (주요 leaf)
```python
def foo(...) -> ...: ...
```

## Cross-cutting
| 파일 | 담당 leaf |

## 역공학 관찰 (finding 후보)
| feature_path | 관찰 | 카테고리 후보 |
```

(파일럿 `05_FindReplace.pg.md` 가 참조 포맷)

## Step 1.5.6 — `_feature_tree.json` 통합 인덱스

모든 L2 파일의 Gantree 를 JSON 으로 합성:

```json
{
  "root": "MSharp (텍스트 에디터)",
  "children": [
    {
      "id": "FileLifecycle",
      "file": "decomposition/01_FileLifecycle.pg.md",
      "children": [...]
    },
    ...
  ],
  "leaf_index": {
    "FindReplace::ComputeMatches::RestoreCurrent": {
      "file": "decomposition/05_FindReplace.pg.md",
      "code_locations": ["src/find.rs:118-128"],
      "inferred_AC": [...]
    },
    ...
  }
}
```

---

## 자기 검증

- [ ] `_feature_tree.json` valid JSON
- [ ] 모든 L2 feature .pg.md 파일 존재 (MSharp 기준 12 개)
- [ ] 각 leaf 에 code_locations ≥ 1, inferred_AC ≥ 1
- [ ] 15분 룰 원자까지 분해
- [ ] cross_cutting_modules 명시된 leaf ≥ 30% (실제로 cross-cutting 많음)
- [ ] grep 'CLAUDE.md\|DESIGN-\|README' in decomposition/ → 0 건 (설계 문서 참조 없음)

## 다음 phase

→ `02_hypothesis.md` (feature_tree 에서 가설)
→ `02_5_scenario_derive.md` (feature_tree 에서 시나리오)
