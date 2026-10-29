#!/usr/bin/env python3
"""Compare the first implementation's results.json with verify.json.

Usage: python compare.py --a results.json --b verify.json

PREREG.md disclosure 3 says a second implementation is written from the file
alone and compared. This is the comparison. Per item it prints AGREE or
DISAGREE (or MISSING where one side has no value), then OVERALL, and exits 0
whatever the outcome: a disagreement is a finding to be read, not an error to
be retried.

Tolerances, from the binding details:
  counts, months, verdict      exact
  coefficients and statistics  within 1e-9 relative (1e-12 absolute)
  t statistics                 within 1e-6 absolute

The first implementation's key names were not visible when this was written,
so each item is looked up under a short list of plausible aliases. A key that
is found under none of them is reported MISSING rather than silently passed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

REL_TOL = 1e-9
ABS_TOL = 1e-12
T_TOL = 1e-6

# (label, kind, [alias paths]); a path is dotted, read on both files.
ITEMS = [
    ("n_oos", "count", ["n_oos", "oos.n", "n", "primary.n", "oos_n"]),
    ("first_oos", "month", ["first_oos", "oos.first", "oos_first", "oos.start", "first_month"]),
    ("last_oos", "month", ["last_oos", "oos.last", "oos_last", "oos.end", "last_month"]),
    ("verdict", "verdict", ["verdict"]),
    ("criteria.primary", "verdict", ["criteria.primary", "primary", "primary_met"]),
    ("c", "coef", ["c", "oos.c", "primary.c", "coef_c", "c_hat"]),
    ("c_t", "t", ["c_t", "t_c", "oos.c_t", "primary.c_t", "c_tstat", "t", "t_stat"]),
    ("a", "coef", ["a", "oos.a", "primary.a", "intercept", "alpha"]),
    ("mean_winter", "coef", ["mean_winter", "winter_mean", "mean_e_winter", "oos.mean_winter"]),
    ("mean_summer", "coef", ["mean_summer", "summer_mean", "mean_e_summer", "oos.mean_summer"]),
    ("share_winter_beats_summer", "coef", [
        "share_winter_beats_summer", "winter_beats_summer", "share_winters_beat_summer",
        "share_winter_beat_summer",
    ]),
    ("full.n", "count", ["full.n", "full_n", "full_sample.n"]),
    ("full.c", "coef", ["full.c", "full_c", "full_sample.c"]),
    ("full.c_t", "t", ["full.c_t", "full.t_c", "full_c_t", "full_sample.c_t"]),
    ("replication.n", "count", ["replication.n", "replication_n", "published.n", "insample.n"]),
    ("replication.c", "coef", ["replication.c", "replication_c", "published.c", "insample.c"]),
    ("replication.c_t", "t", [
        "replication.c_t", "replication.t_c", "replication_c_t", "published.c_t", "insample.c_t",
    ]),
    ("strategy.ann_return", "coef", [
        "strategy.ann_return", "strategy.annual_return", "strategy.cagr", "strategy.ann_ret",
    ]),
    ("strategy.ann_vol", "coef", [
        "strategy.ann_vol", "strategy.volatility", "strategy.vol", "strategy.ann_volatility",
    ]),
    ("strategy.sharpe", "coef", ["strategy.sharpe", "strategy.sharpe_ratio"]),
    ("strategy.max_drawdown", "coef", [
        "strategy.max_drawdown", "strategy.mdd", "strategy.max_dd", "strategy.maximum_drawdown",
    ]),
    ("held.ann_return", "coef", [
        "held.ann_return", "held.annual_return", "held.cagr", "held.ann_ret",
        "buy_and_hold.ann_return", "ndx.ann_return",
    ]),
    ("held.ann_vol", "coef", [
        "held.ann_vol", "held.volatility", "held.vol", "held.ann_volatility",
        "buy_and_hold.ann_vol", "ndx.ann_vol",
    ]),
    ("held.sharpe", "coef", ["held.sharpe", "held.sharpe_ratio", "buy_and_hold.sharpe", "ndx.sharpe"]),
    ("held.max_drawdown", "coef", [
        "held.max_drawdown", "held.mdd", "held.max_dd", "held.maximum_drawdown",
        "buy_and_hold.max_drawdown", "ndx.max_drawdown",
    ]),
]

_SENTINEL = object()


def lookup(doc, path):
    cur = doc
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _SENTINEL
    return cur


def find(doc, aliases):
    """Return (value, path) for the first alias present, else (_SENTINEL, None)."""
    for p in aliases:
        v = lookup(doc, p)
        if v is not _SENTINEL:
            return v, p
    return _SENTINEL, None


_MONTH_RE = re.compile(r"^\s*(\d{4})\D?(\d{2})(?:\D?\d{2})?\s*$")


def norm_month(v):
    """Reduce '2003-01', '2003-01-31', '200301', '2003/01' to '2003-01'."""
    if v is None:
        return None
    m = _MONTH_RE.match(str(v))
    if not m:
        return str(v).strip()
    return "%s-%s" % (m.group(1), m.group(2))


def norm_verdict(v):
    """Map True/False and case variants onto PASS/FAIL/INSUFFICIENT."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "PASS" if v else "FAIL"
    s = str(v).strip().upper()
    if s in {"TRUE", "PASSED", "MET"}:
        return "PASS"
    if s in {"FALSE", "FAILED", "NOT MET", "NOT_MET"}:
        return "FAIL"
    return s


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def close(x, y, rel, abs_):
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False
    if not (is_num(x) and is_num(y)):
        return x == y
    if x != x or y != y:  # NaN on either side never agrees
        return False
    return abs(x - y) <= max(abs_, rel * max(abs(x), abs(y)))


