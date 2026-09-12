# Sovereign Wrapper

**A CISO-proof vault for AI** — an iron cage around the model.

Not a chatbot. Not “another MCP demo.” A control plane that treats the LLM as smart, useful, and **hostile**: it only sees what infrastructure allows, as the **user**, through tiny typed tools.

- Repo: https://github.com/fjkiani/Sovereign-Wrapper-
- Agent rules: [`AGENTS.md`](./AGENTS.md)
- Upstream clone pins (SHAs live there, not here): [`REFERENCES.md`](./REFERENCES.md)
- Live Azure spine status: [`spine/phase-a-status.json`](./spine/phase-a-status.json) — **OPEN** until real smoke artifacts exist

---

## What problem this solves

In a bank or any regulated shop, someone asks an internal agent:

> “Summarize this repo” · “Pull the client ledger” · “Find the Confluence page on SOX”

Without a vault, the model typically:

1. Gets a **master key** or broad service account
2. Reads **whatever files** the tools can reach (including `.env`, keys, credentials)
3. Dumps **whole files** into the prompt (cost + confusion + secret bleed)
4. Optionally runs **free SQL / shell** “to be helpful”

CISOs are right to block that. Employees then use shadow ChatGPT on the side — worse.

**Sovereign Wrapper is the answer that makes “yes, you can deploy agents” true:** the model is physically, cryptographically, and structurally kept from those moves. Bad intent or prompt injection cannot “talk past” the bouncer.

---

## What this means in one picture

```text
  Susan asks a question
           │
           ▼
  Foundry Agent Service     ← the only thing that “runs” the agent loop
           │
           × AGT Deny         ← bouncer: if the rulebook says no, the tool never runs
           │
           ▼
  APIM + user badge (OBO)   ← tollbooth: agent must act as Susan, not as God
           │
           ▼
  Tiny allowlisted tools    ← map-a-repo / read-a-page / query-one-ledger
           │
           ▼
  Answer (no side-channel dump of secrets or mainframes)
```

If you only clone tool repos and never stand up Foundry + the bouncer, you have **parts on a shelf**. That is a silo pile, not a vault.

---

## The four things we are actually building

### 1. The bouncer — AGT Deny

**Meaning:** Before the agent runs *any* tool (`run_sql`, `read_file`, `drop_table`, …), a policy engine checks a rulebook. Fail-closed: no “soft warn,” no “try anyway.” Deny means the tool process never starts.

**Why CISOs care:** Prompt injection and “helpful” models cannot invent a path around a hard drop at the control plane.

**Where the code lives:** Microsoft Agent Governance Toolkit (ACS / Rego / `AgentControl`). Smoke entry in this repo: `spine/run-agt-deny-smoke.sh` → vendor `foundry_agents.py`.

### 2. The badge check — OBO + APIM

**Meaning:** Amateur setups give the agent a shared “integration user” that can see everything. We do the opposite: when Susan asks, the tools must prove they are acting **on Susan’s behalf** (On-Behalf-Of). Azure API Management sits in front like a tollbooth — JWT, quotas, private backends.

**Why CISOs care:** If Susan cannot open HR files, neither can the agent “helping” Susan. Blast radius = user entitlements, not a god key.

**Where the code lives:** Azure MCP OBO sample (ACA + `UseOnBehalfOf`) and APIM Foundry governance terraform/policies. Runbooks under `spine/`.

### 3. The map maker — RepoNavigator

**Meaning:** Repos are not books with a table of contents. Naive agents download the whole tree, burn tokens, get lost, and trip over secrets.

We build a **map** (Tree-sitter architecture skeleton), then allow only **surgical reads** of one symbol window (default cap **8192 bytes**). Paths that look like secrets (`.env`, credentials, keys) are blocked in code.

**Why CISOs care:** “Summarize the codebase” stops meaning “exfiltrate everything the clone can see.”

**Where the code lives:** `packages/repo-navigator/` in **this** repo (owned). Flow: `get_architecture_map` → `find_symbol` → `read_symbol`.

### 4. The translator — Legacy adapter

**Meaning:** Banks still run AS/400, SOAP, dusty Dynamics, read-only SQL behind weird CLIs. Letting an LLM speak those dialects is how you get `DROP TABLE` energy.

We expose **one idiot-proof tool**, e.g. `query_client_ledger(client_id, as_of)`. The adapter talks to the beast inside the bank network. The model never sees SOAP, SQL, or the mainframe.

**Why CISOs care:** Modernize the *interface* without modernizing (or exposing) the core.

**Where the code lives:** `packages/legacy-adapter-mcp/` in **this** repo. Deploy behind private / APIM self-hosted gateway — not laptop → core.

### Docs plane (same cage) — Atlassian

**Meaning:** Confluence/Jira as **read-only** tools (`search`, `get_page`, `get_issue`), with identity the CISO can see. Writes denied at the bouncer even if an upstream MCP grows them.

**Not our approach:** “PAT hijack / bypass procurement / shadow IT on a laptop.” That is the opposite of a vault.

**Where the code lives:** `packages/atlassian-mcp/`.

---

## What each repo is for (no pin soup)

