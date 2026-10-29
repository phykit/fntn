#!/usr/bin/env python3
"""Independent second implementation of tools/volmom/PREREG.md.

Written from the pre-registration alone, as its disclosure 3 requires: run.py,
selftest.py and the results directory were not opened. Only numpy and the
standard library are used, so that the two implementations share as little
machinery as possible. Every ambiguity met in the pre-registration is resolved
here and listed under the ``choices`` key of verify.json, so that a
disagreement with the first implementation can be attributed to a reading
rather than to a defect.

Usage: python verify.py --data DIR --out DIR

Inputs, both under --data:
  mom_daily.csv  columns DATE,Mom; ISO dates; Mom in per cent; one row per
                 trading day (the French daily momentum factor).
  bench.csv      columns DATE,MTUM,SPY; adjusted closes on SPY trading days;
                 blank where missing (MTUM is blank before April 2013).

Output: DIR/verify.json.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Pre-registered constants (PREREG.md sections 2 and 3).
SEED = 20261029
N_BOOT = 10_000
BLOCK = 12
WINDOW = 126
TARGET_ANNUAL_VOL = 0.12
S_T = TARGET_ANNUAL_VOL / math.sqrt(12.0)
NW_LAGS = 3
IS_END: Tuple[int, int] = (2015, 12)
OOS_START: Tuple[int, int] = (2016, 1)
MIN_MONTHS = 96
T_CRIT = 2.0
SHARPE_MULT = 1.2
P_CRIT = 0.05
COST_PER_UNIT_TURNOVER = 0.0020  # 20 bp: two legs at 10 bp each
N_WORST = 5

MonthKey = Tuple[int, int]


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_strictly_increasing(dates: Sequence[dt.date], path: str) -> None:
    for i in range(1, len(dates)):
        if dates[i] <= dates[i - 1]:
            raise ValueError(
                f"{path}: dates not strictly increasing at row {i + 1} "
                f"({dates[i - 1]} then {dates[i]})"
            )


def read_mom(path: str) -> Tuple[List[dt.date], np.ndarray]:
    """DATE,Mom in per cent -> dates and daily decimal returns r_d = Mom / 100."""
    dates: List[dt.date] = []
    vals: List[float] = []
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        names = [c.strip() for c in (rdr.fieldnames or [])]
        if "DATE" not in names or "Mom" not in names:
            raise ValueError(f"{path}: expected columns DATE,Mom; found {rdr.fieldnames}")
        for row in rdr:
            row = {k.strip(): (v or "") for k, v in row.items() if k is not None}
            s = row["DATE"].strip()
            if not s:
                continue
            v = row["Mom"].strip()
            if v == "":
                # Rule 3 of the project: refuse rather than substitute.
                raise ValueError(f"{path}: blank Mom on {s}")
            dates.append(dt.date.fromisoformat(s))
            vals.append(float(v) / 100.0)
    if not dates:
        raise ValueError(f"{path}: no rows")
    _check_strictly_increasing(dates, path)
    return dates, np.asarray(vals, dtype=float)


def read_bench(path: str) -> Tuple[List[dt.date], np.ndarray, np.ndarray]:
    """DATE,MTUM,SPY adjusted closes -> dates, MTUM, SPY (NaN where blank)."""
    dates: List[dt.date] = []
    mt: List[float] = []
    sp: List[float] = []
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        names = [c.strip() for c in (rdr.fieldnames or [])]
        for col in ("DATE", "MTUM", "SPY"):
            if col not in names:
                raise ValueError(f"{path}: expected columns DATE,MTUM,SPY; found {rdr.fieldnames}")
        for row in rdr:
            row = {k.strip(): (v or "") for k, v in row.items() if k is not None}
            s = row["DATE"].strip()
            if not s:
                continue
            dates.append(dt.date.fromisoformat(s))
            for col, dest in (("MTUM", mt), ("SPY", sp)):
                v = row[col].strip()
                if v == "":
                    dest.append(math.nan)
                else:
                    x = float(v)
                    if not (x > 0.0):
                        raise ValueError(f"{path}: non-positive {col} close on {s}: {v}")
                    dest.append(x)
    if not dates:
        raise ValueError(f"{path}: no rows")
    _check_strictly_increasing(dates, path)
    return dates, np.asarray(mt, dtype=float), np.asarray(sp, dtype=float)


# --------------------------------------------------------------------------
# Calendar
# --------------------------------------------------------------------------

def month_key(d: dt.date) -> MonthKey:
    return (d.year, d.month)


def fmt_month(key: MonthKey) -> str:
    return f"{key[0]:04d}-{key[1]:02d}"


def last_weekday_of_month(key: MonthKey) -> dt.date:
    y, m = key
    first_of_next = dt.date(y + (m == 12), (m % 12) + 1, 1)
    d = first_of_next - dt.timedelta(days=1)
    while d.weekday() > 4:  # 5 = Saturday, 6 = Sunday
        d -= dt.timedelta(days=1)
    return d


def month_is_complete(key: MonthKey, last_date_in_file: dt.date) -> bool:
    """PREREG section 2: complete if the file holds a date in a later month, or
    its last date is the final weekday of that month."""
    last_key = month_key(last_date_in_file)
    if key < last_key:
        return True
    if key == last_key:
        return last_date_in_file == last_weekday_of_month(key)
    return False


def next_month(key: MonthKey) -> MonthKey:
    y, m = key
    return (y + (m == 12), (m % 12) + 1)


def month_slices(dates: Sequence[dt.date]) -> List[Tuple[MonthKey, int, int]]:
    """Contiguous [start, end) row ranges per calendar month, in file order."""
    out: List[Tuple[MonthKey, int, int]] = []
    if not dates:
        return out
    start = 0
    for i in range(1, len(dates) + 1):
        if i == len(dates) or month_key(dates[i]) != month_key(dates[start]):
            out.append((month_key(dates[start]), start, i))
            start = i
    return out


# --------------------------------------------------------------------------
# Monthly table
# --------------------------------------------------------------------------

def build_months(
    dates: Sequence[dt.date],
    var_series: np.ndarray,
    month_return: Callable[[int, int], float],
    last_date_in_file: dt.date,
) -> List[Dict]:
    """One row per calendar month present in ``dates``.

    ``var_series`` is the daily series whose squares feed the realised variance
    (r_d for the factor, d for the spread); ``month_return(start, end)`` gives
    the month's return from the row range. v_m uses the WINDOW rows of
    ``var_series`` immediately preceding the month's first row and is undefined
    (None) when fewer than WINDOW rows precede it.
    """
    rows: List[Dict] = []
    for key, s, e in month_slices(dates):
        R = float(month_return(s, e))
        if s >= WINDOW:
            seg = var_series[s - WINDOW:s]
            v = (21.0 / WINDOW) * float(np.sum(seg * seg))
            if not (v > 0.0):
                raise ValueError(f"realised variance not positive for {fmt_month(key)}: {v}")
            w = S_T / math.sqrt(v)
            Rs = w * R
        else:
            v = w = Rs = None
        rows.append(
            dict(key=key, R=R, v=v, w=w, Rs=Rs, n_days=e - s,
                 complete=month_is_complete(key, last_date_in_file))
        )
    return rows


def assert_contiguous(rows: Sequence[Dict], label: str) -> None:
    """A gap inside a test range is an input defect, not something to skip over."""
    for a, b in zip(rows, rows[1:]):
        if next_month(a["key"]) != b["key"]:
            raise ValueError(
                f"{label}: months not contiguous between {fmt_month(a['key'])} "
                f"and {fmt_month(b['key'])}"
            )


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def sharpe(x: np.ndarray) -> float:
    """Annualised: sqrt(12) x mean / sd, sd with ddof = 1."""
    x = np.asarray(x, dtype=float)
    sd = x.std(ddof=1)
    return float(math.sqrt(12.0) * x.mean() / sd)


def ols_newey_west(y: np.ndarray, x: np.ndarray, lags: int) -> Tuple[float, float, float]:
    """y = a + b x + e by OLS; Newey-West (Bartlett, weights 1 - l/(L+1)) standard
    error for a; no small-sample correction. Returns (a, b, t_a)."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    n = len(y)
    X = np.column_stack([np.ones(n), x])
    XtX = X.T @ X
    XtX_inv = np.linalg.inv(XtX)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    xe = X * e[:, None]  # rows are x_t e_t
    S = xe.T @ xe
    for lag in range(1, lags + 1):
        if lag >= n:
            break
        wgt = 1.0 - lag / (lags + 1.0)
        G = xe[lag:].T @ xe[:-lag]
        S = S + wgt * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se_a = math.sqrt(V[0, 0])
    return float(beta[0]), float(beta[1]), float(beta[0] / se_a)


