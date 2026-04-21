# Phase 01 — Context Build (v0.2)

> 분석의 토대. 코드를 깊이 이해할 수 있는 인덱스/그래프/컨텍스트를 구축한다.
> 후속 phase 는 이 산출에 의존한다.
>
> **v0.2 핵심 변경**: `_invariants.json` 은 "design_claims" 로 취급한다.
> 분석 단계 (Phase 1.5 ~ 3) 에서는 접근 금지. Phase 3.5 (Design Drift) 에서만 활성화.

---

## 입력

- `WORKSPACE` — 분석 대상 워크스페이스 절대 경로
- `CONFIG` — `.cc-ra/config.toml` (없으면 default)
- `SCOPE` — config 의 `[scope]` 또는 CLI `--scope`

## 산출 (`{WORKSPACE}/.cc-ra/_context.json`)

```json
{
  "workspace": "/abs/path",
  "cargo_metadata": { ... cargo metadata --format-version 1 그대로 ... },
  "files": [{"path": "src/foo.rs", "lines": 320, "mtime": ...}, ...],
  "module_graph": {
    "nodes": ["crate", "crate::foo", ...],
    "edges": [["crate", "crate::foo"], ...],
    "cycles": [["crate::a", "crate::b"]]
  },
  "symbols": [
    {"file": "src/foo.rs", "kind": "fn", "name": "process",
     "vis": "pub", "line": 42, "signature": "pub fn process(...) -> ..."},
    ...
  ],
  "entry_points": [
    {"kind": "main", "file": "src/main.rs", "fn": "main"},
    {"kind": "frame_loop", "file": "src/app.rs", "fn": "MSharpApp::update"},
    ...
  ],
  "invariants": [
    {"source": "CLAUDE.md", "claim": "Title bar는 보라색", "tags": ["ui","theme"]},
    {"source": "src/document.rs:67", "claim": "multi_cursor_col 은 ...", "tags": ["state"]},
    ...
  ]
}
```

## 단계

### Step 1.1 — 환경 점검

Bash로 다음 확인 (없으면 보고 후 가능한 만큼 진행):
- `cargo --version`
- `python --version` (3.10+)
- `cargo modules --version` (없으면 `cargo install cargo-modules` 안내)
- `python -c "import tree_sitter, tree_sitter_rust; print('ok')"` (없으면 `pip install tree-sitter tree-sitter-rust networkx` 안내)

### Step 1.2 — Workspace Metadata

```bash
python "${CC_RA_LIB}/workspace_meta.py" \
  --workspace "${WORKSPACE}" \
  --output "${WORKSPACE}/.cc-ra/_meta.json"
```

내부적으로 `cargo metadata --format-version 1 --no-deps` 실행 → workspace_root, packages, targets src_path 추출.

### Step 1.3 — Module Graph

```bash
python "${CC_RA_LIB}/module_graph.py" \
  --meta "${WORKSPACE}/.cc-ra/_meta.json" \
  --output "${WORKSPACE}/.cc-ra/_module_graph.json" \
  --max-depth 2
```

내부 동작:
- `cargo modules dependencies --package X --no-externs --no-sysroot --max-depth N` → **DOT 출력**
- DOT 파서가 `"A" -> "B" [label="uses"]` 형태의 use 엣지 추출
- `"A" -> "B" [label="owns"]` 은 소유 트리 (mod 선언)
- networkx 로 in/out degree, 사이클, 최대 depth 계산
- `cargo modules orphans --package X` 로 dead file 식별

없으면 fallback: mod 선언만 스캔 (uses 엣지 없음, orphan 감지 없음).

**`--max-depth` 가이드**:
- `2` (기본): 모듈 수준 — Architect, SpecConformance 페르소나에 충분
- `3~4`: 타입/struct 포함 — StatefulAnalyst 가 struct 의존 볼 때
- `5+`: 함수 수준 — InvariantHunter 의 caller graph (비용 큼)

Phase 02 Hypothesis 단계에서 추가 depth 가 필요하다 판단되면 재호출.

### Step 1.4 — Symbol Index (tree-sitter)

```bash
python "${CC_RA_LIB}/symbol_index.py" \
  --workspace "${WORKSPACE}" \
  --scope-include "src/**/*.rs" \
  --scope-exclude "target/**" \
  --output "${WORKSPACE}/.cc-ra/_symbols.json"
```

추출 대상: `function_item`, `struct_item`, `enum_item`, `impl_item`, `trait_item`, `use_declaration`, `mod_item`, `visibility_modifier`. Pub/private 구분, 시그니처 raw 텍스트 보존.

### Step 1.5 — Invariant Extract

```bash
python "${CC_RA_LIB}/invariant_extract.py" \
  --workspace "${WORKSPACE}" \
  --md-globs "*.md,.pgf/*.md" \
  --output "${WORKSPACE}/.cc-ra/_invariants.json"
```

긁어오는 패턴:
- `// (must|always|never|invariant|assumes|guarantees|보장|가정)`
- `assert!`, `debug_assert!`, `unreachable!`
- markdown 의 `AC-N` 표 행
- `## ` 헤더 아래 "must"/"always" 단어가 있는 단락

### Step 1.6 — Entry Points (AI 추론)

위 산출을 종합해 직접 너가 추론:
- `main` 함수
- `lib.rs::pub fn` (라이브러리 API)
- 이벤트 핸들러 (`impl Foo { fn update(&mut self, ...) }` 같은 패턴)
- frame loop (`update`, `tick`, `render` 같은 이름 + `&mut self`)
- IPC/외부 진입 (`start_server`, `listen`, `accept`)

### Step 1.7 — Data Flow Map (AI 추론)

핵심 mut struct 식별 (>= 5개 `&mut self` 메서드 가진 struct) → 각 struct 의 mutation 경로 그래프:
- 어떤 함수가 어떤 필드를 수정하나
- 어떤 함수가 어떤 필드를 읽나
- 함께 수정되는 필드 (paired updates)

`_context.json` 의 `data_flow` 필드에 저장.

### Step 1.8 — 통합

위 모든 산출을 `_context.json` 으로 병합. 후속 phase 가 이 한 파일을 읽는다.

## 자기 검증 (이 phase 종료 전)

- [ ] `_context.json` 이 valid JSON
- [ ] symbols 가 전체 .rs 파일을 커버 (랜덤 1개 파일 grep 으로 확인)
- [ ] module_graph 에 cycles 필드 존재 (빈 배열도 OK)
- [ ] invariants 가 5개 이상 (medium 이상 프로젝트)
- [ ] entry_points 가 main 함수 포함

## 다음 phase

→ `01_5_feature_reverse.md` (v0.2 신규)
