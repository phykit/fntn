"""Compare run.py's results.json with verify.py's verify.json (PREREG section 6.2)."""
from __future__ import annotations

import argparse
import json
import os
import sys

EXACT = ("n", "first_month", "last_month", "verdict", "discarded")
CLOSE = ("Delta", "lower", "sh_bxm", "sh_spy")
NOWEIGHT = ("boot_mean", "boot_p95", "delta_pre2011", "delta_from2011", "diff_mean_pct", "diff_t", "diff_mean_pct_from2011", "recon_mean_pct")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []

    def cmp(label, x, y, tol, required=True):
        ok = (x == y) if tol is None else (x is not None and y is not None and abs(x - y) <= tol)
        tag = "agree    " if ok else ("DISAGREE " if required else "differ   ")
        print(tag + f"{label}: run={x} verify={y}" + ("" if required else " (no weight)"))
        if not ok and required:
            bad.append(label)

    for k in EXACT:
        x, y = r.get(k), v.get(k)
        if k in ("first_month", "last_month") and x and y:
            x, y = x[:7], y[:7]  # one implementation writes YYYY-MM, the other the full t0 date
        cmp(k, x, y, None)
    for k in CLOSE:
        cmp(k, r.get(k), v.get(k), 1e-9)
    for k in NOWEIGHT:
        cmp(k, r.get(k), v.get(k), 1e-9, required=False)
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
