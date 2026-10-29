"""Frozen test (PREREG.md governs): the short interest index (Rapach, Ringgenberg and Zhou 2016),
recursively detrended, as a predictor of the next month's Nasdaq 100 excess return.

Inputs under --data: sii.csv (a month column and an SII column; the parser finds the column whose
header contains "SII", case-insensitive, and reads months as YYYYMM, YYYY-MM, YYYY/MM, M/D/YYYY or
an ISO date), ndx.csv (FRED NASDAQ100: observation_date,NASDAQ100) and ff5_daily.csv (French daily
factors with RF in per cent).

Choices where the PREREG is silent, fixed before any SII value was seen:
- the recursive trend is fitted by OLS on a constant and a time index over every SII observation
  from the first month of the series to t (the series begins in 1973, so by the first NDX month the
  fit uses more than 150 observations); the signal is the residual at t, not standardised;
- a published SII that was itself detrended on its full sample is an affine function of time plus
  log short interest, and an affine function of time leaves the recursive residual unchanged, so the
  published index serves without recovering the raw ratio;
- month-end NDX = the last FRED observation of the month; monthly RF = the compounded daily French
  RF of the month; the forward excess return is log(NDX_(t+1) / NDX_t) - log(1 + RF_(t+1));
- the shift p counts rotations of the signal by 12 .. n - 12 months whose slope is at or below b;
- the out-of-sample forecast starts at aligned month 121, expanding window, against the expanding
  historical mean; the Clark-West statistic uses the Newey-West (L = 3) standard error of the mean
  of the adjusted loss differential.

Usage: python run.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402  frozen ols() with Newey-West L = 3

MIN_MONTHS = 240
OOS_FROM = 120
MIN_SHIFT = 12


def parse_month(s):
    s = str(s).strip()
    if re.fullmatch(r"\d{6}(\.0)?", s):
        v = int(float(s))
        return v // 100, v % 100
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})([-/]\d{1,2})?.*", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4}).*", s)
    if m:
        return int(m.group(3)), int(m.group(1))
    m = re.fullmatch(r"(\d{4})m(\d{1,2})", s, re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"unrecognised month: {s!r}")


def load_sii(path):
    rows = list(csv.reader(open(path, newline="", encoding="utf-8-sig")))
    rows = [r for r in rows if any(c.strip() for c in r)]
    hdr = rows[0]
    si = [i for i, h in enumerate(hdr) if "sii" in h.lower()]
    if not si:
        raise SystemExit(f"structure: no SII column in header {hdr}")
    si = si[0]
    di = 0 if si != 0 else 1
    out = {}
    for r in rows[1:]:
        if len(r) <= si or not r[si].strip():
            continue
        out[parse_month(r[di])] = float(r[si])
    print(f"sii.csv: header {hdr}; {len(out)} months, {min(out)} to {max(out)}")
    return out


def load_ndx_monthly(path):
    rows = list(csv.reader(open(path, newline="")))[1:]
    last = {}
    for r in rows:
        if r[1].strip():
            d = dt.date.fromisoformat(r[0])
            last[(d.year, d.month)] = float(r[1])  # rows are in date order: the last wins
    print(f"ndx.csv: {len(last)} months, {min(last)} to {max(last)}")
    return last


def load_rf_monthly(path):
    rf = {}
    for r in csv.DictReader(open(path, newline="")):
        if r["RF"].strip():
            d = dt.date.fromisoformat(r["DATE"])
            k = (d.year, d.month)
            rf[k] = rf.get(k, 1.0) * (1 + float(r["RF"]) / 100)
    return {k: v - 1 for k, v in rf.items()}


def next_month(k):
    y, m = k
    return (y + (m == 12), m % 12 + 1)


def recursive_residual(months, s):
    """Residual of SII_t on a constant and a time index fitted on observations 1..t."""
    n = len(s)
    t = np.arange(n, dtype=float)
    out = np.full(n, np.nan)
    for i in range(1, n):
        X = np.column_stack([np.ones(i + 1), t[:i + 1]])
        b, *_ = np.linalg.lstsq(X, s[:i + 1], rcond=None)
        out[i] = s[i] - (b[0] + b[1] * t[i])
    return out


def slope(y, x):
    xc = x - x.mean()
    return float((xc * (y - y.mean())).sum() / (xc * xc).sum())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    sii = load_sii(os.path.join(a.data, "sii.csv"))
    ndx = load_ndx_monthly(os.path.join(a.data, "ndx.csv"))
    rf = load_rf_monthly(os.path.join(a.data, "ff5_daily.csv"))
    sm = sorted(sii)
    resid = dict(zip(sm, recursive_residual(sm, np.array([sii[k] for k in sm]))))
    pairs = []
    for k in sm:
        nk = next_month(k)
        if k in ndx and nk in ndx and nk in rf and not np.isnan(resid[k]):
            y = math.log(ndx[nk] / ndx[k]) - math.log(1 + rf[nk])
            pairs.append((k, resid[k], y))
    n = len(pairs)
    x = np.array([p[1] for p in pairs])
    y = np.array([p[2] for p in pairs])
    res = {"n": n, "first_signal_month": f"{pairs[0][0][0]}-{pairs[0][0][1]:02d}", "last_signal_month": f"{pairs[-1][0][0]}-{pairs[-1][0][1]:02d}",
           "sii_months": len(sm), "sii_first": f"{sm[0][0]}-{sm[0][1]:02d}", "sii_last": f"{sm[-1][0]}-{sm[-1][1]:02d}"}
    if n < MIN_MONTHS:
        res["verdict"] = "INSUFFICIENT"
        print(json.dumps(res, indent=1))
        json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
        return 0
    b = slope(y, x)
    ks = range(MIN_SHIFT, n - MIN_SHIFT + 1)
    sl = np.array([slope(y, np.roll(x, k)) for k in ks])
    p = float((1 + np.sum(sl <= b)) / (1 + len(sl)))
    bb, se = vp.ols(y, x[:, None])
    res.update({"b": b, "b_per_sd": float(b * x.std(ddof=1)), "p_shift": p, "n_shifts": int(len(sl)), "nw_t": float(bb[1] / se[1]),
                "r2_in_sample": float(np.corrcoef(x, y)[0, 1] ** 2)})
    # out-of-sample R-squared and Clark-West
    err_m, err_mean, f = [], [], []
    for i in range(OOS_FROM, n):
        X = np.column_stack([np.ones(i), x[:i]])
        c, *_ = np.linalg.lstsq(X, y[:i], rcond=None)
        yhat = c[0] + c[1] * x[i]
        ybar = y[:i].mean()
        err_m.append(y[i] - yhat)
        err_mean.append(y[i] - ybar)
        f.append((y[i] - ybar) ** 2 - ((y[i] - yhat) ** 2 - (ybar - yhat) ** 2))
    err_m, err_mean, f = np.array(err_m), np.array(err_mean), np.array(f)
    res["r2_oos"] = float(1 - (err_m ** 2).sum() / (err_mean ** 2).sum())
    cw, cse = vp.ols(f, None)
    res["clark_west_t"] = float(cw[0] / cse[0])
    res["n_oos_forecasts"] = int(len(f))
    crit_a = b < 0 and p <= 0.025
    crit_b = res["r2_oos"] > 0 and res["clark_west_t"] >= 1.65
    res["criteria"] = {"primary": bool(crit_a), "oos": bool(crit_b)}
    res["verdict"] = "PASS" if (crit_a and crit_b) else ("WEAK" if crit_a else "FAIL")
    res["minimum_detectable_r2_80pct_power"] = float(2.49 ** 2 / (n + 2.49 ** 2))
    h = n // 2
    res["halves"] = [{"first": f"{pairs[s.start or 0][0][0]}-{pairs[s.start or 0][0][1]:02d}", "slope": slope(y[s], x[s])} for s in (slice(0, h), slice(h, None))]
    post = [i for i, pr in enumerate(pairs) if pr[0] >= (2015, 1)]
    if len(post) >= 24:
        res["post_2014 (no weight)"] = {"n": len(post), "slope": slope(y[post], x[post]),
                                       "nw_t": float((lambda r: r[0][1] / r[1][1])(vp.ols(y[post], x[post][:, None])))}
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
