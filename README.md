# Sovereign Wrapper

Enterprise agent control plane scaffolding: **Foundry** (engine) + **AGT ACS** (kernel) + **APIM** (egress) + **owned MCP tools**.

Remote: https://github.com/fjkiani/Sovereign-Wrapper-

## Agent entry

**Start here:** [`AGENTS.md`](./AGENTS.md) — vision, chokehold, default smoke.  
**Pins:** [`REFERENCES.md`](./REFERENCES.md) — upstream SHAs.  
**Azure spine:** [`spine/`](./spine/) — prereq gate + runbooks (`phase-a-status.json` is OPEN until live Azure smoke).

## Skeleton

```text
Sovereign-Wrapper-/
├── AGENTS.md                 # chokehold + entry (agents read first)
├── REFERENCES.md             # pinned Microsoft/Azure sample SHAs
├── README.md                 # this file
├── spine/                    # Phase A ops (no fake PASS)
│   ├── check-prereqs.sh
│   ├── run-agt-deny-smoke.sh
│   ├── RUNBOOK-foundry-agt.txt
│   ├── RUNBOOK-apim.txt
│   ├── RUNBOOK-obo-azd.txt
│   └── phase-a-status.json   # OPEN until Azure artifacts exist
└── packages/
    ├── repo-navigator/       # Phase B — AST anchors MCP (owned moat)
    ├── atlassian-mcp/        # Phase C — read-only Confluence/Jira MCP
    └── legacy-adapter-mcp/   # Phase D — typed query_client_ledger MCP
```

Upstream megarepos are **not** vendored in git. Set `SOVEREIGN_VENDOR_ROOT` (default: sibling `_sovereign-audit`) after cloning pins from REFERENCES.

## Stack (locked)

| Layer | What |
|-------|------|
| Engine | Microsoft Foundry Agent Service |
| Kernel | AGT ACS @ `0533cea` (`foundry_agents.py`) |
| Egress | APIM Foundry governance @ `2d5478b` |
| OBO tools | `azmcp-obo-template` @ `fd07d5d` (`UseOnBehalfOf`) |
| Moat | `packages/repo-navigator` — map → find → read (8192 byte cap) |

## Quick smokes (owned packages)

```bash
# RepoNavigator
cd packages/repo-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml
python scripts/smoke.py

# Atlassian (dry-run)
cd packages/atlassian-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ATLASSIAN_DRY_RUN=1 python smoke_test.py

# Legacy adapter (fake ledger)
cd packages/legacy-adapter-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python smoke_test.py
```

## Phase A (Azure — Alpha machine)

```bash
export SOVEREIGN_VENDOR_ROOT=/path/to/_sovereign-audit   # clones @ pinned SHAs
cd spine
./check-prereqs.sh          # must exit 0
./run-agt-deny-smoke.sh     # deny proof — save log
# then RUNBOOK-obo-azd.txt / RUNBOOK-apim.txt
```

## Kill list

- Unauthenticated MCP as “the engine”
- Whole-file dumps / free SQL / shell tools
- PASS language without artifact paths
- PAT-hijack / bypass-procurement as architecture
