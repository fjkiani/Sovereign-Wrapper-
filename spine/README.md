# Spine — pillars 1 + 2 ops

**AGT Deny (bouncer)** and **OBO + APIM (badge check)** runbooks live here.

| File | Purpose |
|------|---------|
| `check-prereqs.sh` | Fail closed if Azure/`opa`/vendor clones missing |
| `run-agt-deny-smoke.sh` | Run vendor `foundry_agents.py` deny-proof |
| `RUNBOOK-foundry-agt.txt` | Pillar 1 steps |
| `RUNBOOK-obo-azd.txt` | Pillar 2 OBO `azd up` + Toolbox wiring |
| `RUNBOOK-apim.txt` | Pillar 2 APIM terraform path |
| `phase-a-status.json` | Truth file — **OPEN** until live smoke artifacts exist |

```bash
export SOVEREIGN_VENDOR_ROOT=/path/to/pinned-clones
./check-prereqs.sh
./run-agt-deny-smoke.sh
```

Do not edit `phase-a-status.json` to PASS without an artifact path.
