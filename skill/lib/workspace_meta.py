"""cc-ra: workspace metadata extraction via `cargo metadata`.

`cargo metadata --format-version 1 --no-deps` 의 출력에서 cc-ra가 후속 단계에 쓰는
정보만 추출해서 `_meta.json` 으로 저장한다. 외부 deps 정보는 의도적으로 제외 (no-deps).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_cargo_metadata(workspace: Path) -> dict:
    proc = subprocess.run(
        ["cargo", "metadata", "--format-version", "1", "--no-deps"],
        cwd=workspace,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cargo metadata failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def normalize(meta: dict, workspace: Path) -> dict:
    """cargo metadata 의 sprawling JSON을 cc-ra가 쓰는 슬림 형태로 변환."""
    out = {
        "workspace_root": meta.get("workspace_root", str(workspace)),
        "target_directory": meta.get("target_directory"),
        "workspace_members": meta.get("workspace_members", []),
        "packages": [],
    }
    for pkg in meta.get("packages", []):
        if pkg.get("id") not in out["workspace_members"]:
            continue
        targets = []
        for t in pkg.get("targets", []):
            targets.append({
                "name": t.get("name"),
                "kind": t.get("kind", []),
                "src_path": t.get("src_path"),
                "edition": t.get("edition"),
            })
        out["packages"].append({
            "id": pkg.get("id"),
            "name": pkg.get("name"),
            "version": pkg.get("version"),
            "manifest_path": pkg.get("manifest_path"),
            "edition": pkg.get("edition"),
            "targets": targets,
            "features": pkg.get("features", {}),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    if not (workspace / "Cargo.toml").exists():
        print(f"[workspace_meta] Cargo.toml not found at {workspace}", file=sys.stderr)
        return 2

    meta = run_cargo_metadata(workspace)
    norm = normalize(meta, workspace)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(norm, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[workspace_meta] {len(norm['packages'])} package(s) → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
