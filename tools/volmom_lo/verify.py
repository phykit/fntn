#!/usr/bin/env python3
"""Independent second implementation of tools/volmom_lo/PREREG.md.

Written on 29 October 2026 from the pre-registration alone (plus section 3(b) of
tools/volmom/PREREG.md for the bootstrap), without sight of run.py, selftest.py or
any results. It exists so that compare.py can put two implementations of the same
rule side by side on the headline figures; a disagreement is a finding about the
rule's wording, not about the data.

Usage:
    python verify.py --data DIR --out DIR

DIR holds bench.csv (DATE,MTUM,SPY: adjusted closes on SPY trading days, blank
where MTUM is missing) and ff5_daily.csv (DATE,Mkt-RF,SMB,HML,RMW,CMA,RF, per
cent, daily). verify.json is written to the output directory.

Every resolution of a point the specification leaves open is recorded in the
``choices`` block of the output, so that a disagreement with the first
implementation can be traced to a reading rather than to a defect. Where an
input is missing the figure that needs it is reported as null and the reason is
named; nothing is substituted.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import math
import os
import sys
from datetime import date, timedelta

import numpy as np

# Fixed by the pre-registration (section 1 and 2).
S_T = 0.12 / math.sqrt(12.0)       # target monthly volatility
WINDOW = 126                       # spread days in the realised-variance window
VAR_SCALE = 21.0 / 126.0           # v_m = (21 / 126) x sum d^2
COST_RATE = 0.002                  # 20 bp on |w_m - w_(m-1)|, charged on the execution day
NW_LAGS = 3                        # Bartlett kernel, L = 3
T_MIN = 2.0
SHARPE_MULT = 1.2                  # Sharpe(A) >= 1.2 x Sharpe(S) when Sharpe(S) > 0
SHARPE_GAIN = 0.2                  # Sharpe(A) >= Sharpe(S) + 0.2 x |Sharpe(S)| otherwise
BOOT_SEED = 20261029
BOOT_DRAWS = 10_000
BLOCK = 12
P_MAX = 0.05
MIN_MONTHS = 96
FIFTY = 0.5

ANN = math.sqrt(12.0)


# ----------------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------------

def parse_date(text: str) -> date:
    """Accept ISO (YYYY-MM-DD, optionally with a time suffix) or YYYYMMDD.

    Anything else raises: a guessed day/month order is a silent substitution of
    one sample for another.
    """
    s = text.strip()
    if len(s) == 8 and s.isdigit():
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        raise ValueError(f"unparseable date {text!r}") from None


def parse_float(text: str | None) -> float | None:
    if text is None:
        return None
    s = text.strip()
    if s == "" or s.lower() in {"na", "nan", "null", "none"}:
        return None
    return float(s)


def read_table(path: str, wanted: list[str]) -> list[dict]:
    """Read a CSV with a header row, returning the wanted columns per row.

    Header names are matched after stripping whitespace and a byte-order mark.
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: no header row")
        names = {name.strip(): name for name in reader.fieldnames}
        missing = [c for c in wanted if c not in names]
        if missing:
            raise ValueError(f"{path}: missing columns {missing}; have {list(names)}")
        out = []
        for rec in reader:
            if all((rec.get(names[c]) or "").strip() == "" for c in wanted):
                continue  # wholly blank line
            out.append({c: rec[names[c]] for c in wanted})
    return out


def read_bench(path: str):
    """bench.csv -> (dates, mtum, spy) sorted by date, with None for blanks."""
    recs = read_table(path, ["DATE", "MTUM", "SPY"])
    rows = []
    for rec in recs:
        d = parse_date(rec["DATE"])
        m = parse_float(rec["MTUM"])
        s = parse_float(rec["SPY"])
        for name, val in (("MTUM", m), ("SPY", s)):
            if val is not None and val <= 0.0:
                raise ValueError(f"{path}: non-positive {name} close on {d}")
        rows.append((d, m, s))
    rows.sort(key=lambda r: r[0])
    for i in range(1, len(rows)):
        if rows[i][0] == rows[i - 1][0]:
            raise ValueError(f"{path}: duplicate date {rows[i][0]}")
    if not rows:
        raise ValueError(f"{path}: empty")
    return rows


