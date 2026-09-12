"""Tool implementations (callable without MCP client)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repo_navigator.guards import GuardConfig
from repo_navigator.indexer import load_map


def get_architecture_map(
    cfg: GuardConfig,
    repo_id: str,
    git_sha: str,
    *,
    include_symbols: bool = False,
) -> dict[str, Any]:
    """Return architecture map for (repo_id, git_sha). Symbols omitted by default (summary)."""
    sha = cfg.require_pinned_sha(repo_id, git_sha)
    cfg.require_repo(repo_id)
    arch = load_map(cfg.maps_dir, repo_id, sha)
    if include_symbols:
        return arch
    # Compact view for agents — modules + counts, not full dump unless asked
    return {
        "repo_id": arch["repo_id"],
        "git_sha": arch["git_sha"],
        "indexed_at": arch.get("indexed_at"),
        "language": arch.get("language"),
        "module_count": arch.get("module_count"),
        "symbol_count": arch.get("symbol_count"),
        "modules": arch.get("modules", []),
        "note": "Pass include_symbols=true for full symbol table, or use find_symbol.",
    }


def find_symbol(
    cfg: GuardConfig,
    repo_id: str,
    git_sha: str,
    query: str,
    *,
    limit: int = 25,
) -> dict[str, Any]:
    """Search symbols by name / qualname substring (case-insensitive)."""
    sha = cfg.require_pinned_sha(repo_id, git_sha)
    cfg.require_repo(repo_id)
    if not query or not query.strip():
        raise ValueError("query is required")
    arch = load_map(cfg.maps_dir, repo_id, sha)
    q = query.strip().lower()
    hits = []
    for sym in arch.get("symbols", []):
        hay = f"{sym.get('name', '')} {sym.get('qualname', '')} {sym.get('path', '')}".lower()
        if q in hay:
            hits.append(sym)
        if len(hits) >= max(1, min(limit, 100)):
            break
    return {
        "repo_id": repo_id,
        "git_sha": arch["git_sha"],
        "query": query,
        "count": len(hits),
        "matches": hits,
    }


def read_symbol(
    cfg: GuardConfig,
    repo_id: str,
    git_sha: str,
    *,
    symbol_id: str | None = None,
    qualname: str | None = None,
    path: str | None = None,
    context_lines: int = 0,
) -> dict[str, Any]:
    """Read a capped line window for one symbol. Never whole-file dump."""
    sha = cfg.require_pinned_sha(repo_id, git_sha)
    entry = cfg.require_repo(repo_id)
    arch = load_map(cfg.maps_dir, repo_id, sha)

    sym: dict[str, Any] | None = None
    for s in arch.get("symbols", []):
        if symbol_id and s.get("symbol_id") == symbol_id:
            sym = s
            break
        if qualname and s.get("qualname") == qualname:
            if path is None or s.get("path") == path:
                sym = s
                break
        if path and qualname is None and symbol_id is None and s.get("path") == path:
            # ambiguous — require name
            continue

    if sym is None and path and qualname:
        for s in arch.get("symbols", []):
            if s.get("path") == path and s.get("qualname") == qualname:
                sym = s
                break

    if sym is None:
        raise LookupError(
            "symbol not found — use find_symbol first "
            f"(symbol_id={symbol_id!r}, qualname={qualname!r}, path={path!r})"
        )

    rel = cfg.assert_safe_relpath(sym["path"])
    file_path = (entry.path / rel).resolve()
    if not str(file_path).startswith(str(entry.path.resolve())):
        raise PermissionError("path escape blocked")
    if not file_path.is_file():
        raise FileNotFoundError(f"source missing: {rel}")

    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    start = max(1, int(sym["start_line"]) - max(0, context_lines))
    end = int(sym["end_line"]) + max(0, context_lines)
    # Cap window
    max_lines = cfg.max_symbol_lines
    if end - start + 1 > max_lines:
        end = start + max_lines - 1

    window = lines[start - 1 : end]
    body = "".join(window)
    body = cfg.clamp_bytes(body)

    return {
        "repo_id": repo_id,
        "git_sha": arch["git_sha"],
        "symbol": sym,
        "start_line": start,
        "end_line": min(end, len(lines)),
        "capped": (int(sym["end_line"]) - int(sym["start_line"]) + 1) > max_lines
        or len(body.encode("utf-8")) >= cfg.max_read_bytes,
        "content": body,
    }


def tools_as_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2)
