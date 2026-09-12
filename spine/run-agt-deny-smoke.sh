#!/usr/bin/env bash
# Thin wrapper: AGT ACS deny-proof via foundry_agents.py
# Does NOT fake PASS. Exits non-zero if prereqs or the example fail.
set -euo pipefail

SPINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SPINE/.." && pwd)"
VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/_sovereign-audit}"
AGT_DIR="$VENDOR_ROOT/agent-governance-toolkit/policy-engine/sdk/python/examples/real_packages"
AGT_SCRIPT="$AGT_DIR/foundry_agents.py"

echo "=== AGT Foundry deny-smoke ==="
echo "script=$AGT_SCRIPT"
echo

# Required env (same as _common.require_azure)
REQUIRED=(
  AZURE_OPENAI_ENDPOINT
  AZURE_OPENAI_API_KEY
  AZURE_OPENAI_DEPLOYMENT
  AZURE_OPENAI_API_VERSION
)

echo "Required env vars:"
for v in "${REQUIRED[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "  UNSET  $v"
  else
    _val="${!v}"
    echo "  SET    $v (len=${#_val})"
  fi
done
echo
echo "Also required on PATH: opa (or ACS_OPA_PATH), python3"
echo "pip packages: agent-control-specification azure-ai-agents pyyaml"
echo "Evidence expected: ALLOW on safe SELECT; DENY on DROP/DELETE before tool runs"
echo

if [[ ! -f "$AGT_SCRIPT" ]]; then
  echo "FAIL: foundry_agents.py not found at $AGT_SCRIPT" >&2
  exit 2
fi

if ! "$SPINE/check-prereqs.sh"; then
  echo "FAIL: prereqs OPEN — refuse to invent deny-proof. See RUNBOOK-foundry-agt.txt" >&2
  exit 1
fi

cd "$AGT_DIR"
exec python3 foundry_agents.py
