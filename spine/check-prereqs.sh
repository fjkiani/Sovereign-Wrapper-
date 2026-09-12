#!/usr/bin/env bash
# Phase A spine prereq gate. Exit 0 only when all required tools + Azure login
# + Foundry/AOAI env vars needed for AGT deny-proof are present.
# Non-zero = OPEN: Alpha must install/login before smoke can run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
# Vendor clones (AGT, APIM, OBO). Default: sibling _sovereign-audit next to this repo.
VENDOR_ROOT="${SOVEREIGN_VENDOR_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/_sovereign-audit}"
MISSING=()
WARN=()

need_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    MISSING+=("command:$name")
  fi
}

need_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    MISSING+=("env:$name")
  fi
}

echo "=== spine Phase A prereq check ==="
echo "cwd=$ROOT"
echo "vendor_root=$VENDOR_ROOT"
echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

# Core CLIs
need_cmd az
need_cmd azd
need_cmd terraform
need_cmd python3
need_cmd pip3

# OPA for AGT Rego bundle (or ACS_OPA_PATH)
if ! command -v opa >/dev/null 2>&1 && [[ -z "${ACS_OPA_PATH:-}" ]]; then
  MISSING+=("command:opa_or_env:ACS_OPA_PATH")
fi

# Azure login (only if az exists)
if command -v az >/dev/null 2>&1; then
  if ! az account show >/dev/null 2>&1; then
    MISSING+=("azure:not_logged_in (run: az login)")
  else
    echo "azure:logged_in name=$(az account show --query name -o tsv 2>/dev/null || echo '?')"
    echo "azure:sub=$(az account show --query id -o tsv 2>/dev/null || echo '?')"
  fi
else
  MISSING+=("azure:az_cli_absent_skip_login_check")
fi

# Foundry / AOAI env for foundry_agents.py deny-proof
need_env AZURE_OPENAI_ENDPOINT
need_env AZURE_OPENAI_API_KEY
need_env AZURE_OPENAI_DEPLOYMENT
need_env AZURE_OPENAI_API_VERSION

# Optional for azd / APIM (warn only — not required for AGT smoke alone)
for opt in AZURE_SUBSCRIPTION_ID AZURE_TENANT_ID AZURE_LOCATION AZURE_ENV_NAME; do
  if [[ -z "${!opt:-}" ]]; then
    WARN+=("optional_unset:$opt")
  fi
done

# Point at vendor AGT example (see REFERENCES.md pins)
AGT_EXAMPLE="$VENDOR_ROOT/agent-governance-toolkit/policy-engine/sdk/python/examples/real_packages/foundry_agents.py"
if [[ ! -f "$AGT_EXAMPLE" ]]; then
  MISSING+=("file:foundry_agents.py_missing (set SOVEREIGN_VENDOR_ROOT)")
else
  echo "agt_example=present"
fi

OBO_ROOT="$VENDOR_ROOT/azmcp-obo-template"
APIM_ROOT="$VENDOR_ROOT/apim-foundry-governance"
[[ -d "$OBO_ROOT" ]] || MISSING+=("dir:azmcp-obo-template_missing (set SOVEREIGN_VENDOR_ROOT)")
[[ -d "$APIM_ROOT" ]] || MISSING+=("dir:apim-foundry-governance_missing (set SOVEREIGN_VENDOR_ROOT)")

echo
if ((${#WARN[@]})); then
  echo "WARN (optional):"
  printf '  - %s\n' "${WARN[@]}"
  echo
fi

if ((${#MISSING[@]})); then
  echo "MISSING (blocking):"
  printf '  - %s\n' "${MISSING[@]}"
  echo
  echo "RESULT=OPEN"
  echo "CLEAR_STRATEGY=Alpha installs az/azd/terraform/opa, runs az login, exports AZURE_OPENAI_*"
  echo "See: $ROOT/RUNBOOK-foundry-agt.txt $ROOT/RUNBOOK-apim.txt $ROOT/RUNBOOK-obo-azd.txt"
  exit 1
fi

echo "RESULT=READY"
echo "Next: $ROOT/run-agt-deny-smoke.sh (AGT deny-proof)"
exit 0
