"""Alpha of Cboe's option-selling benchmarks against SPY (tools/vrp_benchmarks/PREREG.md).
Frozen implementation; every rule is the pre-registration's."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

COLS = ("SPY", "IRX", "PUT", "WPUT", "CNDR")
STRATS = ("PUT", "WPUT", "CNDR")
LAST = "2026-09"
SEED = 20261107
B = 1999
BLOCK = 12
MIN_N = 120
PCT = 100 - 1 / 3  # the 99.667th percentile (PREREG section 4, as corrected)
Z_NORMAL = 2.713


def monthly(path: str):
    """Month values on the last date with all five series present (section 3)."""
    with open(path) as f:
        rows = list(csv.reader(f))
    head = rows[0]
    ix = {c: head.index(c) for c in COLS}

    def val(r, c):
        j = ix[c]
        if j >= len(r):
            return None
        try:
            v = float(r[j])
        except ValueError:
            return None
        return v if math.isfinite(v) else None

    last = {}
    for r in sorted(rows[1:], key=lambda r: r[0]):
        vs = {c: val(r, c) for c in COLS}
        if all(v is not None for v in vs.values()):
            last[r[0][:7]] = vs
    ms = sorted(last)
    months, R, RF = [], {c: [] for c in COLS if c != "IRX"}, []
    for prev, cur in zip(ms, ms[1:]):
        py, pm, cy, cm = int(prev[:4]), int(prev[5:7]), int(cur[:4]), int(cur[5:7])
        if (cy * 12 + cm) - (py * 12 + pm) != 1 or cur > LAST:
            continue
        months.append(cur)
        RF.append(last[prev]["IRX"] / 100.0 / 12.0)
        for c in R:
            R[c].append(last[cur][c] / last[prev][c] - 1.0)
    return months, {c: np.array(v) for c, v in R.items()}, np.array(RF)


def ols_nw(y, x):
    """OLS of y on [1, x]; Newey-West sandwich, 3 lags, Bartlett 1 - l/4, no small-sample correction.
    Works row-wise when y and x are 2-D (replications by months)."""
    y = np.atleast_2d(y)
    x = np.atleast_2d(x)
    n = y.shape[1]
    xm, ym = x.mean(1, keepdims=True), y.mean(1, keepdims=True)
    sxx = ((x - xm) ** 2).sum(1)
    b = ((x - xm) * (y - ym)).sum(1) / sxx
    a = ym[:, 0] - b * xm[:, 0]
    u = y - a[:, None] - b[:, None] * x
    # Rows of X are (1, x_t). Score g_t = u_t * (1, x_t).
    g0, g1 = u, u * x
    S00 = (g0 * g0).sum(1)
    S01 = (g0 * g1).sum(1)
    S11 = (g1 * g1).sum(1)
    for l in range(1, 4):
        w = 1.0 - l / 4.0
        S00 = S00 + w * 2 * (g0[:, l:] * g0[:, :-l]).sum(1)
        S11 = S11 + w * 2 * (g1[:, l:] * g1[:, :-l]).sum(1)
        S01 = S01 + w * ((g0[:, l:] * g1[:, :-l]).sum(1) + (g1[:, l:] * g0[:, :-l]).sum(1))
    sx = x.sum(1)
    sxx2 = (x * x).sum(1)
    det = n * sxx2 - sx * sx
    # (X'X)^-1 = [[sxx2, -sx], [-sx, n]] / det
    i00, i01, i11 = sxx2 / det, -sx / det, n / det
    # Variance of the intercept: row 0 of inv * S * col 0 of inv
    var_a = i00 * (i00 * S00 + i01 * S01) + i01 * (i00 * S01 + i01 * S11)
    return a, b, np.sqrt(var_a)


def sh(x) -> float:
    return float(x.mean() / x.std(ddof=1))


def maxdd(r) -> float:
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r)])
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def describe(r, x) -> dict:
    e = x - x.mean()
    return {"ann_excess_mean": float(12 * x.mean()), "ann_vol": float(math.sqrt(12) * x.std(ddof=1)),
            "sharpe_ex": sh(x) * math.sqrt(12), "maxdd": maxdd(r),
            "skew": float(np.mean(e ** 3) / x.std(ddof=0) ** 3), "worst": float(r.min())}


def analyse(months, R, RF, reps: int = B) -> dict:
    n = len(months)
    res = {"n": n, "first_month": months[0] if n else None, "last_month": months[-1] if n else None}
    if n < BLOCK:
        return res
    X = {c: R[c] - RF for c in R}
    rng = np.random.default_rng(SEED)
    starts = rng.integers(0, n - BLOCK + 1, size=(reps, math.ceil(n / BLOCK)))
    idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(reps, -1)[:, :n]
    res["strategies"] = {}
    for s in STRATS:
        a, b, se = (v[0] for v in ols_nw(X[s], X["SPY"]))
        t = float(a / se)
        ab, _, seb = ols_nw(X[s][idx], X["SPY"][idx])
        tstar = (ab - a) / seb
        crit = float(np.percentile(tstar, PCT))
        if n < MIN_N:
            v = vn = "INSUFFICIENT"
        else:
            v = "SUPPORTED" if a > 0 and t >= crit else "NOT SUPPORTED"
            vn = "SUPPORTED" if a > 0 and t >= Z_NORMAL else "NOT SUPPORTED"
        d = {"verdict": v, "verdict_normal": vn, "alpha": float(a), "beta": float(b), "t": t, "crit": crit,
             "alpha_ann": float(12 * a), "alpha_ann_p05": float(12 * np.percentile(ab, 5)),
             "alpha_ann_p95": float(12 * np.percentile(ab, 95)),
             "corr": float(np.corrcoef(X[s], X["SPY"])[0, 1])}
        d.update(describe(R[s], X[s]))
        res["strategies"][s] = d
    res["spy"] = describe(R["SPY"], X["SPY"])
    res["sharpe_diff"] = {}
    for s in ("WPUT", "CNDR"):
        A, P = X[s][idx], X["PUT"][idx]
        dstar = A.mean(1) / A.std(1, ddof=1) - P.mean(1) / P.std(1, ddof=1)
        res["sharpe_diff"][f"{s}_minus_PUT"] = {"diff": sh(X[s]) - sh(X["PUT"]),
                                                "p05": float(np.percentile(dstar, 5)),
                                                "p95": float(np.percentile(dstar, 95))}
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(*monthly(os.path.join(a.data, "series.csv")))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    for s, d in res.get("strategies", {}).items():
        print(f"VERDICT {s}: {d['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
