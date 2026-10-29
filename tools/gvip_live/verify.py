"""Independent second implementation of the GVIP six-factor alpha test.

Governed by tools/gvip_live/PREREG.md, which carries over sections 3 and 4 of
tools/vip_premium/PREREG.md. Written from those two documents and the input
formats alone; no other code in the repository was read.

Usage: python verify.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os

import numpy as np

TICKERS = ("GVIP", "SPY", "QQQ", "RSP")
FACTORS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom")
NW_LAGS = 3
MIN_MONTHS = 96
T_MIN = 2.0
ALPHA_MIN = 0.02


def parse_date(s: str) -> dt.date:
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
    return dt.date.fromisoformat(s[:10])


def parse_num(s):
    if s is None:
        return None
    s = s.strip()
    if s == "" or s.lower() in ("nan", "na", "null", "none"):
        return None
    v = float(s)
    if not math.isfinite(v):
        return None
    return v


def read_table(path, cols):
    out = {}
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        rdr.fieldnames = [f.strip() for f in rdr.fieldnames]
        for row in rdr:
            d = row.get("DATE")
            if d is None or d.strip() == "":
                continue
            out[parse_date(d)] = {c: parse_num(row.get(c)) for c in cols}
    return out


def ym(d: dt.date):
    return (d.year, d.month)


def next_ym(m):
    return (m[0] + 1, 1) if m[1] == 12 else (m[0], m[1] + 1)


def fmt_ym(m):
    return f"{m[0]:04d}-{m[1]:02d}"


# ---------------------------------------------------------------- statistics

def ols(y, X):
    """OLS with intercept already in X. Returns beta and residuals."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta


def nw_cov(X, u, L=NW_LAGS):
    """Plain HAC sandwich (X'X)^-1 S (X'X)^-1, Bartlett 1 - l/(L+1), no
    small-sample correction."""
    n = X.shape[0]
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for l in range(1, L + 1):
        if l >= n:
            break
        w = 1.0 - l / (L + 1.0)
        G = Xu[l:].T @ Xu[:-l]
        S += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    return XtX_inv @ S @ XtX_inv


def regress(y, Xraw):
    """Regress y on [1, Xraw]; return (alpha_monthly, se, t, slopes)."""
    y = np.asarray(y, dtype=float)
    n = y.shape[0]
    if Xraw is None:
        X = np.ones((n, 1))
    else:
        Xraw = np.asarray(Xraw, dtype=float)
        if Xraw.ndim == 1:
            Xraw = Xraw[:, None]
        X = np.column_stack([np.ones(n), Xraw])
    beta, u = ols(y, X)
    V = nw_cov(X, u)
    se = float(math.sqrt(V[0, 0]))
    a = float(beta[0])
    return a, se, a / se, [float(b) for b in beta[1:]]


def max_drawdown(r):
    w = 1.0
    peak = 1.0
    mdd = 0.0
    for x in r:
        w *= 1.0 + x
        peak = max(peak, w)
        mdd = min(mdd, w / peak - 1.0)
    return mdd


# ---------------------------------------------------------------- pipeline

