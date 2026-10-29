"""Compare the first implementation of study R (results_rebound.json) with the independent second
implementation (verify_rebound.json), item by item.

Usage:
    python compare_rebound.py --a results_rebound.json --b verify_rebound.json

Tolerances: n values, counts and verdicts exactly; means and trade figures within 1e-9; p values
within 0.003, since both implementations draw from the same seed but may order or round a pool
differently. Prints AGREE or DISAGREE per item and an OVERALL line. Exits 0 either way:
disagreement is reported, not acted on. A value null in both files agrees; null in one does not.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

TOL_MEAN = 1e-9
TOL_P = 0.003
TOL_TRADE = 1e-9

HEAD = ["n_eligible", "n_signal", "mean_signal", "mean_eligible", "p_upper", "verdict"]
SUB = ["n_signal", "mean_signal", "mean_eligible", "p_upper"]
TRADE = ["trades", "share_profitable", "mean_net", "median_net", "t_mean", "worst",
         "sum_net_per_year"]
EXACT = {"n_eligible", "n_signal", "verdict", "trades"}


def tol_for(key):
    if key in EXACT:
        return None
    if key == "p_upper":
        return TOL_P
    if key in ("mean_signal", "mean_eligible"):
        return TOL_MEAN
    return TOL_TRADE


def missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def same(a, b, tol):
    if missing(a) and missing(b):
        return True
    if missing(a) or missing(b):
        return False
    if tol is None:
        return a == b
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    args = ap.parse_args(argv)
    with open(args.a) as fh:
        A = json.load(fh)
    with open(args.b) as fh:
        B = json.load(fh)

    items = [((), k) for k in HEAD]
    items += [(("basket",), k) for k in HEAD]
    for blk in ("h5", "h10", "declustered"):
        items += [((blk,), k) for k in SUB]
    for blk in ("trade_gvip", "trade_basket"):
        items += [((blk,), k) for k in TRADE]

    ok_all = True
    for path, key in items:
        da, db = A, B
        for p in path:
            da = da.get(p, {}) if isinstance(da, dict) else {}
            db = db.get(p, {}) if isinstance(db, dict) else {}
        va = da.get(key) if isinstance(da, dict) else None
        vb = db.get(key) if isinstance(db, dict) else None
        ok = same(va, vb, tol_for(key))
        ok_all &= ok
        name = ".".join(path + (key,))
        print(f"{'AGREE' if ok else 'DISAGREE':8s} {name:32s} a={va!r} b={vb!r}")
    print(f"OVERALL {'AGREE' if ok_all else 'DISAGREE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
