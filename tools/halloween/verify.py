#!/usr/bin/env python3
"""Independent second implementation of tools/halloween/PREREG.md.

Written on 29 October 2026 from the pre-registration and the binding details
supplied with it, without sight of run.py, selftest.py, fetch.py, any results
directory or docs/. Its purpose is PREREG.md disclosure 3: a second
implementation written from the file alone, to be compared with the first by
compare.py. It therefore uses the standard library only, so that it shares no
numerical machinery (no numpy, pandas or statsmodels) with the first
implementation; a shared library would make an agreement between the two less
informative than it looks.

Usage: python verify.py --data DIR --out DIR

Inputs under --data:
  ndx.csv        observation_date,NASDAQ100  (daily; blank where missing)
  ff5_daily.csv  DATE,...,RF                 (daily; RF in per cent)

Output: DIR/verify.json.

Every choice taken where the specification left room is listed under the
"choices" key of the output, so that a disagreement with the first
implementation can be traced to a reading rather than to arithmetic.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Constants fixed by the pre-registration
# ---------------------------------------------------------------------------

WINTER_MONTHS = frozenset({11, 12, 1, 2, 3, 4})
OOS_START = (2003, 1)
REPLICATION_END = (2002, 12)
MIN_MONTHS = 120
T_THRESHOLD = 2.0
NW_LAGS = 3

CHOICES = {
    "monthly_return": (
        "Last non-missing close of the month over the last non-missing close "
        "of the immediately preceding calendar month, minus one. A month with "
        "no close breaks the chain: neither it nor the month after it has a "
        "return."
    ),
    "complete_month": (
        "Applied to the NDX file only, as the PREREG states it under the NDX "
        "bullet. A month is complete if any row date in the file falls in a "
        "later month, or the last row date in the file (whether or not its "
        "value is blank) is the final Monday-to-Friday day of that month. The "
        "French file is not tested for completeness; months with no French RF "
        "row are dropped, as the binding details say."
    ),
    "monthly_rf": (
        "Product of (1 + RF_d / 100) over the French rows dated in the month, "
        "minus one. A month with no French row is dropped from every sample."
    ),
    "sample_start": (
        "Full sample and replication begin at the first month for which a "
        "return exists, which is the second calendar month in the NDX file; "
        "this is read as 'the first full month after the NDX start'. The "
        "replication runs from that month to 2002-12 inclusive; OOS runs from "
        "2003-01 to the last complete month, both after dropping months "
        "without RF."
    ),
    "regression": (
        "e_m = a + c W_m + u_m by OLS; Newey-West covariance with Bartlett "
        "weights 1 - l / (L + 1), L = 3, no small-sample correction (no "
        "n / (n - k) factor). t = c / sqrt(V[c, c]). The regression is not "
        "scored (null) with fewer than three months or with no variation in W."
    ),
    "verdict": (
        "INSUFFICIENT if the OOS month count is below 120; otherwise PASS if "
        "c > 0 and t >= 2.0, FAIL otherwise. criteria.primary carries the same "
        "three-way label."
    ),
    "winter_beats_summer": (
        "A winter is Nov(Y) to Apr(Y+1) and its following summer is May(Y+1) "
        "to Oct(Y+1). Only pairs with all twelve months inside the OOS sample "
        "are counted, so the winter straddling the 2003-01 OOS start is "
        "excluded. Cumulative return of a season is the compounded NDX total "
        "return (not the excess return) over its six months. Share = pairs "
        "where winter > summer, over pairs counted; null if no pair."
    ),
    "strategy_stats": (
        "Monthly total return: NDX return in winter months, compounded "
        "monthly RF in summer months (held: NDX return every month). Annual "
        "return = (product of (1 + s_m)) ^ (12 / n) - 1. Volatility = sample "
        "standard deviation (n - 1) of s_m times sqrt(12). Sharpe = sqrt(12) "
        "times mean(s_m - rf_m) over sample standard deviation (n - 1) of "
        "(s_m - rf_m). Max drawdown = minimum over months of wealth / running "
        "peak - 1, with the starting wealth of 1 included in the peak; "
        "reported as a non-positive fraction."
    ),
    "missing_values": (
        "In ndx.csv a value that is blank, '.', 'NA', 'NaN' or otherwise "
        "unparseable is a missing close for that date; the date still counts "
        "for the complete-month rule. In ff5_daily.csv a row whose first cell "
        "is not a date (YYYYMMDD or YYYY-MM-DD) is skipped, which covers "
        "French's preamble and footer lines; a row whose RF cell is not a "
        "number is skipped and counted."
    ),
}


# ---------------------------------------------------------------------------
# Dates and months
# ---------------------------------------------------------------------------

_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_COMPACT = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


def parse_date(text: str):
    """Return a date for YYYY-MM-DD or YYYYMMDD, else None.

    Both forms are accepted because FRED writes ISO dates and French writes
    compact ones, and the binding details do not say whether ff5_daily.csv was
    re-formatted before being saved.
    """
    s = text.strip()
    m = _ISO.match(s) or _COMPACT.match(s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def ym(d: date):
    return (d.year, d.month)


def ym_str(key):
    return "%04d-%02d" % key


def next_month(key):
    y, m = key
    return (y + 1, 1) if m == 12 else (y, m + 1)


def prev_month(key):
    y, m = key
    return (y - 1, 12) if m == 1 else (y, m - 1)


def final_weekday(key):
    """The last Monday-to-Friday calendar day of the month, holidays ignored.

    The PREREG says 'final weekday', not 'final trading day', so a month whose
    last weekday is an exchange holiday is complete only if the file carries a
    row for that date; FRED does carry holiday rows with blank values, which is
    why the complete-month rule is applied to row dates and not to closes.
    """
    y, m = key
    d = date(next_month(key)[0], next_month(key)[1], 1) - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


# ---------------------------------------------------------------------------
# Reading the inputs
# ---------------------------------------------------------------------------

_MISSING = {"", ".", "NA", "N/A", "NAN", "NULL", "NONE"}


def read_ndx(path: str):
    """Return (rows, notes): rows is a list of (date, close or None)."""
    rows = []
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise SystemExit("ndx.csv is empty")
        names = [h.strip() for h in header]
        try:
            vcol = names.index("NASDAQ100")
        except ValueError:
            vcol = 1
        for rec in reader:
            if not rec or len(rec) <= vcol:
                skipped += 1
                continue
            d = parse_date(rec[0])
            if d is None:
                skipped += 1
                continue
            raw = rec[vcol].strip()
            if raw.upper() in _MISSING:
                rows.append((d, None))
                continue
            try:
                rows.append((d, float(raw)))
            except ValueError:
                rows.append((d, None))
    rows.sort(key=lambda r: r[0])
    return rows, {"ndx_rows": len(rows), "ndx_rows_skipped": skipped}


def read_rf(path: str):
    """Return (rows, notes): rows is a list of (date, RF in per cent)."""
    rows = []
    skipped_date = 0
    skipped_value = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        rfcol = None
        for rec in reader:
            cells = [c.strip() for c in rec]
            if rfcol is None:
                if "RF" in cells:
                    rfcol = cells.index("RF")
                continue
            if not cells or len(cells) <= rfcol:
                skipped_date += 1
                continue
            d = parse_date(cells[0])
            if d is None:
                skipped_date += 1
                continue
            try:
                rows.append((d, float(cells[rfcol])))
            except ValueError:
                skipped_value += 1
    if rfcol is None:
        raise SystemExit("ff5_daily.csv has no header row naming RF")
    rows.sort(key=lambda r: r[0])
    return rows, {
        "rf_rows": len(rows),
        "rf_rows_skipped_nondate": skipped_date,
        "rf_rows_skipped_nonnumeric": skipped_value,
    }


# ---------------------------------------------------------------------------
# Monthly series
# ---------------------------------------------------------------------------

def last_closes(ndx_rows):
    """Map month -> last non-missing close in that month."""
    out = {}
    for d, v in ndx_rows:
        if v is None:
            continue
        out[ym(d)] = v  # rows are sorted, so the last write wins
    return out


def last_complete_month(ndx_rows):
    """The last complete month under the PREREG rule, or None."""
    if not ndx_rows:
        return None
    last_date = ndx_rows[-1][0]
    last_key = ym(last_date)
    if last_date == final_weekday(last_key):
        return last_key
    return prev_month(last_key)


def monthly_rf(rf_rows):
    """Map month -> compounded RF (fraction) over that month's French rows."""
    acc = {}
    for d, pct in rf_rows:
        key = ym(d)
        acc[key] = acc.get(key, 1.0) * (1.0 + pct / 100.0)
    return {k: v - 1.0 for k, v in acc.items()}


