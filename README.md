# Sovereign Wrapper

**Foundry runs agents. AGT ACS denies unsafe tool calls. APIM owns model egress. Owned MCPs under `packages/` are the tools.**

Repo: https://github.com/fjkiani/Sovereign-Wrapper-

This is the control-plane scaffold — not a vibes README. Agents: read [`AGENTS.md`](./AGENTS.md) first (chokehold). Upstream pins: [`REFERENCES.md`](./REFERENCES.md).

---

## Architecture

```text
User (Entra)
  → Foundry Agent Service              ← ENGINE
       × AGT ACS (allow / deny / escalate)  ← KERNEL
       → APIM AI Gateway               ← EGRESS (models)
       → Toolbox / MCP
            → Azure MCP (OBO / UseOnBehalfOf)
            → packages/repo-navigator
            → packages/atlassian-mcp
            → packages/legacy-adapter-mcp
```

| Layer | What | Anchor |
|-------|------|--------|
| Engine | Microsoft Foundry Agent Service | Azure product |
| Kernel | AGT ACS `foundry_agents.py` | vendor SHA `0533cea` |
| Egress | APIM Foundry governance | vendor SHA `2d5478b` |
| OBO MCP | `azmcp-obo-template` | vendor SHA `fd07d5d` (`UseOnBehalfOf`) |
| Moat | RepoNavigator AST MCP | `packages/repo-navigator/` |
| Docs MCP | Atlassian read-only | `packages/atlassian-mcp/` |
| Legacy | Typed `query_client_ledger` | `packages/legacy-adapter-mcp/` |
| Ops | Phase A runbooks + prereq gate | `spine/` |

Vendor megarepos are **not** in this git tree. Clone pins to `SOVEREIGN_VENDOR_ROOT` (see REFERENCES).

---

## Repo skeleton

```text
Sovereign-Wrapper-/
├── AGENTS.md              # agent entry + chokehold (mandatory)
├── REFERENCES.md          # upstream SHAs + verify commands
├── README.md              # this file
├── spine/
│   ├── check-prereqs.sh
│   ├── run-agt-deny-smoke.sh
│   ├── RUNBOOK-foundry-agt.txt
│   ├── RUNBOOK-apim.txt
│   ├── RUNBOOK-obo-azd.txt
│   └── phase-a-status.json    # OPEN until live Azure smoke artifacts exist
└── packages/
    ├── repo-navigator/        # map → find → read (max 8192 bytes)
    ├── atlassian-mcp/         # search / get_page / get_issue only
    └── legacy-adapter-mcp/    # query_client_ledger (no free SQL)
```

---

## Status (honest)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| A | Foundry + AGT deny + APIM + OBO `azd up` | **OPEN** — needs `az` / `azd` / `opa` / AOAI on Alpha machine (`spine/phase-a-status.json`) |
| B | RepoNavigator MCP | **Code shipped** — run `packages/repo-navigator` smoke |
| C | Atlassian MCP (read-only) | **Code shipped** — dry-run smoke |
| D | Legacy adapter MCP | **Code shipped** — fake ledger smoke |

No PASS language without a this-turn artifact path. See chokehold in AGENTS.md.

---

## Agent entry (default first task)

```bash
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py
```

Tools (only): `get_architecture_map` → `find_symbol` → `read_symbol`. No whole-file dumps.

Other owned smokes:

```bash
cd packages/atlassian-mcp && pip install -r requirements.txt && ATLASSIAN_DRY_RUN=1 python smoke_test.py
cd packages/legacy-adapter-mcp && pip install -r requirements.txt && python smoke_test.py
```

---

## Phase A (Azure spine)

```bash
export SOVEREIGN_VENDOR_ROOT=/path/to/vendor-clones   # SHAs in REFERENCES.md
cd spine
./check-prereqs.sh            # must exit 0
./run-agt-deny-smoke.sh       # AGT deny proof — save log under spine/
# then follow RUNBOOK-obo-azd.txt and RUNBOOK-apim.txt
```

Critical vendor paths after clone:

- `.../foundry_agents.py` + `foundry_governance.acs.yaml` + `policy/foundry_tool_guard.rego`
- `azmcp-obo-template/infra/modules/aca-infrastructure.bicep` (`UseOnBehalfOf`)
- `apim-foundry-governance/infra/main.tf` + `policies/foundry-pipeline.xml.tftpl` (`validate-jwt`)

---

## Kill list

- Unauthenticated MCP as the engine (OpenClaw `/mcp` anti-pattern — REFERENCES)
- Whole-file dumps / free SQL / shell MCP tools
- PASS / online / compliant claims without artifact paths
- PAT-hijack / bypass-procurement as architecture
- Committing secrets; inventing DRAFT/RECAL receipt novels
- Marking Phase A green while `spine/phase-a-status.json` says OPEN
