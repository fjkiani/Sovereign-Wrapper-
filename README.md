# Sovereign Wrapper

**CISO-proof vault for AI** — an iron cage around the model, not a chatbot.

Corporate default: ask an LLM to summarize a codebase or check a client ledger and it grabs raw files, burns tokens, may read `.env`, or run destructive SQL. CISOs block that.

This control plane makes the model **structurally incapable** of those moves: fail-closed policy, user-scoped identity, map-then-read code access, typed legacy translators. The LLM is treated as intelligent and **untrusted**.

- GitHub: https://github.com/fjkiani/Sovereign-Wrapper-
- Agents: [`AGENTS.md`](./AGENTS.md) (chokehold)
- Pins: [`REFERENCES.md`](./REFERENCES.md)
- Phase A truth: [`spine/phase-a-status.json`](./spine/phase-a-status.json) — **OPEN** until live Azure artifacts (do not invent PASS)

---

## Engine vs parts (read this first)

| Layer | What | Engine? |
|-------|------|---------|
| **Microsoft Foundry Agent Service** | Managed run loop: threads, tool calls, scale, identity | **YES — run engine** |
| **AGT ACS** (`AgentControl` / Rego) | Fail-closed policy on every tool/model hop | **YES — policy kernel** |
| APIM Foundry governance | JWT tollbooth, quotas, private backends | No — pipe |
| azmcp-obo-template | Azure MCP with On-Behalf-Of | No — tools |
| microsoft/mcp | Official Azure/Fabric MCP catalog | No — tools |
| EnterpriseMCP | Entra Graph tools | No — tools |
| **This repo `packages/*`** | RepoNavigator, Atlassian RO, legacy adapter | No — owned tools |
| OpenClaw / unauth `/mcp` | Legal SaaS island / master-key anti-pattern | **Never the engine** |

**One sentence:** Foundry runs the agent; AGT makes bad tool calls die before execution; APIM + OBO + Toolbox + owned MCPs are how data is reached — not how the agent “thinks.”

You do **not** get a runnable vault by cloning tools alone. Clones without a Foundry agent + AGT gate are **silos**.

---

## Four pillars (plain English → code)

| # | Pillar | Plain English | Code |
|---|--------|---------------|------|
| 1 | **AGT Deny** (bouncer) | Before `run_sql` / `read_file` / … executes, ACS checks the rulebook. Fail-closed drop. | Vendor AGT @ `0533cea` → `foundry_agents.py` |
| 2 | **OBO + APIM** (badge check) | Agent presents **Susan's** Entra badge, not a master key. APIM verifies JWT. | OBO @ `fd07d5d`, APIM @ `2d5478b` |
| 3 | **RepoNavigator** (map maker) | Table of contents, then ≤8192-byte symbol reads; secret paths blocked. | `packages/repo-navigator/` |
| 4 | **Legacy adapter** (translator) | Only `query_client_ledger` — no free SQL; SOAP/AS400 never exposed. | `packages/legacy-adapter-mcp/` |

Docs plane (same cage): `packages/atlassian-mcp/` — `search` / `get_page` / `get_issue` only. **Reject** “PAT Hijack / bypass procurement” as architecture; use approved OAuth/app + APIM allowlist + AGT write-deny.

---

## All repos — how they stitch

Upstream clones live under `SOVEREIGN_VENDOR_ROOT` (default sibling `_sovereign-audit`). Pins verified in [`REFERENCES.md`](./REFERENCES.md).

### Owned (this git repo)

| Path | Role in stitch |
|------|----------------|
| `spine/` | Phase A ops: prereqs, AGT deny smoke wrapper, OBO/APIM runbooks |
| `packages/repo-navigator/` | Pillar 3 MCP — map → find → read_symbol |
| `packages/atlassian-mcp/` | Governed Confluence/Jira read MCP |
| `packages/legacy-adapter-mcp/` | Pillar 4 typed ledger MCP |

### Vendor (clone @ SHA — not vendored into git)

| Dir under `$SOVEREIGN_VENDOR_ROOT` | SHA | Stitch role |
|------------------------------------|-----|-------------|
| `agent-governance-toolkit` | `0533cea` | Policy kernel; `.../foundry_agents.py`, `foundry_agent_guarded.py` |
| `apim-foundry-governance` | `2d5478b` | Model + MCP egress PEP (`validate-jwt`, terraform) |
| `azmcp-obo-template` | `fd07d5d` | User-scoped Azure tools on ACA (`UseOnBehalfOf`) |
| `mcp` | `797cee3` | Official Azure MCP catalog (pick tools; not the loop) |
| `EnterpriseMCP` | `5c165f1` | Entra Graph read later |

### Anti-pattern (reference only)

| Clone | Why it is not the vault |
|-------|-------------------------|
| `openclaw-saas` @ `9f07708` | Unauthenticated `/mcp` / master-key style — domain cargo only |

```bash
export SOVEREIGN_VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$HOME/Desktop/development/_sovereign-audit}"
```

---

## How the agent stitches this together (runtime path)

One user turn → one governed path. Nothing below is “optional decoration.”

