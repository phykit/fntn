"""Frozen test (PREREG.md governs): the dividend month premium, long-only, out of sample from 2010.

Inputs under --data: prices.csv (DATE then one column per ticker, adjusted closes on SPY trading
days, blank where missing), dividends.csv (ticker,ex_date,amount), ff5_daily.csv (French daily, RF %).

Choices fixed before any data was seen: a stock's monthly return needs its close on the last trading
day of the month and of the prior month; a month is skipped when P or N holds fewer than 20 stocks;
the strategy's turnover is one-way (half the sum of absolute changes between consecutive months'
equal weights, the first month from cash) and costs 10 bp a leg on both legs; the universe
comparator carries no cost.

Usage: python run.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_volmom", os.path.join(HERE, "..", "volmom", "run.py"))
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
complete_months, sharpe_fn, maxdd = _vm.complete_months, _vm.sharpe, _vm.maxdd

OOS_START, FULL_START, MIN_MONTHS, MIN_STOCKS, COST = (2010, 1), (2001, 1), 120, 20, 0.001
LAGS = (3, 6, 9, 12)


def shift_month(k, back):
    y, m = k
    t = y * 12 + (m - 1) - back
    return (t // 12, t % 12 + 1)


def load_prices(path):
    rows = list(csv.reader(open(path, newline="")))
    hdr = rows[0][1:]
    days = [dt.date.fromisoformat(r[0]) for r in rows[1:]]
    px = np.full((len(days), len(hdr)), np.nan)
    for i, r in enumerate(rows[1:]):
        for j, v in enumerate(r[1:]):
            if v.strip():
                px[i, j] = float(v)
    return hdr, days, px


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    tick, days, px = load_prices(os.path.join(a.data, "prices.csv"))
    idx = {t: j for j, t in enumerate(tick)}
    exm = {}
    for r in csv.DictReader(open(os.path.join(a.data, "dividends.csv"), newline="")):
        if r["ticker"] in idx:
            d = dt.date.fromisoformat(r["ex_date"][:10])
            exm.setdefault(r["ticker"], set()).add((d.year, d.month))
    no_hist = sum(1 for t in tick if t not in exm)
    rf = {}
    for r in csv.DictReader(open(os.path.join(a.data, "ff5_daily.csv"), newline="")):
        if r["RF"].strip():
            d = dt.date.fromisoformat(r["DATE"]); k = (d.year, d.month)
            rf[k] = rf.get(k, 1.0) * (1 + float(r["RF"]) / 100)
    rf = {k: v - 1 for k, v in rf.items()}
    keys = [(d.year, d.month) for d in days]
    last_idx = {}
    for i, k in enumerate(keys):
        last_idx[k] = i
    comp = set(complete_months(days))
    months = [k for k in sorted(last_idx) if k in comp and shift_month(k, 1) in last_idx and k >= FULL_START and k in rf]
    P, N, U, nP, nU, weights = [], [], [], [], [], []
    used = []
    skipped = 0
    for k in months:
        i1, i0 = last_idx[k], last_idx[shift_month(k, 1)]
        r = px[i1] / px[i0] - 1
        ok = ~np.isnan(r)
        pred = np.array([any(shift_month(k, L) in exm.get(t, ()) for L in LAGS) for t in tick])
        p_mask, n_mask = ok & pred, ok & ~pred
        if p_mask.sum() < MIN_STOCKS or n_mask.sum() < MIN_STOCKS:
            skipped += 1
            continue
        used.append(k)
        P.append(r[p_mask].mean()); N.append(r[n_mask].mean()); U.append(r[ok].mean())
        nP.append(int(p_mask.sum())); nU.append(int(ok.sum()))
        w = np.where(p_mask, 1.0 / p_mask.sum(), 0.0)
        weights.append(w)
    P, N, U = np.array(P), np.array(N), np.array(U)
    D, S = P - U, P - N
    oos = np.array([k >= OOS_START for k in used])
    res = {"n_oos": int(oos.sum()), "first_oos": f"{used[np.argmax(oos)][0]}-{used[np.argmax(oos)][1]:02d}" if oos.any() else None,
           "last_oos": f"{used[-1][0]}-{used[-1][1]:02d}"}

    def mt(x):
        b, se = vp.ols(x, None)
        return float(b[0]), float(b[0] / se[0])

    res["mean_D"], res["t_D"] = mt(D[oos])
    res["mean_S"], res["t_S"] = mt(S[oos])
    res["criteria"] = {"primary": bool(res["mean_D"] > 0 and res["t_D"] >= 2.0)}
    res["verdict"] = "INSUFFICIENT" if res["n_oos"] < MIN_MONTHS else ("PASS" if res["criteria"]["primary"] else "FAIL")
    fD, fS = mt(D), mt(S)
    res["full"] = {"n": int(len(D)), "mean_D": fD[0], "t_D": fD[1], "mean_S": fS[0], "t_S": fS[1]}
    oi = np.where(oos)[0]; h = len(oi) // 2
    res["halves"] = []
    for sl in (oi[:h], oi[h:]):
        m, t = mt(D[sl])
        res["halves"].append({"first": f"{used[sl[0]][0]}-{used[sl[0]][1]:02d}", "last": f"{used[sl[-1]][0]}-{used[sl[-1]][1]:02d}", "mean_D": m, "t_D": t})
    # strategy, OOS
    W = np.array(weights)
    turn = np.zeros(len(used))
    turn[0] = 0.5 * np.abs(W[0]).sum()
    for i in range(1, len(used)):
        turn[i] = 0.5 * np.abs(W[i] - W[i - 1]).sum()
    net = P - 2 * COST * turn
    rfv = np.array([rf[k] for k in used])

    def st(x, cost_turn=None):
        xo = x[oos]
        out = {"ann_return": float(np.prod(1 + xo) ** (12 / len(xo)) - 1), "ann_vol": float(math.sqrt(12) * xo.std(ddof=1)),
               "sharpe": sharpe_fn(xo - rfv[oos]), "max_drawdown": maxdd(xo)}
        if cost_turn is not None:
            out["mean_turnover"] = float(cost_turn[oos].mean())
        return out

    res["strategy"] = st(net, turn)
    res["universe"] = st(U)
    res["counts"] = {"mean_P": float(np.mean(np.array(nP)[oos])), "mean_U": float(np.mean(np.array(nU)[oos])), "tickers": len(tick),
                     "no_dividend_history": no_hist, "skipped_months": skipped}
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
