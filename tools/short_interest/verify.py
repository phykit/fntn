#!/usr/bin/env python3
"""Independent second implementation of the short-interest pre-registered test.

Written from ``tools/short_interest/PREREG.md`` and the clarifications that form
part of the specification, and from nothing else: ``run.py``, ``selftest.py``,
``fetch.py``, every ``results/`` directory and ``docs/`` were not opened.  The
point of a second implementation is that agreement between ``results.json`` and
``verify.json`` is then evidence about the arithmetic rather than about a shared
source; a shared source would make agreement worthless.

Usage::

    python verify.py --data DIR --out DIR

Inputs under ``--data DIR``:

``sii.csv``
    a header row then one row per month; the first column is the month
    (``YYYYMM``, ``YYYY-MM``, ``YYYY-MM-DD`` or ``M/D/YYYY``) and the column
    whose header contains ``SII`` (case-insensitive) holds the published short
    interest index, already standardised and linearly detrended on the authors'
    full sample.
``ndx.csv``
    FRED ``NASDAQ100``: columns ``observation_date,NASDAQ100``, daily, blank
    (or ``.``) where missing.
``ff5_daily.csv``
    columns ``DATE,Mkt-RF,SMB,HML,RMW,CMA,RF``, per cent, daily.

Output: ``verify.json`` under ``--out DIR``.

Where the specification left a choice, the choice taken is recorded in the
``choices`` list of the output so that a disagreement with ``results.json`` can
be traced to a named decision rather than to a hidden one.  Where an input is
malformed this script raises; it does not substitute a working value for a
broken one.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys

import numpy as np

# Parameters fixed by the pre-registration and its clarifications.
MIN_MONTHS = 240          # PREREG §2: no regression on fewer aligned months
INITIAL_WINDOW = 120      # clarification 4: first 120 aligned months estimate
SHIFT_MARGIN = 12         # clarification 3: rotations k = 12 .. n - 12
NW_LAGS = 3               # clarifications 4 and the nw_t key: Bartlett, L = 3
P_SHIFT_MAX = 0.025       # clarification 3
CW_T_MIN = 1.65           # clarification 4

# A choice, not a parameter of the specification: an OLS residual on a constant
# and a trend is identically zero with two observations and undefined with one,
# so the recursive residual is taken only from the third observation onwards,
# where the fit has at least one degree of freedom.
MIN_DETREND_OBS = 3

MISSING_TOKENS = {"", ".", "na", "n/a", "nan", "null", "none"}

CHOICES = [
    "Recursive detrend: the time index is the calendar month count "
    "(year * 12 + month), so a gap in sii.csv is a gap in time rather than a "
    "shift of row index; for a contiguous series this is identical to the row "
    "index.",
    "Recursive detrend: a residual is taken only where the fit has at least "
    "one degree of freedom, i.e. from the third observation of the series; "
    "the first two months carry no signal (their residual is identically zero "
    "or undefined) and are excluded.",
    "Recursive detrend: the published index is used as supplied, on the "
    "clarification that an affine function of time leaves the recursive "
    "residual unchanged; missing SII values (blank, '.', 'NA') are dropped and "
    "a duplicated month is an error.",
    "SII column: a header equal to 'SII' (case-insensitive, stripped) is "
    "preferred; otherwise the first header containing 'sii'.",
    "NDX_t is the last non-missing FRED observation dated inside calendar "
    "month t, whatever day of the month that is; a partially covered final "
    "month is used as it stands.",
    "RF_(t+1) is the compounded daily French RF over every daily row dated "
    "inside calendar month t+1; log(1 + RF) is formed as the sum of the daily "
    "log(1 + rf / 100); a month with no RF row is unavailable, a partially "
    "covered month is used as it stands.",
    "Month t+1 is the next calendar month; a calendar month with no NDX "
    "observation breaks the pair on either side of it.",
    "Aligned sample: every month t with x_t, NDX_t, NDX_(t+1) and RF_(t+1) "
    "available, in month order; first_signal_month and last_signal_month are "
    "the first and last such t (signal months, not return months).",
    "Primary: OLS of y_(t+1) on x_t with intercept; rotations np.roll(x, k) "
    "for k = 12 .. n-12 inclusive (n_shifts = n - 23); a rotation counts if "
    "its slope <= b; p = (1 + count) / (1 + n_shifts).",
    "Newey-West (nw_t and the Clark-West t): Bartlett weights 1 - j/(L+1), "
    "L = 3, no small-sample correction; applied to the OLS moment conditions "
    "for b and to the demeaned Clark-West loss for its mean.",
    "Secondary: forecast for aligned pair i (0-based, i >= 120) is estimated "
    "on pairs 0..i-1; the benchmark is the mean of y over pairs 0..i-1; "
    "n_oos_forecasts = n - 120.",
    "INSUFFICIENT (n < 240): per PREREG §2 no regression is run; every "
    "statistic is null and both criteria are null, which may not be read as "
    "a pass.",
    "b_per_sd = b * sd(x, ddof=1); r2_in_sample is 1 - SSE/SST of the primary "
    "regression.",
]


# ----------------------------------------------------------------------------
# Date handling.  Months are carried as an integer index year * 12 + (month - 1)
# so that t + 1 is the next calendar month by construction.
# ----------------------------------------------------------------------------

def _clean(s: str) -> str:
    s = s.strip().strip('"').strip("'").strip()
    if re.fullmatch(r"\d+\.0+", s):      # a month written by a float-typed column
        s = s.split(".")[0]
    return s


def parse_month(raw: str) -> int:
    """Month index from YYYYMM, YYYYMMDD, YYYY-MM, YYYY-MM-DD or M/D/YYYY."""
    s = _clean(raw)
    if re.fullmatch(r"\d{6}", s):
        y, m = int(s[:4]), int(s[4:6])
    elif re.fullmatch(r"\d{8}", s):
        y, m = int(s[:4]), int(s[4:6])
    else:
        mo = re.fullmatch(r"(\d{4})[-/](\d{1,2})(?:[-/](\d{1,2}))?", s)
        if mo:
            y, m = int(mo.group(1)), int(mo.group(2))
        else:
            mo = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
            if not mo:
                raise ValueError(f"unrecognised month spelling: {raw!r}")
            y, m = int(mo.group(3)), int(mo.group(1))
    if not (1 <= m <= 12) or y < 1800:
        raise ValueError(f"month out of range: {raw!r}")
    return y * 12 + (m - 1)


def parse_day(raw: str) -> tuple[int, int, int]:
    """(year, month, day) from YYYYMMDD, YYYY-MM-DD or M/D/YYYY."""
    s = _clean(raw)
    if re.fullmatch(r"\d{8}", s):
        y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
    else:
        mo = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
        if mo:
            y, m, d = int(mo.group(1)), int(mo.group(2)), int(mo.group(3))
        else:
            mo = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
            if not mo:
                raise ValueError(f"unrecognised date spelling: {raw!r}")
            y, m, d = int(mo.group(3)), int(mo.group(1)), int(mo.group(2))
    if not (1 <= m <= 12) or not (1 <= d <= 31) or y < 1800:
        raise ValueError(f"date out of range: {raw!r}")
    return y, m, d


def month_index_of_day(ymd: tuple[int, int, int]) -> int:
    y, m, _ = ymd
    return y * 12 + (m - 1)


def month_label(idx: int) -> str:
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def _is_missing(s: str) -> bool:
    return _clean(s).lower() in MISSING_TOKENS


# ----------------------------------------------------------------------------
# Readers.  Each returns plain Python structures and raises on malformed input.
# ----------------------------------------------------------------------------

def _read_rows(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [row for row in csv.reader(fh)]


def _find_header(rows: list[list[str]], required: list[str]) -> int:
    """Index of the first row whose cleaned, lower-cased fields include every
    name in ``required``.  Tolerates preamble lines above the header."""
    want = [r.lower() for r in required]
    for i, row in enumerate(rows):
        fields = [_clean(c).lower() for c in row]
        if all(w in fields for w in want):
            return i
    raise ValueError(f"no header row containing {required} found")


def read_sii(path: str) -> tuple[np.ndarray, np.ndarray, dict]:
    rows = _read_rows(path)
    if not rows:
        raise ValueError("sii.csv is empty")
    header = [_clean(c) for c in rows[0]]
    lower = [h.lower() for h in header]
    if "sii" in lower:
        col = lower.index("sii")
    else:
        cands = [i for i, h in enumerate(lower) if "sii" in h]
        if not cands:
            raise ValueError("sii.csv has no column whose header contains 'SII'")
        col = cands[0]
    months: list[int] = []
    values: list[float] = []
    n_blank = 0
    seen: set[int] = set()
    for row in rows[1:]:
        if not row or all(_clean(c) == "" for c in row):
            continue
        if len(row) <= col:
            raise ValueError(f"sii.csv row too short: {row!r}")
        if _is_missing(row[col]):
            n_blank += 1
            continue
        m = parse_month(row[0])
        if m in seen:
            raise ValueError(f"sii.csv has a duplicated month: {month_label(m)}")
        seen.add(m)
        months.append(m)
        values.append(float(_clean(row[col])))
    if not months:
        raise ValueError("sii.csv holds no SII observations")
    order = np.argsort(np.asarray(months, dtype=np.int64), kind="stable")
    mo = np.asarray(months, dtype=np.int64)[order]
    va = np.asarray(values, dtype=np.float64)[order]
    info = {
        "sii_column": header[col],
        "n_rows_with_value": int(len(mo)),
        "n_rows_blank": int(n_blank),
        "first_month": month_label(int(mo[0])),
        "last_month": month_label(int(mo[-1])),
        "n_calendar_gaps": int((mo[-1] - mo[0] + 1) - len(mo)),
    }
    return mo, va, info


def read_ndx_month_end(path: str) -> tuple[dict[int, float], dict]:
    """Last non-missing NASDAQ100 observation dated inside each calendar month."""
    rows = _read_rows(path)
    h = _find_header(rows, ["observation_date", "NASDAQ100"])
    header = [_clean(c).lower() for c in rows[h]]
    dcol = header.index("observation_date")
    vcol = header.index("nasdaq100")
    last: dict[int, tuple[tuple[int, int, int], float]] = {}
    n_obs = 0
    n_missing = 0
    for row in rows[h + 1:]:
        if not row or all(_clean(c) == "" for c in row):
            continue
        if len(row) <= max(dcol, vcol):
            raise ValueError(f"ndx.csv row too short: {row!r}")
        if _is_missing(row[vcol]):
            n_missing += 1
            continue
        ymd = parse_day(row[dcol])
        v = float(_clean(row[vcol]))
        if not math.isfinite(v) or v <= 0:
            raise ValueError(f"ndx.csv has a non-positive level on {row[dcol]!r}")
        n_obs += 1
        mi = month_index_of_day(ymd)
        if mi not in last or ymd > last[mi][0]:
            last[mi] = (ymd, v)
    if not last:
        raise ValueError("ndx.csv holds no NASDAQ100 observations")
    out = {mi: v for mi, (_, v) in last.items()}
    ks = sorted(out)
    info = {
        "n_daily_obs": int(n_obs),
        "n_daily_missing": int(n_missing),
        "n_months": int(len(ks)),
        "first_month": month_label(ks[0]),
        "last_month": month_label(ks[-1]),
        "last_obs_date": "%04d-%02d-%02d" % last[ks[-1]][0],
    }
    return out, info


def read_rf_month_log(path: str) -> tuple[dict[int, float], dict]:
    """sum over the month of log(1 + rf_d / 100), i.e. log(1 + RF_month) where
    RF_month is the compounded daily French RF in decimals."""
    rows = _read_rows(path)
    h = _find_header(rows, ["DATE", "RF"])
    header = [_clean(c).lower() for c in rows[h]]
    dcol = header.index("date")
    rcol = header.index("rf")
    acc: dict[int, float] = {}
    days: dict[int, int] = {}
    n_skipped = 0
    for row in rows[h + 1:]:
        if not row or all(_clean(c) == "" for c in row):
            continue
        if len(row) <= max(dcol, rcol):
            n_skipped += 1
            continue
        try:
            ymd = parse_day(row[dcol])
        except ValueError:
            # The French files sometimes carry annual blocks below the daily
            # rows, keyed by a four-digit year; those are not daily rows.
            n_skipped += 1
            continue
        if _is_missing(row[rcol]):
            n_skipped += 1
            continue
        rf = float(_clean(row[rcol]))
        if rf <= -100.0:
            raise ValueError(f"ff5_daily.csv has an impossible RF on {row[dcol]!r}")
        mi = month_index_of_day(ymd)
        acc[mi] = acc.get(mi, 0.0) + math.log1p(rf / 100.0)
        days[mi] = days.get(mi, 0) + 1
    if not acc:
        raise ValueError("ff5_daily.csv holds no RF observations")
    ks = sorted(acc)
    info = {
        "n_months": int(len(ks)),
        "n_rows_skipped": int(n_skipped),
        "first_month": month_label(ks[0]),
        "last_month": month_label(ks[-1]),
        "days_in_last_month": int(days[ks[-1]]),
    }
    return acc, info


# ----------------------------------------------------------------------------
# Arithmetic.  Centred closed forms are used for the one-regressor fits because
# they are exact and numerically stable; the Newey-West covariance is formed
# from the moment conditions in the textbook way.
# ----------------------------------------------------------------------------

def ols1(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Intercept and slope of y on x with a constant."""
    xm = x.mean()
    ym = y.mean()
    dx = x - xm
    sxx = float(dx @ dx)
    if sxx <= 0.0:
        raise ValueError("regressor has zero variance; slope undefined")
    b = float(dx @ (y - ym)) / sxx
    a = float(ym - b * xm)
    return a, b


