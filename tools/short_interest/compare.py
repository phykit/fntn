#!/usr/bin/env python3
"""Compare run.py's results.json with verify.py's verify.json, item by item.

Usage::

    python compare.py --a results.json --b verify.json

Tolerances, fixed by the task that commissioned the second implementation:

* ``n``, ``first_signal_month``, ``last_signal_month``, ``n_shifts``,
  ``n_oos_forecasts``, ``verdict`` and ``p_shift``: exact.
* ``b``, ``b_per_sd``, ``r2_in_sample``, ``r2_oos``: within 1e-9 relative,
  with an absolute floor of 1e-12 so that two values near zero are not held to
  a relative test they cannot meet.
* ``nw_t``, ``clark_west_t``: within 1e-6 absolute.
* ``criteria.primary`` and ``criteria.oos``: exact (a check beyond the list,
  included because the verdict is derived from them and a verdict that agrees
  while a criterion disagrees is worth seeing).

A key missing from either file, or null on one side and not the other, is a
DISAGREE; two nulls agree.  The script prints AGREE or DISAGREE for each item
and an OVERALL line, and always exits 0: its job is to report, and a non-zero
exit would let a pipeline mistake a disagreement for a crash.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

EXACT_ITEMS = [
    "n",
    "first_signal_month",
    "last_signal_month",
    "n_shifts",
    "n_oos_forecasts",
    "verdict",
    "p_shift",
    "criteria.primary",
    "criteria.oos",
]
REL_ITEMS = ["b", "b_per_sd", "r2_in_sample", "r2_oos"]
T_ITEMS = ["nw_t", "clark_west_t"]

REL_TOL = 1e-9
ABS_FLOOR = 1e-12
T_ABS_TOL = 1e-6

_MISSING = object()


def _search(obj, key):
    """Depth-first search for the first dict holding ``key``; returns
    (value, path) or (_MISSING, None)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key], key
        for k, v in obj.items():
            found, path = _search(v, key)
            if found is not _MISSING:
                return found, f"{k}.{path}"
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found, path = _search(v, key)
            if found is not _MISSING:
                return found, f"[{i}].{path}"
    return _MISSING, None


def lookup(doc, dotted):
    """Resolve a dotted key.  Each component is looked up at the current level
    first and, failing that, anywhere beneath it; the resolved path is returned
    so that a nested hit is visible in the report."""
    cur = doc
    resolved = []
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            resolved.append(part)
        else:
            found, path = _search(cur, part)
            if found is _MISSING:
                return _MISSING, None
            cur = found
            resolved.append(path)
    return cur, ".".join(resolved)


def _fmt(v):
    if v is _MISSING:
        return "<missing>"
    if v is None:
        return "null"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return repr(v)
    return str(v)


def _both_present(a, b):
    if a is _MISSING or b is _MISSING:
        return False, "key missing"
    if a is None and b is None:
        return True, "both null"
    if a is None or b is None:
        return False, "null on one side only"
    return True, ""


def cmp_exact(a, b):
    ok, note = _both_present(a, b)
    if note:
        return ok, note
    if isinstance(a, bool) or isinstance(b, bool):
        return (a is b), "" if a is b else "differ"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return (a == b), "" if a == b else f"diff={a - b!r}"
    return (a == b), "" if a == b else "differ"


def cmp_rel(a, b):
    ok, note = _both_present(a, b)
    if note:
        return ok, note
    try:
        a = float(a)
        b = float(b)
    except (TypeError, ValueError):
        return False, "not numeric"
    if not (math.isfinite(a) and math.isfinite(b)):
        return False, "non-finite"
    diff = abs(a - b)
    tol = max(ABS_FLOOR, REL_TOL * max(abs(a), abs(b)))
    return diff <= tol, f"|diff|={diff:.3e} tol={tol:.3e}"


def cmp_abs(a, b, tol):
    ok, note = _both_present(a, b)
    if note:
        return ok, note
    try:
        a = float(a)
        b = float(b)
    except (TypeError, ValueError):
        return False, "not numeric"
    if not (math.isfinite(a) and math.isfinite(b)):
        return False, "non-finite"
    diff = abs(a - b)
    return diff <= tol, f"|diff|={diff:.3e} tol={tol:.1e}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--a", required=True, help="results.json from run.py")
    ap.add_argument("--b", required=True, help="verify.json from verify.py")
    args = ap.parse_args(argv)

    with open(args.a, encoding="utf-8") as fh:
        da = json.load(fh)
    with open(args.b, encoding="utf-8") as fh:
        db = json.load(fh)

    plan = ([(k, "exact") for k in EXACT_ITEMS]
            + [(k, "rel") for k in REL_ITEMS]
            + [(k, "t") for k in T_ITEMS])

    n_agree = 0
    lines = []
    for key, kind in plan:
        va, pa = lookup(da, key)
        vb, pb = lookup(db, key)
        if kind == "exact":
            ok, note = cmp_exact(va, vb)
            rule = "exact"
        elif kind == "rel":
            ok, note = cmp_rel(va, vb)
            rule = f"rel {REL_TOL:g} (abs floor {ABS_FLOOR:g})"
        else:
            ok, note = cmp_abs(va, vb, T_ABS_TOL)
            rule = f"abs {T_ABS_TOL:g}"
        n_agree += 1 if ok else 0
        where = ""
        if pa is not None and pa != key:
            where += f" [a at {pa}]"
        if pb is not None and pb != key:
            where += f" [b at {pb}]"
        lines.append((key, _fmt(va), _fmt(vb), "AGREE" if ok else "DISAGREE",
                      rule, note + where))

    kw = max(len(l[0]) for l in lines)
    aw = min(28, max(len(l[1]) for l in lines))
    bw = min(28, max(len(l[2]) for l in lines))
    print(f"{'item':<{kw}}  {'a (results.json)':<{aw}}  "
          f"{'b (verify.json)':<{bw}}  result    rule / note")
    for key, sa, sb, res, rule, note in lines:
        extra = f"{rule}; {note}" if note else rule
        print(f"{key:<{kw}}  {sa:<{aw}}  {sb:<{bw}}  {res:<8}  {extra}")

    total = len(lines)
    overall = "AGREE" if n_agree == total else "DISAGREE"
    print(f"OVERALL: {overall} ({n_agree}/{total} items agree)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