def build_months(ndx_rows, rf_rows):
    """Return the list of scored months in order, and bookkeeping notes.

    Each month is a dict with keys ym, r (NDX return), rf, e (excess) and w.
    Months are kept only when the return exists (consecutive calendar months
    both with closes), the month is complete and a French RF exists.
    """
    closes = last_closes(ndx_rows)
    lcm = last_complete_month(ndx_rows)
    rf_by_month = monthly_rf(rf_rows)
    months = []
    dropped_no_rf = 0
    dropped_gap = 0
    for key in sorted(closes):
        if lcm is not None and key > lcm:
            continue
        prior = prev_month(key)
        if prior not in closes:
            dropped_gap += 1
            continue
        r = closes[key] / closes[prior] - 1.0
        if key not in rf_by_month:
            dropped_no_rf += 1
            continue
        rf = rf_by_month[key]
        months.append({
            "ym": key,
            "r": r,
            "rf": rf,
            "e": r - rf,
            "w": 1 if key[1] in WINTER_MONTHS else 0,
        })
    notes = {
        "last_complete_month": ym_str(lcm) if lcm else None,
        "months_with_close": len(closes),
        "months_dropped_no_prior_close": dropped_gap,
        "months_dropped_no_rf": dropped_no_rf,
    }
    return months, notes


