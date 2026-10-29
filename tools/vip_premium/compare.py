"""Compare run.py's results.json with verify.py's verify.json (PREREG section 5): months used, alpha,
t and verdict must agree (alpha and t to 1e-6). Other fields are reported without weight."""
from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []
    for k, tol in (("n_months", None), ("first_month", None), ("last_month", None), ("verdict", None),
                   ("alpha_annual", 1e-6), ("t", 1e-6)):
        x, y = r.get(k), v.get(k)
        ok = (x == y) if tol is None else (x is not None and y is not None and abs(x - y) <= tol)
        print(("agree    " if ok else "DISAGREE ") + f"{k}: run={x} verify={y}")
        if not ok:
            bad.append(k)
    for k in ("capm_alpha_annual", "qqq_alpha_annual", "share_months_beat_spy"):
        x, y = r.get(k), v.get(k)
        ok = x is not None and y is not None and abs(x - y) <= 1e-6
        print(("agree    " if ok else "DISAGREE ") + f"{k} (no weight): run={x} verify={y}")
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
