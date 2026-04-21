"""cc-ra: tree-sitter 기반 Rust 심볼 인덱스.

추출 대상:
- function_item: 함수 정의 (시그니처 raw 텍스트 보존)
- struct_item: 구조체
- enum_item: 열거형
- impl_item: impl 블록 (대상 타입과 trait 명시)
- trait_item: 트레이트
- mod_item: 모듈 선언
- use_declaration: use 문
- visibility_modifier: pub/pub(crate)/...

각 심볼에 file:line 위치, visibility, 시그니처 raw 보존.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path

import tree_sitter_rust
from tree_sitter import Language, Node, Parser


RUST = Language(tree_sitter_rust.language())
PARSER = Parser(RUST)


KIND_MAP = {
    "function_item": "fn",
    "struct_item": "struct",
    "enum_item": "enum",
    "impl_item": "impl",
    "trait_item": "trait",
    "mod_item": "mod",
    "use_declaration": "use",
    "type_item": "type",
    "const_item": "const",
    "static_item": "static",
    "macro_definition": "macro",
}


def _matches_glob(rel: str, pattern: str) -> bool:
    """fnmatch + recursive ** support."""
    if "**" not in pattern:
        return fnmatch.fnmatch(rel, pattern)
    import re
    rx = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", ".")
    return re.match("^" + rx + "$", rel) is not None


def collect_files(root: Path, includes: list[str], excludes: list[str]) -> list[Path]:
    found: set[Path] = set()
    if not includes:
        includes = ["**/*.rs"]
    for inc in includes:
        # pathlib.glob 가 ** 를 지원
        for p in root.glob(inc):
            if p.is_file() and p.suffix == ".rs":
                found.add(p)
    out: list[Path] = []
    for path in sorted(found):
        rel = path.relative_to(root).as_posix()
        if any(_matches_glob(rel, ex) for ex in excludes):
            continue
        out.append(path)
    return out


def get_text(node: Node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def get_visibility(node: Node, src: bytes) -> str:
    for child in node.children:
        if child.type == "visibility_modifier":
            t = get_text(child, src)
            if "pub" in t:
                return t.strip()
            return "pub"
    return "private"


def get_name(node: Node, src: bytes) -> str:
    # 대부분 "name" field 가 identifier
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return get_text(name_node, src)
    # impl 등은 type_identifier
    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            return get_text(child, src)
    return "<anon>"


def get_signature(node: Node, src: bytes, max_len: int = 200) -> str:
    """fn/struct 등의 라인을 한 줄로 압축한 시그니처."""
    # body 시작 전까지만
    body_node = node.child_by_field_name("body")
    end = body_node.start_byte if body_node else node.end_byte
    text = src[node.start_byte:end].decode("utf-8", errors="replace")
    # 한 줄로
    sig = " ".join(text.split())
    if len(sig) > max_len:
        sig = sig[:max_len - 1] + "…"
    return sig.rstrip(" {")


def extract_use_path(node: Node, src: bytes) -> str:
    # use_declaration 의 path 부분만
    text = get_text(node, src)
    return text.replace("use ", "", 1).rstrip(";").strip()


def walk_collect(node: Node, src: bytes, file: str, out: list[dict],
                 mod_path: list[str]) -> None:
    """재귀 순회. mod_item 진입 시 mod_path 누적."""
    kind = KIND_MAP.get(node.type)
    if kind:
        symbol = {
            "file": file,
            "kind": kind,
            "line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "mod_path": "::".join(mod_path) if mod_path else "<root>",
        }
        if kind == "use":
            symbol["path"] = extract_use_path(node, src)
        else:
            symbol["name"] = get_name(node, src)
            symbol["vis"] = get_visibility(node, src)
            if kind in ("fn", "struct", "enum", "trait", "impl", "type"):
                symbol["signature"] = get_signature(node, src)
        out.append(symbol)

    # 재귀 — mod_item 인 경우 mod_path 확장
    next_mod_path = mod_path
    if node.type == "mod_item":
        name = get_name(node, src)
        if name and name != "<anon>":
            next_mod_path = mod_path + [name]
    for child in node.children:
        walk_collect(child, src, file, out, next_mod_path)


def index_file(path: Path, root: Path) -> list[dict]:
    src = path.read_bytes()
    tree = PARSER.parse(src)
    rel = path.relative_to(root).as_posix()
    out: list[dict] = []
    walk_collect(tree.root_node, src, rel, out, [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path)
    ap.add_argument("--scope-include", default="src/**/*.rs",
                    help="comma-separated include globs")
    ap.add_argument("--scope-exclude", default="target/**,vendor/**",
                    help="comma-separated exclude globs")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    includes = [s.strip() for s in args.scope_include.split(",") if s.strip()]
    excludes = [s.strip() for s in args.scope_exclude.split(",") if s.strip()]

    files = collect_files(workspace, includes, excludes)
    if not files:
        print(f"[symbol_index] no .rs files matched (include={includes}, exclude={excludes})",
              file=sys.stderr)

    all_symbols: list[dict] = []
    file_summary: list[dict] = []
    for path in files:
        try:
            syms = index_file(path, workspace)
        except Exception as e:
            print(f"[symbol_index] {path}: {e}", file=sys.stderr)
            continue
        all_symbols.extend(syms)
        try:
            line_count = sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
        except OSError:
            line_count = 0
        file_summary.append({
            "path": path.relative_to(workspace).as_posix(),
            "lines": line_count,
            "symbols": len(syms),
            "mtime": path.stat().st_mtime,
        })

    out = {
        "workspace": str(workspace),
        "files": file_summary,
        "symbols": all_symbols,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[symbol_index] {len(files)} files, {len(all_symbols)} symbols → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