def read_ff(path: str):
    """ff5_daily.csv -> list of (date, RF in per cent) sorted by date."""
    recs = read_table(path, ["DATE", "RF"])
    rows = []
    for rec in recs:
        rf = parse_float(rec["RF"])
        if rf is None:
            raise ValueError(f"{path}: blank RF on {rec['DATE']}")
        rows.append((parse_date(rec["DATE"]), rf))
    rows.sort(key=lambda r: r[0])
    for i in range(1, len(rows)):
        if rows[i][0] == rows[i - 1][0]:
            raise ValueError(f"{path}: duplicate date {rows[i][0]}")
    if not rows:
        raise ValueError(f"{path}: empty")
    return rows


# ----------------------------------------------------------------------------
# Calendar helpers
# ----------------------------------------------------------------------------

def ym(d: date) -> tuple[int, int]:
    return (d.year, d.month)


def ym_str(key: tuple[int, int]) -> str:
    return f"{key[0]:04d}-{key[1]:02d}"


def next_month(key: tuple[int, int]) -> tuple[int, int]:
    y, m = key
    return (y + 1, 1) if m == 12 else (y, m + 1)


def prev_month(key: tuple[int, int]) -> tuple[int, int]:
    y, m = key
    return (y - 1, 12) if m == 1 else (y, m - 1)


def final_weekday(key: tuple[int, int]) -> date:
    y, m = key
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() > 4:
        d -= timedelta(days=1)
    return d


def last_complete_month(dates: list[date]) -> tuple[int, int]:
    """tools/volmom/PREREG.md section 2: a month is complete if the file holds a
    date in a later month, or its last date is the final weekday of that month."""
    last = dates[-1]
    key = ym(last)
    return key if last == final_weekday(key) else prev_month(key)


# ----------------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------------

def sharpe(x: np.ndarray) -> float:
    """sqrt(12) x mean / sd with ddof = 1, as pre-registered. Returns nan where
    the sd is zero or there are fewer than two observations; the caller decides
    what a nan means."""
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return float("nan")
    sd = float(np.std(x, ddof=1))
    if sd == 0.0:
        return float("nan")
    return ANN * float(np.mean(x)) / sd


