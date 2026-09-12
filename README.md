# Sovereign Wrapper

## What this is

**A CISO-proof vault for AI** — an iron cage around the model.

Corporate default today: ask an LLM to “summarize the codebase” or “check a client ledger,” and it grabs raw files, burns tokens, and can touch `.env` secrets or run destructive SQL. CISOs block that for good reason.

This repo builds the mechanism that makes the model **structurally incapable** of those moves: fail-closed policy, user-scoped identity, map-then-read code access, and typed legacy translators. The LLM is treated as intelligent and **untrusted**.

**Not a chatbot.** A control plane.

Repo: https://github.com/fjkiani/Sovereign-Wrapper-

Agents: start at [`AGENTS.md`](./AGENTS.md). Pins: [`REFERENCES.md`](./REFERENCES.md).

---

## Four pillars (what we are coding)

### 1. AGT Deny — the bouncer

Before any tool runs (`run_sql`, `read_file`, …), ACS/Rego evaluates the call. Fail-closed: if the rulebook says no, the request is dropped — the model never executes it.

- Vendor: Agent Governance Toolkit @ `0533cea`
- Smoke path: `spine/run-agt-deny-smoke.sh` → `foundry_agents.py`
- Status: **OPEN** until Azure/AOAI/`opa` prereqs clear (`spine/phase-a-status.json`)

### 2. OBO + APIM — the badge check

No master key for the agent. Calls carry the **user’s** Entra identity (On-Behalf-Of). APIM is the tollbooth: JWT/`validate-jwt`, quotas, private backends. If Susan cannot see HR data, neither can the agent acting for Susan.

- OBO template @ `fd07d5d` (`UseOnBehalfOf`)
- APIM governance @ `2d5478b`
- Runbooks: `spine/RUNBOOK-obo-azd.txt`, `spine/RUNBOOK-apim.txt`

### 3. RepoNavigator — the map maker

No whole-repo dumps. Tree-sitter builds an architecture map; the agent may only fetch a symbol window (**max 8192 bytes**). Secret path globs (`.env`, credentials, keys) are blocked in code.

- Owned: `packages/repo-navigator/`
- Tools: `get_architecture_map` → `find_symbol` → `read_symbol`

### 4. Legacy adapter — the translator

Mainframes/SOAP stay invisible. One typed tool: `query_client_ledger(client_id, as_of)`. No free SQL, no drop/delete, entitlement-checked.

- Owned: `packages/legacy-adapter-mcp/`
- Deploy posture: private network / APIM self-hosted gateway

**Atlassian** (docs plane): same cage — read-only `search` / `get_page` / `get_issue` in `packages/atlassian-mcp/`; writes denied at AGT.

---

## Architecture

```text
User (Entra)
  → Foundry Agent Service           ← engine (run loop)
       × AGT ACS deny/allow         ← bouncer
       → APIM                       ← badge / model egress
       → MCP Toolbox
            → Azure MCP (OBO)
            → RepoNavigator
            → Atlassian (read-only)
            → Legacy adapter
```

---

## Skeleton

```text
AGENTS.md / REFERENCES.md / README.md
spine/                         # Phase A ops (no fake PASS)
packages/repo-navigator/       # pillar 3
packages/atlassian-mcp/        # governed docs MCP
packages/legacy-adapter-mcp/   # pillar 4
```

Upstream Microsoft trees are **not** vendored here. Set `SOVEREIGN_VENDOR_ROOT` (see REFERENCES).

---

## Status

| Pillar | Status |
|--------|--------|
| AGT Deny + OBO + APIM (Phase A) | **OPEN** — needs Alpha Azure CLIs/creds |
| RepoNavigator | **Shipped** — local smoke |
| Atlassian read-only | **Shipped** — dry-run smoke |
| Legacy adapter | **Shipped** — fake ledger smoke |

---

## Default first task (agents)

```bash
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
```

---

## Kill list

- Master-key agents / unauthenticated MCP as the engine
- Whole-file dumps, free SQL, shell tools
- PASS without artifact paths
- PAT-hijack / bypass-procurement as architecture
- Secrets in git; DRAFT/RECAL receipt novels
- Greening Phase A while `spine/phase-a-status.json` is OPEN
