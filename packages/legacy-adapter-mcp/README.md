# Legacy adapter — translator (pillar 4)

**Problem:** Banks run 40-year-old systems that will not survive a free-form AI talking SOAP/AS400/SQL.

**Vault rule:** One idiot-proof tool. The model never sees the mainframe.

## Tool

`query_client_ledger(client_id, as_of)`

- Fixed response schema
- **No free SQL**
- Entitlement check (unknown clients denied)
- Local smoke uses an in-memory fake ledger only

## Deploy

Behind **APIM self-hosted gateway / private network**. Not public internet. AGT should escalate high-impact ledger calls.

## Smoke

```bash
cd packages/legacy-adapter-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python smoke_test.py
python server.py   # MCP stdio
```

Known smoke IDs: `CLI-1001`, `CLI-2002`, `CLI-3003`. Requires Python ≥3.10.
