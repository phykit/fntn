"""Compare run.py's results.json with verify.py's verify.json (PREREG section 8).

Required to agree: the gate status and matched references; and, on a gate PASS, the primary episode
count, E_T, E_O, Delta and verdict exactly (to 1e-9), and p within 0.01. Secondary tests are
compared and reported, without weight. Exits non-zero on any disagreement in a required field.
"""
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

    def same(name, x, y, tol=None):
        ok = (abs(x - y) <= tol) if tol is not None else (x == y)
        print(("agree    " if ok else "DISAGREE ") + f"{name}: run={x} verify={y}")
        return ok

    if not same("gate.status", r["gate"]["status"], v["gate"]["status"]):
        bad.append("gate.status")
    if not same("gate.matched", r["gate"]["matched"], v["gate"]["matched"]):
        bad.append("gate.matched")
    same("gate.base_rate", r["gate"]["base_rate"], v["gate"]["base_rate"], 1e-12)
    if r["gate"]["status"] == "PASS":
        rp, vp = r["primary"], v["primary"]
        for k in ("n_episodes", "verdict"):
            if not same(f"primary.{k}", rp[k], vp[k]):
                bad.append(k)
        for k in ("E_T", "E_O", "delta"):
            if not same(f"primary.{k}", rp[k], vp[k], 1e-9):
                bad.append(k)
        if not same("primary.p", rp["p"], vp["p"], 0.01):
            bad.append("p")
        for sec in ("secondary_21d_5pct", "secondary_no_sign_filter", "secondary_french_market"):
            rs, vs = r.get(sec), v.get(sec)
            if rs and vs:
                for k in ("n_episodes", "E_T", "E_O", "delta", "p", "verdict"):
                    if isinstance(rs[k], float):
                        same(f"{sec}.{k} (no weight)", rs[k], vs[k], 0.01 if k == "p" else 1e-9)
                    else:
                        same(f"{sec}.{k} (no weight)", rs[k], vs[k])
    if bad:
        print("COMPARE FAILED on required fields:", bad)
        return 1
    print("COMPARE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
