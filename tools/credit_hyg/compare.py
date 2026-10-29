"""Compare results.json (primary implementation) with verify.json (independent second implementation).

Usage: python compare.py --a results.json --b verify.json

Prints AGREE or DISAGREE per item and an OVERALL line. Always exits 0: the
comparison is a report, and a non-zero exit would invite a caller to treat a
disagreement as a crash to be retried rather than a finding to be read.
"""

import argparse
import json
import math
import sys

EXACT = ["n", "verdict"]
REL = ["b", "b_incremental", "b_half1", "b_half2", "b_h5", "b_h10", "b_info", "corr_contemporaneous"]
ABS = {"p_shift": 0.002, "t_incremental": 1e-6}
RULE_FLOAT = ["ann_return", "max_drawdown", "invested_share"]
RULE_COUNT = ["exits", "false_alarms", "missed_declines"]
RULE_TOL = 1e-6
REL_TOL = 1e-9


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    args = ap.parse_args()
    with open(args.a) as fh:
        A = json.load(fh)
    with open(args.b) as fh:
        B = json.load(fh)

    rows = []

    def rec(name, ok, va, vb, rule):
        rows.append(ok)
        print(f"{'AGREE' if ok else 'DISAGREE':9s} {name:32s} a={va!r} b={vb!r} [{rule}]")

    for k in EXACT:
        va, vb = A.get(k), B.get(k)
        rec(k, va is not None and va == vb, va, vb, "exact")

    for k in REL:
        va, vb = num(A.get(k)), num(B.get(k))
        ok = va is not None and vb is not None and (
            va == vb or abs(va - vb) <= REL_TOL * max(abs(va), abs(vb)))
        rec(k, ok, A.get(k), B.get(k), f"rel {REL_TOL:g}")

    for k, tol in ABS.items():
        va, vb = num(A.get(k)), num(B.get(k))
        ok = va is not None and vb is not None and abs(va - vb) <= tol
        rec(k, ok, A.get(k), B.get(k), f"abs {tol:g}")

    for blk in ("rule", "mom_rule"):
        da, db = A.get(blk) or {}, B.get(blk) or {}
        for k in RULE_FLOAT:
            va, vb = num(da.get(k)), num(db.get(k))
            ok = va is not None and vb is not None and abs(va - vb) <= RULE_TOL
            rec(f"{blk}.{k}", ok, da.get(k), db.get(k), f"abs {RULE_TOL:g}")
        for k in RULE_COUNT:
            va, vb = da.get(k), db.get(k)
            ok = va is not None and vb is not None and int(va) == int(vb) and float(va) == float(vb)
            rec(f"{blk}.{k}", ok, va, vb, "exact")

    n_dis = rows.count(False)
    if n_dis == 0:
        print(f"OVERALL AGREE ({len(rows)} items)")
    else:
        print(f"OVERALL DISAGREE ({n_dis} of {len(rows)} items disagree)")
    sys.exit(0)


if __name__ == "__main__":
    main()