def nw_ols(y: np.ndarray, x: np.ndarray, lags: int = NW_LAGS):
    """y = a + b x + e by OLS; Newey-West (Bartlett, L = lags) t for a, with no
    small-sample correction, i.e. no n / (n - k) scaling of the sandwich."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    n = y.size
    X = np.column_stack([np.ones(n), x])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    e = y - X @ beta
    xe = X * e[:, None]
    omega = xe.T @ xe
    for lag in range(1, lags + 1):
        wgt = 1.0 - lag / (lags + 1.0)
        gamma = xe[lag:].T @ xe[:-lag]
        omega = omega + wgt * (gamma + gamma.T)
    cov = xtx_inv @ omega @ xtx_inv
    t_a = float(beta[0]) / math.sqrt(float(cov[0, 0]))
    return float(beta[0]), float(beta[1]), t_a


def bootstrap_p(a: np.ndarray, s: np.ndarray) -> float:
    """tools/volmom/PREREG.md section 3(b), verbatim: one default_rng(20261029);
    10,000 draws; each draw takes ceil(n / 12) block starts
    rng.integers(0, n, size=ceil(n / 12)); each block is the 12 consecutive
    months from its start, wrapping modulo n, concatenated and truncated to n;
    the same indices for A and S; p = (1 + number of draws with
    Sharpe(A) - Sharpe(S) <= 0) / (1 + 10,000).

    Nothing else is drawn from the generator, so the index stream is fixed by
    the seed and n alone. A draw whose Sharpe difference is nan (a degenerate
    resample with zero sd) is counted on the "<= 0" side: a resample that
    cannot show the gain does not count as showing it.
    """
    a = np.asarray(a, dtype=float)
    s = np.asarray(s, dtype=float)
    n = a.size
    k = math.ceil(n / BLOCK)
    rng = np.random.default_rng(BOOT_SEED)
    offsets = np.arange(BLOCK)
    not_positive = 0
    for _ in range(BOOT_DRAWS):
        starts = rng.integers(0, n, size=k)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        diff = sharpe(a[idx]) - sharpe(s[idx])
        if not (diff > 0.0):
            not_positive += 1
    return (1.0 + not_positive) / (1.0 + BOOT_DRAWS)


def ann_return(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    growth = float(np.prod(1.0 + r))
    return growth ** (12.0 / r.size) - 1.0


def ann_vol(r: np.ndarray) -> float:
    return ANN * float(np.std(np.asarray(r, dtype=float), ddof=1))


def max_drawdown(r: np.ndarray) -> float:
    """Wealth from 1 before the first month; the minimum of wealth / running
    peak minus one, so a 25 per cent drawdown is reported as -0.25."""
    wealth = np.concatenate([[1.0], np.cumprod(1.0 + np.asarray(r, dtype=float))])
    peak = np.maximum.accumulate(wealth)
    return float(np.min(wealth / peak - 1.0))


# ----------------------------------------------------------------------------
# The strategy
# ----------------------------------------------------------------------------

class SpreadSeries:
    """Daily returns on the spread days: the rows of bench.csv on which both
    r_MTUM and r_SPY are defined, a return being P_t / P_(t-1) - 1 over
    consecutive file rows on which both closes exist."""

    def __init__(self, rows):
        dates, rm, rs = [], [], []
        for i in range(1, len(rows)):
            d, m1, s1 = rows[i]
            _, m0, s0 = rows[i - 1]
            if m0 is None or m1 is None or s0 is None or s1 is None:
                continue
            dates.append(d)
            rm.append(m1 / m0 - 1.0)
            rs.append(s1 / s0 - 1.0)
        if not dates:
            raise ValueError("no spread days: MTUM and SPY never both present on consecutive rows")
        self.dates = dates
        self.rm = np.array(rm, dtype=float)
        self.rs = np.array(rs, dtype=float)
        self.d = self.rm - self.rs
        self.first_idx: dict[tuple[int, int], int] = {}
        self.last_idx: dict[tuple[int, int], int] = {}
        for i, dt in enumerate(dates):
            key = ym(dt)
            self.first_idx.setdefault(key, i)
            self.last_idx[key] = i
        self.months = sorted(self.last_idx)

    def weight_ending_at(self, i: int):
        """w = min(1, s_T / sqrt(v)) with v over the 126 spread days ending at
        and including index i. None where fewer than 126 are available. A zero
        realised variance gives w = 1 (the limit of the formula)."""
        if i + 1 < WINDOW:
            return None, None
        window = self.d[i - WINDOW + 1 : i + 1]
        v = VAR_SCALE * float(np.sum(window * window))
        sigma = math.sqrt(v)
        w = 1.0 if sigma == 0.0 else min(1.0, S_T / sigma)
        return w, sigma

    def month_product(self, key: tuple[int, int], r: np.ndarray) -> float:
        i0, i1 = self.first_idx[key], self.last_idx[key]
        return float(np.prod(1.0 + r[i0 : i1 + 1])) - 1.0

    def run_sleeve(self, weights: dict[tuple[int, int], float], months: list[tuple[int, int]]):
        """Daily engine. Holdings (x_MTUM, x_SPY) are fractions of wealth that
        sum to one after each rebalance and drift with prices between. On the
        first spread day of each month in ``months`` (the execution day) the
        day's return is earned at the drifted old holdings, the holdings are
        then reset to (w, 1 - w), and 0.002 x |w - w_prev| is deducted from
        that day's return. The sleeve starts all in SPY with w_prev = 0, so the
        first establishment is charged against a prior SPY holding.

        Returns the monthly compounded returns, the traded fraction
        |w - w_prev| per month and the cost deducted per month.
        """
        x_m, x_s = 0.0, 1.0
        w_prev = 0.0
        monthly, traded, costs = [], [], []
        for key in months:
            i0, i1 = self.first_idx[key], self.last_idx[key]
            growth = 1.0
            for i in range(i0, i1 + 1):
                r_m, r_s = float(self.rm[i]), float(self.rs[i])
                r_day = x_m * r_m + x_s * r_s
                if i == i0:
                    w = weights[key]
                    delta = abs(w - w_prev)
                    cost = COST_RATE * delta
                    r_day -= cost
                    x_m, x_s = w, 1.0 - w
                    w_prev = w
                    traded.append(delta)
                    costs.append(cost)
                else:
                    gross = 1.0 + r_day
                    x_m = x_m * (1.0 + r_m) / gross
                    x_s = x_s * (1.0 + r_s) / gross
                growth *= 1.0 + r_day
            monthly.append(growth - 1.0)
        return np.array(monthly), np.array(traded), np.array(costs)


def monthly_rf(ff_rows) -> tuple[dict[tuple[int, int], float], tuple[int, int]]:
    """RF per month = product of (1 + RF / 100) over the file's rows in that
    calendar month, minus one; and the last month the file completes under the
    same completeness rule as bench.csv, so a month the French file has only
    begun is not treated as a (short) month of RF."""
    acc: dict[tuple[int, int], float] = {}
    for d, rf in ff_rows:
        key = ym(d)
        acc[key] = acc.get(key, 1.0) * (1.0 + rf / 100.0)
    out = {k: v - 1.0 for k, v in acc.items()}
    return out, last_complete_month([d for d, _ in ff_rows])


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def py(x):
    """JSON-safe scalar: nan -> None, numpy scalars -> Python."""
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    x = float(x)
    return None if math.isnan(x) else x


def compute(bench_path: str, ff_path: str) -> dict:
    rows = read_bench(bench_path)
    bench_dates = [r[0] for r in rows]
    series = SpreadSeries(rows)

    # Decided weights at every month-end (the last spread day of the month).
    decided: dict[tuple[int, int], float] = {}
    sigmas: dict[tuple[int, int], float] = {}
    for key in series.months:
        w, sigma = series.weight_ending_at(series.last_idx[key])
        if w is not None:
            decided[key] = w
            sigmas[key] = sigma
    if not decided:
        raise ValueError(f"no month-end with {WINDOW} spread days available")
    m0 = min(decided)
    last_complete = last_complete_month(bench_dates)

    # Strategy months: the calendar months after m0, up to the last complete month.
    strat_months = [k for k in series.months if m0 < k <= last_complete]
    if not strat_months:
        raise ValueError(
            f"no strategy month: first decided month-end {ym_str(m0)}, "
            f"last complete month {ym_str(last_complete)}"
        )
    expected = m0
    for key in strat_months:
        expected = next_month(expected)
        if key != expected:
            raise ValueError(f"spread days absent for {ym_str(expected)}: the monthly chain is broken")
    exec_weights = {k: decided[prev_month(k)] for k in strat_months}
    n = len(strat_months)
    if n < 3:
        raise ValueError(f"only {n} strategy month(s): nothing below three can be regressed or bootstrapped")

    # Monthly return series on the same months and the same spread days.
    strat_r, strat_traded, strat_cost = series.run_sleeve(exec_weights, strat_months)
    fifty_r, _, _ = series.run_sleeve({k: FIFTY for k in strat_months}, strat_months)
    spy_r = np.array([series.month_product(k, series.rs) for k in strat_months])
    mtum_r = np.array([series.month_product(k, series.rm) for k in strat_months])
    w_series = np.array([exec_weights[k] for k in strat_months])

    # Risk-free rate per month, where the French file completes the month.
    ff_rows = read_ff(ff_path)
    rf_by_month, ff_last_complete = monthly_rf(ff_rows)
    rf = np.array(
        [rf_by_month[k] if (k in rf_by_month and k <= ff_last_complete) else np.nan for k in strat_months]
    )
    rf_ok = ~np.isnan(rf)
    rf_missing = [ym_str(k) for k, ok in zip(strat_months, rf_ok) if not ok]

    # Tests.
    active = strat_r - spy_r            # A_m
    static_active = mtum_r - spy_r      # S_m
    alpha, b_coef, t_alpha = nw_ols(active, static_active)
    crit_a = bool(alpha > 0.0 and t_alpha >= T_MIN)

    sh_a = sharpe(active)
    sh_s = sharpe(static_active)
    if sh_s > 0.0:
        sharpe_threshold = SHARPE_MULT * sh_s
    else:
        sharpe_threshold = sh_s + SHARPE_GAIN * abs(sh_s)
    p_boot = bootstrap_p(active, static_active)
    crit_b = bool(sh_a >= sharpe_threshold and p_boot <= P_MAX)

    def excess_sharpe(r: np.ndarray):
        if rf_ok.sum() < 2:
            return None
        return sharpe(r[rf_ok] - rf[rf_ok])

    sh_strategy = excess_sharpe(strat_r)
    sh_spy = excess_sharpe(spy_r)
    crit_c = None if sh_strategy is None else bool(sh_strategy >= sh_spy)

    if n < MIN_MONTHS:
        verdict = "INSUFFICIENT"
    elif crit_c is None:
        verdict = "UNSCORABLE"   # (c) has no RF for any month: refused, not defaulted
    elif crit_a and crit_b and crit_c:
        verdict = "PASS"
    elif crit_a or crit_b:
        verdict = "WEAK"
    else:
        verdict = "FAIL"

    def stats(r: np.ndarray) -> dict:
        return {
            "ann_return": py(ann_return(r)),
            "ann_vol": py(ann_vol(r)),
            "sharpe": py(excess_sharpe(r)),
            "max_drawdown": py(max_drawdown(r)),
        }

    # Turnover and cost: sum of |w_m - w_(m-1)| including the establishment
    # against the prior SPY holding, annualised by 12 / n.
    turnover_total = float(np.sum(strat_traded))
    turnover_annual = turnover_total * 12.0 / n
    cost_annual = float(np.sum(strat_cost)) * 12.0 / n

    # Year by year.
    yearly = []
    for year in sorted({k[0] for k in strat_months}):
        mask = np.array([k[0] == year for k in strat_months])
        yearly.append({
            "year": year,
            "strategy": py(float(np.prod(1.0 + strat_r[mask])) - 1.0),
            "spy": py(float(np.prod(1.0 + spy_r[mask])) - 1.0),
            "months": int(mask.sum()),
        })

    # Live weights.
    live_last_complete = decided.get(last_complete)
    live_latest, sigma_latest = series.weight_ending_at(len(series.dates) - 1)

    vs_mtum = strat_r - mtum_r

    choices = {
        "returns": "P_t / P_(t-1) - 1 over consecutive file rows (sorted by date) on which both closes exist; "
                   "spread days are rows with both r_MTUM and r_SPY defined",
        "month_end": "the last spread day of the calendar month; v_m over the 126 spread days ending at and "
                     "including it; a zero realised variance gives w = 1",
        "first_month_end": "the first month-end with 126 spread days available (m0); the first strategy month "
                           "is the calendar month after m0",
        "last_month": "the last complete month of bench.csv: complete if the file has a date in a later month "
                      "or its last date is the final weekday (Mon-Fri) of the month",
        "execution": "on the first spread day of each strategy month the day's return is earned at the drifted "
                     "old holdings, then holdings reset to (w, 1 - w) and 0.002 x |w - w_prev| is deducted from "
                     "that day's return; the sleeve starts all in SPY with w_prev = 0",
        "monthly_returns": "all four series compound daily returns over the strategy month's spread days; no "
                           "other SPY trading days are used",
        "mtum_held": "pure MTUM daily returns from the first spread day of the first strategy month, no cost, no "
                     "delay; so S_m is the raw ETF difference, as the regressor in (a) should be",
        "fifty_fifty": "the same daily engine with w = 0.5 every month and the same cost rule on decided weights: "
                       "0.002 x |0.5 - 0| at establishment and 0.002 x |0.5 - 0.5| = 0 thereafter, i.e. the "
                       "drift re-balance is not charged because the rule charges |w_m - w_(m-1)|, not the "
                       "drifted fraction",
        "costs": "no drift cost for the strategy either: the charge is on the decided-weight change only, as "
                 "the PREREG defines the traded fraction; the cost is deducted additively from the execution "
                 "day's return, 1 + r_day = 1 + x.r - 0.002 x |w - w_prev|, not multiplicatively",
        "rf": "RF per month = prod(1 + RF / 100) - 1 over all ff5_daily.csv rows in the calendar month; a "
              "month the French file has not completed (same completeness rule) is treated as missing; (c) and "
              "the four Sharpes then use only the months with RF, and rf_months_missing lists the rest",
        "sharpe_b_threshold": "Sharpe(S) > 0: Sharpe(A) >= 1.2 x Sharpe(S); otherwise Sharpe(A) >= Sharpe(S) + "
                              "0.2 x |Sharpe(S)|",
        "bootstrap": "tools/volmom/PREREG.md 3(b) verbatim; a nan Sharpe difference in a resample is counted on "
                     "the <= 0 side",
        "newey_west": "sandwich with Bartlett weights 1 - l / (L + 1), L = 3, no n / (n - k) factor",
        "verdict": "INSUFFICIENT below 96 months; UNSCORABLE if (c) has no RF month at all; else PASS / WEAK / "
                   "FAIL per the PREREG",
        "stats": "ann_return geometric ((prod(1 + r))^(12 / n) - 1); ann_vol sqrt(12) x sd (ddof 1); sharpe over "
                 "RF; max_drawdown from monthly wealth starting at 1, reported as a negative fraction",
        "weight_series": "the n executed weights (decided at the month-ends from m0 to the month before the last "
                         "complete month); share_capped is w >= 1; share_below_half is w < 0.5",
        "turnover": "sum of |w_m - w_(m-1)| over the executed rebalances, the first term being |w_m0 - 0|, "
                    "annualised by 12 / n; cost_annual = 0.002 x turnover_annual",
        "yearly": "calendar-year compounding of the strategy months in that year; partial first and last years "
                  "included as they stand, with the month count",
        "live_weight": "last_complete_month: the weight decided at the last spread day of the last complete "
                       "month; latest: the weight over the 126 spread days ending at the last spread day in "
                       "the file",
        "rf_months_missing": rf_missing,
        "ff_last_complete_month": ym_str(ff_last_complete),
        "bench_last_date": bench_dates[-1].isoformat(),
        "first_spread_day": series.dates[0].isoformat(),
        "first_decided_month_end": ym_str(m0),
        "sharpe_threshold_b": py(sharpe_threshold),
    }

    return {
        "n_months": n,
        "first_month": ym_str(strat_months[0]),
        "last_month": ym_str(strat_months[-1]),
        "alpha_monthly": py(alpha),
        "alpha_t": py(t_alpha),
        "b": py(b_coef),
        "sharpe_active": py(sh_a),
        "sharpe_static_active": py(sh_s),
        "p_boot": py(p_boot),
        "sharpe_strategy": py(sh_strategy),
        "sharpe_spy": py(sh_spy),
        "criteria": {"a": crit_a, "b": crit_b, "c": crit_c},
        "verdict": verdict,
        "stats": {
            "spy": stats(spy_r),
            "mtum": stats(mtum_r),
            "fifty": stats(fifty_r),
            "strategy": stats(strat_r),
        },
        "weight": {
            "min": py(np.min(w_series)),
            "median": py(np.median(w_series)),
            "max": py(np.max(w_series)),
            "share_capped": py(np.mean(w_series >= 1.0)),
            "share_below_half": py(np.mean(w_series < 0.5)),
        },
        "turnover_annual": py(turnover_annual),
        "cost_annual": py(cost_annual),
        "live_weight_last_complete_month": py(live_last_complete),
        "live_weight_latest": py(live_latest),
        "yearly": yearly,
        "active_vs_mtum": {
            "mean_monthly": py(np.mean(vs_mtum)),
            "sharpe": py(sharpe(vs_mtum)),
        },
        "n_months_rf": int(rf_ok.sum()),
        "sigma_last_complete_month": py(sigmas.get(last_complete)),
        "sigma_latest": py(sigma_latest),
        "choices": choices,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True, help="directory holding bench.csv and ff5_daily.csv")
    ap.add_argument("--out", required=True, help="directory to write verify.json into")
    args = ap.parse_args(argv)

    bench_path = os.path.join(args.data, "bench.csv")
    ff_path = os.path.join(args.data, "ff5_daily.csv")
    for p in (bench_path, ff_path):
        if not os.path.isfile(p):
            print(f"missing input: {p}", file=sys.stderr)
            return 2

    result = compute(bench_path, ff_path)

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "verify.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")

    c = result["criteria"]
    print(f"verify.json written to {out_path}")
    print(f"months {result['n_months']} ({result['first_month']} to {result['last_month']}), "
          f"RF months {result['n_months_rf']}")
    print(f"(a) alpha {result['alpha_monthly']:+.5f}/month, t {result['alpha_t']:.3f}, b {result['b']:.3f} -> {c['a']}")
    print(f"(b) Sharpe(A) {result['sharpe_active']:.3f} vs Sharpe(S) {result['sharpe_static_active']:.3f}, "
          f"p_boot {result['p_boot']:.4f} -> {c['b']}")
    print(f"(c) Sharpe strategy {result['sharpe_strategy']} vs SPY {result['sharpe_spy']} -> {c['c']}")
    print(f"verdict {result['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
