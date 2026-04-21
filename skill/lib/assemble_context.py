"""cc-ra: Phase 01 산출물들을 _context.json 으로 통합.

AI 가 후속 phase 에서 한 파일만 읽어 컨텍스트 전체를 얻을 수 있도록.
data_flow / entry_points 는 AI 단계에서 채울 placeholder 만 둔다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cc-ra-dir", required=True, type=Path,
                    help="대상 워크스페이스의 .cc-ra 디렉터리")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    d = args.cc_ra_dir
    ctx = {
        "workspace": str(d.parent.resolve()),
        "cargo_metadata": _load_or_empty(d / "_meta.json", default={}),
        "module_graph": _load_or_empty(d / "_module_graph.json", default={"packages": {}}),
        "files": [],
        "symbols": [],
        "invariants": _load_or_empty(d / "_invariants.json", default=[]),
        "entry_points": [],   # Phase 01 Step 1.6 — AI 가 추론하여 채움
        "data_flow": {},      # Phase 01 Step 1.7 — AI 가 추론하여 채움
    }

    sym = _load_or_empty(d / "_symbols.json", default={})
    if isinstance(sym, dict):
        ctx["files"] = sym.get("files", [])
        ctx["symbols"] = sym.get("symbols", [])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")

    n_files = len(ctx["files"])
    n_syms = len(ctx["symbols"])
    n_inv = len(ctx["invariants"])
    n_pkg = len(ctx["module_graph"].get("packages", {})) if isinstance(ctx["module_graph"], dict) else 0
    print(f"[assemble] files={n_files} symbols={n_syms} invariants={n_inv} packages={n_pkg} → {args.output}")
    return 0


def _load_or_empty(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[assemble] {path}: {e}")
        return default


if __name__ == "__main__":
    raise SystemExit(main())
