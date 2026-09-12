"""Offline Tree-sitter indexer → architecture_map.json keyed by (repo_id, git_sha)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython

from repo_navigator.guards import GuardConfig, is_secret_path, load_config

PY_LANGUAGE = Language(tspython.language())

# Capture class / function definitions with names (tree-sitter 0.22+ Query API).
_QUERY = Query(
    PY_LANGUAGE,
    """
(class_definition
  name: (identifier) @name) @def

(function_definition
  name: (identifier) @name) @def
""",
)

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
}


@dataclass
class SymbolRecord:
    symbol_id: str
    name: str
    kind: str
    path: str
    start_line: int
    end_line: int
    qualname: str


def resolve_git_sha(repo_path: Path, pinned: str | None = None) -> str:
    if pinned:
        sha = pinned.strip().lower()
        # Verify object exists when possible
        r = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--verify", pinned],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"cannot resolve git_sha {pinned!r} in {repo_path}: {r.stderr.strip()}")
        return r.stdout.strip().lower()
    r = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"repo at {repo_path} has no HEAD — init git or pass --git-sha. {r.stderr.strip()}"
        )
    return r.stdout.strip().lower()


def iter_python_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        if is_secret_path(rel):
            continue
        yield p


def _kind_for_node(node) -> str:
    if node.type == "class_definition":
        return "class"
    if node.type == "function_definition":
        # async_function_definition wraps differently in some grammars;
        # tree-sitter-python uses function_definition for both with async keyword.
        return "function"
    return node.type


def extract_symbols(source: bytes, relpath: str) -> list[SymbolRecord]:
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(source)
    cursor = QueryCursor(_QUERY)
    records: list[SymbolRecord] = []

    for _pattern_idx, caps in cursor.matches(tree.root_node):
        defn_nodes = caps.get("def") or []
        name_nodes = caps.get("name") or []
        if not defn_nodes or not name_nodes:
            continue
        defn = defn_nodes[0]
        name_node = name_nodes[0]
        name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
        parts: list[str] = []
        cur = defn.parent
        while cur is not None:
            if cur.type in ("class_definition", "function_definition"):
                for ch in cur.children:
                    if ch.type == "identifier":
                        parts.append(
                            source[ch.start_byte : ch.end_byte].decode("utf-8")
                        )
                        break
            cur = cur.parent
        parts.reverse()
        parts.append(name)
        qualname = ".".join(parts)
        start_line = defn.start_point[0] + 1
        end_line = defn.end_point[0] + 1
        symbol_id = hashlib.sha1(
            f"{relpath}:{qualname}:{start_line}".encode()
        ).hexdigest()[:16]
        records.append(
            SymbolRecord(
                symbol_id=symbol_id,
                name=name,
                kind=_kind_for_node(defn),
                path=relpath,
                start_line=start_line,
                end_line=end_line,
                qualname=qualname,
            )
        )
    records.sort(key=lambda r: (r.path, r.start_line, r.qualname))
    return records


def build_architecture_map(
    repo_id: str,
    repo_path: Path,
    git_sha: str,
) -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []
    for py in sorted(iter_python_files(repo_path)):
        rel = py.relative_to(repo_path).as_posix()
        try:
            source = py.read_bytes()
        except OSError:
            continue
        mod_syms = extract_symbols(source, rel)
        modules.append(
            {
                "path": rel,
                "symbol_count": len(mod_syms),
                "bytes": len(source),
            }
        )
        symbols.extend(asdict(s) for s in mod_syms)

    return {
        "repo_id": repo_id,
        "git_sha": git_sha,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "language": "python",
        "module_count": len(modules),
        "symbol_count": len(symbols),
        "modules": modules,
        "symbols": symbols,
    }


def map_path(maps_dir: Path, repo_id: str, git_sha: str) -> Path:
    return maps_dir / repo_id / git_sha / "architecture_map.json"


def write_map(maps_dir: Path, arch: dict[str, Any]) -> Path:
    out = map_path(maps_dir, arch["repo_id"], arch["git_sha"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(arch, indent=2) + "\n")
    return out


def load_map(maps_dir: Path, repo_id: str, git_sha: str) -> dict[str, Any]:
    path = map_path(maps_dir, repo_id, git_sha)
    # Allow short SHA prefix match among indexed dirs
    if not path.is_file():
        repo_dir = maps_dir / repo_id
        if repo_dir.is_dir():
            matches = [
                d for d in repo_dir.iterdir()
                if d.is_dir() and (d.name.startswith(git_sha) or git_sha.startswith(d.name))
            ]
            if len(matches) == 1:
                path = matches[0] / "architecture_map.json"
            elif len(matches) > 1:
                raise FileNotFoundError(
                    f"ambiguous git_sha prefix {git_sha!r}; candidates={[m.name for m in matches]}"
                )
    if not path.is_file():
        raise FileNotFoundError(
            f"no architecture_map for ({repo_id}, {git_sha}) at {path}. Run indexer first."
        )
    return json.loads(path.read_text())


def index_repo(cfg: GuardConfig, repo_id: str, git_sha: str | None = None) -> Path:
    entry = cfg.require_repo(repo_id)
    if not entry.path.is_dir():
        raise FileNotFoundError(f"allowlisted path missing: {entry.path}")
    sha = resolve_git_sha(entry.path, git_sha)
    cfg.require_pinned_sha(repo_id, sha)
    arch = build_architecture_map(repo_id, entry.path, sha)
    return write_map(cfg.maps_dir, arch)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Index allowlisted repo → architecture_map.json")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--git-sha", default=None, help="Pin revision (default: HEAD)")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    out = index_repo(cfg, args.repo_id, args.git_sha)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
