"""Independent second implementation of PREREG.md sections 3 to 5.

Written from PREREG.md alone, without reading any other module under tools/,
so that agreement with the primary implementation is evidence that both read
the registered rules the same way rather than that one copied the other.

Usage: python verify.py --data DIR --out DIR
Reads DIR/series.csv and writes OUT/verify.json. numpy and the standard
library only; all arithmetic in float64.
"""

import argparse
import csv
import json
import math
import os

import numpy as np

COLS = ("SPY", "IRX", "PUT", "WPUT", "CNDR")
STRATS = ("PUT", "WPUT", "CNDR")
LAST_MONTH = (2026, 9)
SEED = 20261107
B = 1999
BLOCK = 12
LAGS = 3
N_MIN = 120
NORMAL_CRIT = 2.713


def parse_cell(text):
    """Return a float, or None where the cell is blank, non-numeric or non-finite.

    A missing value stays missing; it is never replaced by a working value,
    because a substituted number would enter the month-end selection silently.
    """
    if text is None:
        return None
    text = text.strip()
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def load(path):
    rows = []
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        for rec in reader:
            date = (rec.get("date") or "").strip()
            if len(date) < 10:
                continue
            try:
                y, m, d = int(date[0:4]), int(date[5:7]), int(date[8:10])
            except ValueError:
                continue
            values = tuple(parse_cell(rec.get(c)) for c in COLS)
            rows.append(((y, m, d), values))
    rows.sort(key=lambda r: r[0])
    return rows


def month_values(rows):
    """Map (year, month) to the five values on the last fully populated date.

    Only dates on which all five columns are present qualify; months after
    2026-09 are excluded.
    """
    chosen = {}
    for (y, m, d), values in rows:
        if (y, m) > LAST_MONTH:
            continue
        if any(v is None for v in values):
            continue
        key = (y, m)
        if key not in chosen or (y, m, d) > chosen[key][0]:
            chosen[key] = ((y, m, d), values)
    return {k: v[1] for k, v in chosen.items()}


def previous_month(ym):
    y, m = ym
    return (y - 1, 12) if m == 1 else (y, m - 1)


def build_returns(chosen):
    """Monthly total returns and bill rates, in calendar order.

    A month has a return only when the immediately preceding calendar month
    has a chosen date; the bill rate is that preceding month's IRX / 100 / 12.
    """
    months, rets, rf = [], [], []
    for ym in sorted(chosen):
        prev = previous_month(ym)
        if prev not in chosen:
            continue
        cur, pre = chosen[ym], chosen[prev]
        r = {}
        for i, c in enumerate(COLS):
            if c == "IRX":
                continue
            r[c] = cur[i] / pre[i] - 1.0
        months.append(ym)
        rets.append(r)
        rf.append(pre[COLS.index("IRX")] / 100.0 / 12.0)
    total = {c: np.array([r[c] for r in rets], dtype=np.float64) for c in ("SPY",) + STRATS}
    return months, total, np.array(rf, dtype=np.float64)


def ols_nw(y, x):
    """OLS of y on [1, x] with a Newey-West (3 lags, Bartlett) sandwich.

    No small-sample correction is applied, as section 3 registers.
    Returns (alpha, beta, se_alpha).
    """
    n = y.shape[0]
    X = np.column_stack([np.ones(n, dtype=np.float64), x])
    XtX = X.T @ X
    XtX_inv = np.linalg.inv(XtX)
    coef = XtX_inv @ (X.T @ y)
    u = y - X @ coef
    g = X * u[:, None]
    S = g.T @ g
    for lag in range(1, LAGS + 1):
        if lag >= n:
            break
        w = 1.0 - lag / (LAGS + 1.0)
        G = g[lag:].T @ g[:-lag]
        S = S + w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return float(coef[0]), float(coef[1]), float(math.sqrt(V[0, 0]))


def sharpe_monthly(x):
    return float(np.mean(x) / np.std(x, ddof=1))


