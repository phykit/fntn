#!/usr/bin/env python3
"""verify.py: independent second implementation of PREREG.md (gvip_concentration).

Usage: python verify.py --data DIR --out DIR

Reads DIR/bench.csv (columns DATE,GVIP,QQQ,QQQE,RSP,SPY: adjusted closes on SPY
trading days, blank where missing) and writes OUT/verify.json, plus
OUT/verify_months.csv holding the monthly return table the statistics were
computed from, so that a disagreement with the first implementation can be
traced to a month rather than argued about at the coefficient.

Written from PREREG.md and the stated interface alone. run.py, selftest.py, the
results directories and docs/ were not opened (PREREG section 4, disclosure 3).
Every ambiguity met on the way is resolved explicitly and listed under
"choices" in the output, so that a disagreement can be attributed to a reading
rather than to a defect.

Dependencies: Python 3 standard library and numpy. No statsmodels, no pandas:
the estimator is written out in full below so that it can be read against the
PREREG rather than against a library's defaults.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

SERIES = ("GVIP", "QQQ", "QQQE", "RSP", "SPY")
FIRST_MONTH = (2016, 12)       # PREREG section 1: December 2016, GVIP's first full month
NW_LAGS = 3                    # PREREG section 2: Newey-West, Bartlett, L = 3
MIN_MONTHS = 96                # PREREG section 2: INSUFFICIENT below 96 months
MONTHS_PER_YEAR = 12
MISSING_TOKENS = {"", "nan", "na", "n/a", "null", "none"}

CHOICES = [
    "Units: returns are decimal fractions (0.01 is one per cent), not percentages. "
    "a_monthly, b, gvip_minus_qqqe_annual and every half-sample coefficient are in those units.",
    "Daily return for a row is close / close of the immediately preceding row in the file "
    "(rows sorted by DATE), whatever calendar month that preceding row falls in. The PREREG's "
    "'previous month's last close' is read as that preceding row; calendar adjacency of the two "
    "months is not separately enforced.",
    "Monthly return is the product of the daily ratios over the month's rows minus one, computed "
    "day by day as stated rather than as the ratio of the two endpoint closes. The two are "
    "algebraically equal when every day is present; floating point may differ at the 1e-16 level.",
    "A month is used only if every row in it has all five closes AND the row immediately before "
    "its first row exists and has all five closes. A month that fails is dropped, never imputed; "
    "the statistics run on the surviving months as one sequence, so the Newey-West lags are taken "
    "over neighbours in that sequence even where a dropped month sits between them. n_months counts "
    "survivors; first_month and last_month are the first and last survivors.",
    "Months before 2016-12 are never used, even where every close is present.",
    "Last complete month (PREREG section 1): the final calendar month present in the file is kept "
    "only if the file's last DATE equals the last Monday-to-Friday day of that month; market "
    "holidays are not consulted, because the PREREG says 'weekday'. Every earlier month in the "
    "file is complete by the 'file holds a later month's date' limb.",
    "Missing value tokens: an empty or whitespace-only cell, or (case-insensitive) nan, na, n/a, "
    "null, none. A non-finite float is also missing. A non-positive close is an error that aborts "
    "the run rather than a missing value, because an adjusted close cannot be zero or negative.",
    "DATE is parsed as ISO YYYY-MM-DD from the first ten characters of the cell; any time "
    "component is ignored. Duplicate dates abort the run. Column names are matched exactly after "
    "stripping whitespace and a byte-order mark; extra columns are ignored.",
    "OLS with intercept by the normal equations. Newey-West: S = sum_t e_t^2 x_t x_t' + "
    "sum_{l=1..L} (1 - l/(L+1)) sum_{t>l} e_t e_{t-l} (x_t x_{t-l}' + x_{t-l} x_t'), "
    "V = (X'X)^-1 S (X'X)^-1, L = 3, no n/(n-k) or any other small-sample factor. "
    "t = coefficient / sqrt(diagonal of V).",
    "R-squared is the ordinary 1 - SSR/SST with SST about the sample mean of y; not adjusted.",
    "gvip_minus_qqqe_annual = 12 x arithmetic mean of the monthly (GVIP_m - QQQE_m) differences, "
    "no compounding. gvip_minus_qqqe_t is the t of the mean from regressing the differences on a "
    "constant alone with the same Newey-West estimator (L = 3); it equals the t of the annualised "
    "figure because the factor of 12 cancels.",
    "The RSP regression keeps y = GVIP_m - QQQ_m and replaces x with RSP_m - SPY_m over the full "
    "sample, because the PREREG says 'the same regression with x = RSP - SPY'. It is not "
    "GVIP - SPY on RSP - SPY.",
    "Halves: the first floor(n/2) surviving months, then the remaining n - floor(n/2). Each half "
    "is regressed on its own with the same Newey-West estimator; no R-squared is reported for "
    "a half because none was asked for.",
    "Verdict order: INSUFFICIENT when n_months < 96; else CONCENTRATION EXPLAINS when b >= 0.5 "
    "and t(b) >= 2.0 and t(a) > -2.0; else RESIDUAL SHORTFALL when t(a) <= -2.0; else "
    "INDETERMINATE. The two named outcomes are mutually exclusive through t(a), so the order "
    "between them cannot matter. Thresholds are compared exactly, with no tolerance.",
    "When INSUFFICIENT, the regression and the side statistics are still computed and reported "
    "wherever at least three months are available (two parameters plus one degree of freedom); "
    "otherwise the affected fields are null. A verdict of INSUFFICIENT is never read as a "
    "statement about a or b.",
    "A regression whose t-statistics are not finite (a zero Newey-West variance) with n_months "
    ">= 96 aborts the run rather than being mapped onto a verdict.",
]


class DataError(Exception):
    """Raised where the input cannot support the computation; the run refuses rather than guesses."""


# ----------------------------------------------------------------------------
# Reading
# ----------------------------------------------------------------------------

def parse_date(cell: str) -> dt.date:
    text = cell.strip()
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError as exc:
        raise DataError(f"unparseable DATE {cell!r}") from exc


def parse_close(cell: str | None, where: str) -> float | None:
    if cell is None:
        return None
    text = cell.strip()
    if text.lower() in MISSING_TOKENS:
        return None
    try:
        value = float(text)
    except ValueError as exc:
        raise DataError(f"non-numeric close {cell!r} at {where}") from exc
    if not math.isfinite(value):
        return None
    if value <= 0.0:
        raise DataError(f"non-positive close {value!r} at {where}")
    return value


def read_bench(path: str) -> list[tuple[dt.date, dict[str, float | None]]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise DataError(f"{path} is empty")
        header = [h.strip() for h in header]
        index: dict[str, int] = {}
        for name in ("DATE",) + SERIES:
            if name not in header:
                raise DataError(f"column {name} missing from {path}; header is {header}")
            index[name] = header.index(name)
        rows: list[tuple[dt.date, dict[str, float | None]]] = []
        for lineno, record in enumerate(reader, start=2):
            if not record or all(cell.strip() == "" for cell in record):
                continue
            date = parse_date(record[index["DATE"]])
            closes = {
                name: parse_close(record[index[name]] if index[name] < len(record) else "",
                                  f"line {lineno} column {name}")
                for name in SERIES
            }
            rows.append((date, closes))
    if not rows:
        raise DataError(f"{path} holds no data rows")
    rows.sort(key=lambda row: row[0])
    for earlier, later in zip(rows, rows[1:]):
        if earlier[0] == later[0]:
            raise DataError(f"duplicate DATE {later[0].isoformat()} in {path}")
    return rows


# ----------------------------------------------------------------------------
# Months
# ----------------------------------------------------------------------------

def last_weekday_of_month(year: int, month: int) -> dt.date:
    day = dt.date(year, month, calendar.monthrange(year, month)[1])
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    return day


def month_label(key: tuple[int, int]) -> str:
    return f"{key[0]:04d}-{key[1]:02d}"


def build_months(rows):
    """Return (used, excluded, meta).

    used: list of dicts, one per surviving month in date order, with the five
    compounded monthly returns. excluded: list of {month, reason} for every
    calendar month in the file that was not used, so that the count of
    survivors is auditable against the file.
    """
    groups: list[tuple[tuple[int, int], int, int]] = []
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or (rows[i][0].year, rows[i][0].month) != (rows[start][0].year, rows[start][0].month):
            key = (rows[start][0].year, rows[start][0].month)
            groups.append((key, start, i))
            start = i

    last_key = groups[-1][0]
    last_date = rows[-1][0]
    last_complete = last_date == last_weekday_of_month(*last_key)

    used = []
    excluded = []
    for key, s, e in groups:
        label = month_label(key)
        if key < FIRST_MONTH:
            excluded.append({"month": label, "reason": "before_2016-12"})
            continue
        if key == last_key and not last_complete:
            excluded.append({"month": label, "reason": "last_month_incomplete",
                             "last_date": last_date.isoformat(),
                             "last_weekday": last_weekday_of_month(*last_key).isoformat()})
            continue
        if s == 0:
            excluded.append({"month": label, "reason": "no_prior_row"})
            continue
        prior = rows[s - 1][1]
        missing_prior = [name for name in SERIES if prior[name] is None]
        if missing_prior:
            excluded.append({"month": label, "reason": "prior_close_missing",
                             "prior_date": rows[s - 1][0].isoformat(), "series": missing_prior})
            continue
        missing_days = [f"{rows[i][0].isoformat()}:{name}" for i in range(s, e)
                        for name in SERIES if rows[i][1][name] is None]
        if missing_days:
            excluded.append({"month": label, "reason": "close_missing", "cells": missing_days})
            continue
        returns = {}
        for name in SERIES:
            growth = 1.0
            for i in range(s, e):
                growth *= rows[i][1][name] / rows[i - 1][1][name]
            returns[name] = growth - 1.0
        used.append({
            "month": label,
            "prior_date": rows[s - 1][0].isoformat(),
            "first_date": rows[s][0].isoformat(),
            "last_date": rows[e - 1][0].isoformat(),
            "n_days": e - s,
            **returns,
        })

    meta = {
        "n_rows": len(rows),
        "first_date": rows[0][0].isoformat(),
        "last_date": last_date.isoformat(),
        "last_month_in_file": month_label(last_key),
        "last_month_complete": last_complete,
        "months_in_file": len(groups),
    }
    return used, excluded, meta


# ----------------------------------------------------------------------------
# Estimator
# ----------------------------------------------------------------------------

def ols_newey_west(y: np.ndarray, X: np.ndarray, lags: int):
    """OLS coefficients with Newey-West (Bartlett) standard errors, no small-sample correction.

    Returns None where the sample cannot carry the regression (n <= k), so that
    the caller records a null rather than a number.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    n, k = X.shape
    if n <= k:
        return None
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    scores = X * resid[:, None]
    meat = scores.T @ scores
    for lag in range(1, lags + 1):
        if lag >= n:
            break
        weight = 1.0 - lag / (lags + 1.0)
        gamma = scores[lag:].T @ scores[:-lag]
        meat = meat + weight * (gamma + gamma.T)
    cov = xtx_inv @ meat @ xtx_inv
    variances = np.diag(cov)
    with np.errstate(divide="ignore", invalid="ignore"):
        se = np.sqrt(variances)
        t = beta / se
    ssr = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ssr / sst if sst > 0.0 else float("nan")
    return {"beta": beta, "se": se, "t": t, "r2": r2, "n": n}