def bootstrap_p(R: np.ndarray, Rs: np.ndarray, seed: int = SEED) -> float:
    """Circular block bootstrap of Sharpe(R*) - Sharpe(R), exactly as pre-registered:
    default_rng(seed); 10,000 draws; each draw ceil(n/12) block starts from
    rng.integers(0, n, size=ceil(n/12)); blocks of 12 consecutive months wrapping
    modulo n; concatenated and truncated to n; the same indices for R and R*;
    p = (1 + #draws with difference <= 0) / (1 + 10,000)."""
    R = np.asarray(R, dtype=float)
    Rs = np.asarray(Rs, dtype=float)
    n = len(R)
    k = math.ceil(n / BLOCK)
    rng = np.random.default_rng(seed)
    offsets = np.arange(BLOCK)
    count_le = 0
    for _ in range(N_BOOT):
        starts = rng.integers(0, n, size=k)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        diff = sharpe(Rs[idx]) - sharpe(R[idx])
        if diff <= 0.0:
            count_le += 1
    return (1.0 + count_le) / (1.0 + N_BOOT)


def max_drawdown(R: np.ndarray) -> float:
    """Wealth from 1, compounding monthly; most negative wealth / running peak - 1."""
    W = np.concatenate([[1.0], np.cumprod(1.0 + np.asarray(R, dtype=float))])
    peak = np.maximum.accumulate(W)
    return float(np.min(W / peak - 1.0))


