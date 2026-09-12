# AGENTS — entry + chokehold

Read this before any edit, claim, smoke, or push.

## Vision

We are building a **CISO-proof vault for AI**: an iron cage where the model is treated as intelligent and **hostile**. It only sees data through user-scoped identity, fail-closed policy, and tiny typed tools. It cannot “just read the repo” or “just run SQL.”

Not a chatbot. A Sovereign Wrapper.

## Four pillars → code

| Pillar | Plain English | Where |
|--------|---------------|--------|
| **1. AGT Deny** | Bouncer: tool calls die before execution if Rego/ACS says no | Vendor AGT @ `0533cea`; `spine/run-agt-deny-smoke.sh` |
| **2. OBO + APIM** | Badge check: agent acts as Susan, not with a master key; APIM verifies JWT | OBO @ `fd07d5d`, APIM @ `2d5478b`; `spine/RUNBOOK-*.txt` |
| **3. RepoNavigator** | Map maker: table-of-contents + ≤8192-byte symbol reads; block secret paths | `packages/repo-navigator/` |
| **4. Legacy adapter** | Translator: only `query_client_ledger`; AS400/SOAP never exposed | `packages/legacy-adapter-mcp/` |

Docs plane: `packages/atlassian-mcp/` — read-only Confluence/Jira; AGT denies writes.

## Entry order

1. This file
2. [`README.md`](./README.md) — vault story + status
3. [`REFERENCES.md`](./REFERENCES.md) — pinned SHAs
4. `spine/phase-a-status.json` — Phase A truth (OPEN until Azure artifacts)
5. Package README for the surface you touch

## Chokehold — must not

1. Claim PASS / online / compliant without a this-turn **artifact path** (smoke log, `architecture_map.json`, APIM/`azd` output under `spine/`).
2. Ship vibes: empty stubs labeled production-ready, fake deny transcripts, brochure MCP.
3. Give the agent a master key or unauthenticated `/mcp` “engine” (OpenClaw anti-pattern — REFERENCES).
4. Add Atlassian **write** tools without AGT write-deny + Alpha OK.
5. Expose free SQL, shell, or whole-file dump tools.
6. Commit secrets. Use `.env.example` only.
7. Vendor Microsoft megarepos into git without Alpha OK — use `SOVEREIGN_VENDOR_ROOT`.
8. Create `DRAFT-*` / `RECALIBRATION-*` receipt markdown.
9. Mark Phase A green while `spine/phase-a-status.json` says `OPEN` or prereqs fail.
10. Let the model read `.env` / credential paths — RepoNavigator guards are mandatory, not optional.

## Chokehold — must

1. Evidence from `Read` / `Grep` / `Shell` over memory.
2. RepoNavigator flow only: `get_architecture_map` → `find_symbol` → `read_symbol`.
3. Smoke before claiming a package works (commands below).
4. After Azure work: update `spine/phase-a-status.json` with real status + artifact paths.
5. Keep tool surfaces allowlisted and typed.

## Default first task

```bash
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
```

If smoke fails, fix RepoNavigator. Do not invent Foundry PASS.