def as_float(value) -> float | None:
    value = float(value)
    return value if math.isfinite(value) else None


def regress_with_intercept(y, x, lags: int) -> dict:
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    X = np.column_stack([np.ones(len(y)), x])
    fit = ols_newey_west(y, X, lags)
    if fit is None:
        return {"a_monthly": None, "a_t": None, "b": None, "b_t": None, "r2": None, "n": int(len(y))}
    return {
        "a_monthly": as_float(fit["beta"][0]),
        "a_t": as_float(fit["t"][0]),
        "b": as_float(fit["beta"][1]),
        "b_t": as_float(fit["t"][1]),
        "r2": as_float(fit["r2"]),
        "n": int(fit["n"]),
    }


def mean_with_nw_t(d, lags: int) -> tuple[float | None, float | None]:
    d = np.asarray(d, dtype=float)
    X = np.ones((len(d), 1))
    fit = ols_newey_west(d, X, lags)
    if fit is None:
        return None, None
    return as_float(fit["beta"][0]), as_float(fit["t"][0])


def verdict_for(n_months: int, a_t, b, b_t) -> str:
    if n_months < MIN_MONTHS:
        return "INSUFFICIENT"
    if a_t is None or b is None or b_t is None:
        raise DataError("regression statistics are not finite with n_months >= 96; refusing to map onto a verdict")
    if b >= 0.5 and b_t >= 2.0 and a_t > -2.0:
        return "CONCENTRATION EXPLAINS"
    if a_t <= -2.0:
        return "RESIDUAL SHORTFALL"
    return "INDETERMINATE"


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def compute(rows) -> tuple[dict, list[dict]]:
    used, excluded, meta = build_months(rows)
    n = len(used)
    gvip = np.array([m["GVIP"] for m in used])
    qqq = np.array([m["QQQ"] for m in used])
    qqqe = np.array([m["QQQE"] for m in used])
    rsp = np.array([m["RSP"] for m in used])
    spy = np.array([m["SPY"] for m in used])

    y = gvip - qqq
    x_qqqe = qqqe - qqq
    x_rsp = rsp - spy
    d_qqqe = gvip - qqqe

    main = regress_with_intercept(y, x_qqqe, NW_LAGS)
    verdict = verdict_for(n, main["a_t"], main["b"], main["b_t"])

    mean_d, t_d = mean_with_nw_t(d_qqqe, NW_LAGS)
    annual = MONTHS_PER_YEAR * mean_d if mean_d is not None else None

    rsp_fit = regress_with_intercept(y, x_rsp, NW_LAGS)

    half = n // 2
    halves = []
    for lo, hi in ((0, half), (half, n)):
        if hi > lo:
            fit = regress_with_intercept(y[lo:hi], x_qqqe[lo:hi], NW_LAGS)
            halves.append({
                "first_month": used[lo]["month"],
                "last_month": used[hi - 1]["month"],
                "n_months": hi - lo,
                "a_monthly": fit["a_monthly"],
                "a_t": fit["a_t"],
                "b": fit["b"],
                "b_t": fit["b_t"],
            })
        else:
            halves.append({"first_month": None, "last_month": None, "n_months": 0,
                           "a_monthly": None, "a_t": None, "b": None, "b_t": None})

    result = {
        "n_months": n,
        "first_month": used[0]["month"] if n else None,
        "last_month": used[-1]["month"] if n else None,
        "a_monthly": main["a_monthly"],
        "a_t": main["a_t"],
        "b": main["b"],
        "b_t": main["b_t"],
        "r2": main["r2"],
        "verdict": verdict,
        "gvip_minus_qqqe_annual": annual,
        "gvip_minus_qqqe_t": t_d,
        "rsp": {
            "a_monthly": rsp_fit["a_monthly"],
            "a_t": rsp_fit["a_t"],
            "b": rsp_fit["b"],
            "b_t": rsp_fit["b_t"],
            "r2": rsp_fit["r2"],
        },
        "halves": halves,
        "choices": CHOICES,
        "parameters": {
            "first_month_allowed": month_label(FIRST_MONTH),
            "newey_west_lags": NW_LAGS,
            "min_months": MIN_MONTHS,
            "months_per_year": MONTHS_PER_YEAR,
        },
        "input": meta,
        "excluded_months": excluded,
        "implementation": "verify.py, written from PREREG.md alone",
    }
    return result, used