def evaluate(R: np.ndarray, Rs: np.ndarray, seed: int = SEED) -> Dict:
    """Criteria (a) and (b) and the verdict over one block of months."""
    n = len(R)
    out: Dict = dict(
        n=n, alpha_monthly=None, alpha_t=None, b=None, sharpe_raw=None,
        sharpe_managed=None, sharpe_ratio=None, p_boot=None,
        criteria=dict(a=False, b=False),
    )
    if n >= 3:
        a, b, t = ols_newey_west(Rs, R, NW_LAGS)
        sr = sharpe(R)
        sm = sharpe(Rs)
        p = bootstrap_p(R, Rs, seed)
        out.update(
            alpha_monthly=a, alpha_t=t, b=b, sharpe_raw=sr, sharpe_managed=sm,
            sharpe_ratio=(sm / sr) if sr != 0.0 else None, p_boot=p,
            criteria=dict(
                a=bool(a > 0.0 and t >= T_CRIT),
                # Gain form of "at least 1.2 x the raw Sharpe" (coordinator's
                # clarification, 29 Oct 2026): identical to 1.2 x for a positive
                # raw Sharpe; for a raw Sharpe at or below zero, where a ratio is
                # meaningless, it requires an improvement of 0.2 x |raw|.
                b=bool((sm - sr) >= (SHARPE_MULT - 1.0) * abs(sr) and p <= P_CRIT),
            ),
        )
    if n < MIN_MONTHS:
        verdict = "INSUFFICIENT"
    elif out["criteria"]["a"] and out["criteria"]["b"]:
        verdict = "PASS"
    elif out["criteria"]["a"] or out["criteria"]["b"]:
        verdict = "WEAK"
    else:
        verdict = "FAIL"
    out["verdict"] = verdict
    return out


# --------------------------------------------------------------------------
# The two tests
# --------------------------------------------------------------------------