```text
1. User (Entra ID)
      │
2. ──► Microsoft Foundry Agent Service          ← RUN ENGINE (loop / tools / threads)
      │         │
      │         × AGT ACS (AgentControl + Rego)  ← every proposed tool/model hop
      │         │    ALLOW → continue
      │         │    DENY  → drop (tool never runs)   ← pillar 1
      │         │
3. ──► APIM (apim-foundry-governance)           ← badge + egress tollbooth
      │         │    validate-jwt / MI / quotas / private backends
      │         │
4. ──► Foundry Toolbox / remote MCP endpoints
      │         ├─ Azure MCP (azmcp-obo-template)     ← acts as USER (OBO)     pillar 2
      │         ├─ EnterpriseMCP (optional)           ← Entra Graph read
      │         ├─ RepoNavigator (this repo)          ← map / find / read_symbol  pillar 3
      │         ├─ Atlassian MCP (this repo)          ← search / get_page / get_issue
      │         └─ Legacy adapter (this repo)         ← query_client_ledger only   pillar 4
      │
5. Response returns only through the same cage (no side-channel raw file dump)
```

### What the agent is allowed to do (tool choreography)

| Goal | Ordered tools | Forbidden |
|------|---------------|-----------|
| Understand code | `get_architecture_map` → `find_symbol` → `read_symbol` | Whole-repo / whole-file dump, reading `.env` / credential globs |
| Read docs/tickets | `search` → `get_page` / `get_issue` | create/update/delete (AGT deny even if upstream grows writes) |
| Client ledger | `query_client_ledger(client_id, as_of)` | Free SQL, SOAP, shell, drop/delete |
| Azure ops | OBO Azure MCP tools only | Agent master key / shared god credential |

AGT sits on **every** hop. APIM does not replace AGT; OBO does not replace AGT.

### What “stitched” means in practice

| State | Meaning |
|-------|---------|
| **Silo** (today for packages) | MCP smokes pass locally; Foundry does not call them yet |
| **Kernel proven** | `spine/run-agt-deny-smoke.sh` log shows ALLOW + DENY + OK line |
| **Stitched** | One Foundry agent has Toolbox entries for owned + OBO MCPs, traffic via APIM, ACS policy attached |

Package smoke ≠ stitched vault. Phase A OPEN = not stitched.

---

## Execution order (kill the silo)

| Step | Deliverable | Gate artifact |
|------|-------------|---------------|
| **E0** | Alpha: install `az` `azd` `terraform` `opa`; `az login`; export `AZURE_OPENAI_*` | `spine/check-prereqs.sh` exit 0 |
| **E1** | AGT deny-proof via vendor `foundry_agents.py` | Smoke log under `spine/` with ALLOW/DENY/OK |
| **E2** | Foundry project + one hosted/prompt agent + `foundry_agent_guarded.py` path | Live agent id / thread evidence |
| **E3** | `azd up` OBO Azure MCP | ACA MCP URL + OBO (`RUNBOOK-obo-azd.txt`) |
| **E4** | Attach `packages/*` MCPs to Toolbox (allowlisted tools only) | Agent can call map / Atlassian RO / ledger |
| **E5** | APIM in front of model + MCP egress | `RUNBOOK-apim.txt` deploy evidence |

Runbooks: [`spine/README.md`](./spine/README.md).

---

## Status (evidence-backed — re-check `phase-a-status.json`)

| Surface | Status | Notes |
|---------|--------|-------|
| Foundry run engine live | **OPEN** | Needs E0–E2 |
| AGT deny smoke live | **OPEN** | `azure_smoke_ran: false`, `pass_claimed: false` |
| RepoNavigator | Local smoke + demo `architecture_map.json` | Not yet on Foundry Toolbox |
| Atlassian MCP | Dry-run smoke | Governed pattern; not hijack |
| Legacy adapter | Fake-ledger smoke | Real AS400/SOAP behind private GW later |
| OBO + APIM deploy | **OPEN** | CLIs/creds absent on last prereq check |

---

## Repo layout

```text
AGENTS.md  REFERENCES.md  README.md
spine/                          # E0–E5 ops (no fake PASS)
packages/repo-navigator/        # pillar 3
packages/atlassian-mcp/         # docs plane
packages/legacy-adapter-mcp/    # pillar 4
```

---

## Local package smokes (silo proof only)

```bash
# Pillar 3
cd packages/repo-navigator && python3 -m venv .venv && source .venv/bin/activate
pip install -e . && export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml && python scripts/smoke.py

# Docs plane
cd packages/atlassian-mcp && pip install -r requirements.txt
ATLASSIAN_DRY_RUN=1 python smoke_test.py

# Pillar 4
cd packages/legacy-adapter-mcp && pip install -r requirements.txt && python smoke_test.py
```

Phase A (engine + kernel):

```bash
cd spine && ./check-prereqs.sh && ./run-agt-deny-smoke.sh
```

---

## Kill list

- Treating any MCP / APIM / OpenClaw as the **run engine**
- Master-key agents or unauthenticated `/mcp`
- Whole-file dumps, free SQL, shell tools, secret-path reads
- Claiming PASS / “stitched” / Phase A green without artifact paths this turn
- PAT-hijack / bypass-procurement as the Atlassian strategy
- Secrets in git; `DRAFT-*` / `RECALIBRATION-*` receipt novels
- Greening `spine/phase-a-status.json` while status is OPEN
