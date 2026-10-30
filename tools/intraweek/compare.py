#!/usr/bin/env python3
"""Compare two implementations of tools/intraweek/PREREG.md key by key.

Usage:
    python compare.py --a results.json --b verify.json

Walks every key PREREG section 5 lists, for both pairs and the top level, and
prints one line per item: AGREE or DISAGREE, the key, and both values. Ends
with an OVERALL line carrying the counts. Always exits 0: the comparison is a
report, not a gate, and a non-zero exit would let a wrapper mistake a
disagreement for a crash.

Tolerances, by kind of item:
    count, label, bool        exact
    p-value                   exact; a difference under 0.002 is noted "(within 0.002)"
    mean, d, slope, trade     |a - b| <= max(1e-12, 1e-9 * max(|a|, |b|))
    t-statistic               |a - b| <= 1e-6
A key missing on one side is a DISAGREE naming the side. Null on both sides
agrees; null on one side only disagrees.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

MISSING = object()

# (key path, kind). The path is dotted; a trailing [i] indexes a list.
PAIR_KEYS = [
    ("legs", "label"),
    ("n_admissible", "count"),
    ("n_eligible", "count"),
    ("first_eligible", "label"),
    ("last_eligible", "label"),
    ("n_signal", "count"),
    ("mean_R_signal", "mean"),
    ("mean_R_other", "mean"),
    ("d", "mean"),
    ("p_shift", "pvalue"),
    ("n_shifts", "count"),
    ("share_R_negative_signal", "mean"),
    ("top.n_signal", "count"),
    ("top.d", "mean"),
    ("top.p_shift", "pvalue"),
    ("one_day.n_signal", "count"),
    ("one_day.d", "mean"),
    ("one_day.p_shift", "pvalue"),
    ("daily.slope1", "slope"),
    ("daily.t1", "tstat"),
    ("daily.n1", "count"),
    ("daily.slope23", "slope"),
    ("daily.t23", "tstat"),
    ("daily.n23", "count"),
    ("episodes.n", "count"),
    ("episodes.mean_by_day[0]", "mean"),
    ("episodes.mean_by_day[1]", "mean"),
    ("episodes.mean_by_day[2]", "mean"),
    ("episodes.mean_by_day[3]", "mean"),
    ("episodes.mean_by_day[4]", "mean"),
    ("episodes.mean_S", "mean"),
    ("episodes.mean_R", "mean"),
    ("episodes.hit_rate", "mean"),
    ("episodes.n_with_reference", "count"),
    ("trade.n", "count"),
    ("trade.share_profitable", "trade"),
    ("trade.mean", "trade"),
    ("trade.median", "trade"),
    ("trade.t", "tstat"),
    ("trade.worst", "trade"),
    ("trade.net_per_year", "trade"),
    ("trade.trade_passes", "bool"),
]

TOP_KEYS = [
    ("criteria.p1", "bool"),
    ("criteria.p2", "bool"),
    ("p1_alone", "bool"),
    ("verdict", "label"),
]


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def walk(obj, path: str):
    """Follow a dotted path with optional [i] list indices; MISSING if absent."""
    cur = obj
    for part in path.split("."):
        idx = None
        if part.endswith("]") and "[" in part:
            part, rest = part.split("[", 1)
            idx = int(rest[:-1])
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
        if idx is not None:
            if not isinstance(cur, list) or idx >= len(cur):
                return MISSING
            cur = cur[idx]
    return cur


def is_null(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def normalise_label(v):
    # A label may be a list of strings or a string; compare canonically.
    if isinstance(v, list):
        return [str(x) for x in v]
    return v


def compare_value(a, b, kind: str) -> tuple[bool, str]:
    """Return (agree, note)."""
    if a is MISSING or b is MISSING:
        side = "a" if a is MISSING else "b"
        if a is MISSING and b is MISSING:
            side = "both"
        return False, f"missing on {side}"
    if is_null(a) and is_null(b):
        return True, "null on both"
    if is_null(a) or is_null(b):
        return False, "null on one side"
    if kind in ("count", "label", "bool"):
        if kind == "label":
            return normalise_label(a) == normalise_label(b), ""
        if kind == "bool":
            return bool(a) == bool(b), ""
        try:
            return int(a) == int(b) and float(a) == float(b), ""
        except (TypeError, ValueError):
            return a == b, ""
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return a == b, "non-numeric"
    diff = abs(fa - fb)
    if kind == "pvalue":
        if fa == fb:
            return True, ""
        note = "(within 0.002)" if diff < 0.002 else ""
        return False, note
    if kind == "tstat":
        return diff <= 1e-6, ""
    # mean, d, slope, trade statistics
    tol = max(1e-12, 1e-9 * max(abs(fa), abs(fb)))
    return diff <= tol, ""


def fmt(v) -> str:
    if v is MISSING:
        return "<missing>"
    if v is None:
        return "null"
    if isinstance(v, float):
        return repr(v)
    return json.dumps(v)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--a", required=True, help="first results file (results.json)")
    ap.add_argument("--b", required=True, help="second results file (verify.json)")
    args = ap.parse_args(argv)

    try:
        A = load(args.a)
    except Exception as exc:  # noqa: BLE001
        print(f"DISAGREE  <file a>  cannot read {args.a}: {exc}")
        A = {}
    try:
        B = load(args.b)
    except Exception as exc:  # noqa: BLE001
        print(f"DISAGREE  <file b>  cannot read {args.b}: {exc}")
        B = {}

    items: list[tuple[str, str]] = []
    for pair in ("P1", "P2"):
        for key, kind in PAIR_KEYS:
            items.append((f"pairs.{pair}.{key}", kind))
    items.extend(TOP_KEYS)

    n_agree = n_disagree = 0
    for path, kind in items:
        a = walk(A, path)
        b = walk(B, path)
        agree, note = compare_value(a, b, kind)
        tag = "AGREE   " if agree else "DISAGREE"
        if agree:
            n_agree += 1
        else:
            n_disagree += 1
        line = f"{tag}  {path:<42} a={fmt(a)}  b={fmt(b)}"
        if note:
            line += f"  {note}"
        print(line)
    print(f"OVERALL  {n_agree} AGREE, {n_disagree} DISAGREE, {n_agree + n_disagree} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
