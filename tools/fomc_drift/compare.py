#!/usr/bin/env python3
"""Compare the two implementations of the pre-FOMC drift test item by item.

Usage::

    python compare.py --a results.json --b verify.json

``--a`` is the first implementation's output and ``--b`` the independent
second implementation's. Each item is reported AGREE or DISAGREE under the
tolerance the item carries, then OVERALL. The exit status is always 0: a
disagreement is a finding to be read, not a failure to be retried, and a
non-zero status would invite exactly the retry loop this comparison exists to
prevent.

Tolerances (from the brief):

* counts and the verdict: exact;
* p values: exact, with a note where the two are within 0.002 (a shift test
  with the same rotations and the same arithmetic yields the same p; a p that
  is close but not equal usually means one rotation sat at a tie or the range
  of k differed by one, and the note says which to look at);
* differences, means and shares: within 1e-9 relative or 1e-12 absolute;
* the Newey-West t: within 1e-6 absolute;
* strategy figures: within 1e-9 relative (with the same 1e-12 absolute floor,
  since a figure that is exactly zero has no relative tolerance).

Nested keys are written with dots. A key missing on either side is a
DISAGREE with the reason stated, never a silent skip.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REL_TOL = 1e-9
ABS_TOL = 1e-12
T_TOL = 1e-6
P_NOTE_BAND = 0.002

# (key path, kind). Kinds: count, exact, p, rel, t.
ITEMS: list[tuple[str, str]] = [
    ("n_oos_days", "count"),
    ("n_oos_announcements", "count"),
    ("n_dropped", "count"),
    ("n_shifts", "count"),
    ("n_full_announcements", "count"),
    ("verdict", "exact"),
    ("criteria.primary", "exact"),
    ("p_shift_oos", "p"),
    ("p_shift_full", "p"),
    ("day_before.p", "p"),
    ("two_day.p", "p"),
    ("d_oos", "rel"),
    ("d_full", "rel"),
    ("mean_ann_bp_oos", "rel"),
    ("mean_other_bp_oos", "rel"),
    ("share_positive_ann", "rel"),
    ("share_positive_all", "rel"),
    ("day_before.d", "rel"),
    ("two_day.d", "rel"),
    ("nw_t_oos", "t"),
    ("strategy.ann_return", "rel"),
    ("strategy.sharpe", "rel"),
    ("strategy.invested_share", "rel"),
    ("strategy.qqq_ann_return", "rel"),
    ("strategy.qqq_sharpe", "rel"),
]

_MISSING = object()


def get_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def _is_nan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fmt(v: Any) -> str:
    if v is _MISSING:
        return "<missing>"
    if v is None:
        return "null"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def compare_values(a: Any, b: Any, kind: str) -> tuple[bool, str]:
    """Return (agree, note) for one item under the given kind."""
    if a is _MISSING or b is _MISSING:
        side = "a" if a is _MISSING else "b"
        if a is _MISSING and b is _MISSING:
            side = "both"
        return False, f"missing in {side}"
    # null (a NaN written to JSON) on both sides is an agreement that the
    # quantity is undefined; on one side only it is a disagreement.
    a_undef = a is None or _is_nan(a)
    b_undef = b is None or _is_nan(b)
    if a_undef and b_undef:
        return True, "both undefined"
    if a_undef or b_undef:
        return False, "undefined on one side only"

    if kind in ("count", "exact"):
        if kind == "count":
            if not (_is_number(a) and _is_number(b)):
                return False, "non-numeric count"
            if float(a) != float(b):
                return False, f"differ by {float(a) - float(b):+g}"
            return True, ""
        return (a == b, "" if a == b else "differ")

    if not (_is_number(a) and _is_number(b)):
        return False, "non-numeric"
    a = float(a)
    b = float(b)
    diff = abs(a - b)

    if kind == "p":
        if a == b:
            return True, ""
        note = f"differ by {a - b:+.6g}"
        if diff <= P_NOTE_BAND:
            note += f" (within {P_NOTE_BAND})"
        return False, note

    if kind == "rel":
        bound = max(ABS_TOL, REL_TOL * max(abs(a), abs(b)))
        if diff <= bound:
            return True, ""
        rel = diff / max(abs(a), abs(b)) if max(abs(a), abs(b)) > 0 else float("inf")
        return False, f"differ by {a - b:+.6g} (relative {rel:.3g})"

    if kind == "t":
        if diff <= T_TOL:
            return True, ""
        return False, f"differ by {a - b:+.6g}"

    return False, f"unknown kind {kind}"


def compare_by_year(a: Any, b: Any) -> list[tuple[str, Any, Any, bool, str]]:
    """The by-year table: the set of years exact, n_ann exact per year, the two
    sums within the relative tolerance per year."""
    rows: list[tuple[str, Any, Any, bool, str]] = []
    if a is _MISSING or b is _MISSING or not isinstance(a, list) or not isinstance(b, list):
        rows.append(("by_year", "<missing or not a list>" if a is _MISSING or not isinstance(a, list) else f"{len(a)} rows",
                     "<missing or not a list>" if b is _MISSING or not isinstance(b, list) else f"{len(b)} rows",
                     False, "by_year absent or malformed"))
        return rows
    ay = {int(r["year"]): r for r in a if isinstance(r, dict) and "year" in r}
    by = {int(r["year"]): r for r in b if isinstance(r, dict) and "year" in r}
    same_years = sorted(ay) == sorted(by)
    rows.append(("by_year.years", sorted(ay), sorted(by), same_years, "" if same_years else "year sets differ"))
    for yr in sorted(set(ay) | set(by)):
        ra = ay.get(yr, {})
        rb = by.get(yr, {})
        for field, kind in (("n_ann", "count"), ("ann_sum", "rel"), ("total_sum", "rel")):
            va = ra.get(field, _MISSING) if yr in ay else _MISSING
            vb = rb.get(field, _MISSING) if yr in by else _MISSING
            ok, note = compare_values(va, vb, kind)
            rows.append((f"by_year[{yr}].{field}", va, vb, ok, note))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare results.json (a) against verify.json (b).")
    ap.add_argument("--a", required=True, type=Path, help="first implementation's results.json")
    ap.add_argument("--b", required=True, type=Path, help="second implementation's verify.json")
    args = ap.parse_args(argv)

    try:
        a = json.loads(args.a.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - the file, not the code, is at fault
        print(f"cannot read {args.a}: {exc}")
        print("OVERALL: DISAGREE (a unreadable)")
        return 0
    try:
        b = json.loads(args.b.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"cannot read {args.b}: {exc}")
        print("OVERALL: DISAGREE (b unreadable)")
        return 0

    rows: list[tuple[str, Any, Any, bool, str]] = []
    for key, kind in ITEMS:
        va = get_path(a, key)
        vb = get_path(b, key)
        ok, note = compare_values(va, vb, kind)
        rows.append((key, va, vb, ok, note))
    rows.extend(compare_by_year(get_path(a, "by_year"), get_path(b, "by_year")))

    # Diagnostic cross-check for the one item whose definition the brief left
    # open: if nw_t_oos disagrees, say whether a's figure matches b's t of the
    # difference (the A coefficient alone), which is the other reading.
    extra_notes: list[str] = []
    nw_row = next(r for r in rows if r[0] == "nw_t_oos")
    if not nw_row[3]:
        alt = get_path(b, "nw_t_diff_oos")
        va = get_path(a, "nw_t_oos")
        if _is_number(alt) and _is_number(va) and abs(float(alt) - float(va)) <= T_TOL:
            extra_notes.append(
                "nw_t_oos: a's value matches b's nw_t_diff_oos (t of the A coefficient), so the "
                "two implementations read 'the t of the announcement-day mean' differently"
            )

    width = max(len(r[0]) for r in rows)
    n_agree = 0
    for key, va, vb, ok, note in rows:
        status = "AGREE" if ok else "DISAGREE"
        n_agree += ok
        line = f"{status:8s} {key:<{width}s}  a={_fmt(va)}  b={_fmt(vb)}"
        if note:
            line += f"  [{note}]"
        print(line)
    for n in extra_notes:
        print(f"NOTE     {n}")
    overall = "AGREE" if n_agree == len(rows) else "DISAGREE"
    print(f"OVERALL: {overall} ({n_agree}/{len(rows)} items agree)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