def write_months_csv(path: str, used: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["month", "prior_date", "first_date", "last_date", "n_days",
                         *SERIES, "y_gvip_minus_qqq", "x_qqqe_minus_qqq", "x_rsp_minus_spy", "d_gvip_minus_qqqe"])
        for m in used:
            writer.writerow([
                m["month"], m["prior_date"], m["first_date"], m["last_date"], m["n_days"],
                *(repr(m[name]) for name in SERIES),
                repr(m["GVIP"] - m["QQQ"]), repr(m["QQQE"] - m["QQQ"]),
                repr(m["RSP"] - m["SPY"]), repr(m["GVIP"] - m["QQQE"]),
            ])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True, help="directory holding bench.csv")
    parser.add_argument("--out", required=True, help="directory to write verify.json into")
    args = parser.parse_args(argv)

    bench = os.path.join(args.data, "bench.csv")
    if not os.path.isfile(bench):
        print(f"verify.py: {bench} not found", file=sys.stderr)
        return 2
    try:
        rows = read_bench(bench)
        result, used = compute(rows)
    except DataError as exc:
        print(f"verify.py: refusing to score: {exc}", file=sys.stderr)
        return 3

    result["input"]["path"] = os.path.abspath(bench)
    os.makedirs(args.out, exist_ok=True)
    out_json = os.path.join(args.out, "verify.json")
    with open(out_json, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    write_months_csv(os.path.join(args.out, "verify_months.csv"), used)

    print(f"verify.py: {result['n_months']} months {result['first_month']} to {result['last_month']}; "
          f"a = {result['a_monthly']} (t {result['a_t']}), b = {result['b']} (t {result['b_t']}), "
          f"r2 = {result['r2']}; verdict {result['verdict']}")
    print(f"verify.py: wrote {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
