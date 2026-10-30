"""Compare run.py's results.json with verify.py's verify.json (PREREG section 6.2)."""
from __future__ import annotations

import argparse
import json
import os
import sys

EXACT = ("n", "first_month", "last_month", "verdict")
CLOSE = ("mean_y", "t", "t_crit", "mean_y_pre", "mean_y_post")
NOWEIGHT = ("t_pre", "t_post", "verdict_normal")


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
        cmp(k, r.get(k), v.get(k), 1e-12 if k.startswith("mean_y") else 1e-9)  # PREREG section 6.2
    for k in NOWEIGHT:
        tol = None if k == "verdict_normal" else 1e-9
        cmp(k, r.get(k), v.get(k), tol, required=False)
    if bad:
        print("COMPARE FAILED:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