def build_months(data_dir):
    bench = read_table(os.path.join(data_dir, "bench.csv"), TICKERS)
    ff = read_table(os.path.join(data_dir, "ff5_daily.csv"),
                    ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"))
    mom = read_table(os.path.join(data_dir, "mom_daily.csv"), ("Mom",))

    spy_days = sorted(d for d, r in bench.items() if r["SPY"] is not None)
    if len(spy_days) < 2:
        raise SystemExit("bench.csv: fewer than two SPY trading days")

    # Daily returns on SPY trading days: close(d) / close(previous SPY day) - 1.
    rets = {t: {} for t in TICKERS}
    for i in range(1, len(spy_days)):
        d, p = spy_days[i], spy_days[i - 1]
        for t in TICKERS:
            c1, c0 = bench[d][t], bench[p][t]
            if c1 is not None and c0 is not None and c0 != 0.0:
                rets[t][d] = c1 / c0 - 1.0

    # Daily factor values in decimals, on French dates, all seven required.
    fac = {}
    for d, r in ff.items():
        m = mom.get(d)
        vals = dict(r)
        vals["Mom"] = None if m is None else m["Mom"]
        if all(vals[k] is not None for k in FACTORS + ("RF",)):
            fac[d] = {k: vals[k] / 100.0 for k in FACTORS + ("RF",)}

    gvip_first = next((d for d in spy_days if bench[d]["GVIP"] is not None), None)
    if gvip_first is None:
        raise SystemExit("bench.csv: GVIP has no price on any SPY trading day")
    first_m = next_ym(ym(gvip_first))
    # A month is known to be complete only if SPY trades in a later month.
    last_spy_m = ym(spy_days[-1])

    by_month = {}
    for d in spy_days:
        by_month.setdefault(ym(d), []).append(d)

    months = []
    for m in sorted(by_month):
        if m < first_m or m >= last_spy_m:
            continue
        days = by_month[m]
        if not all(d in rets[t] for d in days for t in TICKERS):
            continue
        if not all(d in fac for d in days):
            continue
        rec = {"month": m}
        for t in TICKERS:
            rec[t] = float(np.prod([1.0 + rets[t][d] for d in days]) - 1.0)
        for k in FACTORS + ("RF",):
            rec[k] = float(np.prod([1.0 + fac[d][k] for d in days]) - 1.0)
        months.append(rec)
    return months


def six_factor(ms):
    y = np.array([r["GVIP"] - r["RF"] for r in ms])
    X = np.array([[r[k] for k in FACTORS] for r in ms])
    return regress(y, X)


def analyse(months):
    n = len(months)
    if n < 8:
        raise SystemExit(f"only {n} usable months; too few to regress")
    a, se, t, slopes = six_factor(months)
    a_ann = 12.0 * a
    if n < MIN_MONTHS:
        verdict = "INSUFFICIENT"
    elif t >= T_MIN and a_ann >= ALPHA_MIN:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    rf = np.array([r["RF"] for r in months])
    x = np.array([r["GVIP"] for r in months]) - rf
    mkt = np.array([r["Mkt-RF"] for r in months])
    ca, _, ct, _ = regress(x, mkt)
    qx = np.array([r["QQQ"] for r in months]) - rf
    qa, _, qt, _ = regress(x, qx)

    g = np.array([r["GVIP"] for r in months])
    excess = {}
    for b in ("SPY", "QQQ", "RSP"):
        diff = g - np.array([r[b] for r in months])
        ea, _, et, _ = regress(diff, None)
        excess[b] = {"annual": 12.0 * ea, "t": et}

    stats = {"ann_mean": {}, "ann_vol": {}, "max_drawdown": {}}
    for key, tick in (("basket", "GVIP"), ("SPY", "SPY"), ("QQQ", "QQQ"), ("RSP", "RSP")):
        s = np.array([r[tick] for r in months])
        stats["ann_mean"][key] = 12.0 * float(s.mean())
        stats["ann_vol"][key] = math.sqrt(12.0) * float(s.std(ddof=1))
        stats["max_drawdown"][key] = max_drawdown(s)

    h = n // 2
    halves = []
    for part in (months[:h], months[h:]):
        ha, _, ht, _ = six_factor(part)
        halves.append({"first_month": fmt_ym(part[0]["month"]),
                       "last_month": fmt_ym(part[-1]["month"]),
                       "alpha_annual": 12.0 * ha, "t": ht})

    out = {
        "n_months": n,
        "first_month": fmt_ym(months[0]["month"]),
        "last_month": fmt_ym(months[-1]["month"]),
        "alpha_monthly": a,
        "alpha_annual": a_ann,
        "se": se,
        "t": t,
        "verdict": verdict,
        "loadings": dict(zip(FACTORS, slopes)),
        "capm_alpha_annual": 12.0 * ca,
        "capm_t": ct,
        "qqq_alpha_annual": 12.0 * qa,
        "qqq_t": qt,
        "excess_vs": excess,
        "share_months_beat_spy": float(np.mean(g > np.array([r["SPY"] for r in months]))),
        **stats,
        "halves": halves,
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    months = build_months(a.data)
    res = analyse(months)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"{res['first_month']}..{res['last_month']} n={res['n_months']} "
          f"alpha={res['alpha_annual']:.4%} t={res['t']:.3f} {res['verdict']}")
    return res


if __name__ == "__main__":
    main()
