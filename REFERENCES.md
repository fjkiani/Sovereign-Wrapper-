# Upstream baselines (pinned)

Clone these beside or under a vendor root. Do **not** commit full trees here unless Alpha orders it.

```bash
export SOVEREIGN_VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$HOME/Desktop/development/_sovereign-audit}"
# or: mkdir -p vendor && clone into vendor/
```

| Component | Repo | Pinned SHA | Role |
|-----------|------|------------|------|
| AGT ACS | https://github.com/microsoft/agent-governance-toolkit | `0533cea` | Policy kernel; `foundry_agents.py` deny-proof |
| APIM AI Gateway | https://github.com/microsoft/apim-foundry-governance | `2d5478b` | Model egress; `validate-jwt` policies |
| OBO Azure MCP | https://github.com/Azure-Samples/azmcp-obo-template | `fd07d5d` | Entra OBO + ACA; `UseOnBehalfOf` |
| Azure MCP catalog | https://github.com/microsoft/mcp | `797cee3` | Official Azure/Fabric MCP servers |
| Enterprise Graph MCP | https://github.com/microsoft/EnterpriseMCP | `5c165f1` | Entra Graph read MCP (hosted) |

### Critical vendor paths (after clone @ SHA)

- AGT example: `agent-governance-toolkit/policy-engine/sdk/python/examples/real_packages/foundry_agents.py`
- ACS manifest: `.../foundry_governance.acs.yaml`
- Rego: `.../policy/foundry_tool_guard.rego`
- OBO bicep: `azmcp-obo-template/infra/modules/aca-infrastructure.bicep` (`UseOnBehalfOf`)
- APIM TF: `apim-foundry-governance/infra/main.tf`
- JWT policy: `apim-foundry-governance/policies/foundry-pipeline.xml.tftpl`

### Anti-pattern (not an upstream to copy)

OpenClaw SaaS mounts `/mcp` without Clerk auth gate (`openclaw-saas` @ `9f07708`, `artifacts/api-server/src/app.ts`). Domain cargo only — never the control-plane engine.

### Verify pin

```bash
git -C "$SOVEREIGN_VENDOR_ROOT/agent-governance-toolkit" rev-parse --short HEAD   # expect 0533cea
git -C "$SOVEREIGN_VENDOR_ROOT/apim-foundry-governance" rev-parse --short HEAD     # expect 2d5478b
git -C "$SOVEREIGN_VENDOR_ROOT/azmcp-obo-template" rev-parse --short HEAD           # expect fd07d5d
```
