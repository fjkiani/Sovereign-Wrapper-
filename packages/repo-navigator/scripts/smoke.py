#!/usr/bin/env python3
"""Smoke: ensure fixture git SHA, index, exercise three tools (no MCP client)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repo_navigator.guards import load_config  # noqa: E402
from repo_navigator.indexer import index_repo  # noqa: E402
from repo_navigator import tools as T  # noqa: E402


def ensure_fixture_git(repo: Path) -> str:
    if not (repo / ".git").exists():
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "smoke@repo-navigator.local"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "RepoNavigator Smoke"], cwd=repo, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fixture: demo-repo v0"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    return sha.lower()


def main() -> int:
    cfg = load_config(ROOT / "config.yaml")
    demo = cfg.repos["demo"].path
    sha = ensure_fixture_git(demo)
    out = index_repo(cfg, "demo", sha)
    print(f"INDEX OK → {out}")
    print(f"SHA={sha}")

    arch = T.get_architecture_map(cfg, "demo", sha)
    print("\n=== get_architecture_map ===")
    print(json.dumps(arch, indent=2)[:1200])

    found = T.find_symbol(cfg, "demo", sha, "Ledger")
    print("\n=== find_symbol(Ledger) ===")
    print(json.dumps(found, indent=2)[:1200])

    if not found["matches"]:
        print("FAIL: no Ledger matches", file=sys.stderr)
        return 1
    sym = found["matches"][0]
    read = T.read_symbol(cfg, "demo", sha, symbol_id=sym["symbol_id"])
    print("\n=== read_symbol ===")
    print(json.dumps(read, indent=2)[:1600])

    # Guard: secret path must fail
    try:
        cfg.assert_safe_relpath(".env")
        print("FAIL: .env should be blocked", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"\nGUARD OK secret blocked: {e}")

    # Guard: empty sha refused
    try:
        T.get_architecture_map(cfg, "demo", "")
        print("FAIL: empty sha should be refused", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"GUARD OK pinned sha required: {e}")

    print("\nSMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
