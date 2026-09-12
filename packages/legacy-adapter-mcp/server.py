"""Legacy typed adapter MCP (Phase D scaffold).

One tool: query_client_ledger(client_id, as_of) — fixed schema, no free SQL.
Fake in-memory ledger for local smoke (no real AS400/SOAP).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP(
    "legacy-adapter-ledger",
    instructions=(
        "Typed legacy ledger adapter. Only query_client_ledger is exposed. "
        "No free-form SQL. Deploy behind APIM self-hosted / private network."
    ),
)

# Fake in-memory ledger — stand-in for AS400; never expose raw host to the model.
FAKE_LEDGER: dict[str, dict[str, Any]] = {
    "CLI-1001": {
        "client_id": "CLI-1001",
        "client_name": "Acme Holdings",
        "balance": 125000.50,
        "currency": "USD",
        "status": "active",
        "as_of_snapshots": {
            "2024-12-31": 118000.00,
            "2025-06-30": 125000.50,
        },
    },
    "CLI-2002": {
        "client_id": "CLI-2002",
        "client_name": "Beta Mutual",
        "balance": 4200.00,
        "currency": "USD",
        "status": "active",
        "as_of_snapshots": {
            "2024-12-31": 4000.00,
            "2025-06-30": 4200.00,
        },
    },
    "CLI-3003": {
        "client_id": "CLI-3003",
        "client_name": "Gamma Trust (closed)",
        "balance": 0.0,
        "currency": "USD",
        "status": "closed",
        "as_of_snapshots": {
            "2024-12-31": 0.0,
        },
    },
}


class LedgerRow(BaseModel):
    """Fixed response schema — model never sees SQL/AS400 shapes."""

    client_id: str
    client_name: str
    balance: float
    currency: Literal["USD"] = "USD"
    status: Literal["active", "closed", "unknown"]
    as_of: str
    source: Literal["fake_memory", "live_adapter"] = "fake_memory"


class LedgerError(BaseModel):
    error: Literal["entitlement_denied", "not_found", "invalid_as_of"]
    client_id: str
    message: str


def _correlation_id() -> str:
    return os.environ.get("MCP_CORRELATION_ID") or str(uuid.uuid4())


def _envelope(payload: dict[str, Any], *, ok: bool) -> str:
    return json.dumps(
        {
            "correlation_id": _correlation_id(),
            "tool": "query_client_ledger",
            "ok": ok,
            "data": payload,
        },
        indent=2,
    )


def _entitled_ids() -> set[str]:
    raw = (os.environ.get("LEGACY_ENTITLED_CLIENT_IDS") or "").strip()
    if raw:
        return {x.strip() for x in raw.split(",") if x.strip()}
    # Default smoke entitlement: known fake ledger keys only
    return set(FAKE_LEDGER.keys())


def check_entitlement(client_id: str) -> bool:
    """Stub entitlement: deny unknown client_ids (and any not in allowlist)."""
    return client_id in _entitled_ids()


def _parse_as_of(as_of: str) -> str:
    """Normalize as_of to ISO date string; raise ValueError if invalid."""
    as_of = as_of.strip()
    try:
        return date.fromisoformat(as_of).isoformat()
    except ValueError as exc:
        raise ValueError(f"as_of must be YYYY-MM-DD, got {as_of!r}") from exc


@mcp.tool()
def query_client_ledger(client_id: str, as_of: str) -> str:
    """Return ledger fields for a client as of a date. Fixed schema — no SQL.

    Args:
        client_id: Entitled client identifier (e.g. CLI-1001).
        as_of: Snapshot date YYYY-MM-DD.
    """
    client_id = (client_id or "").strip()
    if not check_entitlement(client_id):
        err = LedgerError(
            error="entitlement_denied",
            client_id=client_id,
            message="Client id is not entitled for this caller. Denied by adapter stub.",
        )
        return _envelope(err.model_dump(), ok=False)

    try:
        as_of_norm = _parse_as_of(as_of)
    except ValueError as exc:
        err = LedgerError(
            error="invalid_as_of",
            client_id=client_id,
            message=str(exc),
        )
        return _envelope(err.model_dump(), ok=False)

    row = FAKE_LEDGER.get(client_id)
    if row is None:
        err = LedgerError(
            error="not_found",
            client_id=client_id,
            message="No ledger row for entitled client (data gap).",
        )
        return _envelope(err.model_dump(), ok=False)

    snapshots: dict[str, float] = row.get("as_of_snapshots") or {}
    if as_of_norm in snapshots:
        balance = float(snapshots[as_of_norm])
    else:
        # Fall back to current balance with note in name field path — still fixed schema
        balance = float(row["balance"])

    out = LedgerRow(
        client_id=row["client_id"],
        client_name=row["client_name"],
        balance=balance,
        currency="USD",
        status=row["status"],
        as_of=as_of_norm,
        source="fake_memory",
    )
    return _envelope(out.model_dump(), ok=True)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