def describe(total, excess):
    wealth = np.concatenate([[1.0], np.cumprod(1.0 + total)])
    peak = np.maximum.accumulate(wealth)
    maxdd = float(np.min(wealth / peak - 1.0))
    e = excess - np.mean(excess)
    sd_pop = np.std(excess, ddof=0)
    return {
        "ann_excess_mean": float(12.0 * np.mean(excess)),
        "ann_vol": float(math.sqrt(12.0) * np.std(excess, ddof=1)),
        "sharpe_ex": float(math.sqrt(12.0) * np.mean(excess) / np.std(excess, ddof=1)),
        "maxdd": maxdd,
        "skew": float(np.mean(e ** 3) / sd_pop ** 3),
        "worst": float(np.min(total)),
    }


def fmt(ym):
    return "%04d-%02d" % ym


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = load(os.path.join(args.data, "series.csv"))
    months, total, rf = build_returns(month_values(rows))
    n = len(months)
    excess = {c: total[c] - rf for c in total}

    # One draw of block starts, shared by all three strategies and by the
    # Sharpe-difference bootstrap, because the strategies are correlated and
    # independent draws would misstate the joint uncertainty (section 7.1).
    idx_rows = None
    if n >= BLOCK:
        rng = np.random.default_rng(SEED)
        starts = rng.integers(0, n - 11, size=(B, math.ceil(n / BLOCK)))
        idx_rows = [
            np.concatenate([np.arange(s, s + BLOCK) for s in row])[:n] for row in starts
        ]

    xs = excess["SPY"]
    out = {
        "n": n,
        "first_month": fmt(months[0]) if n else None,
        "last_month": fmt(months[-1]) if n else None,
        "strategies": {},
        "spy": describe(total["SPY"], xs),
        "sharpe_diff": {},
    }

    for s in STRATS:
        y = excess[s]
        a, b, se = ols_nw(y, xs)
        t = a / se
        crit = None
        alpha_p05 = alpha_p95 = None
        if idx_rows is not None:
            tstar = np.empty(B, dtype=np.float64)
            astar = np.empty(B, dtype=np.float64)
            for k, idx in enumerate(idx_rows):
                a_b, _, se_b = ols_nw(y[idx], xs[idx])
                astar[k] = a_b
                tstar[k] = (a_b - a) / se_b
            # Section 5: the bootstrap alpha's 5th and 95th percentiles,
            # annualised, from the same rows as the critical value. These are
            # reported without weight; the verdict does not read them.
            alpha_p05 = float(np.percentile(12.0 * astar, 5))
            alpha_p95 = float(np.percentile(12.0 * astar, 95))
            # The 99.667th percentile: a one-sided 1/3% test per strategy
            # (PREREG section 4 as corrected on 30 October 2026; the formula
            # first committed gave the 66.667th percentile in error).
            crit = float(np.percentile(tstar, 100.0 - 1.0 / 3.0))
        if n < N_MIN:
            verdict = verdict_normal = "INSUFFICIENT"
        else:
            verdict = "SUPPORTED" if (a > 0 and t >= crit) else "NOT SUPPORTED"
            verdict_normal = "SUPPORTED" if (a > 0 and t >= NORMAL_CRIT) else "NOT SUPPORTED"
        rec = {
            "verdict": verdict,
            "verdict_normal": verdict_normal,
            "alpha": a,
            "beta": b,
            "t": t,
            "crit": crit,
            "alpha_ann": 12.0 * a,
            "alpha_ann_p05": alpha_p05,
            "alpha_ann_p95": alpha_p95,
            "corr": float(np.corrcoef(y, xs)[0, 1]),
        }
        rec.update(describe(total[s], y))
        out["strategies"][s] = rec

    xp = excess["PUT"]
    for s in ("WPUT", "CNDR"):
        xa = excess[s]
        diff = sharpe_monthly(xa) - sharpe_monthly(xp)
        p05 = p95 = None
        if idx_rows is not None:
            d = np.array([sharpe_monthly(xa[i]) - sharpe_monthly(xp[i]) for i in idx_rows])
            p05 = float(np.percentile(d, 5))
            p95 = float(np.percentile(d, 95))
        out["sharpe_diff"][s + "_minus_PUT"] = {"diff": diff, "p05": p05, "p95": p95}

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as handle:
        json.dump(out, handle, indent=2)


if __name__ == "__main__":
    main()
