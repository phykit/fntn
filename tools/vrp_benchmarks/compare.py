"""Compare run.py's results.json with verify.py's verify.json (PREREG section 6.2): n, first and last
month, and per strategy the verdict, alpha and beta (1e-12), t and the critical value (1e-9)."""
from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []

    def cmp(label, x, y, tol, required=True):
        ok = (x == y) if tol is None else (x is not None and y is not None and abs(x - y) <= tol)
        print(("agree    " if ok else ("DISAGREE " if required else "differ   ")) + f"{label}: run={x} verify={y}"
              + ("" if required else " (no weight)"))
        if not ok and required:
            bad.append(label)

    cmp("n", r.get("n"), v.get("n"), None)
    for k in ("first_month", "last_month"):
        cmp(k, (r.get(k) or "")[:7], (v.get(k) or "")[:7], None)
    for s in ("PUT", "WPUT", "CNDR"):
        R, V = r["strategies"][s], v["strategies"][s]
        cmp(f"{s}.verdict", R["verdict"], V["verdict"], None)
        for k, tol in (("alpha", 1e-12), ("beta", 1e-12), ("t", 1e-9), ("crit", 1e-9)):
            cmp(f"{s}.{k}", R[k], V[k], tol)
        for k in ("alpha_ann_p05", "alpha_ann_p95", "sharpe_ex", "maxdd"):
            cmp(f"{s}.{k}", R.get(k), V.get(k), 1e-9, required=False)
    for k in ("WPUT_minus_PUT", "CNDR_minus_PUT"):
        cmp(f"sharpe_diff.{k}", r["sharpe_diff"][k]["diff"], v["sharpe_diff"][k]["diff"], 1e-9, required=False)
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
