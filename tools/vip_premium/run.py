"""Frozen test: does the hedge-fund VIP basket earn a six-factor alpha? (PREREG.md governs.)

The basket's daily returns come from Version B's frozen run.py (daily_legs), imported so that the
basket is exactly the one Version B registered. NON-EVIDENTIARY side test outside the FNTN funnel.

Usage: python run.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "degross_proxy_b"))
import run as vb  # noqa: E402  Version B's frozen run.py

FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]
L = 3


def read_daily(path, cols):
    out = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            vals = [r[c].strip() for c in cols]
            if all(vals):
                out[dt.date.fromisoformat(r["DATE"])] = [float(v) for v in vals]
    return out


def nw_se(X, e, lags=L):
    """Plain HAC sandwich with Bartlett weights 1 - l/(L+1); no small-sample correction."""
    XtX_inv = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(V))


def ols(y, F):
    X = np.column_stack([np.ones(len(y)), F]) if F is not None else np.ones((len(y), 1))
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    return b, nw_se(X, e)


def monthly(days, daily, ok):
    """Compound daily values over calendar months; months with any not-ok day are None."""
    out = {}
    for d, v, k in zip(days, daily, ok):
        key = (d.year, d.month)
        cur = out.setdefault(key, [1.0, True])
        if not k:
            cur[1] = False
        else:
            cur[0] *= 1 + v
    return {k: (v[0] - 1 if v[1] else None) for k, v in out.items()}


def maxdd(r):
    v = np.cumprod(1 + np.array(r))
    return float(np.min(v / np.maximum.accumulate(v)) - 1)


def analyse(months, x, F, ret, rf):
    n = len(months)
    res = {"n_months": n, "first_month": f"{months[0][0]}-{months[0][1]:02d}" if n else None,
           "last_month": f"{months[-1][0]}-{months[-1][1]:02d}" if n else None}
    b, se = ols(x, F)
    res.update({"alpha_monthly": float(b[0]), "alpha_annual": float(12 * b[0]), "se": float(se[0]),
                "t": float(b[0] / se[0]), "loadings": {f: float(b[i + 1]) for i, f in enumerate(FACTORS)}})
    if n < 120:
        res["verdict"] = "INSUFFICIENT"
    elif res["t"] >= 2.0 and res["alpha_annual"] >= 0.02:
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
    bc, sec = ols(x, F[:, [0]])
    res["capm_alpha_annual"], res["capm_t"] = float(12 * bc[0]), float(bc[0] / sec[0])
    qx = ret["QQQ"] - rf
    bq, seq = ols(x, qx[:, None])
    res["qqq_alpha_annual"], res["qqq_t"] = float(12 * bq[0]), float(bq[0] / seq[0])
    res["excess_vs"] = {}
    for k in ("SPY", "QQQ", "RSP"):
        dlt = ret["basket"] - ret[k]
        bb, ss = ols(dlt, None)
        res["excess_vs"][k] = {"annual": float(12 * bb[0]), "t": float(bb[0] / ss[0])}
    res["share_months_beat_spy"] = float(np.mean(ret["basket"] > ret["SPY"]))
    res["ann_mean"] = {k: float(12 * ret[k].mean()) for k in ("basket", "SPY", "QQQ", "RSP")}
    res["ann_vol"] = {k: float(np.sqrt(12) * ret[k].std(ddof=1)) for k in ("basket", "SPY", "QQQ", "RSP")}
    res["max_drawdown"] = {k: maxdd(ret[k]) for k in ("basket", "SPY", "QQQ", "RSP")}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, col, px = vb.load_prices(a.data)
    bk = vb.load_baskets(a.data)
    bk = {e: {"long": v["long"], "short": []} for e, v in bk.items() if v["long"]}
    W, _, _, cov = vb.daily_legs(days, col, px, bk)
    ff = read_daily(os.path.join(a.data, "ff5_daily.csv"), ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
    mom = read_daily(os.path.join(a.data, "mom_daily.csv"), ["Mom"])
    bench = {}
    with open(os.path.join(a.data, "bench.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            bench[dt.date.fromisoformat(r["DATE"])] = [float(r[s]) if r[s].strip() else np.nan for s in ("SPY", "QQQ", "RSP")]
    n = len(days)
    bpx = np.array([bench.get(d, [np.nan] * 3) for d in days])
    bret = np.full((n, 3), np.nan)
    bret[1:] = bpx[1:] / bpx[:-1] - 1
    series = {"basket": W}
    for j, s in enumerate(("SPY", "QQQ", "RSP")):
        series[s] = bret[:, j]
    for j, f in enumerate(["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]):
        series[f] = np.array([ff[d][j] / 100 if d in ff else np.nan for d in days])
    series["Mom"] = np.array([mom[d][0] / 100 if d in mom else np.nan for d in days])
    ok = np.ones(n, bool)
    for v in series.values():
        ok &= ~np.isnan(v)
    first_earn = days[int(np.argmax(~np.isnan(W)))]
    start = (first_earn.year + (first_earn.month == 12), first_earn.month % 12 + 1)
    last_factor = max(d for d in ff if d in mom)
    mon = {k: monthly(days, np.nan_to_num(v), ok) for k, v in series.items()}
    keys = sorted(k for k in mon["basket"] if k >= start and k <= (last_factor.year, last_factor.month)
                  and all(mon[s][k] is not None for s in mon))
    # the last factor month must be full: drop it if the factors end before that month's last SPY day
    last_spy_in_month = max(d for d in days if (d.year, d.month) == (last_factor.year, last_factor.month))
    if last_factor < last_spy_in_month and keys and keys[-1] == (last_factor.year, last_factor.month):
        keys = keys[:-1]
    ret = {k: np.array([mon[k][m] for m in keys]) for k in mon}
    rf = ret["RF"]
    x = ret["basket"] - rf
    F = np.column_stack([ret[f] for f in FACTORS])
    res = analyse(keys, x, F, ret, rf)
    h = len(keys) // 2
    res["halves"] = []
    for sl in (slice(0, h), slice(h, None)):
        sub = keys[sl]
        b, se = ols(x[sl], F[sl])
        res["halves"].append({"first_month": f"{sub[0][0]}-{sub[0][1]:02d}", "last_month": f"{sub[-1][0]}-{sub[-1][1]:02d}",
                              "alpha_annual": float(12 * b[0]), "t": float(b[0] / se[0])})
    res["basket_entered_median"] = float(np.median([c["long_entered"] for c in cov]))
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    with open(os.path.join(a.out, "results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
