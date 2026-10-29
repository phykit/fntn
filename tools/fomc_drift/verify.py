#!/usr/bin/env python3
"""Independent second implementation of the pre-FOMC announcement-drift test.

Written from ``tools/fomc_drift/PREREG.md`` and the binding details supplied
with it, and from nothing else: ``run.py``, ``selftest.py``, ``fetch.py``, the
results directory and ``docs/`` were not opened. The point of a second
implementation is that it shares no code and no reading with the first, so an
agreement between the two means something and a disagreement locates an
ambiguity in the pre-registration rather than a shared bug. Every place where
the text admitted more than one reading is resolved here in one named way and
the resolution is written to ``choices`` in the output, so that a disagreement
can be traced to a reading rather than argued over.

Usage::

    python verify.py --data DIR --dates FILE --out DIR

Inputs under ``--data``: ``ndx.csv`` (observation_date, NASDAQ100; daily;
blank where missing), ``ff5_daily.csv`` (DATE, Mkt-RF, SMB, HML, RMW, CMA, RF;
per cent; daily), ``qqq.csv`` (DATE, QQQ adjusted closes; daily). ``--dates``
is ``fomc_dates.csv`` (year, meeting_start, meeting_end, announcement_day,
source_url; ISO dates).

Output: ``verify.json`` under ``--out``.

Non-evidentiary side test outside the FNTN funnel; not investment advice;
authorises nothing.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Fixed parameters, all taken from PREREG.md and the binding details.
# ---------------------------------------------------------------------------

FULL_START = pd.Timestamp("1994-02-01")  # first same-day-announced meeting
OOS_START = pd.Timestamp("2016-01-01")   # after publication
MIN_OOS_ANNOUNCEMENTS = 60               # INSUFFICIENT below this
P_MAX = 0.025                            # one-sided circular-shift threshold
SHIFT_MIN = 5                            # k = 5 .. n - 5
NW_LAGS = 5                              # Bartlett, L = 5
COST_PER_TRADE = 0.0002                  # 2 bp a trade
TRADES_PER_WINDOW = 2                    # in at close t-1, out at close t
TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------------------------------
# Loading. Each loader is deliberately literal about the column layout given
# in the binding details and refuses, rather than guessing, when the layout is
# not what was specified. Rows that cannot be parsed are counted and reported
# rather than silently discarded, because a silently discarded row is a value
# the test never saw and nobody can tell.
# ---------------------------------------------------------------------------


def _parse_dates(raw: pd.Series) -> pd.Series:
    """Parse a column of dates given as ISO (YYYY-MM-DD) or as YYYYMMDD.

    French's daily file carries YYYYMMDD; FRED, Yahoo and the agent-collected
    date list carry ISO. Accepting both means the test does not depend on
    whether a fetcher reformatted the column. Anything else becomes NaT and is
    counted by the caller.
    """
    s = raw.astype(str).str.strip()
    s = s.str.replace(r"^(\d{4})(\d{2})(\d{2})$", r"\1-\2-\3", regex=True)
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")


def _require_columns(df: pd.DataFrame, path: Path, required: list[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(
            f"{path}: missing required column(s) {missing}; found {list(df.columns)}"
        )


def _require_rows(df: pd.DataFrame, path: Path, what: str) -> None:
    if len(df) == 0:
        raise SystemExit(f"{path}: no usable {what} rows after parsing; refusing to continue")


def load_ndx(path: Path) -> tuple[pd.DataFrame, dict]:
    """NDX daily closes. A trading day is a row with a close; blank and '.'
    (FRED's two conventions for a missing value) are not closes."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(raw, path, ["observation_date", "NASDAQ100"])
    dates = _parse_dates(raw["observation_date"])
    vals = raw["NASDAQ100"].str.strip().replace({"": np.nan, ".": np.nan})
    close = pd.to_numeric(vals, errors="coerce")
    df = pd.DataFrame({"date": dates, "ndx": close})
    info = {
        "ndx_rows": int(len(df)),
        "ndx_rows_unparsed_date": int(df["date"].isna().sum()),
        "ndx_rows_without_close": int(df["date"].notna().sum() - df.dropna().shape[0]),
    }
    df = df.dropna().sort_values("date")
    _require_rows(df, path, "NDX close")
    dup = int(df["date"].duplicated().sum())
    if dup:
        raise SystemExit(f"{path}: {dup} duplicated date(s); refusing to choose between them")
    info["ndx_trading_days"] = int(len(df))
    info["ndx_first"] = df["date"].iloc[0].strftime("%Y-%m-%d")
    info["ndx_last"] = df["date"].iloc[-1].strftime("%Y-%m-%d")
    return df.reset_index(drop=True), info


def load_rf(path: Path) -> tuple[pd.DataFrame, dict]:
    """The daily risk-free rate from French's five-factor file, in per cent."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(raw, path, ["DATE", "RF"])
    dates = _parse_dates(raw["DATE"])
    rf = pd.to_numeric(raw["RF"].str.strip().replace({"": np.nan}), errors="coerce")
    df = pd.DataFrame({"date": dates, "rf_pct": rf})
    info = {
        "ff5_rows": int(len(df)),
        "ff5_rows_unparsed_date": int(df["date"].isna().sum()),
        "ff5_rows_without_rf": int(df["date"].notna().sum() - df.dropna().shape[0]),
    }
    df = df.dropna().sort_values("date")
    _require_rows(df, path, "RF")
    dup = int(df["date"].duplicated().sum())
    if dup:
        raise SystemExit(f"{path}: {dup} duplicated date(s); refusing to choose between them")
    info["ff5_last"] = df["date"].iloc[-1].strftime("%Y-%m-%d")
    return df.reset_index(drop=True), info


def load_qqq(path: Path) -> tuple[pd.DataFrame, dict]:
    """QQQ adjusted closes. The binding details name the columns DATE and QQQ;
    if the second is not literally 'QQQ' the second column is taken, because a
    Yahoo download may label it 'Adj Close'. That is the one place a header is
    not read literally, and it is recorded."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(raw, path, ["DATE"])
    if "QQQ" in raw.columns:
        vcol = "QQQ"
    elif len(raw.columns) >= 2:
        vcol = [c for c in raw.columns if c != "DATE"][0]
    else:
        raise SystemExit(f"{path}: no price column beside DATE")
    dates = _parse_dates(raw["DATE"])
    px = pd.to_numeric(raw[vcol].str.strip().replace({"": np.nan, ".": np.nan, "null": np.nan}),
                       errors="coerce")
    df = pd.DataFrame({"date": dates, "qqq": px})
    info = {
        "qqq_price_column": vcol,
        "qqq_rows": int(len(df)),
        "qqq_rows_unparsed_date": int(df["date"].isna().sum()),
        "qqq_rows_without_close": int(df["date"].notna().sum() - df.dropna().shape[0]),
    }
    df = df.dropna().sort_values("date")
    _require_rows(df, path, "QQQ close")
    dup = int(df["date"].duplicated().sum())
    if dup:
        raise SystemExit(f"{path}: {dup} duplicated date(s); refusing to choose between them")
    info["qqq_first"] = df["date"].iloc[0].strftime("%Y-%m-%d")
    info["qqq_last"] = df["date"].iloc[-1].strftime("%Y-%m-%d")
    return df.reset_index(drop=True), info


def load_announcements(path: Path) -> tuple[list[pd.Timestamp], dict]:
    """The announcement day of each scheduled meeting. Duplicated days are
    collapsed and counted; a day that cannot be parsed stops the run, because
    a date list the agent froze should not contain one."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(raw, path, ["announcement_day"])
    dates = _parse_dates(raw["announcement_day"])
    n_unparsed = int(dates.isna().sum())
    if n_unparsed:
        bad = raw.loc[dates.isna(), "announcement_day"].tolist()[:5]
        raise SystemExit(f"{path}: {n_unparsed} unparseable announcement_day value(s), e.g. {bad}")
    uniq = sorted(set(dates.tolist()))
    if not uniq:
        raise SystemExit(f"{path}: no announcement days; refusing to continue")
    info = {
        "fomc_rows": int(len(raw)),
        "fomc_duplicate_days": int(len(raw) - len(uniq)),
        "fomc_first": uniq[0].strftime("%Y-%m-%d"),
        "fomc_last": uniq[-1].strftime("%Y-%m-%d"),
    }
    return uniq, info


# ---------------------------------------------------------------------------
# Statistics.
# ---------------------------------------------------------------------------


def mean_difference(x: np.ndarray, a: np.ndarray) -> float:
    """mean(x | a) - mean(x | not a); NaN when either group is empty, because
    an empty group has no mean and a sentinel would be read as one."""
    n1 = int(a.sum())
    if n1 == 0 or n1 == len(a):
        return float("nan")
    return float(x[a].mean() - x[~a].mean())


def shift_test(x: np.ndarray, a: np.ndarray) -> tuple[float, float, int]:
    """One-sided circular-shift test.

    The indicator is rotated by k = SHIFT_MIN .. n - SHIFT_MIN inclusive (the
    pre-registration writes 'k = 5 .. n - 5'; a range written with its two
    ends is read as including both) with ``np.roll``, and
    p = (1 + #{k: d_k >= d}) / (1 + #k). Each rotation is evaluated as two
    masked means, exactly as the observed difference is, so that the rotations
    and the observed value share one arithmetic.
    """
    x = np.asarray(x, dtype=float)
    a = np.asarray(a, dtype=bool)
    n = len(x)
    d = mean_difference(x, a)
    ks = range(SHIFT_MIN, n - SHIFT_MIN + 1)
    n_shifts = len(ks)
    if math.isnan(d) or n_shifts <= 0:
        return d, float("nan"), int(max(n_shifts, 0))
    count = 0
    for k in ks:
        ak = np.roll(a, k)
        dk = x[ak].mean() - x[~ak].mean()
        if dk >= d:
            count += 1
    p = (1 + count) / (1 + n_shifts)
    return d, float(p), int(n_shifts)


def newey_west_ols(y: np.ndarray, X: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    """OLS with a Newey-West (Bartlett kernel) covariance, no small-sample
    correction: weights 1 - l/(L+1), no n/(n-k) factor, no prewhitening."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    e = y - X @ beta
    u = X * e[:, None]
    S = u.T @ u
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        G = u[lag:].T @ u[:-lag]
        S = S + w * (G + G.T)
    V = xtx_inv @ S @ xtx_inv
    return beta, V


def annualised_geometric(r: np.ndarray) -> float:
    """(prod(1 + r)) ** (252 / n) - 1 over the days actually in the sample."""
    r = np.asarray(r, dtype=float)
    if len(r) == 0:
        return float("nan")
    growth = float(np.prod(1.0 + r))
    return growth ** (TRADING_DAYS_PER_YEAR / len(r)) - 1.0


def sharpe(excess: np.ndarray) -> float:
    """mean / sample standard deviation (ddof = 1), times sqrt(252)."""
    excess = np.asarray(excess, dtype=float)
    if len(excess) < 2:
        return float("nan")
    sd = float(excess.std(ddof=1))
    if sd == 0.0:
        return float("nan")
    return float(excess.mean() / sd * math.sqrt(TRADING_DAYS_PER_YEAR))


# ---------------------------------------------------------------------------
# The test.
# ---------------------------------------------------------------------------


def _ffloat(v: float) -> float | None:
    """JSON has no NaN; a NaN is written as null so the file stays strict JSON
    and a reader sees an absence, not a number."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v)


def run(data_dir: Path, dates_file: Path, out_dir: Path) -> dict:
    ndx, ndx_info = load_ndx(data_dir / "ndx.csv")
    rf, rf_info = load_rf(data_dir / "ff5_daily.csv")
    qqq, qqq_info = load_qqq(data_dir / "qqq.csv")
    ann_days, ann_info = load_announcements(dates_file)

    # ---- trading days and daily excess returns ---------------------------
    # The return on a trading day is taken against the previous NDX close
    # (the previous trading day), before any day is dropped for want of RF, so
    # that dropping a day never silently lengthens its neighbour's window.
    s = ndx.copy()
    s["ret"] = s["ndx"] / s["ndx"].shift(1) - 1.0
    s = s.merge(rf, on="date", how="left")
    n_trading_without_rf = int(s["rf_pct"].isna().sum())
    trading_without_rf_after_last_rf = int(
        (s["rf_pct"].isna() & (s["date"] > rf["date"].max())).sum()
    )
    s = s.dropna(subset=["ret", "rf_pct"]).reset_index(drop=True)
    s["x"] = s["ret"] - s["rf_pct"] / 100.0

    # ---- announcement indicator -----------------------------------------
    trading_set = set(ndx["date"].tolist())
    sample_set = set(s["date"].tolist())
    n_dropped = sum(1 for d in ann_days if d not in trading_set)
    n_ann_trading_without_rf = sum(1 for d in ann_days if d in trading_set and d not in sample_set)
    ann_set = set(ann_days)
    s["A"] = s["date"].isin(ann_set).to_numpy()
    # Day before: the indicator moved one trading day earlier on the sample
    # series, so that the first OOS day can carry an announcement in 2016 only
    # if its successor does, and the last day of the series is never flagged.
    s["A_before"] = np.concatenate([s["A"].to_numpy()[1:], [False]])
    # Two-day window: the sum of x over t-1 and t on the sample series
    # (excess returns summed, not compounded), undefined on the first row.
    s["w"] = s["x"] + s["x"].shift(1)

    full = s[s["date"] >= FULL_START].reset_index(drop=True)
    oos = s[s["date"] >= OOS_START].reset_index(drop=True)

    # ---- primary, OOS ----------------------------------------------------
    x_oos = oos["x"].to_numpy(dtype=float)
    a_oos = oos["A"].to_numpy(dtype=bool)
    n_oos_days = int(len(oos))
    n_oos_ann = int(a_oos.sum())
    d_oos, p_oos, n_shifts = shift_test(x_oos, a_oos)

    sufficient = n_oos_ann >= MIN_OOS_ANNOUNCEMENTS
    primary = bool((not math.isnan(d_oos)) and d_oos > 0 and (not math.isnan(p_oos)) and p_oos <= P_MAX)
    if not sufficient:
        verdict = "INSUFFICIENT"
    elif primary:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    # ---- reported without weight ----------------------------------------
    mean_ann_bp = float(x_oos[a_oos].mean() * 1e4) if n_oos_ann else float("nan")
    mean_other_bp = float(x_oos[~a_oos].mean() * 1e4) if n_oos_ann < n_oos_days else float("nan")
    share_pos_ann = float((x_oos[a_oos] > 0).mean()) if n_oos_ann else float("nan")
    share_pos_all = float((x_oos > 0).mean()) if n_oos_days else float("nan")

    # Newey-West t of the OOS announcement-day mean. The regression is x on a
    # constant and A; the announcement-day mean is the sum of the two
    # coefficients, so its t uses c = [1, 1] against the HAC covariance. The
    # t on the A coefficient alone (the t of the difference) is reported
    # beside it as nw_t_diff_oos, because the text can be read either way.
    if n_oos_ann and n_oos_ann < n_oos_days:
        X = np.column_stack([np.ones(n_oos_days), a_oos.astype(float)])
        beta, V = newey_west_ols(x_oos, X, NW_LAGS)
        c = np.array([1.0, 1.0])
        var_mean = float(c @ V @ c)
        nw_t_mean = float((c @ beta) / math.sqrt(var_mean)) if var_mean > 0 else float("nan")
        nw_t_diff = float(beta[1] / math.sqrt(V[1, 1])) if V[1, 1] > 0 else float("nan")
    else:
        nw_t_mean = nw_t_diff = float("nan")

    # Day before and two-day window, OOS, with the same shift test.
    ab_oos = oos["A_before"].to_numpy(dtype=bool)
    d_before, p_before, n_shifts_before = shift_test(x_oos, ab_oos)
    w_mask = oos["w"].notna().to_numpy()
    d_two, p_two, n_shifts_two = shift_test(
        oos.loc[w_mask, "w"].to_numpy(dtype=float), a_oos[w_mask]
    )

    # Full sample.
    x_full = full["x"].to_numpy(dtype=float)
    a_full = full["A"].to_numpy(dtype=bool)
    d_full, p_full, n_shifts_full = shift_test(x_full, a_full)
    n_full_ann = int(a_full.sum())

    # By calendar year, OOS: the sum of announcement-day x against the year's
    # sum of x, in decimals (the units of x), one row per OOS year present.
    by_year = []
    years = oos["date"].dt.year
    for yr in sorted(years.unique().tolist()):
        rows = oos[years == yr]
        ann_rows = rows[rows["A"]]
        by_year.append({
            "year": int(yr),
            "ann_sum": float(ann_rows["x"].sum()),
            "total_sum": float(rows["x"].sum()),
            "n_ann": int(len(ann_rows)),
        })

    # ---- strategy on QQQ, OOS -------------------------------------------
    # The strategy runs on QQQ's own trading days (its return on day t is
    # against QQQ's previous close), matched to RF by date and dropping days
    # without RF under the same rule as NDX. It is long from the close of t-1
    # to the close of t for each announcement day t that was not dropped from
    # the NDX sample, paying 2 bp a trade, two trades a window, out of the
    # window return; cash earns RF on every other day. QQQ held is the same
    # days, invested throughout.
    q = qqq.copy()
    q["ret"] = q["qqq"] / q["qqq"].shift(1) - 1.0
    q = q.merge(rf, on="date", how="left")
    q = q.dropna(subset=["ret", "rf_pct"]).reset_index(drop=True)
    q = q[q["date"] >= OOS_START].reset_index(drop=True)
    q_rf = q["rf_pct"].to_numpy(dtype=float) / 100.0
    q_ret = q["ret"].to_numpy(dtype=float)
    q_a = q["date"].isin(ann_set & trading_set).to_numpy(dtype=bool)
    strat = np.where(q_a, q_ret - COST_PER_TRADE * TRADES_PER_WINDOW, q_rf)
    n_strat = int(len(q))
    strategy = {
        "ann_return": _ffloat(annualised_geometric(strat)),
        "sharpe": _ffloat(sharpe(strat - q_rf)),
        "invested_share": _ffloat(q_a.sum() / n_strat) if n_strat else None,
        "qqq_ann_return": _ffloat(annualised_geometric(q_ret)),
        "qqq_sharpe": _ffloat(sharpe(q_ret - q_rf)),
        "n_days": n_strat,
        "n_announcement_days": int(q_a.sum()),
        "first_day": q["date"].iloc[0].strftime("%Y-%m-%d") if n_strat else None,
        "last_day": q["date"].iloc[-1].strftime("%Y-%m-%d") if n_strat else None,
    }

    choices = {
        "return_definition": (
            "x_t = NDX_t / NDX_(t-1) - 1 - RF_t / 100, with NDX_(t-1) the previous NDX close "
            "(the previous trading day), computed before any day is dropped for want of RF"
        ),
        "trading_day_without_rf": (
            "dropped from the sample after its return is computed; the next day's return is "
            "still taken against that dropped day's close"
        ),
        "n_dropped_scope": (
            "every listed announcement day that is not an NDX day with a close, over the whole "
            "NDX file, irrespective of sample window; an announcement day that is an NDX "
            "trading day but lacks RF is not in n_dropped and is counted separately below"
        ),
        "sample_windows": (
            "full = sample days with date >= 1994-02-01; OOS = sample days with date >= "
            "2016-01-01, both to the last day with a return and RF"
        ),
        "shift_range": "k = 5 .. n - 5 inclusive at both ends, n the number of days in the window being tested; n_shifts = n - 9",
        "shift_comparison": "a rotation counts when its difference is >= the observed difference (float comparison, no tolerance)",
        "day_before": (
            "the announcement indicator moved one trading day earlier on the sample series "
            "(A_before[i] = A[i+1], last element 0), then restricted to the window; shift "
            "test rotates A_before"
        ),
        "two_day": (
            "w_t = x_(t-1) + x_t on the sample series (sum, not compounded), compared on "
            "announcement days against all other days with w defined; shift test rotates A over "
            "those days"
        ),
        "nw_t_oos": (
            "t of the announcement-day mean a + b from x = a + b A + e, Newey-West Bartlett "
            "L = 5, weights 1 - l / (L + 1), no small-sample correction; nw_t_diff_oos is the "
            "t of b alone"
        ),
        "mean_bp": "means of x in basis points (x * 1e4)",
        "share_positive_all": "share of all OOS sample days (announcement days included) with x > 0",
        "by_year_units": "sums of x in decimals; one row per calendar year present in the OOS sample, including years with no announcement day",
        "criteria_primary": (
            "d_oos > 0 and p_shift_oos <= 0.025, evaluated regardless of the sample floor; the "
            "verdict applies the floor (INSUFFICIENT below 60 OOS announcement days)"
        ),
        "strategy_days": (
            "QQQ trading days (rows with an adjusted close) from 2016-01-01 with RF, QQQ return "
            "against QQQ's previous close; announcement days are listed days that are NDX "
            "trading days"
        ),
        "strategy_cost": "window return minus 2 x 2 bp = 4 bp on each announcement day; cash days earn RF_t / 100",
        "annual_return": "(prod(1 + r)) ** (252 / n_days) - 1",
        "sharpe": "mean(r - RF) / std(r - RF, ddof = 1) * sqrt(252)",
        "diagnostics": {
            **ndx_info, **rf_info, **qqq_info, **ann_info,
            "trading_days_without_rf": n_trading_without_rf,
            "trading_days_without_rf_after_last_rf_date": trading_without_rf_after_last_rf,
            "announcement_days_trading_but_without_rf": int(n_ann_trading_without_rf),
            "sample_first": s["date"].iloc[0].strftime("%Y-%m-%d") if len(s) else None,
            "sample_last": s["date"].iloc[-1].strftime("%Y-%m-%d") if len(s) else None,
            "n_full_days": int(len(full)),
            "n_shifts_full": n_shifts_full,
            "n_shifts_day_before": n_shifts_before,
            "n_shifts_two_day": n_shifts_two,
            "n_two_day_days": int(w_mask.sum()),
        },
    }

    result = {
        "n_oos_days": n_oos_days,
        "n_oos_announcements": n_oos_ann,
        "n_dropped": int(n_dropped),
        "d_oos": _ffloat(d_oos),
        "p_shift_oos": _ffloat(p_oos),
        "n_shifts": n_shifts,
        "nw_t_oos": _ffloat(nw_t_mean),
        "nw_t_diff_oos": _ffloat(nw_t_diff),
        "mean_ann_bp_oos": _ffloat(mean_ann_bp),
        "mean_other_bp_oos": _ffloat(mean_other_bp),
        "share_positive_ann": _ffloat(share_pos_ann),
        "share_positive_all": _ffloat(share_pos_all),
        "d_full": _ffloat(d_full),
        "p_shift_full": _ffloat(p_full),
        "n_full_announcements": n_full_ann,
        "day_before": {"d": _ffloat(d_before), "p": _ffloat(p_before)},
        "two_day": {"d": _ffloat(d_two), "p": _ffloat(p_two)},
        "by_year": by_year,
        "strategy": strategy,
        "criteria": {"primary": primary},
        "verdict": verdict,
        "choices": choices,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "verify.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, allow_nan=False)
        fh.write("\n")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, type=Path, help="directory holding ndx.csv, ff5_daily.csv, qqq.csv")
    ap.add_argument("--dates", required=True, type=Path, help="fomc_dates.csv")
    ap.add_argument("--out", required=True, type=Path, help="output directory for verify.json")
    args = ap.parse_args(argv)
    for p in (args.data / "ndx.csv", args.data / "ff5_daily.csv", args.data / "qqq.csv", args.dates):
        if not p.is_file():
            print(f"missing input: {p}", file=sys.stderr)
            return 2
    res = run(args.data, args.dates, args.out)
    print(
        f"verdict={res['verdict']} n_oos_days={res['n_oos_days']} "
        f"n_oos_announcements={res['n_oos_announcements']} n_dropped={res['n_dropped']} "
        f"d_oos={res['d_oos']} p_shift_oos={res['p_shift_oos']} n_shifts={res['n_shifts']} "
        f"nw_t_oos={res['nw_t_oos']}"
    )
    print(f"wrote {args.out / 'verify.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