# ---------------------------------------------------------------------------
# Regression with Newey-West standard errors
# ---------------------------------------------------------------------------

def _mat2_mul(A, B):
    return [
        [A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]],
        [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]],
    ]


def ols_nw(y, w, lags=NW_LAGS):
    """OLS of y on a constant and the dummy w, with Newey-West (Bartlett) t.

    Returns a dict with n, a, c, a_t, c_t, or n alone with the rest None when
    the regression cannot be scored. Written out in full rather than through a
    library so that an agreement with the first implementation is an agreement
    between two derivations and not two calls of the same routine.
    """
    n = len(y)
    nw = sum(w)
    out = {"n": n, "a": None, "c": None, "a_t": None, "c_t": None}
    if n < 3 or nw == 0 or nw == n:
        return out
    # X'X and its inverse, X = [1, w]
    det = float(n * nw - nw * nw)
    inv = [[nw / det, -nw / det], [-nw / det, n / det]]
    sy = math.fsum(y)
    swy = math.fsum(yi for yi, wi in zip(y, w) if wi)
    a = inv[0][0] * sy + inv[0][1] * swy
    c = inv[1][0] * sy + inv[1][1] * swy
    u = [yi - a - c * wi for yi, wi in zip(y, w)]
    x = [(1.0, float(wi)) for wi in w]
    # Long-run covariance S = G0 + sum_l w_l (G_l + G_l')
    S = [[0.0, 0.0], [0.0, 0.0]]
    terms = [[[], []], [[], []]]
    for t in range(n):
        uu = u[t] * u[t]
        for i in range(2):
            for j in range(2):
                terms[i][j].append(uu * x[t][i] * x[t][j])
    for lag in range(1, lags + 1):
        wl = 1.0 - lag / (lags + 1.0)
        for t in range(lag, n):
            uu = u[t] * u[t - lag]
            for i in range(2):
                for j in range(2):
                    terms[i][j].append(
                        wl * uu * (x[t][i] * x[t - lag][j] + x[t - lag][i] * x[t][j])
                    )
    for i in range(2):
        for j in range(2):
            S[i][j] = math.fsum(terms[i][j])
    V = _mat2_mul(_mat2_mul(inv, S), inv)
    va, vc = V[0][0], V[1][1]
    out["a"] = a
    out["c"] = c
    out["a_t"] = a / math.sqrt(va) if va > 0 else None
    out["c_t"] = c / math.sqrt(vc) if vc > 0 else None
    return out


# ---------------------------------------------------------------------------
# Reported-without-weight statistics
# ---------------------------------------------------------------------------

def mean(xs):
    return math.fsum(xs) / len(xs) if xs else None


def sample_sd(xs):
    n = len(xs)
    if n < 2:
        return None
    m = math.fsum(xs) / n
    return math.sqrt(math.fsum((v - m) ** 2 for v in xs) / (n - 1))


def performance(total, rf):
    """Annual return, volatility, Sharpe over RF and max drawdown."""
    n = len(total)
    if n == 0:
        return {"ann_return": None, "ann_vol": None, "sharpe": None, "max_drawdown": None}
    growth = 1.0
    peak = 1.0
    mdd = 0.0
    for s in total:
        growth *= 1.0 + s
        if growth > peak:
            peak = growth
        dd = growth / peak - 1.0
        if dd < mdd:
            mdd = dd
    ann_return = growth ** (12.0 / n) - 1.0
    sd = sample_sd(total)
    ann_vol = sd * math.sqrt(12.0) if sd is not None else None
    excess = [s - f for s, f in zip(total, rf)]
    sd_x = sample_sd(excess)
    sharpe = None
    if sd_x is not None and sd_x > 0:
        sharpe = math.sqrt(12.0) * mean(excess) / sd_x
    return {
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": mdd,
    }


