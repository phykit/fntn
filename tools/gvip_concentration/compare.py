#!/usr/bin/env python3
"""compare.py: compare the two implementations' outputs item by item.

Usage: python compare.py --a results.json --b verify.json

Rules, fixed in advance:
  counts, month strings and the verdict      exact
  coefficients and R-squared                 |a - b| <= max(1e-9 * max(|a|, |b|), 1e-12)
  t-statistics                               |a - b| <= 1e-6 (absolute)

Prints AGREE or DISAGREE for every item and an OVERALL line, and always exits 0:
the verdict is in the printed output, not in the exit code, so that a
disagreement is read rather than swallowed by a shell.

Lookup: each item is a dotted path (list indices as integers). If the path is
not found at the top of a file, the first segment is searched for by name
anywhere in that file and used only where exactly one occurrence exists; the
path actually used is printed, so a renamed or nested key is visible rather
than silently matched. A path missing from either file is a DISAGREE.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

COEF_REL = 1e-9
COEF_ABS = 1e-12
T_ABS = 1e-6

ITEMS = [
    ("n_months", "exact"),
    ("first_month", "exact"),
    ("last_month", "exact"),
    ("verdict", "exact"),
    ("a_monthly", "coef"),
    ("a_t", "t"),
    ("b", "coef"),
    ("b_t", "t"),
    ("r2", "coef"),
    ("gvip_minus_qqqe_annual", "coef"),
    ("gvip_minus_qqqe_t", "t"),
    ("rsp.a_monthly", "coef"),
    ("rsp.a_t", "t"),
    ("rsp.b", "coef"),
    ("rsp.b_t", "t"),
    ("rsp.r2", "coef"),
    ("halves.#", "count"),
    ("halves.0.first_month", "exact"),
    ("halves.0.last_month", "exact"),
    ("halves.0.a_monthly", "coef"),
    ("halves.0.a_t", "t"),
    ("halves.0.b", "coef"),
    ("halves.0.b_t", "t"),
    ("halves.1.first_month", "exact"),
    ("halves.1.last_month", "exact"),
    ("halves.1.a_monthly", "coef"),
    ("halves.1.a_t", "t"),
    ("halves.1.b", "coef"),
    ("halves.1.b_t", "t"),
]

MISSING = object()


def walk(node, segments):
    for seg in segments:
        if seg == "#":
            return len(node) if isinstance(node, (list, dict)) else MISSING
        if isinstance(node, list):
            try:
                node = node[int(seg)]
            except (ValueError, IndexError):
                return MISSING
        elif isinstance(node, dict):
            if seg not in node:
                return MISSING
            node = node[seg]
        else:
            return MISSING
    return node


def find_key(node, name, prefix=""):
    hits = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            if key == name:
                hits.append(path)
            hits.extend(find_key(value, name, path))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            hits.extend(find_key(value, name, f"{prefix}.{i}"))
    return hits


SUB_BLOCKS = {"rsp", "halves"}


def resolve(doc, path):
    """Return (value, path_used). value is MISSING where nothing usable was found.

    The fallback search ignores occurrences inside the known sub-blocks (rsp,
    halves) when looking for a headline key, because a_monthly, b, n_months and
    the rest recur there by design and would otherwise make every headline
    key ambiguous.
    """
    segments = path.split(".")
    value = walk(doc, segments)
    if value is not MISSING:
        return value, path
    hits = find_key(doc, segments[0])
    if segments[0] not in SUB_BLOCKS:
        hits = [h for h in hits if not (set(h.split(".")) & SUB_BLOCKS)]
    if len(hits) != 1:
        return MISSING, None
    value = walk(walk(doc, hits[0].split(".")), segments[1:])
    if value is MISSING:
        return MISSING, None
    return value, ".".join([hits[0]] + segments[1:])


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def compare_values(kind, a, b):
    """Return (agree: bool, note: str)."""
    if a is None and b is None:
        return True, "both null"
    if a is None or b is None:
        return False, "one side null"
    if kind in ("exact", "count"):
        if is_number(a) and is_number(b):
            return a == b, ""
        return str(a).strip() == str(b).strip(), ""
    if not (is_number(a) and is_number(b)):
        return False, "non-numeric"
    a = float(a)
    b = float(b)
    if not (math.isfinite(a) and math.isfinite(b)):
        return False, "non-finite"
    diff = abs(a - b)
    if kind == "coef":
        tol = max(COEF_REL * max(abs(a), abs(b)), COEF_ABS)
    elif kind == "t":
        tol = T_ABS
    else:
        raise ValueError(kind)
    return diff <= tol, f"diff {diff:.3e} tol {tol:.3e}"


def fmt(value):
    if value is MISSING:
        return "<missing>"
    if value is None:
        return "null"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--a", required=True, help="first implementation's results.json")
    parser.add_argument("--b", required=True, help="second implementation's verify.json")
    args = parser.parse_args(argv)

    with open(args.a, encoding="utf-8") as handle:
        doc_a = json.load(handle)
    with open(args.b, encoding="utf-8") as handle:
        doc_b = json.load(handle)

    print(f"A: {args.a}")
    print(f"B: {args.b}")
    print(f"rules: exact for counts, months, verdict; coefficients and r2 within {COEF_REL:g} relative "
          f"({COEF_ABS:g} absolute near zero); t within {T_ABS:g} absolute")
    print()
    width = max(len(path) for path, _ in ITEMS)
    agreed = 0
    for path, kind in ITEMS:
        value_a, used_a = resolve(doc_a, path)
        value_b, used_b = resolve(doc_b, path)
        if value_a is MISSING or value_b is MISSING:
            agree, note = False, "missing in " + " and ".join(
                side for side, value in (("A", value_a), ("B", value_b)) if value is MISSING)
        else:
            agree, note = compare_values(kind, value_a, value_b)
        if agree:
            agreed += 1
        relocated = []
        if used_a not in (None, path):
            relocated.append(f"A at {used_a}")
        if used_b not in (None, path):
            relocated.append(f"B at {used_b}")
        if relocated:
            note = (note + "; " if note else "") + ", ".join(relocated)
        print(f"{'AGREE   ' if agree else 'DISAGREE'}  {path:<{width}}  {kind:<5}  "
              f"A={fmt(value_a)}  B={fmt(value_b)}" + (f"  [{note}]" if note else ""))
    print()
    overall = "AGREE" if agreed == len(ITEMS) else "DISAGREE"
    print(f"OVERALL: {overall} ({agreed} of {len(ITEMS)} items agree)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
