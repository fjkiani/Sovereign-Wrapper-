# Upstream baselines (pinned)

These are the **vendor pillars** behind the CISO vault. Clone to `SOVEREIGN_VENDOR_ROOT`. Do not commit full trees unless Alpha orders it.

```bash
export SOVEREIGN_VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$HOME/Desktop/development/_sovereign-audit}"
```

| Pillar | Component | Repo | SHA | Role in the vault |
|--------|-----------|------|-----|-------------------|
| 1 AGT Deny | Agent Governance Toolkit | https://github.com/microsoft/agent-governance-toolkit | `0533cea` | Bouncer — ACS/Rego fail-closed |
| 2 APIM | AI Gateway | https://github.com/microsoft/apim-foundry-governance | `2d5478b` | Tollbooth — JWT, TPM, private backends |
| 2 OBO | Azure MCP OBO template | https://github.com/Azure-Samples/azmcp-obo-template | `fd07d5d` | User badge — `UseOnBehalfOf` on ACA |
| Catalog | Azure / Fabric MCP | https://github.com/microsoft/mcp | `797cee3` | Official tool servers (not the engine) |
| Entra Graph | Enterprise MCP | https://github.com/microsoft/EnterpriseMCP | `5c165f1` | Read Graph / CA posture later |

### Paths after clone @ SHA

**Pillar 1**

- `agent-governance-toolkit/policy-engine/sdk/python/examples/real_packages/foundry_agents.py`
- `.../foundry_governance.acs.yaml`
- `.../policy/foundry_tool_guard.rego`

**Pillar 2**

- `azmcp-obo-template/infra/modules/aca-infrastructure.bicep` — `UseOnBehalfOf`
- `apim-foundry-governance/infra/main.tf`
- `apim-foundry-governance/policies/foundry-pipeline.xml.tftpl` — `validate-jwt`

### Anti-pattern (never the vault engine)

OpenClaw mounts `/mcp` without auth gate (`openclaw-saas` @ `9f07708`). Master-key / open-MCP style. Domain cargo only.

### Verify pins

```bash
git -C "$SOVEREIGN_VENDOR_ROOT/agent-governance-toolkit" rev-parse --short HEAD   # 0533cea
git -C "$SOVEREIGN_VENDOR_ROOT/apim-foundry-governance" rev-parse --short HEAD     # 2d5478b
git -C "$SOVEREIGN_VENDOR_ROOT/azmcp-obo-template" rev-parse --short HEAD           # fd07d5d
```