Upstream trees are cloned beside this project (`SOVEREIGN_VENDOR_ROOT`, usually `_sovereign-audit`). Exact commit pins stay in [`REFERENCES.md`](./REFERENCES.md) so this README stays about **meaning**.

| Piece | In human terms | Role |
|-------|----------------|------|
| **Foundry Agent Service** | Microsoft’s managed agent runtime | **Run engine** — loop, threads, tool calls |
| **agent-governance-toolkit** | Microsoft’s agent policy toolkit | **Bouncer / policy kernel** |
| **apim-foundry-governance** | APIM patterns for Foundry | **Tollbooth** for models + MCP egress |
| **azmcp-obo-template** | Sample Azure MCP that uses the user’s token | **Badge-bound Azure tools** |
| **microsoft/mcp** | Official Azure / Fabric MCP servers | Tool catalog — pick, don’t worship |
| **EnterpriseMCP** | Entra / Graph oriented MCP | Later: directory / CA posture reads |
| **This repo `packages/*`** | Our map maker, docs reader, ledger translator | **Owned vault tools** |
| **This repo `spine/`** | Scripts + runbooks to prove Phase A | **How we start the engine** |
| OpenClaw-style unauth `/mcp` | SaaS with open tool mounts | **Anti-pattern** — never the engine |

**Remember:** cloning those Microsoft repos does not “give you an engine.” Foundry is a **service**. AGT is the kernel you **wire on**. The rest is fuel lines.

---

## How an agent turn actually runs

Example: Susan asks *“Where is rate limiting implemented, and what’s client CLI-1001’s ledger as of today?”*

1. **Foundry** starts/continues her thread (engine).
2. Model proposes tools. **AGT** inspects each proposal:
   - `read_file(.env)` → **DENY** (never runs)
   - `get_architecture_map` → **ALLOW**
   - `read_symbol(...)` within byte cap → **ALLOW**
   - `query_client_ledger("CLI-1001", …)` → **ALLOW** if policy says so; escalate if high-risk
3. Allowed calls leave through **APIM**, carrying **Susan’s** identity where OBO applies.
4. **RepoNavigator** returns map + a tiny symbol window — not the whole repo.
5. **Legacy adapter** returns a fixed ledger schema — no SQL string from the model.
6. Model answers Susan. Secrets and mainframes never entered the prompt as raw surfaces.

That stitching — engine × bouncer × badge × tiny tools — **is** the product.

| State | What it means |
|-------|----------------|
| **Silo** | Package smokes pass on a laptop; Foundry never called them |
| **Kernel proven** | Deny smoke log shows ALLOW + DENY + OK |
| **Stitched** | One Foundry agent, ACS on, APIM on, Toolbox points at our MCPs |

Today: owned packages are **silo-proven**. Phase A (engine + kernel live) is **OPEN**.

---

## Build order (what “done” looks like)

| Step | What you actually get |
|------|------------------------|
| **E0** | Machine can talk to Azure (`az` / `azd` / `terraform` / `opa` + AOAI env) |
| **E1** | Proof the bouncer drops bad tool calls (`spine` deny smoke log) |
| **E2** | A real Foundry agent exists and is guarded |
| **E3** | Azure tools run as the user (OBO MCP up) |
| **E4** | Foundry Toolbox calls **our** RepoNavigator / Atlassian / legacy MCPs |
| **E5** | APIM sits in front of model + tool egress |

Details: [`spine/README.md`](./spine/README.md) and the `RUNBOOK-*.txt` files there.

---

## Status (honest)

| Surface | Reality |
|---------|---------|
| Foundry + AGT + OBO + APIM live | **OPEN** — needs Alpha Azure login/CLIs; see `phase-a-status.json` |
| RepoNavigator | Local smoke + demo architecture map — not on Foundry yet |
| Atlassian MCP | Dry-run smoke — governed pattern, not hijack |
| Legacy adapter | Fake in-memory ledger for smoke — real backend later, private only |

Do not mark Phase A green while that JSON says OPEN.

---

## Layout

```text
AGENTS.md / REFERENCES.md / README.md
spine/                       # start the engine (Phase A)
packages/repo-navigator/     # map maker
packages/atlassian-mcp/      # read-only docs/tickets
packages/legacy-adapter-mcp/ # ledger translator
```

### Silo smokes (prove tools; not the vault)

```bash
cd packages/repo-navigator && python3 -m venv .venv && source .venv/bin/activate
pip install -e . && export REPO_NAVIGATOR_CONFIG=$PWD/config.yaml && python scripts/smoke.py

cd packages/atlassian-mcp && pip install -r requirements.txt
ATLASSIAN_DRY_RUN=1 python smoke_test.py

cd packages/legacy-adapter-mcp && pip install -r requirements.txt && python smoke_test.py
```

### Engine path (when Azure is ready)

```bash
cd spine && ./check-prereqs.sh && ./run-agt-deny-smoke.sh
```

---

## Kill list

- Calling any MCP, APIM, or OpenClaw the **run engine**
- Master-key agents / unauthenticated tool mounts
- Whole-file dumps, free SQL, shell, secret-path reads
- “PAT hijack / bypass procurement” as the Atlassian plan
- PASS / “stitched” / Phase A green without artifact paths
- Secrets in git; receipt-novel markdown (`DRAFT-*`, `RECALIBRATION-*`)
