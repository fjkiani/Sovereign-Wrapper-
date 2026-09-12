# Legacy Adapter MCP — typed ledger (Phase D)

One system, one tool: `query_client_ledger(client_id, as_of)`.

Fixed response schema. **No free-form SQL.** AS400/SOAP stay invisible to the model — this scaffold uses an in-memory fake ledger for local smoke only.

## Deploy posture

Run behind **APIM self-hosted gateway / private network** (ExpressRoute or equivalent). Do not expose this MCP on the public internet. Register only `query_client_ledger` on Foundry Toolbox; AGT should escalate high-impact ledger calls per policy.

## Tool

| Arg | Type | Notes |
|-----|------|--------|
| `client_id` | string | Must pass entitlement stub |
| `as_of` | string | `YYYY-MM-DD` |

Entitlement stub denies unknown `client_id`s (and any not in `LEGACY_ENTITLED_CLIENT_IDS` when set).

## Install / smoke

Requires **Python ≥3.10** (official `mcp` SDK).

```bash
cd legacy-adapter-mcp
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python smoke_test.py
# MCP stdio:
python server.py
```

Known smoke clients: `CLI-1001`, `CLI-2002`, `CLI-3003`.
