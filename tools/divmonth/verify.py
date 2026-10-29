#!/usr/bin/env python3
"""Independent second implementation of tools/divmonth/PREREG.md (disclosure 3).

Written from PREREG.md and the binding details that accompany it, without
reading run.py, selftest.py, fetch.py, any results directory or docs/. Where the
specification left a choice open, the choice taken is recorded under the
``choices`` key of verify.json so that a disagreement with results.json can be
traced to a reading rather than to arithmetic.

Usage:
    python verify.py --data DIR --out DIR [--last-month YYYY-MM]

Inputs under --data:
    prices.csv      DATE then one column per ticker; adjusted closes on SPY
                    trading days; blank where missing.
    dividends.csv   ticker,ex_date,amount; one row per ex-dividend event.
    ff5_daily.csv   DATE,...,RF; RF in per cent per day.

Output: verify.json under --out.

Nothing here falls back to a default. A statistic that cannot be computed is
written as null and the reason is recorded; a malformed input raises.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd

OOS_FIRST_YM = 2010 * 12 + 0      # January 2010
FULL_FIRST_YM = 2001 * 12 + 0     # January 2001
MIN_STOCKS = 20                   # a month with fewer than this in P or N is undefined
MIN_OOS_MONTHS = 120              # INSUFFICIENT below this
T_THRESHOLD = 2.0
NW_LAGS = 3
COST_PER_LEG = 0.0010             # 10 bp
LAGS = (3, 6, 9, 12)


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def ym_of(ts: pd.Timestamp) -> int:
    return ts.year * 12 + (ts.month - 1)


def ym_label(ym: int) -> str:
    return f"{ym // 12:04d}-{ym % 12 + 1:02d}"


def parse_ym_label(s: str) -> int:
    m = re.fullmatch(r"(\d{4})-(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"--last-month must be YYYY-MM, got {s!r}")
    return int(m.group(1)) * 12 + int(m.group(2)) - 1


def parse_dates(col: pd.Series, what: str) -> pd.Series:
    """Parse a date column that may be ISO (YYYY-MM-DD) or Ken French style
    (YYYYMMDD). Raises on anything unparseable: a date that cannot be read is
    not a date that can be silently dropped, because dropping it changes the
    trading-day calendar."""
    s = col.astype(str).str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    eight = s.str.fullmatch(r"\d{8}")
    if eight.any():
        out[eight] = pd.to_datetime(s[eight], format="%Y%m%d", errors="coerce")
    rest = ~eight
    if rest.any():
        out[rest] = pd.to_datetime(s[rest], errors="coerce")
    bad = out.isna()
    if bad.any():
        raise SystemExit(
            f"{what}: {int(bad.sum())} unparseable date(s), e.g. {s[bad].head(3).tolist()}")
    return out


def fnum(x):
    """JSON-safe float: None where not finite."""
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


# ----------------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------------

def newey_west_t(y, lags: int = NW_LAGS):
    """t-statistic of the mean of ``y`` from a regression on a constant with a
    Newey-West (Bartlett) HAC variance, ``lags`` lags, no small-sample
    correction. For a constant-only regression the HAC variance of the mean is
    S / T with S = g0 + 2 * sum_{l=1}^{L} (1 - l/(L+1)) g_l and
    g_l = (1/T) * sum_{t>l} e_t e_{t-l}."""
    y = np.asarray(y, dtype=float)
    T = len(y)
    if T < 2:
        return None
    mu = y.mean()
    e = y - mu
    S = float(e @ e) / T
    for l in range(1, lags + 1):
        if l >= T:
            break
        g = float(e[l:] @ e[:-l]) / T
        S += 2.0 * (1.0 - l / (lags + 1.0)) * g
    if not (S > 0):
        return None
    return float(mu / math.sqrt(S / T))


def series_stats(y):
    y = np.asarray(y, dtype=float)
    if len(y) == 0:
        return None, None
    return float(y.mean()), newey_west_t(y)


def performance(r, rf):
    """Annualised statistics of a monthly return series ``r``.

    ann_return   geometric: wealth ** (12 / n) - 1
    ann_vol      sample standard deviation (ddof = 1) times sqrt(12)
    sharpe       mean(r - rf) / std(r - rf, ddof = 1) * sqrt(12), over the
                 months where rf is available; ``rf`` may contain NaN
    max_drawdown minimum of wealth / running peak - 1 (a non-positive number)
    """
    r = np.asarray(r, dtype=float)
    rf = np.asarray(rf, dtype=float)
    n = len(r)
    if n == 0:
        return {"ann_return": None, "ann_vol": None, "sharpe": None,
                "max_drawdown": None, "n": 0, "n_rf": 0}
    wealth = np.cumprod(1.0 + r)
    ann_return = wealth[-1] ** (12.0 / n) - 1.0 if wealth[-1] > 0 else -1.0
    ann_vol = float(r.std(ddof=1) * math.sqrt(12.0)) if n >= 2 else None
    mdd = float((wealth / np.maximum.accumulate(wealth) - 1.0).min())
    have = np.isfinite(rf)
    sharpe = None
    if have.sum() >= 2:
        ex = r[have] - rf[have]
        sd = ex.std(ddof=1)
        sharpe = float(ex.mean() / sd * math.sqrt(12.0)) if sd > 0 else None
    return {"ann_return": fnum(ann_return), "ann_vol": fnum(ann_vol),
            "sharpe": fnum(sharpe), "max_drawdown": fnum(mdd),
            "n": int(n), "n_rf": int(have.sum())}


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------

def load_prices(path):
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    if raw.shape[1] < 2:
        raise SystemExit("prices.csv needs DATE plus at least one ticker column")
    date_col = raw.columns[0]
    dates = parse_dates(raw[date_col], "prices.csv DATE")
    tickers = [c for c in raw.columns[1:]]
    excluded = [c for c in tickers if c.strip().upper() == "SPY"]
    tickers = [c for c in tickers if c not in excluded]
    closes = raw[tickers].replace("", np.nan).apply(pd.to_numeric, errors="raise")
    closes.index = dates
    if not closes.index.is_monotonic_increasing:
        order = np.argsort(closes.index.values, kind="stable")
        closes = closes.iloc[order]
    if closes.index.has_duplicates:
        dup = closes.index[closes.index.duplicated()]
        raise SystemExit(f"prices.csv has duplicate dates, e.g. {dup[:3].tolist()}")
    return closes, excluded


def load_dividends(path, universe):
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    cols = {c.strip().lower(): c for c in raw.columns}
    for need in ("ticker", "ex_date"):
        if need not in cols:
            raise SystemExit(f"dividends.csv lacks column {need!r}; has {list(raw.columns)}")
    tick = raw[cols["ticker"]].astype(str).str.strip()
    exd = parse_dates(raw[cols["ex_date"]], "dividends.csv ex_date")
    uni = set(universe)
    in_uni = tick.isin(uni)
    events = set(zip(tick[in_uni], (exd[in_uni].dt.year * 12 + exd[in_uni].dt.month - 1).astype(int)))
    rows_per_ticker = tick[in_uni].value_counts()
    return events, rows_per_ticker, int((~in_uni).sum()), int(len(raw))


def load_rf_monthly(path):
    """Monthly risk-free rate by calendar month: the daily RF (per cent)
    compounded over the file's rows falling in that month."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    rf_cols = [c for c in raw.columns if c.strip().upper() == "RF"]
    if len(rf_cols) != 1:
        raise SystemExit(f"ff5_daily.csv needs exactly one RF column; has {list(raw.columns)}")
    dates = parse_dates(raw[raw.columns[0]], "ff5_daily.csv DATE")
    rf = pd.to_numeric(raw[rf_cols[0]].str.strip(), errors="raise").astype(float) / 100.0
    ym = (dates.dt.year * 12 + dates.dt.month - 1).astype(int)
    grp = (1.0 + rf).groupby(ym.values).prod() - 1.0
    return {int(k): float(v) for k, v in grp.items()}