def compare_item(kind, x, y):
    """Return (status, note)."""
    if kind == "count":
        if x is None and y is None:
            return "AGREE", ""
        try:
            ok = int(x) == int(y)
        except (TypeError, ValueError):
            ok = x == y
        return ("AGREE" if ok else "DISAGREE"), ""
    if kind == "month":
        return ("AGREE" if norm_month(x) == norm_month(y) else "DISAGREE"), ""
    if kind == "verdict":
        return ("AGREE" if norm_verdict(x) == norm_verdict(y) else "DISAGREE"), ""
    if kind == "t":
        if x is None and y is None:
            return "AGREE", ""
        if x is None or y is None or not (is_num(x) and is_num(y)):
            return "DISAGREE", ""
        return ("AGREE" if abs(x - y) <= T_TOL else "DISAGREE"), "diff %.3e" % (x - y)
    # coefficients and statistics
    if close(x, y, REL_TOL, ABS_TOL):
        return "AGREE", ""
    note = ""
    if is_num(x) and is_num(y):
        note = "diff %.3e" % (x - y)
        if close(abs(x), abs(y), REL_TOL, ABS_TOL):
            note += " (magnitudes agree; sign convention differs)"
    return "DISAGREE", note


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, float):
        return "%.12g" % v
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare results.json with verify.json")
    ap.add_argument("--a", required=True, help="first implementation's results.json")
    ap.add_argument("--b", required=True, help="verify.json from verify.py")
    args = ap.parse_args(argv)

    with open(args.a, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(args.b, encoding="utf-8") as fh:
        b = json.load(fh)

    statuses = []
    width = max(len(label) for label, _, _ in ITEMS)
    print("%-*s  %-8s  %-24s  %-24s  %s" % (width, "item", "status", "a", "b", "note"))
    for label, kind, aliases in ITEMS:
        va, pa = find(a, aliases)
        vb, pb = find(b, aliases)
        if va is _SENTINEL or vb is _SENTINEL:
            missing = []
            if va is _SENTINEL:
                missing.append("a")
            if vb is _SENTINEL:
                missing.append("b")
            status = "MISSING"
            note = "not found in %s" % ",".join(missing)
            sa = "-" if va is _SENTINEL else fmt(va)
            sb = "-" if vb is _SENTINEL else fmt(vb)
        else:
            status, note = compare_item(kind, va, vb)
            sa, sb = fmt(va), fmt(vb)
            if pa != label or pb != label:
                note = (note + " " if note else "") + "[a:%s b:%s]" % (pa, pb)
        statuses.append(status)
        print("%-*s  %-8s  %-24s  %-24s  %s" % (width, label, status, sa, sb, note))

    n_agree = statuses.count("AGREE")
    n_dis = statuses.count("DISAGREE")
    n_miss = statuses.count("MISSING")
    overall = "AGREE" if n_dis == 0 and n_miss == 0 else "DISAGREE"
    print()
    print("OVERALL %s  (%d agree, %d disagree, %d missing of %d items)" % (
        overall, n_agree, n_dis, n_miss, len(statuses)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
