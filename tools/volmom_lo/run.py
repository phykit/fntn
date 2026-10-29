"""Frozen test (PREREG.md governs): volatility-managed momentum as a long-only MTUM/SPY tilt, net of
costs, with the published 12% target capped at a weight of one.

Inputs under --data: bench.csv (DATE,MTUM,SPY adjusted closes) and ff5_daily.csv (French daily, RF
in per cent). Writes results.json to --out.

Choices where the PREREG is silent, fixed before any figure was computed: the spread day series is
the rows where both daily returns exist; a month-end is the last spread day of a calendar month;
holdings drift with prices between rebalances and are reset to (w, 1 - w) after the execution
day's return; the first decided weight is charged against a prior all-SPY holding; comparators
"MTUM held" and SPY are in place from the first day of the first strategy month (no delay, no
cost) and never trade; the weight statistics and turnover cover the executed weights; the 50/50 comparator
resets to 0.5/0.5 on each execution day with the same 20 bp x |traded fraction| cost.

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
import run as vp  # noqa: E402  frozen ols() with Newey-West L = 3

_spec = importlib.util.spec_from_file_location("run_volmom", os.path.join(HERE, "..", "volmom", "run.py"))
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
complete_months, sharpe_fn, maxdd, boot_p = _vm.complete_months, _vm.sharpe, _vm.maxdd, _vm.boot_p

WIN, SCALE = 126, 21
S_T = 0.12 / math.sqrt(12)
COST = 0.002
MIN_MONTHS = 96
SEED = 20261029


def load(data):
    rows = [r for r in csv.DictReader(open(os.path.join(data, "bench.csv"), newline="")) if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {k: np.array([float(r[k]) if r[k].strip() else np.nan for r in rows]) for k in ("MTUM", "SPY")}
    ret = {}
    for k, v in px.items():
        x = np.full(len(days), np.nan)
        x[1:] = v[1:] / v[:-1] - 1
        ret[k] = x
    ok = ~np.isnan(ret["MTUM"]) & ~np.isnan(ret["SPY"])
    idx = np.where(ok)[0]
    sd = [days[i] for i in idx]
    rm, rs = ret["MTUM"][idx], ret["SPY"][idx]
    rf = {}
    for r in csv.DictReader(open(os.path.join(data, "ff5_daily.csv"), newline="")):
        if r["RF"].strip():
            d = dt.date.fromisoformat(r["DATE"])
            k = (d.year, d.month)
            rf[k] = rf.get(k, 1.0) * (1 + float(r["RF"]) / 100)
    return days, sd, rm, rs, {k: v - 1 for k, v in rf.items()}


def simulate(sd, rm, rs, weights_at, policy):
    """Daily wealth path for a policy: 'strategy' (decided weights), 'fifty' (0.5 each month), or a
    float (static MTUM fraction held from the start, never traded). weights_at: {month-end index:
    decided w}. Returns daily returns (NaN before the first strategy month) and the trade log."""
    n = len(sd)
    out = np.full(n, np.nan)
    keys = [(d.year, d.month) for d in sd]
    decided = sorted(weights_at)
    if not decided:
        return out, []
    start = decided[0] + 1  # first spread day of the month after the first decided weight
    xm = xs = None
    w_prev = 0.0
    trades = []
    pending = {decided[j] + 1: weights_at[decided[j]] for j in range(len(decided)) if decided[j] + 1 < n}
    for t in range(start, n):
        if t == start:
            if policy in ("strategy", "fifty"):
                w = pending[t] if policy == "strategy" else 0.5
                out[t] = rs[t] - COST * abs(w - w_prev)  # earned at the prior all-SPY holding, then switched
                trades.append((sd[t], w))
                w_prev = w
            else:
                w = float(policy)  # a static holding is in place from the first day: no delay, no cost
                out[t] = w * rm[t] + (1 - w) * rs[t]
            xm, xs = w, 1 - w
            continue
        r = xm * rm[t] + xs * rs[t]
        xm, xs = xm * (1 + rm[t]), xs * (1 + rs[t])
        tot = xm + xs
        xm, xs = xm / tot, xs / tot
        if t in pending and policy in ("strategy", "fifty"):
            w = pending[t] if policy == "strategy" else 0.5
            r -= COST * abs(w - w_prev)
            xm, xs = w, 1 - w
            w_prev = w
            trades.append((sd[t], w))
        out[t] = r
    return out, trades


def monthly(sd, daily, months):
    keys = [(d.year, d.month) for d in sd]
    out = {}
    for k in months:
        seg = daily[[i for i, kk in enumerate(keys) if kk == k]]
        out[k] = float(np.prod(1 + seg) - 1) if len(seg) and not np.isnan(seg).any() else np.nan
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, sd, rm, rs, rf = load(a.data)
    d = rm - rs
    n = len(sd)
    keys = [(x.year, x.month) for x in sd]
    month_end = [i for i in range(n) if i + 1 == n or keys[i + 1] != keys[i]]
    weights_at = {}
    for i in month_end:
        if i + 1 >= WIN:
            v = SCALE / WIN * float(np.sum(d[i + 1 - WIN:i + 1] ** 2))
            weights_at[i] = min(1.0, S_T / math.sqrt(v))
    strat, trades = simulate(sd, rm, rs, weights_at, "strategy")
    fifty, _ = simulate(sd, rm, rs, weights_at, "fifty")
    held, _ = simulate(sd, rm, rs, weights_at, 1.0)
    spy_d, _ = simulate(sd, rm, rs, weights_at, 0.0)
    comp = complete_months(days)
    first_k = keys[sorted(weights_at)[0] + 1] if weights_at else None
    months = [k for k in comp if first_k and k >= first_k and k in rf]
    ms = {name: monthly(sd, arr, months) for name, arr in (("strategy", strat), ("fifty", fifty), ("mtum", held), ("spy", spy_d))}
    months = [k for k in months if all(not np.isnan(ms[nm][k]) for nm in ms)]
    nm = len(months)
    res = {"n_months": nm, "first_month": f"{months[0][0]}-{months[0][1]:02d}" if nm else None,
           "last_month": f"{months[-1][0]}-{months[-1][1]:02d}" if nm else None}
    R = {name: np.array([ms[name][k] for k in months]) for name in ms}
    RF = np.array([rf[k] for k in months])
    A = R["strategy"] - R["spy"]
    S = R["mtum"] - R["spy"]
    b, se = vp.ols(A, S[:, None])
    res.update({"alpha_monthly": float(b[0]), "alpha_t": float(b[0] / se[0]), "b": float(b[1]),
                "sharpe_active": sharpe_fn(A), "sharpe_static_active": sharpe_fn(S),
                "p_boot": boot_p(S, A, np.random.default_rng(SEED)),
                "sharpe_strategy": sharpe_fn(R["strategy"] - RF), "sharpe_spy": sharpe_fn(R["spy"] - RF)})
    ca = res["alpha_monthly"] > 0 and res["alpha_t"] >= 2.0
    cb = (res["sharpe_active"] - res["sharpe_static_active"]) >= 0.2 * abs(res["sharpe_static_active"]) and res["p_boot"] <= 0.05
    cc = res["sharpe_strategy"] >= res["sharpe_spy"]
    res["criteria"] = {"a": bool(ca), "b": bool(cb), "c": bool(cc)}
    if nm < MIN_MONTHS:
        res["verdict"] = "INSUFFICIENT"
    elif ca and cb and cc:
        res["verdict"] = "PASS"
    elif ca or cb:
        res["verdict"] = "WEAK"
    else:
        res["verdict"] = "FAIL"
    res["stats"] = {}
    for name in ("spy", "mtum", "fifty", "strategy"):
        x = R[name]
        res["stats"][name] = {"ann_return": float(np.prod(1 + x) ** (12 / nm) - 1), "ann_vol": float(math.sqrt(12) * x.std(ddof=1)),
                              "sharpe": sharpe_fn(x - RF), "max_drawdown": maxdd(x)}
    w = np.array([t[1] for t in trades])  # the executed weights, as PREREG section 3 reports them
    res["weight"] = {"min": float(w.min()), "median": float(np.median(w)), "max": float(w.max()),
                     "share_capped": float(np.mean(w >= 1.0)), "share_below_half": float(np.mean(w < 0.5))}
    tw = np.array([t[1] for t in trades])
    turn = float(np.sum(np.abs(np.diff(np.concatenate([[0.0], tw])))))
    years = nm / 12
    res["turnover_annual"], res["cost_annual"] = turn / years, COST * turn / years
    res["active_vs_mtum_held"] = {"ann": float(12 * np.mean(R["strategy"] - R["mtum"])), "sharpe": sharpe_fn(R["strategy"] - R["mtum"])}
    yr = {}
    for k, s, p in zip(months, R["strategy"], R["spy"]):
        yr.setdefault(k[0], [[], []])
        yr[k[0]][0].append(s); yr[k[0]][1].append(p)
    res["yearly"] = [{"year": y, "strategy": float(np.prod(1 + np.array(v[0])) - 1), "spy": float(np.prod(1 + np.array(v[1])) - 1)} for y, v in sorted(yr.items())]
    last_complete_me = max(i for i in weights_at if keys[i] in comp)
    res["live_weight_last_complete_month"] = {"as_at": sd[last_complete_me].isoformat(), "w": weights_at[last_complete_me]}
    vlast = SCALE / WIN * float(np.sum(d[n - WIN:] ** 2))
    res["live_weight_latest"] = {"as_at": sd[-1].isoformat(), "w": min(1.0, S_T / math.sqrt(vlast))}
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
