#!/usr/bin/env python3
"""Compare the first implementation's results.json with verify.py's verify.json.

Usage:
    python compare.py --a results.json --b verify.json

Items and tolerances:
  exact      n_months, first_month, last_month, verdict, criteria.a/b/c, p_boot
             (p_boot is exact; a mismatch within 0.002 is noted as such)
  1e-9 rel   returns, Sharpes, alphas, weights, drawdowns, turnover, cost, yearly
             (1e-12 absolute near zero)
  1e-6 abs   alpha_t

Prints AGREE or DISAGREE per item and OVERALL. Always exits 0: the comparison is a
report, not a gate, and the operator reads it.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

REL_TOL = 1e-9
ABS_TOL = 1e-12
T_TOL = 1e-6
P_NOTE = 0.002

EXACT_ITEMS = [
    "n_months",
    "first_month",
    "last_month",
    "verdict",
    "criteria.a",
    "criteria.b",
    "criteria.c",
]

FLOAT_ITEMS = [
    "alpha_monthly",
    "b",
    "sharpe_active",
    "sharpe_static_active",
    "sharpe_strategy",
    "sharpe_spy",
    "weight.min",
    "weight.median",
    "weight.max",
    "weight.share_capped",
    "weight.share_below_half",
    "turnover_annual",
    "cost_annual",
    "live_weight_last_complete_month",
    "live_weight_latest",
]
for _series in ("spy", "mtum", "fifty", "strategy"):
    for _stat in ("ann_return", "ann_vol", "sharpe", "max_drawdown"):
        FLOAT_ITEMS.append(f"stats.{_series}.{_stat}")

_MISSING = object()


def dig(obj, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def fmt(v) -> str:
    if v is _MISSING:
        return "<missing>"
    if isinstance(v, float):
        return repr(v)
    return json.dumps(v)


def close(a: float, b: float, rel: float = REL_TOL, abs_: float = ABS_TOL) -> bool:
    return abs(a - b) <= max(rel * max(abs(a), abs(b)), abs_)


def compare_exact(name: str, a, b):
    if a is _MISSING or b is _MISSING:
        return False, "missing on one side"
    return a == b, ""


def compare_float(name: str, a, b, tol_abs: float | None = None):
    if a is _MISSING or b is _MISSING:
        return False, "missing on one side"
    if a is None or b is None:
        both = a is None and b is None
        return both, ("" if both else "null on one side")
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False, "not numeric"
    if math.isnan(fa) or math.isnan(fb):
        both = math.isnan(fa) and math.isnan(fb)
        return both, ("" if both else "nan on one side")
    if tol_abs is not None:
        return abs(fa - fb) <= tol_abs, ""
    ok = close(fa, fb)
    note = ""
    if not ok and name.endswith("max_drawdown") and close(abs(fa), abs(fb)):
        note = "magnitudes agree; sign convention differs"
    return ok, note


def compare_p(a, b):
    if a is _MISSING or b is _MISSING:
        return False, "missing on one side"
    if a == b:
        return True, ""
    try:
        if abs(float(a) - float(b)) <= P_NOTE:
            return False, f"differs but within {P_NOTE}"
    except (TypeError, ValueError):
        pass
    return False, ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--a", required=True, help="first implementation's results.json")
    ap.add_argument("--b", required=True, help="verify.py's verify.json")
    args = ap.parse_args(argv)

    with open(args.a, encoding="utf-8") as fh:
        ra = json.load(fh)
    with open(args.b, encoding="utf-8") as fh:
        rb = json.load(fh)

    rows = []  # (ok, name, a, b, note)

    for name in EXACT_ITEMS:
        a, b = dig(ra, name), dig(rb, name)
        ok, note = compare_exact(name, a, b)
        rows.append((ok, name, a, b, note))

    a, b = dig(ra, "p_boot"), dig(rb, "p_boot")
    ok, note = compare_p(a, b)
    rows.append((ok, "p_boot", a, b, note))

    a, b = dig(ra, "alpha_t"), dig(rb, "alpha_t")
    ok, note = compare_float("alpha_t", a, b, tol_abs=T_TOL)
    rows.append((ok, "alpha_t", a, b, note))

    for name in FLOAT_ITEMS:
        a, b = dig(ra, name), dig(rb, name)
        ok, note = compare_float(name, a, b)
        rows.append((ok, name, a, b, note))

    # Year by year, keyed on the year.
    ya = {int(e["year"]): e for e in (dig(ra, "yearly") if dig(ra, "yearly") is not _MISSING else [])}
    yb = {int(e["year"]): e for e in (dig(rb, "yearly") if dig(rb, "yearly") is not _MISSING else [])}
    for year in sorted(set(ya) | set(yb)):
        for field in ("strategy", "spy"):
            a = ya[year].get(field, _MISSING) if year in ya else _MISSING
            b = yb[year].get(field, _MISSING) if year in yb else _MISSING
            ok, note = compare_float(f"yearly.{year}.{field}", a, b)
            rows.append((ok, f"yearly.{year}.{field}", a, b, note))

    width = max(len(r[1]) for r in rows)
    n_bad = 0
    for ok, name, a, b, note in rows:
        status = "AGREE" if ok else "DISAGREE"
        if not ok:
            n_bad += 1
        line = f"{status:8s} {name:{width}s}  a={fmt(a)}  b={fmt(b)}"
        if note:
            line += f"  ({note})"
        print(line)

    print()
    print(f"OVERALL {'AGREE' if n_bad == 0 else 'DISAGREE'}: {len(rows) - n_bad} of {len(rows)} items agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
