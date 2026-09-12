# Atlassian MCP — read-only scaffold (Phase C)

Governed Confluence/Jira access for the Sovereign Wrapper. **Tools only:** `search`, `get_page`, `get_issue`.

## AGT / policy (non-negotiable)

Write tools (`create_*`, `update_*`, `delete_*`, comment/transition) **must be denied at the AGT ACS policy layer**, even if a future upstream MCP exposes them. This server does not register write tools; APIM allowlist + AGT deny are the real control plane. Do not rely on “the model won’t call them.”

Deploy behind Foundry Toolbox + APIM; OAuth app preferred (read scopes). Vaulted PAT only as credential material behind the gateway — never laptop PAT scripts.

## Env

| Variable | Purpose |
|----------|---------|
| `ATLASSIAN_BASE_URL` | Site URL, e.g. `https://your-site.atlassian.net` |
| `ATLASSIAN_OAUTH_CLIENT_ID` / `ATLASSIAN_OAUTH_CLIENT_SECRET` / `ATLASSIAN_OAUTH_ACCESS_TOKEN` | OAuth placeholders |
| `ATLASSIAN_API_TOKEN` / `ATLASSIAN_EMAIL` | Optional vaulted PAT material |
| `ATLASSIAN_DRY_RUN` | `1` forces stub JSON; default dry-run when no creds |

Copy `.env.example` → `.env` locally. **Never commit secrets.**

## Install / run

Requires **Python ≥3.10** (official `mcp` SDK).

```bash
cd atlassian-mcp
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python smoke_test.py
# MCP stdio (Foundry / Claude Desktop style):
python server.py
```

## Dry-run

With no creds (or `ATLASSIAN_DRY_RUN=1`), each tool returns structured JSON including `correlation_id`, `mode: dry_run`, and stub `data`. Live HTTP client is intentionally not wired in this scaffold.
