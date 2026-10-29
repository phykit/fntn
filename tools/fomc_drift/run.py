"""Frozen test (PREREG.md governs): the pre-FOMC announcement drift on the Nasdaq 100, out of
sample from 2016.

Inputs under --data: ndx.csv (observation_date,NASDAQ100), ff5_daily.csv (French daily, RF %),
qqq.csv (DATE,QQQ adjusted closes); --dates fomc_dates.csv (announcement_day column).

Choices fixed before any data was seen: a trading day without a French RF is dropped; the day-before
indicator marks the trading day immediately before each announcement day; the two-day window is the
sum of x over t-1 and t, compared with the same sum ending on every non-announcement day; the
Newey-West t is the coefficient on the indicator in x = a + b A + e with L = 5; the strategy's cash
earns the daily French RF; the QQQ window return is QQQ_t / QQQ_(t-1) - 1 less 4 bp (two trades).

Usage: python run.py --data DATA_DIR --dates FILE --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402

OOS_START, FULL_START, MIN_ANN, MIN_SHIFT, NW_L = dt.date(2016, 1, 1), dt.date(1994, 2, 1), 60, 5, 5
COST = 0.0004


def load_ndx(path):
    rows = list(csv.reader(open(path, newline="")))[1:]
    out = [(dt.date.fromisoformat(r[0]), float(r[1])) for r in rows if r[1].strip()]
    return [o[0] for o in out], np.array([o[1] for o in out])


def load_rf(path):
    return {dt.date.fromisoformat(r["DATE"]): float(r["RF"]) / 100 for r in csv.DictReader(open(path, newline="")) if r["RF"].strip()}


def load_qqq(path):
    return {dt.date.fromisoformat(r["DATE"]): float(r["QQQ"]) for r in csv.DictReader(open(path, newline="")) if r["QQQ"].strip()}


def diff_and_p(x, A, lo, hi):
    """Mean on indicator days minus mean on other days, and the one-sided circular-shift p."""
    d = float(x[A].mean() - x[~A].mean())
    n = len(x)
    cnt = 0
    for k in range(lo, hi + 1):
        Ak = np.roll(A, k)
        if x[Ak].mean() - x[~Ak].mean() >= d:
            cnt += 1
    return d, float((1 + cnt) / (1 + (hi - lo + 1))), hi - lo + 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dates", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, px = load_ndx(os.path.join(a.data, "ndx.csv"))
    rf = load_rf(os.path.join(a.data, "ff5_daily.csv"))
    ann = {dt.date.fromisoformat(r["announcement_day"]) for r in csv.DictReader(open(a.dates, newline=""))}
    # daily excess returns on trading days with RF
    keep = [i for i in range(1, len(days)) if days[i] in rf]
    td = [days[i] for i in keep]
    x = np.array([px[i] / px[i - 1] - 1 - rf[days[i]] for i in keep])
    tset = set(td)
    n_dropped = sum(1 for d in ann if d >= FULL_START and d <= td[-1] and d not in tset)
    A = np.array([d in ann for d in td])
    Aprev = np.zeros(len(td), bool); Aprev[:-1] = A[1:]
    full = np.array([d >= FULL_START for d in td])
    oos = np.array([d >= OOS_START for d in td])
    res = {"n_oos_days": int(oos.sum()), "n_oos_announcements": int((A & oos).sum()), "n_dropped": int(n_dropped),
           "n_full_announcements": int((A & full).sum())}
    xo, Ao = x[oos], A[oos]
    d, p, ns = diff_and_p(xo, Ao, MIN_SHIFT, len(xo) - MIN_SHIFT)
    res.update({"d_oos": d, "p_shift_oos": p, "n_shifts": ns})
    X = np.column_stack([np.ones(len(xo)), Ao.astype(float)])
    bb, *_ = np.linalg.lstsq(X, xo, rcond=None)
    e = xo - X @ bb
    XtX = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, NW_L + 1):
        wgt = 1 - l / (NW_L + 1)
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += wgt * (G + G.T)
    seb = np.sqrt(np.diag(XtX @ S @ XtX))
    res["nw_t_oos"] = float(bb[1] / seb[1])
    res["mean_ann_bp_oos"], res["mean_other_bp_oos"] = float(1e4 * xo[Ao].mean()), float(1e4 * xo[~Ao].mean())
    res["share_positive_ann"], res["share_positive_all"] = float(np.mean(xo[Ao] > 0)), float(np.mean(xo > 0))
    res["criteria"] = {"primary": bool(d > 0 and p <= 0.025)}
    res["verdict"] = "INSUFFICIENT" if res["n_oos_announcements"] < MIN_ANN else ("PASS" if res["criteria"]["primary"] else "FAIL")
    xf, Af = x[full], A[full]
    df, pf, _ = diff_and_p(xf, Af, MIN_SHIFT, len(xf) - MIN_SHIFT)
    res["d_full"], res["p_shift_full"] = df, pf
    dpb, ppb, _ = diff_and_p(xo, Aprev[oos], MIN_SHIFT, len(xo) - MIN_SHIFT)
    res["day_before"] = {"d": dpb, "p": ppb}
    two = np.full(len(x), np.nan); two[1:] = x[1:] + x[:-1]
    to = two[oos]; ok = ~np.isnan(to)
    d2, p2, _ = diff_and_p(to[ok], Ao[ok], MIN_SHIFT, int(ok.sum()) - MIN_SHIFT)
    res["two_day"] = {"d": d2, "p": p2}
    by = {}
    for dd, xx, aa in zip([t for t, o in zip(td, oos) if o], xo, Ao):
        y = by.setdefault(dd.year, [0.0, 0.0, 0])
        y[1] += xx
        if aa:
            y[0] += xx; y[2] += 1
    res["by_year"] = [{"year": y, "ann_sum": v[0], "total_sum": v[1], "n_ann": v[2]} for y, v in sorted(by.items())]
    # strategy on QQQ, OOS
    q = load_qqq(os.path.join(a.data, "qqq.csv"))
    qd = [t for t in td if t in q]
    prev = {qd[i]: qd[i - 1] for i in range(1, len(qd))}
    sr, rfs, qr, inv = [], [], [], 0
    for t in td:
        if t < OOS_START or t not in prev:
            continue
        r_q = q[t] / q[prev[t]] - 1
        qr.append(r_q); rfs.append(rf[t])
        if t in ann:
            sr.append(r_q - COST); inv += 1
        else:
            sr.append(rf[t])
    sr, rfs, qr = np.array(sr), np.array(rfs), np.array(qr)
    n = len(sr)
    ann_ret = lambda r: float(np.prod(1 + r) ** (252 / len(r)) - 1)
    shp = lambda r: float(math.sqrt(252) * (r - rfs).mean() / (r - rfs).std(ddof=1))
    res["strategy"] = {"ann_return": ann_ret(sr), "sharpe": shp(sr), "invested_share": inv / n,
                       "qqq_ann_return": ann_ret(qr), "qqq_sharpe": shp(qr)}
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