def factor_test(dates: Sequence[dt.date], r: np.ndarray) -> Dict:
    rows = build_months(
        dates, r, lambda s, e: float(np.prod(1.0 + r[s:e]) - 1.0), dates[-1]
    )
    usable = [m for m in rows if m["v"] is not None and m["complete"]]
    is_rows = [m for m in usable if m["key"] <= IS_END]
    oos_rows = [m for m in usable if m["key"] >= OOS_START]
    assert_contiguous(is_rows, "in-sample")
    assert_contiguous(oos_rows, "out-of-sample")

    out: Dict = dict(
        n_is=len(is_rows), n_oos=len(oos_rows),
        is_first=fmt_month(is_rows[0]["key"]) if is_rows else None,
        is_last=fmt_month(is_rows[-1]["key"]) if is_rows else None,
        oos_first=fmt_month(oos_rows[0]["key"]) if oos_rows else None,
        oos_last=fmt_month(oos_rows[-1]["key"]) if oos_rows else None,
    )

    # In-sample: the replication, reported without weight.
    out.update(is_sharpe_raw=None, is_sharpe_managed=None, is_alpha_monthly=None, is_alpha_t=None)
    if len(is_rows) >= 3:
        R_is = np.array([m["R"] for m in is_rows])
        Rs_is = np.array([m["Rs"] for m in is_rows])
        a, _b, t = ols_newey_west(Rs_is, R_is, NW_LAGS)
        out.update(
            is_sharpe_raw=sharpe(R_is), is_sharpe_managed=sharpe(Rs_is),
            is_alpha_monthly=a, is_alpha_t=t,
        )

    # Out-of-sample: the test.
    R = np.array([m["R"] for m in oos_rows])
    Rs = np.array([m["Rs"] for m in oos_rows])
    ev = evaluate(R, Rs, SEED)
    out.update(
        oos_alpha_monthly=ev["alpha_monthly"], oos_alpha_t=ev["alpha_t"], oos_b=ev["b"],
        oos_sharpe_raw=ev["sharpe_raw"], oos_sharpe_managed=ev["sharpe_managed"],
        oos_sharpe_ratio=ev["sharpe_ratio"], p_boot=ev["p_boot"],
        criteria=ev["criteria"], verdict=ev["verdict"],
    )

    # Section 4.2: drawdowns, worst months, weight distribution.
    if len(oos_rows) >= 1:
        w = np.array([m["w"] for m in oos_rows])
        out.update(
            oos_maxdd_raw=max_drawdown(R), oos_maxdd_managed=max_drawdown(Rs),
            weight_min=float(w.min()), weight_median=float(np.median(w)),
            weight_max=float(w.max()), weight_share_above_2=float(np.mean(w > 2.0)),
        )
        order = sorted(range(len(oos_rows)), key=lambda i: (oos_rows[i]["R"], i))
        out["worst_raw_months"] = [
            dict(month=fmt_month(oos_rows[i]["key"]), raw=oos_rows[i]["R"], managed=oos_rows[i]["Rs"])
            for i in order[:N_WORST]
        ]
    else:
        out.update(
            oos_maxdd_raw=None, oos_maxdd_managed=None, weight_min=None, weight_median=None,
            weight_max=None, weight_share_above_2=None, worst_raw_months=[],
        )
    return out


def mtum_test(dates: Sequence[dt.date], mtum: np.ndarray, spy: np.ndarray) -> Dict:
    def daily_returns(p: np.ndarray) -> np.ndarray:
        r = np.full(len(p), np.nan)
        r[1:] = p[1:] / p[:-1] - 1.0  # NaN wherever either close is blank
        return r

    rm_all = daily_returns(mtum)
    rs_all = daily_returns(spy)
    d_all = rm_all - rs_all
    keep = ~np.isnan(d_all)
    idx = np.flatnonzero(keep)
    d_dates = [dates[i] for i in idx]
    rm = rm_all[idx]
    rs = rs_all[idx]
    d = d_all[idx]

    out: Dict = dict(
        n=0, first=None, last=None, alpha_monthly=None, alpha_t=None, b=None,
        sharpe_raw=None, sharpe_managed=None, sharpe_ratio=None, p_boot=None,
        criteria=dict(a=False, b=False), verdict="INSUFFICIENT",
        ann_return_managed=None, cost_estimate_annual=None,
        maxdd_raw=None, maxdd_managed=None, n_spread_days=int(len(d)),
    )
    if len(d) == 0:
        return out

    rows = build_months(
        d_dates, d,
        lambda s, e: float(np.prod(1.0 + rm[s:e]) - np.prod(1.0 + rs[s:e])),
        dates[-1],  # completeness judged on the bench file's own last date
    )
    test_rows = [m for m in rows if m["v"] is not None and m["complete"]]
    assert_contiguous(test_rows, "MTUM spread")
    if not test_rows:
        return out

    S = np.array([m["R"] for m in test_rows])
    Ss = np.array([m["Rs"] for m in test_rows])
    w = np.array([m["w"] for m in test_rows])
    ev = evaluate(S, Ss, SEED)  # a fresh default_rng(SEED) inside bootstrap_p
    n = len(test_rows)
    turnover = float(np.sum(np.abs(np.diff(w))))
    out.update(
        n=n, first=fmt_month(test_rows[0]["key"]), last=fmt_month(test_rows[-1]["key"]),
        alpha_monthly=ev["alpha_monthly"], alpha_t=ev["alpha_t"], b=ev["b"],
        sharpe_raw=ev["sharpe_raw"], sharpe_managed=ev["sharpe_managed"],
        sharpe_ratio=ev["sharpe_ratio"], p_boot=ev["p_boot"],
        criteria=ev["criteria"], verdict=ev["verdict"],
        ann_return_managed=float(12.0 * Ss.mean()),
        cost_estimate_annual=float(COST_PER_UNIT_TURNOVER * turnover / (n / 12.0)),
        maxdd_raw=max_drawdown(S), maxdd_managed=max_drawdown(Ss),
        weight_min=float(w.min()), weight_median=float(np.median(w)),
        weight_max=float(w.max()), weight_share_above_2=float(np.mean(w > 2.0)),
    )
    return out


