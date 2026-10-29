#!/usr/bin/env python3
"""Compare results.json (run.py) with verify.json (verify.py) item by item.

Usage:
    python compare.py --a results.json --b verify.json

Tolerances, from the comparison brief:
    exact   counts, month labels, verdicts: identical after light normalisation
            (whitespace stripped; a verdict given as a boolean is read as
            PASS / FAIL; a month label longer than YYYY-MM is cut to YYYY-MM)
    mean    means and performance statistics: |a - b| <= max(1e-12, 1e-9 * max(|a|, |b|))
    t       t-statistics: |a - b| <= 1e-6 (absolute)

Both null counts as agreement; one null, or a key missing on either side, is a
disagreement and is said to be so. Every item prints AGREE or DISAGREE, then
OVERALL. The exit status is always 0: the verdict is on the page, not in the
shell.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys

REL_TOL = 1e-9
ABS_TOL = 1e-12
T_TOL = 1e-6

# (dotted path, kind). halves[i] is addressed as halves.0 and halves.1.
ITEMS = [
    ("n_oos", "exact"),
    ("first_oos", "exact"),
    ("last_oos", "exact"),
    ("mean_D", "mean"),
    ("t_D", "t"),
    ("mean_S", "mean"),
    ("t_S", "t"),
    ("full.n", "exact"),
    ("full.mean_D", "mean"),
    ("full.t_D", "t"),
    ("full.mean_S", "mean"),
    ("full.t_S", "t"),
    ("halves.0.first", "exact"),
    ("halves.0.last", "exact"),
    ("halves.0.mean_D", "mean"),
    ("halves.0.t_D", "t"),
    ("halves.1.first", "exact"),
    ("halves.1.last", "exact"),
    ("halves.1.mean_D", "mean"),
    ("halves.1.t_D", "t"),
    ("strategy.ann_return", "mean"),
    ("strategy.ann_vol", "mean"),
    ("strategy.sharpe", "mean"),
    ("strategy.max_drawdown", "mean"),
    ("strategy.mean_turnover", "mean"),
    ("universe.ann_return", "mean"),
    ("universe.ann_vol", "mean"),
    ("universe.sharpe", "mean"),
    ("universe.max_drawdown", "mean"),
    ("counts.mean_P", "mean"),
    ("counts.mean_U", "mean"),
    ("counts.tickers", "exact"),
    ("counts.no_dividend_history", "exact"),
    ("counts.skipped_months", "exact"),
    ("criteria.primary", "exact"),
    ("verdict", "exact"),
]

_MISSING = object()


def get(d, path):
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return _MISSING
            cur = cur[part]
        elif isinstance(cur, list):
            if not part.isdigit() or int(part) >= len(cur):
                return _MISSING
            cur = cur[int(part)]
        else:
            return _MISSING
    return cur


def norm_exact(v):
    if isinstance(v, bool):
        return "PASS" if v else "FAIL"
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return v
    if isinstance(v, str):
        s = v.strip()
        m = re.match(r"^(\d{4}-\d{2})(?:-\d{2})?$", s)
        if m:
            return m.group(1)
        return s.upper() if s.upper() in ("PASS", "FAIL", "INSUFFICIENT") else s
    return v


def to_float(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


def judge(kind, a, b):
    """Returns (agree: bool, note: str)."""
    if a is _MISSING or b is _MISSING:
        return False, "missing on " + ("both" if a is _MISSING and b is _MISSING
                                        else "a" if a is _MISSING else "b")
    if a is None and b is None:
        return True, "both null"
    if a is None or b is None:
        return False, "null on one side"
    if kind == "exact":
        na, nb = norm_exact(a), norm_exact(b)
        return na == nb, "" if na == nb else "differ"
    fa, fb = to_float(a), to_float(b)
    if fa is None or fb is None:
        return False, "not numeric"
    diff = abs(fa - fb)
    if kind == "mean":
        tol = max(ABS_TOL, REL_TOL * max(abs(fa), abs(fb)))
    else:
        tol = T_TOL
    return diff <= tol, f"diff {diff:.3e} tol {tol:.1e}"


def show(v):
    if v is _MISSING:
        return "<missing>"
    if v is None:
        return "null"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(description="compare results.json with verify.json")
    ap.add_argument("--a", required=True, help="results.json")
    ap.add_argument("--b", required=True, help="verify.json")
    args = ap.parse_args(argv)
    with open(args.a) as fh:
        A = json.load(fh)
    with open(args.b) as fh:
        B = json.load(fh)

    width = max(len(p) for p, _ in ITEMS)
    n_dis = 0
    for path, kind in ITEMS:
        a, b = get(A, path), get(B, path)
        ok, note = judge(kind, a, b)
        tag = "AGREE   " if ok else "DISAGREE"
        if not ok:
            n_dis += 1
        print(f"{tag} {path:<{width}} {kind:<5} a={show(a)} b={show(b)}" + (f"  [{note}]" if note else ""))
    print(f"OVERALL: {'AGREE' if n_dis == 0 else 'DISAGREE'} ({len(ITEMS) - n_dis} of {len(ITEMS)} items agree)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
