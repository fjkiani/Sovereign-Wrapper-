#!/usr/bin/env python3
"""Local smoke for legacy-adapter-mcp (no MCP client / AS400 required)."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.pop("LEGACY_ENTITLED_CLIENT_IDS", None)

from server import FAKE_LEDGER, check_entitlement, query_client_ledger  # noqa: E402


def _parse(s: str) -> dict:
    return json.loads(s)


def main() -> int:
    failures: list[str] = []

    # 1) happy path
    r = _parse(query_client_ledger("CLI-1001", "2025-06-30"))
    if not r.get("ok") or "correlation_id" not in r:
        failures.append(f"happy path failed: {r}")
    data = r.get("data") or {}
    if data.get("client_id") != "CLI-1001" or data.get("balance") != 125000.50:
        failures.append(f"ledger fields wrong: {data}")
    if data.get("source") != "fake_memory":
        failures.append("expected fake_memory source")

    # 2) entitlement deny
    r = _parse(query_client_ledger("CLI-UNKNOWN", "2025-06-30"))
    if r.get("ok") is not False:
        failures.append("unknown client should fail")
    if (r.get("data") or {}).get("error") != "entitlement_denied":
        failures.append(f"expected entitlement_denied: {r}")

    # 3) entitlement stub helper
    if check_entitlement("CLI-UNKNOWN"):
        failures.append("check_entitlement should deny unknown")
    if not check_entitlement("CLI-2002"):
        failures.append("check_entitlement should allow CLI-2002")

    # 4) invalid as_of
    r = _parse(query_client_ledger("CLI-1001", "not-a-date"))
    if (r.get("data") or {}).get("error") != "invalid_as_of":
        failures.append(f"expected invalid_as_of: {r}")

    # 5) no free SQL surface — only one tool name in envelope
    if r.get("tool") != "query_client_ledger":
        failures.append("tool name drift")

    # 6) custom entitlement env
    os.environ["LEGACY_ENTITLED_CLIENT_IDS"] = "CLI-1001"
    # re-import not needed — check reads env each call
    if check_entitlement("CLI-2002"):
        failures.append("env allowlist should deny CLI-2002")
    r = _parse(query_client_ledger("CLI-2002", "2025-06-30"))
    if (r.get("data") or {}).get("error") != "entitlement_denied":
        failures.append(f"env entitlement deny failed: {r}")
    os.environ.pop("LEGACY_ENTITLED_CLIENT_IDS", None)

    if failures:
        print("SMOKE FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SMOKE PASS — legacy-adapter-mcp ledger + entitlement OK")
    print(f"  fake_clients={sorted(FAKE_LEDGER)}")
    print(f"  sample_correlation_id={_parse(query_client_ledger('CLI-1001', '2024-12-31'))['correlation_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