def newey_west_cov(X: np.ndarray, e: np.ndarray, lags: int) -> np.ndarray:
    """HAC covariance of OLS coefficients, Bartlett kernel, no small-sample
    correction: (X'X)^-1 S (X'X)^-1 with S the weighted sum of the
    autocovariances of X_i e_i."""
    U = X * e[:, None]
    S = U.T @ U
    for j in range(1, lags + 1):
        w = 1.0 - j / (lags + 1.0)
        G = U[j:].T @ U[:-j]
        S = S + w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    return XtX_inv @ S @ XtX_inv


def recursive_detrend(months: np.ndarray, values: np.ndarray) -> np.ndarray:
    """x_t: residual at t of an OLS of SII on a constant and the calendar month
    index over observations 1..t.  NaN where the fit has no degree of freedom."""
    n = len(values)
    u = months.astype(np.float64)
    out = np.full(n, np.nan)
    for t in range(n):
        if t + 1 < MIN_DETREND_OBS:
            continue
        uu = u[: t + 1]
        ss = values[: t + 1]
        um = uu.mean()
        sm = ss.mean()
        du = uu - um
        beta = float(du @ (ss - sm)) / float(du @ du)
        out[t] = (ss[t] - sm) - beta * (uu[t] - um)
    return out


def align(sii_months, x_all, ndx_last, rf_log):
    months, x, y = [], [], []
    dropped = {"x_undefined": 0, "ndx_t": 0, "ndx_t1": 0, "rf_t1": 0}
    for t, xt in zip(sii_months.tolist(), x_all.tolist()):
        if not math.isfinite(xt):
            dropped["x_undefined"] += 1
            continue
        if t not in ndx_last:
            dropped["ndx_t"] += 1
            continue
        if (t + 1) not in ndx_last:
            dropped["ndx_t1"] += 1
            continue
        if (t + 1) not in rf_log:
            dropped["rf_t1"] += 1
            continue
        months.append(t)
        x.append(xt)
        y.append(math.log(ndx_last[t + 1] / ndx_last[t]) - rf_log[t + 1])
    return (np.asarray(months, dtype=np.int64),
            np.asarray(x, dtype=np.float64),
            np.asarray(y, dtype=np.float64),
            dropped)


