#!/usr/bin/env python3
"""Local smoke for atlassian-mcp (no MCP client required)."""

from __future__ import annotations

import json
import os
import sys

# Ensure package dir is importable when run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force dry-run for smoke unless caller overrides
os.environ.setdefault("ATLASSIAN_DRY_RUN", "1")
# Clear creds so default dry-run path is exercised
for k in (
    "ATLASSIAN_OAUTH_ACCESS_TOKEN",
    "ATLASSIAN_API_TOKEN",
):
    os.environ.pop(k, None)

from server import (  # noqa: E402
    READ_TOOLS,
    create_page,
    get_issue,
    get_page,
    search,
    update_issue,
)


def _parse(s: str) -> dict:
    return json.loads(s)


def main() -> int:
    failures: list[str] = []

    # 1) search stub
    r = _parse(search("sovereign wrapper", limit=5))
    if r.get("mode") != "dry_run" or "correlation_id" not in r:
        failures.append(f"search envelope bad: {r}")
    if not r.get("data", {}).get("results"):
        failures.append("search missing stub results")

    # 2) get_page stub
    r = _parse(get_page("100"))
    if r.get("tool") != "get_page" or r.get("mode") != "dry_run":
        failures.append(f"get_page envelope bad: {r}")

    # 3) get_issue stub
    r = _parse(get_issue("SOV-1"))
    if r.get("tool") != "get_issue" or "correlation_id" not in r:
        failures.append(f"get_issue envelope bad: {r}")

    # 4) write refuse (local stubs — not registered MCP tools)
    for name, fn in (
        ("create_page", create_page),
        ("update_issue", update_issue),
    ):
        r = _parse(fn())
        if r.get("data", {}).get("error") != "write_denied":
            failures.append(f"{name} did not refuse write: {r}")

    # 5) allowlist surface
    if READ_TOOLS != frozenset({"search", "get_page", "get_issue"}):
        failures.append(f"READ_TOOLS drift: {READ_TOOLS}")

    if failures:
        print("SMOKE FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SMOKE PASS — atlassian-mcp dry-run stubs + write refuse OK")
    print(f"  tools={sorted(READ_TOOLS)}")
    print(f"  sample_correlation_id={_parse(search('ping'))['correlation_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