# ----------------------------------------------------------------------------
# Core computation
# ----------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--last-month", default=None,
                    help="override the last complete month (YYYY-MM); default is "
                         "the last month in prices.csv that is followed by at "
                         "least one later trading day")
    args = ap.parse_args(argv)

    closes, excluded_cols = load_prices(os.path.join(args.data, "prices.csv"))
    tickers = list(closes.columns)
    n_tickers = len(tickers)

    # Month-end closes: the close on the last SPY trading day of each calendar
    # month, with no forward filling. A stock with a close earlier in the month
    # but a blank on the last trading day has no month-end close.
    ym_index = pd.Index((closes.index.year * 12 + closes.index.month - 1).astype(int))
    months_present = sorted(set(ym_index.tolist()))
    last_pos = {}
    for pos, ym in enumerate(ym_index.tolist()):
        last_pos[ym] = pos           # ascending order, so the last write wins
    month_end = np.vstack([closes.values[last_pos[ym]] for ym in months_present]).astype(float)
    month_end_date = {ym: closes.index[last_pos[ym]] for ym in months_present}
    ym_pos = {ym: k for k, ym in enumerate(months_present)}

    # Last complete month.
    if args.last_month is not None:
        last_complete = parse_ym_label(args.last_month)
        if last_complete not in ym_pos:
            raise SystemExit(f"--last-month {args.last_month} has no trading days in prices.csv")
        complete_rule = "operator override via --last-month"
    else:
        complete = [ym for ym in months_present if ym < months_present[-1]]
        if not complete:
            raise SystemExit("prices.csv holds a single month; no complete month")
        last_complete = complete[-1]
        complete_rule = ("a month is complete when prices.csv holds at least one "
                         "trading day in a later month; the last month present is "
                         "therefore never complete")

    # Monthly returns: R[k, i] = C[k, i] / C[k-1, i] - 1 where both month-end
    # closes exist, are positive, and the two months are consecutive calendar
    # months. A non-positive close is treated as absent rather than divided by.
    R = np.full(month_end.shape, np.nan)
    for k in range(1, len(months_present)):
        if months_present[k] - months_present[k - 1] != 1:
            continue
        a, b = month_end[k - 1], month_end[k]
        ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        R[k, ok] = b[ok] / a[ok] - 1.0

    # Dividends and the predicted-payer flag.
    events, rows_per_ticker, n_div_rows_outside_universe, n_div_rows = load_dividends(
        os.path.join(args.data, "dividends.csv"), tickers)
    tick_pos = {t: i for i, t in enumerate(tickers)}
    if events:
        ev_min = min(ym for _, ym in events)
        ev_max = max(ym for _, ym in events)
    else:
        ev_min, ev_max = months_present[0], months_present[0]
    base = min(ev_min, months_present[0] - 12)
    top = max(ev_max, months_present[-1])
    div_flag = np.zeros((top - base + 1, n_tickers), dtype=bool)
    for t, ym in events:
        div_flag[ym - base, tick_pos[t]] = True

    def predicted(ym: int) -> np.ndarray:
        out = np.zeros(n_tickers, dtype=bool)
        for lag in LAGS:
            j = ym - lag - base
            if 0 <= j < div_flag.shape[0]:
                out |= div_flag[j]
        return out

    no_div_history = [t for t in tickers if t not in rows_per_ticker.index]

    # Month-by-month portfolios from January 2001 to the last complete month.
    rows = []
    skipped = []
    missing_months = []
    for ym in range(FULL_FIRST_YM, last_complete + 1):
        if ym not in ym_pos:
            missing_months.append(ym_label(ym))
            continue
        r = R[ym_pos[ym]]
        defined = np.isfinite(r)
        pred = predicted(ym)
        inP = defined & pred
        inN = defined & ~pred
        nP, nN, nU = int(inP.sum()), int(inN.sum()), int(defined.sum())
        if nP < MIN_STOCKS or nN < MIN_STOCKS:
            skipped.append({"month": ym_label(ym), "n_P": nP, "n_N": nN})
            continue
        P = float(r[inP].mean())
        N = float(r[inN].mean())
        U = float(r[defined].mean())
        rows.append({"ym": ym, "P": P, "N": N, "U": U, "D": P - U, "S": P - N,
                     "nP": nP, "nN": nN, "nU": nU,
                     "members": frozenset(np.flatnonzero(inP).tolist())})

    full_rows = rows
    oos_rows = [x for x in rows if x["ym"] >= OOS_FIRST_YM]
    skipped_oos = [s for s in skipped if parse_ym_label(s["month"]) >= OOS_FIRST_YM]

    # Primary.
    n_oos = len(oos_rows)
    D_oos = [x["D"] for x in oos_rows]
    S_oos = [x["S"] for x in oos_rows]
    mean_D, t_D = series_stats(D_oos)
    mean_S, t_S = series_stats(S_oos)
    if n_oos < MIN_OOS_MONTHS:
        primary = "INSUFFICIENT"
    elif mean_D is not None and t_D is not None and mean_D > 0 and t_D >= T_THRESHOLD:
        primary = "PASS"
    else:
        primary = "FAIL"
    verdict = primary

    # Full sample from January 2001.
    fD = [x["D"] for x in full_rows]
    fS = [x["S"] for x in full_rows]
    f_mean_D, f_t_D = series_stats(fD)
    f_mean_S, f_t_S = series_stats(fS)

    # Halves of the OOS: the defined OOS months split by count, the first half
    # taking floor(n / 2) months.
    h = n_oos // 2
    halves = []
    for part in (oos_rows[:h], oos_rows[h:]):
        if part:
            m, t = series_stats([x["D"] for x in part])
            halves.append({"first": ym_label(part[0]["ym"]), "last": ym_label(part[-1]["ym"]),
                           "n": len(part), "mean_D": fnum(m), "t_D": fnum(t)})
        else:
            halves.append({"first": None, "last": None, "n": 0, "mean_D": None, "t_D": None})

    # Strategy: hold P_m, equal weight, rebalanced each month, over the defined
    # OOS months. One-way turnover is half the L1 distance between consecutive
    # months' target weights; the first month is bought from cash, so its
    # turnover is 0.5 and its cost is 10 bp on the whole book. The cost is
    # 10 bp per leg on both legs: 2 * 10 bp * turnover.
    rf_month = load_rf_monthly(os.path.join(args.data, "ff5_daily.csv"))
    prev_w = {}
    turnovers, net, gross_U, rfs = [], [], [], []
    for x in oos_rows:
        w = {i: 1.0 / x["nP"] for i in x["members"]}
        keys = set(w) | set(prev_w)
        to = 0.5 * sum(abs(w.get(i, 0.0) - prev_w.get(i, 0.0)) for i in keys)
        turnovers.append(to)
        net.append(x["P"] - COST_PER_LEG * to * 2.0)
        gross_U.append(x["U"])
        rfs.append(rf_month.get(x["ym"], float("nan")))
        prev_w = w
    strat = performance(net, rfs)
    strat["mean_turnover"] = fnum(float(np.mean(turnovers))) if turnovers else None
    univ = performance(gross_U, rfs)
    n_no_rf = int(sum(1 for v in rfs if not math.isfinite(v)))

    # Alternative readings, recorded so a disagreement can be reconciled
    # without a rerun.
    alt = {
        "skipped_months_oos": len(skipped_oos),
        "skipped_months_full": len(skipped),
        "mean_P_full": fnum(np.mean([x["nP"] for x in full_rows])) if full_rows else None,
        "mean_U_full": fnum(np.mean([x["nU"] for x in full_rows])) if full_rows else None,
        "mean_turnover_excluding_first_month": fnum(np.mean(turnovers[1:])) if len(turnovers) > 1 else None,
        "first_oos_nominal": ym_label(OOS_FIRST_YM),
        "last_complete_month": ym_label(last_complete),
        "last_trading_day_in_prices": str(closes.index[-1].date()),
        "last_complete_month_end_date": str(month_end_date[last_complete].date()),
    }

    out = {
        "n_oos": n_oos,
        "first_oos": ym_label(oos_rows[0]["ym"]) if oos_rows else None,
        "last_oos": ym_label(oos_rows[-1]["ym"]) if oos_rows else None,
        "mean_D": fnum(mean_D), "t_D": fnum(t_D),
        "mean_S": fnum(mean_S), "t_S": fnum(t_S),
        "full": {"n": len(full_rows),
                 "first": ym_label(full_rows[0]["ym"]) if full_rows else None,
                 "last": ym_label(full_rows[-1]["ym"]) if full_rows else None,
                 "mean_D": fnum(f_mean_D), "t_D": fnum(f_t_D),
                 "mean_S": fnum(f_mean_S), "t_S": fnum(f_t_S)},
        "halves": halves,
        "strategy": {k: strat[k] for k in ("ann_return", "ann_vol", "sharpe", "max_drawdown", "mean_turnover")},
        "universe": {k: univ[k] for k in ("ann_return", "ann_vol", "sharpe", "max_drawdown")},
        "counts": {
            "mean_P": fnum(np.mean([x["nP"] for x in oos_rows])) if oos_rows else None,
            "mean_U": fnum(np.mean([x["nU"] for x in oos_rows])) if oos_rows else None,
            "tickers": n_tickers,
            "no_dividend_history": len(no_div_history),
            "skipped_months": len(skipped),
        },
        "criteria": {"primary": primary},
        "verdict": verdict,
        "choices": {
            "complete_month": complete_rule,
            "month_end_close": "the close on the last SPY trading day of the calendar month, "
                               "taken from prices.csv as given, no forward fill; a blank or "
                               "non-positive close means no month-end close",
            "monthly_return": "month-end close over the prior calendar month's month-end close "
                              "minus 1; undefined unless both exist and the months are consecutive",
            "predicted_payer": "any dividends.csv row for the ticker whose ex_date falls in "
                               "calendar month m-3, m-6, m-9 or m-12; amount not consulted; "
                               "rows for tickers absent from prices.csv ignored",
            "portfolio_membership": "P, N and U are formed over stocks with a defined return in m; "
                                    "a month with fewer than 20 in P or fewer than 20 in N is skipped",
            "skipped_months_scope": "counts.skipped_months counts the full computed range "
                                    "(2001-01 to the last complete month); the OOS-only count "
                                    "is under choices.alternatives",
            "first_last_oos": "first_oos and last_oos are the first and last DEFINED OOS months, "
                              "which equal the nominal bounds unless an end month was skipped",
            "newey_west": "regression on a constant; Bartlett kernel; L = 3; weights 1 - l/(L+1); "
                          "autocovariances divided by T; no small-sample correction; t = mean / sqrt(S/T)",
            "halves": "the defined OOS months split by count; first half takes floor(n/2) months",
            "strategy_period": "the defined OOS months, consecutive in the series (a skipped month "
                               "is simply absent, so turnover is measured between the months on "
                               "either side of it)",
            "turnover": "one-way: half the sum of absolute differences between consecutive months' "
                        "equal-weight target weights; the first month is bought from cash "
                        "(turnover 0.5); cost = 2 * 10 bp * turnover deducted from P_m",
            "annualisation": "geometric annual return wealth**(12/n) - 1; volatility and Sharpe use "
                             "the sample standard deviation (ddof = 1) and sqrt(12)",
            "risk_free": "monthly RF = product of (1 + RF/100) over the ff5_daily.csv rows in the "
                         "calendar month, minus 1; Sharpe is computed over the months for which "
                         "a monthly RF exists; the number lacking one is recorded",
            "max_drawdown": "minimum of wealth / running peak - 1 on the cumulative monthly series; "
                            "reported as a non-positive number",
            "counts_scope": "counts.mean_P and counts.mean_U average over the defined OOS months; "
                            "full-sample means are under choices.alternatives",
            "tickers": "every column of prices.csv after DATE except a column named SPY, which is "
                       "the calendar instrument and not a constituent",
            "verdict_when_insufficient": "criteria.primary and verdict both read INSUFFICIENT below "
                                         "120 OOS months; neither is coerced to FAIL",
            "alternatives": alt,
            "diagnostics": {
                "excluded_price_columns": excluded_cols,
                "dividend_rows": n_div_rows,
                "dividend_rows_outside_universe": n_div_rows_outside_universe,
                "tickers_without_dividend_history": no_div_history,
                "skipped": skipped,
                "calendar_months_absent_from_prices": missing_months,
                "strategy_months_without_rf": n_no_rf,
                "strategy_months": strat["n"],
                "first_month_in_prices": ym_label(months_present[0]),
            },
        },
    }

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "verify.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)

    def f(x, nd=6):
        return "null" if x is None else f"{x:.{nd}f}"
    print(f"verify.py: {n_tickers} tickers, {len(no_div_history)} without dividend history, "
          f"last complete month {ym_label(last_complete)}")
    print(f"OOS {out['first_oos']} to {out['last_oos']}: n = {n_oos}, "
          f"mean D = {f(out['mean_D'])}, t = {f(out['t_D'], 3)}; "
          f"mean S = {f(out['mean_S'])}, t = {f(out['t_S'], 3)}")
    print(f"full {out['full']['first']} to {out['full']['last']}: n = {out['full']['n']}, "
          f"mean D = {f(out['full']['mean_D'])}, t = {f(out['full']['t_D'], 3)}")
    for i, hh in enumerate(halves):
        print(f"half {i + 1} {hh['first']} to {hh['last']}: n = {hh['n']}, "
              f"mean D = {f(hh['mean_D'])}, t = {f(hh['t_D'], 3)}")
    s, u = out["strategy"], out["universe"]
    print(f"strategy net: ann {f(s['ann_return'], 4)} vol {f(s['ann_vol'], 4)} "
          f"sharpe {f(s['sharpe'], 3)} mdd {f(s['max_drawdown'], 4)} turnover {f(s['mean_turnover'], 4)}")
    print(f"universe:     ann {f(u['ann_return'], 4)} vol {f(u['ann_vol'], 4)} "
          f"sharpe {f(u['sharpe'], 3)} mdd {f(u['max_drawdown'], 4)}")
    print(f"skipped months: {len(skipped)} (OOS {len(skipped_oos)}); "
          f"mean |P| = {f(out['counts']['mean_P'], 2)}, mean |U| = {f(out['counts']['mean_U'], 2)}")
    print(f"primary: {primary}; verdict: {verdict}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