def primary_test(x: np.ndarray, y: np.ndarray) -> dict:
    n = len(x)
    a, b = ols1(x, y)
    resid = y - (a + b * x)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / sst if sst > 0 else float("nan")
    X = np.column_stack([np.ones(n), x])
    V = newey_west_cov(X, resid, NW_LAGS)
    nw_t = b / math.sqrt(V[1, 1]) if V[1, 1] > 0 else float("nan")

    ks = list(range(SHIFT_MARGIN, n - SHIFT_MARGIN + 1))
    count = 0
    for k in ks:
        _, bk = ols1(np.roll(x, k), y)
        if bk <= b:
            count += 1
    p = (1 + count) / (1 + len(ks))
    sd_x = float(np.std(x, ddof=1))
    return {
        "b": b,
        "b_per_sd": b * sd_x,
        "p_shift": p,
        "n_shifts": len(ks),
        "n_shifts_le": count,
        "nw_t": nw_t,
        "r2_in_sample": r2,
        "passed": bool(b < 0.0 and p <= P_SHIFT_MAX),
    }


def secondary_test(x: np.ndarray, y: np.ndarray) -> dict:
    n = len(x)
    f = []
    sse_model = 0.0
    sse_mean = 0.0
    for i in range(INITIAL_WINDOW, n):
        a, b = ols1(x[:i], y[:i])
        yhat = a + b * x[i]
        ybar = float(y[:i].mean())
        em = y[i] - yhat
        eb = y[i] - ybar
        sse_model += em * em
        sse_mean += eb * eb
        f.append(eb * eb - (em * em - (ybar - yhat) ** 2))
    m = len(f)
    if m == 0:
        return {"r2_oos": None, "clark_west_t": None, "n_oos_forecasts": 0,
                "passed": None}
    r2_oos = 1.0 - sse_model / sse_mean if sse_mean > 0 else float("nan")
    fa = np.asarray(f)
    V = newey_west_cov(np.ones((m, 1)), fa - fa.mean(), NW_LAGS)
    se = math.sqrt(V[0, 0]) if V[0, 0] > 0 else float("nan")
    cw_t = float(fa.mean()) / se if se > 0 else float("nan")
    return {
        "r2_oos": r2_oos,
        "clark_west_t": cw_t,
        "n_oos_forecasts": m,
        "passed": bool(r2_oos > 0.0 and cw_t >= CW_T_MIN),
    }


