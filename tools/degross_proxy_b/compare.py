"""Compare Version B: build.py's baskets with verify.py's, and run.py's results.json with
verify.py's verify.json (PREREG section 6).

Baskets must agree row for row.

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
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    r = json.load(open(os.path.join(a.out, "results.json")))
    v = json.load(open(os.path.join(a.out, "verify.json")))
    bad = []
    import csv

    def rows(p):
        with open(p, newline="") as fh:
            return sorted(tuple(r[k] for k in ("period", "effective", "leg", "rank", "cusip", "symbol"))
                          for r in csv.DictReader(fh))

    rb, vb = rows(os.path.join(a.data, "baskets.csv")), rows(os.path.join(a.out, "verify_baskets.csv"))
    only_r, only_v = sorted(set(rb) - set(vb)), sorted(set(vb) - set(rb))
    print(f"baskets: build rows {len(rb)}, verify rows {len(vb)}, only in build {len(only_r)}, only in verify {len(only_v)}")
    for x in only_r[:10]:
        print("  only build :", x[:4])
    for x in only_v[:10]:
        print("  only verify:", x[:4])
    if only_r or only_v:
        bad.append("baskets")

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
        for sec in ("secondary_21d_5pct", "secondary_no_sign_filter"):
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
