# Atlassian MCP — governed docs (same vault)

**Vault rule:** AI may search/read Confluence/Jira pages and issues **as the user**, not with a master key and not with write tools.

**Tools only:** `search`, `get_page`, `get_issue`.

Write operations (`create_*`, `update_*`, `delete_*`, …) must be **denied at AGT ACS** even if an upstream MCP grows them. This server does not register writes. APIM allowlist + AGT deny are the control plane.

OAuth app preferred (read scopes). Vaulted PAT only as gateway credential material — not laptop PAT-hijack architecture.

## Env

See `.env.example`. Never commit secrets.

| Variable | Purpose |
|----------|---------|
| `ATLASSIAN_BASE_URL` | Site URL |
| `ATLASSIAN_OAUTH_*` / `ATLASSIAN_API_TOKEN` | Creds behind gateway |
| `ATLASSIAN_DRY_RUN=1` | Stub JSON + `correlation_id` |

## Smoke

```bash
cd packages/atlassian-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ATLASSIAN_DRY_RUN=1 python smoke_test.py
python server.py   # MCP stdio
```

Requires Python ≥3.10.
