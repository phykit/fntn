#!/usr/bin/env bash
# Fill the registration with the agreed values and fetch the one master that is
# complete by construction. Run from the repo root, after `template`.
#
# US only, deliberately. The SEC's ticker file IS the US population, so US
# coverage is 100% without an estimate. The other four markets need a listed
# total you have to source, and a market whose coverage is unknown is not
# readable: unknown is not a synonym for complete.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

REG=discovery_registration.json
[[ -f "$REG" ]] || { echo "run: python -m fntn.scanner template"; exit 1; }

mkdir -p master corpora/us
echo "fetching the SEC ticker file (the regulator's own list)..."
curl -fsS -A "fntn research ${SEC_CONTACT:-set SEC_CONTACT to your email}" \
  https://www.sec.gov/files/company_tickers.json -o master/us.json
echo "  $(python3 -c "import json;print(len(json.load(open('master/us.json'))))") issuers"

python3 - "$REG" <<'PY'
import json, sys
from datetime import datetime, timezone

path = sys.argv[1]
reg = json.load(open(path))

if reg.get("registered_at"):
    print(f"already stamped {reg['registered_at']}; refusing to re-stamp.")
    print("A timestamp whose whole purpose is that it cannot move must not move.")
    raise SystemExit(1)

# Agreed in conversation, 26 August 2026.
reg["control_arm_delta"]   = 50.0    # half a midpoint round trip in the $10-100m bucket
reg["control_arm_n_min"]   = 30      # §6.1's own minimum sample, not a second one
reg["control_arm_ratio"]   = 1.0     # matched arms: max power per unit of segment
reg["control_arm_seed"]    = 20260826
reg["theta"]               = 0.25    # non-binding while segment_sessions is 0
reg["delta_min_floor"]     = 25.0    # rounded up from the 22.5 bps cheapest break-even
reg["registered_by"]       = "operator"
reg["rationale"] = (
    "delta 50 bps: an agent beating a random draw by less than half a round "
    "trip is not paying for the search it consumes. n_min 30: §6.1 already "
    "refuses below 30 non-overlapping trades, so this reuses the paper's "
    "minimum rather than inventing a second. ratio 1.0: equal n maximises "
    "power for a fixed total, and an underpowered control arm is worse than "
    "none because it consumes segment and returns undetermined forever. "
    "delta_min_floor 25 bps: the cheapest break-even in §5.2.2 is 22.5 bps, so "
    "an effect below that could never be traded in any cell. theta 0.25 is a "
    "placeholder, non-binding until the archive exists."
)

# US only for now: the only market whose coverage is complete by construction.
reg["security_master_files"] = ["./master/us.json:US"]
reg["corpora"] = [c for c in reg["corpora"] if c["market"] == "US"]

reg["registered_at"] = datetime.now(timezone.utc).isoformat()
json.dump(reg, open(path, "w"), indent=2, sort_keys=True)
print(f"stamped {reg['registered_at']}")
PY

echo
python -m fntn.scanner check
echo
echo "Put pre-archive US material in corpora/us/ (EDGAR Form 4 filings and"
echo "guidance predating the archive's opening boundary), then:"
echo "    python -m fntn.scanner sweep"
