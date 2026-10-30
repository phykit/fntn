"""Compare run.py's results.json with verify.py's verify.json (PREREG section 10).

Cells must match one for one on their keys; the listed statistics must agree to 1e-9 absolute,
every z_D to 1e-6, and the verdict and every check's pass flag exactly. The two scripts were
written separately from the pre-registration, so agreement here is evidence that the document,
not either implementation, decided the figures.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

STATS = ("mean_y", "sd_y", "mean_y1", "mean_y2", "mean_g", "sd_g", "assign_1", "assign_2",
         "assign_both", "mdd_median", "mdd_p05", "frac_written", "mean_y_written", "sd_y_written",
         "worst_g")


def key(c: dict) -> tuple:
    return (c["arm"], round(float(c["m"]), 6), c["variant"],
            round(float(c.get("rho", -9)), 6), round(float(c.get("rho_d", -9)), 6),
            round(float(c.get("rho_j", -9)), 6))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []
    rc = {key(c): c for c in r["cells"]}
    vc = {key(c): c for c in v["cells"]}
    if set(rc) != set(vc):
        print("DISAGREE cell sets differ:", sorted(set(rc) ^ set(vc)))
        bad.append("cells")
    n_ok = 0
    for k in sorted(set(rc) & set(vc)):
        for s in STATS:
            x, y = rc[k].get(s), vc[k].get(s)
            if x is None and y is None:
                continue
            ok = x is not None and y is not None and abs(float(x) - float(y)) <= 1e-9
            if ok:
                n_ok += 1
            else:
                print(f"DISAGREE {k} {s}: run={x} verify={y}")
                bad.append(f"{k}:{s}")
    print(f"agree    {n_ok} cell statistics within 1e-9")
    rp = {(p["arm"], round(float(p["m"]), 6), p["variant"]): p for p in r["paired"]}
    vp = {(p["arm"], round(float(p["m"]), 6), p["variant"]): p for p in v["paired"]}
    for k in sorted(set(rp) | set(vp)):
        for z in ("z_D", "z2"):
            x = rp.get(k, {}).get(z)
            y = vp.get(k, {}).get(z)
            if x is None and y is None:
                continue
            ok = x is not None and y is not None and abs(float(x) - float(y)) <= 1e-6
            print(("agree    " if ok else "DISAGREE ") + f"{z} {k}: run={x} verify={y}")
            if not ok:
                bad.append(f"{z}:{k}")
    for k in ("check1_analytic", "check2_theorem", "check3_armB", "check4_variance", "check5_jump"):
        x = r["checks"].get(k, {}).get("pass")
        y = v["checks"].get(k, {}).get("pass")
        ok = x is not None and x == y
        print(("agree    " if ok else "DISAGREE ") + f"{k}: run={x} verify={y}")
        if not ok:
            bad.append(k)
    ok = r.get("verdict") == v.get("verdict")
    print(("agree    " if ok else "DISAGREE ") + f"verdict: run={r.get('verdict')} verify={v.get('verdict')}")
    if not ok:
        bad.append("verdict")
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