def winter_beats_summer(months):
    """Share of complete winter/summer pairs where winter compounded higher."""
    by_key = {m["ym"]: m for m in months}
    years = sorted({k[0] for k in by_key})
    beats = 0
    pairs = 0
    for y in years:
        winter_keys = [(y, 11), (y, 12)] + [(y + 1, mm) for mm in (1, 2, 3, 4)]
        summer_keys = [(y + 1, mm) for mm in (5, 6, 7, 8, 9, 10)]
        if not all(k in by_key for k in winter_keys + summer_keys):
            continue
        cw = 1.0
        for k in winter_keys:
            cw *= 1.0 + by_key[k]["r"]
        cs = 1.0
        for k in summer_keys:
            cs *= 1.0 + by_key[k]["r"]
        pairs += 1
        if cw - 1.0 > cs - 1.0:
            beats += 1
    return (beats / pairs if pairs else None), pairs, beats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def regress_block(months):
    res = ols_nw([m["e"] for m in months], [m["w"] for m in months])
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="directory holding ndx.csv and ff5_daily.csv")
    ap.add_argument("--out", required=True, help="directory to write verify.json into")
    args = ap.parse_args(argv)

    ndx_path = os.path.join(args.data, "ndx.csv")
    rf_path = os.path.join(args.data, "ff5_daily.csv")
    for p in (ndx_path, rf_path):
        if not os.path.isfile(p):
            raise SystemExit("missing input: %s" % p)

    ndx_rows, ndx_notes = read_ndx(ndx_path)
    rf_rows, rf_notes = read_rf(rf_path)
    months, build_notes = build_months(ndx_rows, rf_rows)

    oos = [m for m in months if m["ym"] >= OOS_START]
    rep = [m for m in months if m["ym"] <= REPLICATION_END]
    full = list(months)

    oos_reg = regress_block(oos)
    full_reg = regress_block(full)
    rep_reg = regress_block(rep)

    n_oos = len(oos)
    if n_oos < MIN_MONTHS:
        primary = "INSUFFICIENT"
    elif oos_reg["c"] is not None and oos_reg["c_t"] is not None \
            and oos_reg["c"] > 0 and oos_reg["c_t"] >= T_THRESHOLD:
        primary = "PASS"
    else:
        primary = "FAIL"

    winter_e = [m["e"] for m in oos if m["w"] == 1]
    summer_e = [m["e"] for m in oos if m["w"] == 0]
    share, pairs, beats = winter_beats_summer(oos)

    strat_total = [m["r"] if m["w"] == 1 else m["rf"] for m in oos]
    held_total = [m["r"] for m in oos]
    rf_series = [m["rf"] for m in oos]

    result = {
        "n_oos": n_oos,
        "first_oos": ym_str(oos[0]["ym"]) if oos else None,
        "last_oos": ym_str(oos[-1]["ym"]) if oos else None,
        "c": oos_reg["c"],
        "c_t": oos_reg["c_t"],
        "a": oos_reg["a"],
        "mean_winter": mean(winter_e),
        "mean_summer": mean(summer_e),
        "share_winter_beats_summer": share,
        "full": {"n": full_reg["n"], "c": full_reg["c"], "c_t": full_reg["c_t"]},
        "replication": {"n": rep_reg["n"], "c": rep_reg["c"], "c_t": rep_reg["c_t"]},
        "strategy": performance(strat_total, rf_series),
        "held": performance(held_total, rf_series),
        "criteria": {"primary": primary},
        "verdict": primary,
        "choices": CHOICES,
        "aux": {
            "a_t": oos_reg["a_t"],
            "n_winter_oos": len(winter_e),
            "n_summer_oos": len(summer_e),
            "winter_summer_pairs": pairs,
            "winter_summer_pairs_winter_won": beats,
            "full_first": ym_str(full[0]["ym"]) if full else None,
            "full_last": ym_str(full[-1]["ym"]) if full else None,
            "full_a": full_reg["a"],
            "replication_first": ym_str(rep[0]["ym"]) if rep else None,
            "replication_last": ym_str(rep[-1]["ym"]) if rep else None,
            "replication_a": rep_reg["a"],
            "nw_lags": NW_LAGS,
            "t_threshold": T_THRESHOLD,
            "min_months": MIN_MONTHS,
            **ndx_notes,
            **rf_notes,
            **build_notes,
        },
    }

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "verify.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")

    print("verify.py: %s" % out_path)
    print("  OOS %s to %s, n = %d" % (result["first_oos"], result["last_oos"], n_oos))
    print("  c = %s, t = %s, verdict = %s" % (
        _fmt(result["c"]), _fmt(result["c_t"]), primary))
    return 0


def _fmt(v):
    return "null" if v is None else "%.6g" % v


if __name__ == "__main__":
    sys.exit(main())
