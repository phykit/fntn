#!/usr/bin/env python3
"""Compare the two implementations of tools/volmom/PREREG.md on every headline figure.

Usage: python compare.py --a results.json --b verify.json

Both files carry the same top-level keys (the first implementation's results.json
and the second's verify.json). Rules, per the comparison brief:

  counts, verdicts, criteria booleans and month strings    exact
  alphas, b, Sharpe ratios, drawdowns, weights, returns    within 1e-9 relative,
                                                           or 1e-12 absolute near zero
  Newey-West t                                             within 1e-6 absolute
  p_boot                                                   exact (identical draw procedure);
                                                           a NOTE, not a disagreement, if
                                                           within 0.002
  mtum sub-keys                                            likewise

Prints AGREE / DISAGREE per item and OVERALL. Always exits 0: the verdict is on the
printed record, not in the exit status.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, List, Optional, Tuple

REL_TOL = 1e-9
ABS_TOL = 1e-12
T_TOL = 1e-6
P_NOTE_TOL = 0.002

_MISSING = object()


def get(d: Any, dotted: str) -> Any:
    cur = d
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return _MISSING
    return cur


def fmt(v: Any) -> str:
    if v is _MISSING:
        return "<absent>"
    if isinstance(v, float):
        return repr(v)
    return json.dumps(v)


def close_rel(a: float, b: float) -> bool:
    diff = abs(a - b)
    return diff <= ABS_TOL or diff <= REL_TOL * max(abs(a), abs(b))


# Each row: (dotted key, kind, required). Kinds: int, str, bool, rel, t, p.
# Required keys count as DISAGREE when absent from either file; optional ones
# (extras one implementation may not emit) are SKIPPED when absent.
ITEMS: List[Tuple[str, str, bool]] = [
    ("n_is", "int", True),
    ("n_oos", "int", True),
    ("oos_first", "str", True),
    ("oos_last", "str", True),
    ("oos_alpha_monthly", "rel", True),
    ("oos_alpha_t", "t", True),
    ("oos_b", "rel", True),
    ("oos_sharpe_raw", "rel", True),
    ("oos_sharpe_managed", "rel", True),
    ("oos_sharpe_ratio", "rel", True),
    ("p_boot", "p", True),
    ("criteria.a", "bool", True),
    ("criteria.b", "bool", True),
    ("verdict", "str", True),
    ("is_sharpe_raw", "rel", True),
    ("is_sharpe_managed", "rel", True),
    ("is_alpha_monthly", "rel", True),
    ("is_alpha_t", "t", True),
    ("oos_maxdd_raw", "rel", True),
    ("oos_maxdd_managed", "rel", True),
    ("weight_min", "rel", True),
    ("weight_median", "rel", True),
    ("weight_max", "rel", True),
    ("weight_share_above_2", "rel", True),
]
for _i in range(5):
    ITEMS += [
        (f"worst_raw_months.{_i}.month", "str", True),
        (f"worst_raw_months.{_i}.raw", "rel", True),
        (f"worst_raw_months.{_i}.managed", "rel", True),
    ]
ITEMS += [
    ("mtum.n", "int", True),
    ("mtum.first", "str", True),
    ("mtum.last", "str", True),
    ("mtum.alpha_monthly", "rel", True),
    ("mtum.alpha_t", "t", True),
    ("mtum.b", "rel", False),
    ("mtum.sharpe_raw", "rel", True),
    ("mtum.sharpe_managed", "rel", True),
    ("mtum.sharpe_ratio", "rel", True),
    ("mtum.p_boot", "p", True),
    ("mtum.criteria.a", "bool", False),
    ("mtum.criteria.b", "bool", False),
    ("mtum.verdict", "str", True),
    ("mtum.ann_return_managed", "rel", True),
    ("mtum.cost_estimate_annual", "rel", True),
    ("mtum.maxdd_raw", "rel", False),
    ("mtum.maxdd_managed", "rel", False),
]


def compare_item(key: str, kind: str, required: bool, a: Any, b: Any) -> Tuple[str, str]:
    """Returns (status, detail); status in AGREE / DISAGREE / NOTE / SKIP."""
    if a is _MISSING or b is _MISSING:
        if required:
            return "DISAGREE", f"absent in {'A' if a is _MISSING else 'B'}"
        return "SKIP", f"absent in {'A' if a is _MISSING else 'B'} (optional key)"
    if a is None or b is None:
        if a is None and b is None:
            return "AGREE", "both null"
        return "DISAGREE", f"A={fmt(a)} B={fmt(b)} (one null)"

    if kind == "int":
        return ("AGREE" if int(a) == int(b) else "DISAGREE"), f"A={fmt(a)} B={fmt(b)}"
    if kind == "str":
        return ("AGREE" if str(a) == str(b) else "DISAGREE"), f"A={fmt(a)} B={fmt(b)}"
    if kind == "bool":
        return ("AGREE" if bool(a) == bool(b) else "DISAGREE"), f"A={fmt(a)} B={fmt(b)}"

    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return "DISAGREE", f"A={fmt(a)} B={fmt(b)} (not numeric)"
    if math.isnan(fa) or math.isnan(fb):
        return ("AGREE" if math.isnan(fa) and math.isnan(fb) else "DISAGREE"), f"A={fmt(a)} B={fmt(b)}"
    diff = abs(fa - fb)

    if kind == "rel":
        ok = close_rel(fa, fb)
        return ("AGREE" if ok else "DISAGREE"), f"A={fmt(fa)} B={fmt(fb)} |diff|={diff:.3e}"
    if kind == "t":
        ok = diff <= T_TOL
        return ("AGREE" if ok else "DISAGREE"), f"A={fmt(fa)} B={fmt(fb)} |diff|={diff:.3e} (tol {T_TOL:g})"
    if kind == "p":
        if fa == fb:
            return "AGREE", f"A={fmt(fa)} B={fmt(fb)} (exact)"
        if diff <= P_NOTE_TOL:
            return "NOTE", (f"A={fmt(fa)} B={fmt(fb)} |diff|={diff:.3e}: not identical, within "
                            f"{P_NOTE_TOL}; the draw procedures differ somewhere even if the "
                            f"inference does not")
        return "DISAGREE", f"A={fmt(fa)} B={fmt(fb)} |diff|={diff:.3e}"
    raise ValueError(kind)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="first implementation's results.json")
    ap.add_argument("--b", required=True, help="second implementation's verify.json")
    args = ap.parse_args(argv)

    with open(args.a) as fh:
        A = json.load(fh)
    with open(args.b) as fh:
        B = json.load(fh)

    counts = dict(AGREE=0, DISAGREE=0, NOTE=0, SKIP=0)
    width = max(len(k) for k, _, _ in ITEMS)
    print(f"A = {args.a}")
    print(f"B = {args.b}")
    print()
    for key, kind, required in ITEMS:
        status, detail = compare_item(key, kind, required, get(A, key), get(B, key))
        counts[status] += 1
        print(f"{status:<8} {key:<{width}}  {detail}")

    # Keys one file carries and the other does not, outside the item list: informational.
    extra_a = sorted(set(A) - set(B))
    extra_b = sorted(set(B) - set(A))
    if extra_a or extra_b:
        print()
        if extra_a:
            print(f"top-level keys only in A: {', '.join(extra_a)}")
        if extra_b:
            print(f"top-level keys only in B: {', '.join(extra_b)}")

    for label, obj in (("A", A), ("B", B)):
        ch = obj.get("choices")
        if isinstance(ch, list) and ch:
            print()
            print(f"{label} recorded {len(ch)} choice(s):")
            for c in ch:
                print(f"  - {c}")

    print()
    if counts["DISAGREE"]:
        overall = "DISAGREE"
    elif counts["NOTE"]:
        overall = "AGREE (with notes)"
    else:
        overall = "AGREE"
    print(f"OVERALL {overall}: {counts['AGREE']} agree, {counts['DISAGREE']} disagree, "
          f"{counts['NOTE']} note(s), {counts['SKIP']} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
