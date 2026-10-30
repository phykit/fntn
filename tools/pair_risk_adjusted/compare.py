"""Compare run.py's results.json with verify.py's verify.json (PREREG section 7.2)."""
from __future__ import annotations

import argparse
import json
import os
import sys

EXACT = ("n", "first_month", "last_month", "verdict", "discarded")
CLOSE = ("D", "lower")
PAIR_KEYS = ("ir", "delta", "sharpe_held", "sharpe_covered", "sharpe_diff")
NOWEIGHT = ("boot_mean", "boot_p95", "spearman_c_ir", "spearman_c_divratio", "decomp_mean_diff",
            "decomp_sd_diff", "recon_low_pct", "recon_high_pct")


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
        cmp(k, r.get(k), v.get(k), None)
    for k in CLOSE:
        cmp(k, r.get(k), v.get(k), 1e-9)
    for p in r.get("pairs", {}):
        for k in PAIR_KEYS:
            cmp(f"{p}.{k}", r["pairs"][p].get(k), v.get("pairs", {}).get(p, {}).get(k), 1e-9)
    for k in NOWEIGHT:
        cmp(k, r.get(k), v.get(k), 1e-9, required=False)
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
