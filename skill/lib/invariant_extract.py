"""cc-ra: invariant 후보 추출.

소스 라인 (.rs) + 마크다운 (.md) 에서 invariant 가 명시된 곳을 긁는다.

긁어오는 패턴:
- 주석 안에 must/always/never/invariant/assumes/guarantees/보장/가정
- assert! / debug_assert! / unreachable!
- 마크다운의 AC-N 표 row
- 마크다운 헤더 아래 단락에 must/always 단어
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path


KEYWORDS_EN = ["must", "always", "never", "invariant", "assumes", "guarantees", "ensures", "requires"]
KEYWORDS_KO = ["보장", "가정", "반드시", "항상", "절대", "불변"]
KEYWORDS = KEYWORDS_EN + KEYWORDS_KO

KEYWORD_RE = re.compile(
    r"\b(?:" + "|".join(KEYWORDS_EN) + r")\b|" + "|".join(KEYWORDS_KO),
    re.IGNORECASE,
)
COMMENT_RE = re.compile(r"^\s*//+\s?(.*)|^\s*/\*+\s?(.*?)\*+/\s*$|^\s*\*\s?(.*)", re.MULTILINE)
ASSERT_RE = re.compile(r"\b(assert!|debug_assert!|debug_assert_eq!|debug_assert_ne!|unreachable!|panic!)\s*\(([^)]*)", re.MULTILINE)
AC_TABLE_RE = re.compile(r"^\|\s*(AC-\d+)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)


def scan_rust(path: Path, rel: str) -> list[dict]:
    out: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for ln, line in enumerate(text.splitlines(), 1):
        # 주석에서 키워드
        m = re.match(r"^\s*//+\s?(.*)", line)
        if m:
            content = m.group(1)
            if KEYWORD_RE.search(content):
                out.append({
                    "source": f"{rel}:{ln}",
                    "kind": "comment",
                    "claim": content.strip(),
                    "tags": _tag(content),
                })

    # assert/panic
    for m in ASSERT_RE.finditer(text):
        ln = text[:m.start()].count("\n") + 1
        out.append({
            "source": f"{rel}:{ln}",
            "kind": m.group(1).rstrip("!"),
            "claim": m.group(0)[:200],
            "tags": ["panic_path"],
        })
    return out


def scan_markdown(path: Path, rel: str) -> list[dict]:
    out: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    # AC-N 표 행
    for m in AC_TABLE_RE.finditer(text):
        ln = text[:m.start()].count("\n") + 1
        out.append({
            "source": f"{rel}:{ln}",
            "kind": "acceptance_criteria",
            "claim": f"{m.group(1)}: {m.group(2).strip()}",
            "tags": ["AC", m.group(1)],
        })

    # 헤더 아래 단락 키워드
    sections = re.split(r"^(#{1,6}\s+.+)$", text, flags=re.MULTILINE)
    cur_header = ""
    for chunk in sections:
        if chunk.startswith("#"):
            cur_header = chunk.strip().lstrip("# ").strip()
            continue
        # 단락 단위
        for para in re.split(r"\n\s*\n", chunk):
            if KEYWORD_RE.search(para):
                first_line = para.strip().splitlines()[0][:200]
                ln = text.find(para)
                ln = (text[:ln].count("\n") + 1) if ln >= 0 else 0
                out.append({
                    "source": f"{rel}:{ln}",
                    "kind": "doc",
                    "claim": f"[{cur_header}] {first_line}".strip(),
                    "tags": _tag(para),
                })
    return out


def _tag(text: str) -> list[str]:
    tags = []
    low = text.lower()
    if "cursor" in low or "커서" in text:
        tags.append("cursor")
    if "scroll" in low or "스크롤" in text:
        tags.append("scroll")
    if "config" in low or "설정" in text:
        tags.append("config")
    if "session" in low:
        tags.append("session")
    if "thread" in low or "panic" in low or "borrow" in low:
        tags.append("safety")
    if "ui" in low or "render" in low or "ime" in low:
        tags.append("ui")
    return tags


def collect(workspace: Path, md_globs: list[str], rs_globs: list[str], excludes: list[str]) -> list[dict]:
    items: list[dict] = []
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace).as_posix()
        if any(fnmatch.fnmatch(rel, ex) for ex in excludes):
            continue
        if path.suffix == ".md" and any(fnmatch.fnmatch(rel, g) for g in md_globs):
            items.extend(scan_markdown(path, rel))
        elif path.suffix == ".rs" and any(fnmatch.fnmatch(rel, g) for g in rs_globs):
            items.extend(scan_rust(path, rel))
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path)
    ap.add_argument("--md-globs", default="*.md,**/*.md", help="comma-separated")
    ap.add_argument("--rs-globs", default="src/**/*.rs", help="comma-separated")
    ap.add_argument("--exclude", default="target/**,vendor/**,.cc-ra/**", help="comma-separated")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    md_globs = [s.strip() for s in args.md_globs.split(",") if s.strip()]
    rs_globs = [s.strip() for s in args.rs_globs.split(",") if s.strip()]
    excludes = [s.strip() for s in args.exclude.split(",") if s.strip()]

    items = collect(workspace, md_globs, rs_globs, excludes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[invariant_extract] {len(items)} candidate(s) → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
