"""RepoNavigator MCP server (stdio) — three guarded tools."""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from repo_navigator.guards import load_config
from repo_navigator import tools as T

mcp = FastMCP("RepoNavigator")


def _cfg():
    path = os.environ.get("REPO_NAVIGATOR_CONFIG")
    return load_config(Path(path) if path else None)


@mcp.tool()
def get_architecture_map(
    repo_id: str,
    git_sha: str,
    include_symbols: bool = False,
) -> str:
    """Return the offline architecture map for an allowlisted (repo_id, git_sha).

    Requires a pinned git_sha. By default returns modules summary only;
    set include_symbols=true for the full symbol table.
    """
    try:
        result = T.get_architecture_map(
            _cfg(), repo_id, git_sha, include_symbols=include_symbols
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool()
def find_symbol(
    repo_id: str,
    git_sha: str,
    query: str,
    limit: int = 25,
) -> str:
    """Find symbols by name/qualname/path substring in the indexed map."""
    try:
        result = T.find_symbol(_cfg(), repo_id, git_sha, query, limit=limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


@mcp.tool()
def read_symbol(
    repo_id: str,
    git_sha: str,
    symbol_id: str = "",
    qualname: str = "",
    path: str = "",
    context_lines: int = 0,
) -> str:
    """Read a capped source window for one symbol (never whole-file dump).

    Prefer symbol_id from find_symbol. Secret paths are blocked.
    """
    try:
        result = T.read_symbol(
            _cfg(),
            repo_id,
            git_sha,
            symbol_id=symbol_id or None,
            qualname=qualname or None,
            path=path or None,
            context_lines=context_lines,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
