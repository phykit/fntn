"""Compare run.py's results.json with verify.py's verify.json (PREREG section 5.2): months used,
primary mean and t, verdict, and the no-weight VRP, SVRP, ex-post and covered-call figures."""
from __future__ import annotations

import argparse
import json
import os
import sys

EXACT = ("n_months", "first_month", "last_month", "verdict")
MEANS = ("ivrp_mean", "vrp_mean", "svrp_mean", "expost_ivrp_mean", "cc_mean_pct")
TS = ("ivrp_t", "vrp_t", "svrp_t", "expost_ivrp_t", "cc_t")
NOWEIGHT = ("share_ivrp_of_vrp", "implied_idio_mean", "pair_low_mean_pct", "pair_high_mean_pct",
            "pair_n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []
    for k in EXACT + MEANS + TS:
        x, y = r.get(k), v.get(k)
        tol = None if k in EXACT else (1e-9 if k in MEANS else 1e-6)
        ok = (x == y) if tol is None else (x is not None and y is not None and abs(x - y) <= tol)
        print(("agree    " if ok else "DISAGREE ") + f"{k}: run={x} verify={y}")
        if not ok:
            bad.append(k)
    for k in NOWEIGHT:
        x, y = r.get(k), v.get(k)
        ok = x is not None and y is not None and abs(float(x) - float(y)) <= 1e-9
        print(("agree    " if ok else "differ   ") + f"{k} (no weight, not required): run={x} verify={y}")
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
