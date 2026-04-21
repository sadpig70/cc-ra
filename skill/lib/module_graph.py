"""cc-ra: module graph + use-dependency + orphan 파일 추출.

우선 `cargo-modules 0.26+` 의 `dependencies`(DOT) / `orphans` 서브커맨드를 사용.
없으면 `mod` 선언을 직접 스캔하는 가벼운 fallback (소유 트리만).

산출: `_module_graph.json`
```json
{
  "tool": "cargo-modules|fallback",
  "packages": {
    "<pkg>": {
      "root": "crate|<name>",
      "src_path": "...",
      "nodes": ["crate", "crate::app", ...],
      "owns": [["crate","crate::app"], ...],     // 소유 트리 (mod 선언)
      "uses": [["crate::app","crate::find"], ...], // 실제 use 의존 (dependencies 서브커맨드만)
      "cycles": [["crate::a","crate::b"], ...],   // uses 그래프 상의 사이클
      "metrics": {
        "crate::app": {"in_degree": 0, "out_degree": 9, "used_by": [], "uses": [...]}
      },
      "orphans": ["src/old.rs", ...]             // mod 선언되지 않은 .rs 파일 (있으면)
    }
  }
}
```
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx


MOD_DECL_RE = re.compile(
    r"^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?mod\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\{|;)",
    re.MULTILINE,
)

DOT_NODE_RE = re.compile(r'^\s*"([^"]+)"\s*\[')
DOT_EDGE_RE = re.compile(
    r'^\s*"([^"]+)"\s*->\s*"([^"]+)"\s*\[label="([^"]+)"'
)

ORPHAN_PATH_RE = re.compile(r'"(?P<path>[^"]+\.rs)"')


def has_cargo_modules() -> bool:
    if not shutil.which("cargo"):
        return False
    try:
        proc = subprocess.run(
            ["cargo", "modules", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return proc.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def run_cargo_modules_dependencies(workspace: Path, package: str, *, max_depth: int = 2) -> str:
    """cargo-modules 의 dependencies 서브커맨드를 DOT 으로 받는다."""
    args = [
        "cargo", "modules", "dependencies",
        "--package", package,
        "--no-externs", "--no-sysroot",
        "--no-fns", "--no-types", "--no-traits",
        "--max-depth", str(max_depth),
    ]
    proc = subprocess.run(args, cwd=workspace, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"cargo modules dependencies failed: {proc.stderr}")
    return proc.stdout


def run_cargo_modules_orphans(workspace: Path, package: str) -> list[str]:
    """orphans 서브커맨드 — mod 선언 안 된 dead .rs 파일 식별."""
    args = ["cargo", "modules", "orphans", "--package", package]
    try:
        proc = subprocess.run(args, cwd=workspace, capture_output=True, text=True, encoding="utf-8")
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    # 출력은 human-readable. "No orphans found." 또는 path 목록.
    if "No orphans found" in proc.stdout:
        return []
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        m = ORPHAN_PATH_RE.search(line)
        if m:
            paths.append(m.group("path"))
        else:
            # 따옴표 없이 그냥 path 가 오는 경우도
            stripped = line.strip()
            if stripped.endswith(".rs") and not stripped.startswith("-"):
                paths.append(stripped)
    return paths


def parse_dot_graph(dot: str) -> dict:
    """간단 DOT 파서 — node / edge 만 추출.
    우리는 cargo-modules 의 안정된 포맷만 파싱하므로 정규식으로 충분."""
    nodes: list[str] = []
    owns: list[list[str]] = []
    uses: list[list[str]] = []
    for line in dot.splitlines():
        if m := DOT_NODE_RE.match(line):
            n = m.group(1)
            if n not in nodes:
                nodes.append(n)
            continue
        if m := DOT_EDGE_RE.match(line):
            a, b, label = m.group(1), m.group(2), m.group(3)
            if a not in nodes:
                nodes.append(a)
            if b not in nodes:
                nodes.append(b)
            if label == "owns":
                owns.append([a, b])
            elif label == "uses":
                uses.append([a, b])
            # 기타 라벨은 무시 (향후 확장)
    return {"nodes": nodes, "owns": owns, "uses": uses}


def compute_metrics(graph: dict) -> dict:
    g_uses = nx.DiGraph()
    for n in graph["nodes"]:
        g_uses.add_node(n)
    for a, b in graph["uses"]:
        g_uses.add_edge(a, b)

    metrics = {}
    for n in graph["nodes"]:
        metrics[n] = {
            "in_degree": g_uses.in_degree(n),
            "out_degree": g_uses.out_degree(n),
            "used_by": sorted(g_uses.predecessors(n)),
            "uses": sorted(g_uses.successors(n)),
        }

    try:
        cycles = list(nx.simple_cycles(g_uses))
    except Exception:
        cycles = []

    return {"metrics": metrics, "cycles": cycles}


def via_fallback_scan(workspace: Path, src_path: Path, crate_root: str) -> dict:
    """cargo-modules 없을 때 — mod 선언만 따라가는 fallback.
    owns 트리만 생성, uses 는 없음."""
    nodes = [crate_root]
    owns: list[list[str]] = []
    visited: set[Path] = set()

    def walk(file: Path, mod_path: str) -> None:
        if file in visited or not file.exists():
            return
        visited.add(file)
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        for m in MOD_DECL_RE.finditer(text):
            child = m.group(1)
            child_path = f"{mod_path}::{child}"
            if child_path not in nodes:
                nodes.append(child_path)
            owns.append([mod_path, child_path])
            base = file.parent
            for cand in (base / f"{child}.rs", base / child / "mod.rs"):
                if cand.exists():
                    walk(cand, child_path)
                    break

    walk(src_path, crate_root)
    return {"nodes": nodes, "owns": owns, "uses": []}


def analyze_package(workspace: Path, pkg_name: str, src_path: Path, *, max_depth: int) -> dict:
    use_cm = has_cargo_modules()
    tool = "cargo-modules" if use_cm else "fallback"

    graph: dict
    if use_cm:
        try:
            dot = run_cargo_modules_dependencies(workspace, pkg_name, max_depth=max_depth)
            graph = parse_dot_graph(dot)
            # cargo-modules 의 root 는 crate 이름 (예: "MSharp")
            if graph["nodes"] and graph["nodes"][0] != pkg_name:
                pass  # 관계없음 — 루트가 무엇이든 그대로 사용
        except Exception as e:
            print(f"[module_graph] cargo-modules failed ({e}); fallback scan", file=sys.stderr)
            use_cm = False
            tool = "fallback"
            graph = via_fallback_scan(workspace, src_path, "crate")
    else:
        graph = via_fallback_scan(workspace, src_path, "crate")

    m = compute_metrics(graph)
    graph.update(m)
    graph["tool"] = tool
    graph["src_path"] = str(src_path)

    if use_cm:
        graph["orphans"] = run_cargo_modules_orphans(workspace, pkg_name)
    else:
        graph["orphans"] = []  # fallback 에서는 생략

    # 루트 추정
    if graph["nodes"]:
        graph["root"] = graph["nodes"][0]
    return graph


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--max-depth", type=int, default=2,
                    help="모듈만: 2 / 타입까지: 3~4 / 함수까지: 5~")
    args = ap.parse_args()

    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    workspace = Path(meta["workspace_root"])

    aggregate = {"tool": "cargo-modules" if has_cargo_modules() else "fallback", "packages": {}}

    for pkg in meta["packages"]:
        pkg_name = pkg["name"]
        lib_target = next((t for t in pkg["targets"] if "lib" in t["kind"]), None)
        bin_target = next((t for t in pkg["targets"] if "bin" in t["kind"]), None)
        target = lib_target or bin_target
        if target is None:
            continue
        src_path = Path(target["src_path"])
        graph = analyze_package(workspace, pkg_name, src_path, max_depth=args.max_depth)
        aggregate["packages"][pkg_name] = graph

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")

    n_pkgs = len(aggregate["packages"])
    n_nodes = sum(len(g["nodes"]) for g in aggregate["packages"].values())
    n_uses = sum(len(g["uses"]) for g in aggregate["packages"].values())
    n_cycles = sum(len(g["cycles"]) for g in aggregate["packages"].values())
    n_orph = sum(len(g.get("orphans", [])) for g in aggregate["packages"].values())
    tool = aggregate["tool"]
    print(f"[module_graph] tool={tool} pkgs={n_pkgs} nodes={n_nodes} uses_edges={n_uses} "
          f"cycles={n_cycles} orphans={n_orph} → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