# --------------------------------------------------------------------------
# Choices: every ambiguity in PREREG.md and how this file resolves it
# --------------------------------------------------------------------------

CHOICES = [
    "Months are calendar months of the dates in the file; a month's days are the file rows "
    "falling in it; the monthly factor return compounds those rows in file order.",
    "The 126-day variance window is the 126 rows of the same file immediately preceding the "
    "month's first row, regardless of which months those rows fall in; v_m is undefined when "
    "fewer than 126 rows precede, and the month is then excluded from every range.",
    "A realised variance of exactly zero raises rather than producing an infinite weight.",
    "Completeness: every month before the file's last month is complete; the last month is "
    "complete only if the file's last date equals the last Monday-to-Friday calendar day of "
    "that month (a holiday falling on that day makes the month incomplete, as the rule is "
    "written).",
    "In-sample = months with v_m defined AND complete, from the first such month to 2015-12 "
    "inclusive; OOS = months with v_m defined AND complete from 2016-01 to the last complete "
    "month. If the file ends before 2016 the OOS is empty and the verdict INSUFFICIENT.",
    "A gap (missing calendar month) inside the in-sample or OOS range raises; months are not "
    "silently skipped.",
    "Criterion (a) regresses managed on raw (R* = a + b R + e) with an intercept; the "
    "Newey-West sandwich uses Bartlett weights 1 - l/(L+1), L = 3, and no small-sample or "
    "degrees-of-freedom correction; t = a / se(a); the test is a > 0 and t >= 2.0.",
    "Sharpe = sqrt(12) x mean / sd with ddof = 1, applied to monthly returns; the ratio "
    "reported is Sharpe(R*) / Sharpe(R), null if Sharpe(R) is exactly zero.",
    "Criterion (b)'s 'at least 1.2 x the raw Sharpe' is applied as a gain test, per the "
    "coordinator's clarification of 29 October 2026 treated as part of the specification: "
    "(Sharpe(R*) - Sharpe(R)) >= 0.2 x |Sharpe(R)| and p_boot <= 0.05. For a positive raw "
    "Sharpe this is identical to the 1.2 x rule; for a raw Sharpe at or below zero, where a "
    "ratio is meaningless, it requires an improvement of 0.2 x |raw|.",
    "Bootstrap: one rng = default_rng(20261029) per test; each of the 10,000 draws makes one "
    "call rng.integers(0, n, size=ceil(n/12)) (sequential calls, not one vectorised call); "
    "blocks are start, start+1, ..., start+11 modulo n, concatenated in draw order and "
    "truncated to n; the difference is Sharpe(R*[idx]) - Sharpe(R[idx]) with the same "
    "formula as the headline Sharpe; a draw with difference <= 0 (or NaN, which fails the "
    "comparison) is counted as not positive. The MTUM test re-seeds a fresh rng.",
    "Criteria a and b are reported as computed even when the verdict is INSUFFICIENT; the "
    "96-month floor sets the verdict only. With fewer than 3 months the statistics are null "
    "and the criteria false.",
    "Maximum drawdown: wealth path W_0 = 1, W_t = W_(t-1)(1 + R_t); drawdown_t = W_t / "
    "max(W_0..W_t) - 1; reported value is the minimum (a non-positive fraction, 0 if wealth "
    "never falls below its running peak).",
    "Weight distribution over OOS months: numpy min, median (mean of the two middle values "
    "when n is even) and max; share above 2 is the fraction of months with w_m strictly "
    "greater than 2.",
    "Worst months: OOS months sorted ascending by raw R_m (ties by calendar order), the first "
    "five, each with the managed return of the same month.",
    "MTUM version: daily returns r_t = P_t / P_(t-1) - 1 from consecutive rows of bench.csv "
    "where both closes are present (NaN otherwise); the spread day series is the set of rows "
    "where both r_MTUM and r_SPY are defined; months, monthly products and the 126-day window "
    "are taken over that day series only, so the two legs are always compounded over "
    "identical days. S_m = prod(1 + r_MTUM) - prod(1 + r_SPY), not prod(1 + d) - 1.",
    "MTUM completeness is judged against the last date of bench.csv (its last SPY trading "
    "day), not against mom_daily.csv.",
    "MTUM test range: every month with v_m defined and complete, with no in-sample/OOS split; "
    "the same 96-month floor, criteria and verdict labels apply.",
    "Cost estimate: 0.0020 x sum over m = 2..n of |w_m - w_(m-1)|, divided by n/12 years "
    "(the first month's establishment of the position is not charged); ann_return_managed is "
    "the arithmetic 12 x mean of the managed monthly spread, in the same units as the cost.",
    "Inputs are validated: dates must be strictly increasing, Mom must not be blank, closes "
    "must be positive; any violation raises rather than being repaired.",
]


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def _jsonable(obj):
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if (math.isnan(f) or math.isinf(f)) else f
    return obj


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="directory holding mom_daily.csv and bench.csv")
    ap.add_argument("--out", required=True, help="directory to write verify.json into")
    args = ap.parse_args(argv)

    mom_path = os.path.join(args.data, "mom_daily.csv")
    bench_path = os.path.join(args.data, "bench.csv")

    dates, r = read_mom(mom_path)
    factor = factor_test(dates, r)

    b_dates, mtum, spy = read_bench(bench_path)
    mt = mtum_test(b_dates, mtum, spy)

    result: Dict = dict(
        prereg="tools/volmom/PREREG.md",
        implementation="verify.py (independent second implementation, numpy + stdlib)",
        inputs=dict(
            mom_daily=dict(path=mom_path, sha256=_sha256(mom_path), rows=len(dates),
                           first=dates[0].isoformat(), last=dates[-1].isoformat()),
            bench=dict(path=bench_path, sha256=_sha256(bench_path), rows=len(b_dates),
                       first=b_dates[0].isoformat(), last=b_dates[-1].isoformat()),
        ),
        parameters=dict(
            seed=SEED, n_boot=N_BOOT, block=BLOCK, window=WINDOW, target_annual_vol=TARGET_ANNUAL_VOL,
            s_T=S_T, nw_lags=NW_LAGS, min_months=MIN_MONTHS, t_crit=T_CRIT, sharpe_mult=SHARPE_MULT,
            p_crit=P_CRIT, cost_per_unit_turnover=COST_PER_UNIT_TURNOVER,
        ),
    )
    result.update(factor)
    result["mtum"] = mt
    result["choices"] = CHOICES

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "verify.json")
    with open(out_path, "w") as fh:
        json.dump(_jsonable(result), fh, indent=2)
        fh.write("\n")

    print(f"wrote {out_path}")
    print(f"  factor: n_is={factor['n_is']} n_oos={factor['n_oos']} "
          f"OOS {factor['oos_first']}..{factor['oos_last']} verdict={factor['verdict']} "
          f"a={factor['oos_alpha_monthly']} t={factor['oos_alpha_t']} "
          f"SR raw={factor['oos_sharpe_raw']} managed={factor['oos_sharpe_managed']} p={factor['p_boot']}")
    print(f"  mtum:   n={mt['n']} {mt['first']}..{mt['last']} verdict={mt['verdict']} "
          f"a={mt['alpha_monthly']} t={mt['alpha_t']} SR raw={mt['sharpe_raw']} "
          f"managed={mt['sharpe_managed']} p={mt['p_boot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
