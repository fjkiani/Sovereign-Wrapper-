# RepoNavigator MCP v0

Offline Tree-sitter architecture maps + three guarded MCP tools.

## Install

```bash
cd /Users/fahadkiani/Desktop/development/_sovereign-audit/repo-navigator
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Index fixture

```bash
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
# smoke creates git commit in fixtures/demo-repo if needed
python scripts/smoke.py
# or manually after fixture has a HEAD:
repo-navigator-index --repo-id demo --config config.yaml
```

## Run MCP (stdio)

```bash
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
repo-navigator
# or: python -m repo_navigator.server
```

## Tools

| Tool | Args | Notes |
|------|------|-------|
| `get_architecture_map` | `repo_id`, `git_sha`, `include_symbols?` | Allowlisted + pinned SHA only |
| `find_symbol` | `repo_id`, `git_sha`, `query`, `limit?` | Substring search on map |
| `read_symbol` | `repo_id`, `git_sha`, `symbol_id` / `qualname`+`path` | Capped line/byte window |

Guards: allowlist (`config.yaml`), required `git_sha`, `max_read_bytes` / `max_symbol_lines`, blocked secret paths (`.env`, credentials, keys, …).

Maps land at `data/maps/<repo_id>/<git_sha>/architecture_map.json`.
