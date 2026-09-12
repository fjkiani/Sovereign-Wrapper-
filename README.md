# Sovereign Wrapper

**What this repo is today:** three local MCP packages + Azure spine runbooks.  
**What it is not yet:** a running Foundry agent, live AGT deny smoke, or APIM/OBO deploy.

Target (not claimed shipped): Foundry Agent Service as the run loop, AGT ACS as fail-closed policy, APIM + OBO for egress/identity, these MCPs as allowlisted tools. Pins for upstream clones: [`REFERENCES.md`](./REFERENCES.md). Agent chokehold: [`AGENTS.md`](./AGENTS.md).

| Gate | File | Status (this machine) |
|------|------|------------------------|
| Phase A (Foundry / AGT / OBO / APIM) | [`spine/phase-a-status.json`](./spine/phase-a-status.json) | **OPEN** — `az`/`azd`/`terraform`/`opa` missing; no `AZURE_OPENAI_*`; `azure_smoke_ran: false` |
| Package smokes | commands below | **PASS** on Python **3.11** (2026-09-12) |

Do not invent Phase A PASS. Package smoke ≠ stitched vault.

---

## Layout (everything that exists)

```text
AGENTS.md
REFERENCES.md
README.md
spine/
  check-prereqs.sh          # exits non-zero while Phase A OPEN
  run-agt-deny-smoke.sh     # wraps vendor foundry_agents.py (needs Azure+opa)
  RUNBOOK-foundry-agt.txt
  RUNBOOK-obo-azd.txt
  RUNBOOK-apim.txt
  phase-a-status.json       # truth file
  README.md
packages/
  repo-navigator/           # MCP: map / find / read_symbol
  atlassian-mcp/            # MCP: search / get_page / get_issue (dry-run OK)
  legacy-adapter-mcp/       # MCP: query_client_ledger (in-memory fake)
```

Upstream Microsoft trees are **not** in this git repo. Point at sibling clones:

```bash
export SOVEREIGN_VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$HOME/Desktop/development/_sovereign-audit}"
# expect: agent-governance-toolkit, apim-foundry-governance, azmcp-obo-template, mcp, EnterpriseMCP
```

AGT example present on disk when vendor root is set:  
`$SOVEREIGN_VENDOR_ROOT/agent-governance-toolkit/policy-engine/sdk/python/examples/real_packages/foundry_agents.py`

---

## Packages (runnable now)

Use **Python ≥3.10** (verified **3.11** via Homebrew). System 3.9 + old pip fails (`mcp` / editable install).

### 1. `packages/repo-navigator`

Tree-sitter index of an allowlisted repo → architecture map → capped symbol read (`max_read_bytes: 8192` in `config.yaml`). Secret path globs blocked in `guards.py`.

| Tool | Purpose |
|------|---------|
| `get_architecture_map` | Map for `(repo_id, git_sha)` |
| `find_symbol` | Lookup on the map |
| `read_symbol` | Read one symbol window |

Allowlisted fixture only today: `demo` → `fixtures/demo-repo`.

```bash
cd packages/repo-navigator
python3.11 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
# expect: SMOKE PASS + data/maps/demo/<sha>/architecture_map.json
```

This-turn artifact: `packages/repo-navigator/data/maps/demo/f6766d5ac674948747e829bbf7ebd727a0f67bf1/architecture_map.json`

### 2. `packages/atlassian-mcp`

Read tools only: `search`, `get_page`, `get_issue`. Write helpers refuse. Live Atlassian needs env from `.env.example`; smoke uses `ATLASSIAN_DRY_RUN=1`.

```bash
cd packages/atlassian-mcp
python3.11 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
ATLASSIAN_DRY_RUN=1 python smoke_test.py
# expect: SMOKE PASS — dry-run stubs + write refuse OK
```

### 3. `packages/legacy-adapter-mcp`

One tool: `query_client_ledger(client_id, as_of)`. No SQL string from the model. Smoke uses an **in-memory fake** ledger (`CLI-1001`, `CLI-2002`, `CLI-3003`). Not a mainframe connector yet.

```bash
cd packages/legacy-adapter-mcp
python3.11 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
python smoke_test.py
# expect: SMOKE PASS — ledger + entitlement OK
```

---

## Spine (not runnable until Alpha Azure)

```bash
cd spine
./check-prereqs.sh    # RESULT=OPEN until CLIs + AOAI env exist
./run-agt-deny-smoke.sh
```

Blocking misses from last prereq run: `az`, `azd`, `terraform`, `opa` (or `ACS_OPA_PATH`), `AZURE_OPENAI_ENDPOINT|API_KEY|DEPLOYMENT|API_VERSION`.

Clear strategy is in `phase-a-status.json`. Runbooks describe Foundry+AGT deny-proof, OBO `azd up`, and APIM terraform — **documents only** until those commands succeed and logs land under `spine/`.

---

## Intended stitch (backlog — not implemented in this repo)

```text
User (Entra)
  → Foundry Agent Service          # run engine (Azure service — not code in this git)
       × AGT ACS                   # vendor foundry_agents.py / foundry_agent_guarded.py
       → APIM                      # vendor apim-foundry-governance
       → Toolbox MCP
            → Azure MCP OBO        # vendor azmcp-obo-template
            → repo-navigator       # this repo (stdio/remote — not wired yet)
            → atlassian-mcp        # this repo (not wired yet)
            → legacy-adapter-mcp   # this repo (not wired yet)
```

There is **no** Foundry agent definition, Toolbox registration, or APIM deploy config checked into this repository. Wiring = future work after Phase A prereqs clear.

---

## Vendor roles (clones next door)

| Directory under `SOVEREIGN_VENDOR_ROOT` | Used for |
|------------------------------------------|----------|
| `agent-governance-toolkit` | Policy kernel examples / ACS |
| `apim-foundry-governance` | APIM terraform + JWT policies |
| `azmcp-obo-template` | OBO Azure MCP on ACA |
| `mcp` | Official Azure MCP catalog |
| `EnterpriseMCP` | Entra Graph MCP (later) |

OpenClaw-style unauthenticated `/mcp` is an **anti-pattern** (see REFERENCES) — not the engine.

---

## Kill list

- Claiming a running vault / Foundry / AGT PASS without a `spine/` log path
- Treating these MCPs as “stitched” because smoke passed
- Master-key or unauthenticated MCP as the runtime
- Free SQL / whole-file dump tools
- Secrets in git