# ----------------------------------------------------------------------------
# Driver.
# ----------------------------------------------------------------------------

def _json_safe(v):
    if isinstance(v, (np.floating, float)):
        v = float(v)
        return v if math.isfinite(v) else None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, dict):
        return {k: _json_safe(w) for k, w in v.items()}
    if isinstance(v, (list, tuple)):
        return [_json_safe(w) for w in v]
    return v


def run(data_dir: str) -> dict:
    sii_months, sii_vals, sii_info = read_sii(os.path.join(data_dir, "sii.csv"))
    ndx_last, ndx_info = read_ndx_month_end(os.path.join(data_dir, "ndx.csv"))
    rf_log, rf_info = read_rf_month_log(os.path.join(data_dir, "ff5_daily.csv"))

    x_all = recursive_detrend(sii_months, sii_vals)
    months, x, y, dropped = align(sii_months, x_all, ndx_last, rf_log)
    n = int(len(x))

    out = {
        "n": n,
        "first_signal_month": month_label(int(months[0])) if n else None,
        "last_signal_month": month_label(int(months[-1])) if n else None,
        "b": None,
        "b_per_sd": None,
        "p_shift": None,
        "n_shifts": None,
        "nw_t": None,
        "r2_in_sample": None,
        "r2_oos": None,
        "clark_west_t": None,
        "n_oos_forecasts": None,
        "criteria": {"primary": None, "oos": None},
        "verdict": None,
        "choices": list(CHOICES),
        "parameters": {
            "min_months": MIN_MONTHS,
            "initial_window": INITIAL_WINDOW,
            "shift_margin": SHIFT_MARGIN,
            "nw_lags": NW_LAGS,
            "p_shift_max": P_SHIFT_MAX,
            "cw_t_min": CW_T_MIN,
            "min_detrend_obs": MIN_DETREND_OBS,
        },
        "diagnostics": {
            "sii": sii_info,
            "ndx": ndx_info,
            "rf": rf_info,
            "months_dropped": dropped,
            "sd_x": float(np.std(x, ddof=1)) if n > 1 else None,
            "mean_y": float(y.mean()) if n else None,
            "sd_y": float(np.std(y, ddof=1)) if n > 1 else None,
        },
    }

    if n < MIN_MONTHS:
        # PREREG §2: no regression is run on a shorter series.  The nulls above
        # stand; they are a refusal with a reason, not a result of zero.
        out["verdict"] = "INSUFFICIENT"
        out["diagnostics"]["insufficient_reason"] = (
            f"aligned sample of {n} months is below the pre-registered floor "
            f"of {MIN_MONTHS}; no regression run")
        return _json_safe(out)

    prim = primary_test(x, y)
    sec = secondary_test(x, y)
    out.update({
        "b": prim["b"],
        "b_per_sd": prim["b_per_sd"],
        "p_shift": prim["p_shift"],
        "n_shifts": prim["n_shifts"],
        "nw_t": prim["nw_t"],
        "r2_in_sample": prim["r2_in_sample"],
        "r2_oos": sec["r2_oos"],
        "clark_west_t": sec["clark_west_t"],
        "n_oos_forecasts": sec["n_oos_forecasts"],
        "criteria": {"primary": prim["passed"], "oos": sec["passed"]},
    })
    out["diagnostics"]["n_shifts_with_slope_le_b"] = prim["n_shifts_le"]
    if prim["passed"] and sec["passed"]:
        out["verdict"] = "PASS"
    elif prim["passed"]:
        out["verdict"] = "WEAK"
    else:
        out["verdict"] = "FAIL"
    return _json_safe(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="directory holding sii.csv, "
                    "ndx.csv and ff5_daily.csv")
    ap.add_argument("--out", required=True, help="directory to write verify.json")
    args = ap.parse_args(argv)

    result = run(args.data)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "verify.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, allow_nan=False)
        fh.write("\n")

    summary = {k: result[k] for k in (
        "n", "first_signal_month", "last_signal_month", "b", "b_per_sd",
        "p_shift", "n_shifts", "nw_t", "r2_in_sample", "r2_oos",
        "clark_west_t", "n_oos_forecasts", "criteria", "verdict")}
    print(json.dumps(summary, indent=2))
    print(f"written {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
