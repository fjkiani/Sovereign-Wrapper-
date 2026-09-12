"""Atlassian read-only MCP server (Phase C scaffold).

Tools: search, get_page, get_issue only.
Write operations are refused here and MUST also be denied at the AGT policy layer.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from mcp.server.fastmcp import FastMCP

# Allowed tool surface (APIM + AGT must mirror this allowlist).
READ_TOOLS = frozenset({"search", "get_page", "get_issue"})
WRITE_TOOL_DENY_MSG = (
    "Write tools are denied. Register only search/get_page/get_issue on Toolbox; "
    "AGT ACS must deny create/update/delete/comment tools at the policy layer."
)

mcp = FastMCP(
    "atlassian-readonly",
    instructions=(
        "Read-only Atlassian (Confluence/Jira) MCP. "
        "Write tools must be denied at AGT policy layer — this server does not expose them."
    ),
)


def _correlation_id() -> str:
    return os.environ.get("MCP_CORRELATION_ID") or str(uuid.uuid4())


def _has_creds() -> bool:
    token = (os.environ.get("ATLASSIAN_OAUTH_ACCESS_TOKEN") or "").strip()
    api_token = (os.environ.get("ATLASSIAN_API_TOKEN") or "").strip()
    return bool(token or api_token)


def _dry_run() -> bool:
    flag = (os.environ.get("ATLASSIAN_DRY_RUN") or "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    if flag in {"0", "false", "no", "off"}:
        return not _has_creds()
    # Default: dry-run when no credentials
    return not _has_creds()


def _envelope(payload: dict[str, Any], *, tool: str, dry_run: bool) -> str:
    body = {
        "correlation_id": _correlation_id(),
        "tool": tool,
        "mode": "dry_run" if dry_run else "live",
        "read_only": True,
        "data": payload,
    }
    return json.dumps(body, indent=2)


def _refuse_write(op: str) -> str:
    return _envelope(
        {
            "error": "write_denied",
            "operation": op,
            "message": WRITE_TOOL_DENY_MSG,
        },
        tool=op,
        dry_run=_dry_run(),
    )


@mcp.tool()
def search(query: str, limit: int = 10) -> str:
    """Search Confluence/Jira (read-only). Returns matching pages/issues.

    Args:
        query: CQL/JQL-style search string (stub accepts any string).
        limit: Max results (capped at 25).
    """
    limit = max(1, min(int(limit), 25))
    if _dry_run():
        return _envelope(
            {
                "query": query,
                "limit": limit,
                "results": [
                    {
                        "type": "page",
                        "id": "stub-page-100",
                        "title": f"[dry-run] Hit for: {query}",
                        "space": "SOV",
                    },
                    {
                        "type": "issue",
                        "id": "SOV-1",
                        "title": f"[dry-run] Issue match: {query}",
                        "status": "Open",
                    },
                ],
                "note": "Stub JSON — set ATLASSIAN_* creds and ATLASSIAN_DRY_RUN=0 for live.",
            },
            tool="search",
            dry_run=True,
        )

    # Live path placeholder: wire OAuth/token HTTP client behind APIM in a later phase.
    base = os.environ.get("ATLASSIAN_BASE_URL", "").rstrip("/")
    return _envelope(
        {
            "error": "live_not_wired",
            "message": (
                f"Credentials present for {base or '(no ATLASSIAN_BASE_URL)'}, "
                "but live Atlassian HTTP client is not wired in this scaffold. "
                "Use dry-run or implement the API client behind APIM."
            ),
            "query": query,
            "limit": limit,
        },
        tool="search",
        dry_run=False,
    )


@mcp.tool()
def get_page(page_id: str) -> str:
    """Fetch a Confluence page by id (read-only).

    Args:
        page_id: Confluence page id.
    """
    if _dry_run():
        return _envelope(
            {
                "page_id": page_id,
                "title": f"[dry-run] Page {page_id}",
                "space": "SOV",
                "body_storage": "<p>Stub Confluence body. No live call.</p>",
                "version": 1,
            },
            tool="get_page",
            dry_run=True,
        )

    base = os.environ.get("ATLASSIAN_BASE_URL", "").rstrip("/")
    return _envelope(
        {
            "error": "live_not_wired",
            "message": (
                f"Credentials present for {base or '(no ATLASSIAN_BASE_URL)'}, "
                "but live get_page is not wired in this scaffold."
            ),
            "page_id": page_id,
        },
        tool="get_page",
        dry_run=False,
    )


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Fetch a Jira issue by key (read-only).

    Args:
        issue_key: Jira issue key (e.g. SOV-42).
    """
    if _dry_run():
        return _envelope(
            {
                "issue_key": issue_key,
                "summary": f"[dry-run] Issue {issue_key}",
                "status": "Open",
                "assignee": None,
                "fields": {"priority": "Medium", "labels": ["scaffold"]},
            },
            tool="get_issue",
            dry_run=True,
        )

    base = os.environ.get("ATLASSIAN_BASE_URL", "").rstrip("/")
    return _envelope(
        {
            "error": "live_not_wired",
            "message": (
                f"Credentials present for {base or '(no ATLASSIAN_BASE_URL)'}, "
                "but live get_issue is not wired in this scaffold."
            ),
            "issue_key": issue_key,
        },
        tool="get_issue",
        dry_run=False,
    )


# Explicit refuse stubs — never register as MCP tools on Toolbox; kept for local policy demos.
def create_page(*_args: Any, **_kwargs: Any) -> str:
    return _refuse_write("create_page")


def update_issue(*_args: Any, **_kwargs: Any) -> str:
    return _refuse_write("update_issue")


def delete_page(*_args: Any, **_kwargs: Any) -> str:
    return _refuse_write("delete_page")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
