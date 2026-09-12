# RepoNavigator — map maker (pillar 3)

**Problem:** “Summarize this codebase” makes the model download everything, burn tokens, and often hit `.env` / secrets.

**Vault rule:** Give a **table of contents** (Tree-sitter architecture map), then only a **capped symbol window** (default **8192 bytes**). Secret path globs are blocked in code.

## Tools

| Tool | Purpose |
|------|---------|
| `get_architecture_map` | Map for `(repo_id, git_sha)` — allowlisted + pinned SHA |
| `find_symbol` | Locate class/function on the map |
| `read_symbol` | Read only that symbol’s window |

Flow for agents: **map → find → read**. Never whole-file dump.

## Install / smoke

```bash
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
```

MCP stdio: `repo-navigator` or `python -m repo_navigator.server`

## Guards (`config.yaml` + `guards.py`)

- Repo allowlist
- Required pinned `git_sha`
- `max_read_bytes` / `max_symbol_lines`
- Blocked paths: `.env`, credentials, keys, etc.
