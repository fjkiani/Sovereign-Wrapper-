# AGENTS — entry + chokehold

Read this file before any edit, claim, smoke, or push in this repository.

## Vision (one line)

**Foundry runs agents. AGT ACS denies unsafe tool calls. APIM owns model egress. Owned MCPs under `packages/` are the tools. This repo is not vibes.**

## Entry order

1. `README.md` — skeleton map
2. This file — chokehold rules
3. `REFERENCES.md` — pinned upstream SHAs (vendor clones; do not invent)
4. `spine/phase-a-status.json` — live Phase A status (OPEN until Azure smoke artifacts exist)
5. Package README under the package you touch

## Architecture roles (do not confuse)

| Role | What | In this repo |
|------|------|--------------|
| Engine | Microsoft Foundry Agent Service | product — not code here |
| Kernel | AGT ACS (`foundry_agents.py`) | vendor via `SOVEREIGN_VENDOR_ROOT` |
| Egress | APIM Foundry governance | vendor |
| OBO tools | `azmcp-obo-template` | vendor |
| Owned tools | RepoNavigator / Atlassian / Legacy | `packages/*` |
| Ops spine | prereq gate + runbooks | `spine/` |

## Chokehold — agents must not

1. **Claim PASS / online / compliant / ready** without a this-turn artifact path:
   - smoke stdout file, or
   - `packages/repo-navigator/data/maps/<repo>/<sha>/architecture_map.json`, or
   - APIM request id / `azd` deploy output path under `spine/`
2. **Push “vibes”** — README novels, empty stubs labeled production-ready, fake MCP, fabricated deny logs.
3. **Treat OpenClaw unauthenticated `/mcp` as the engine** — anti-pattern only (see REFERENCES).
4. **Add write tools** to Atlassian package without AGT write-deny + explicit Alpha OK.
5. **Expose free SQL / shell / whole-file dump** as MCP tools.
6. **Commit secrets** (`.env`, PATs, API keys). Use `.env.example` only.
7. **Vendor entire Microsoft megarepos into git** without Alpha OK — clone to `SOVEREIGN_VENDOR_ROOT` / `vendor/` (gitignored) and pin SHA in REFERENCES.
8. **Create `DRAFT-*` / `RECALIBRATION-*` receipt markdown** — chat audit or append existing canon only.
9. **Mark Phase A green** while `spine/phase-a-status.json` says `OPEN` or prereqs fail.

## Chokehold — agents must

1. Prefer `Read` / `Grep` / `Shell` evidence over memory.
2. For RepoNavigator: map-then-read only — `get_architecture_map` → `find_symbol` → `read_symbol` (max 8192 bytes).
3. Run package smoke before claiming a package works:
   - `packages/repo-navigator`: `python scripts/smoke.py`
   - `packages/atlassian-mcp`: `python smoke_test.py`
   - `packages/legacy-adapter-mcp`: `python smoke_test.py`
4. After Azure work: update `spine/phase-a-status.json` with real status + artifact paths.
5. Keep tool surfaces allowlisted and typed.

## Default first task for a new agent session

```bash
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
```

If smoke fails, fix RepoNavigator. Do not invent Foundry PASS.
