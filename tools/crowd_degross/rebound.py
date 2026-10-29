"""Study R (PREREG_rebound.md governs): after a bad week for crowded longs against QQQ, do the next
20 trading days rebound? Primary GVIP minus QQQ; the reconstructed basket, other horizons, a
de-clustered version and the long-GVIP short-QQQ trade without weight.

Choices where the PREREG is silent, fixed before any data was seen: the 10th percentile uses numpy's
default (linear); "no other signal in the 4 preceding weeks" refers to the raw signal (x at or below
its percentile, window complete), whatever the eligibility of those weeks; the trade skips a signal
whose entry day is on or before the open trade's exit day; years spanned = (last eligible week-end -
first eligible week-end) / 365.25 days.

Usage: python rebound.py --bench DIR --data-b DIR --episodes CSV --out DIR
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crowd2 as k2  # noqa: E402
import run as c2  # noqa: E402

SEED = 20261029
N_PERM = 10_000
WIN, PCT, GAP, MIN_SIG = 104, 0.10, 14, 20
COST, BORROW = 0.004, 0.005


def fwd(r, e, h):
    """Compounded simple return over daily returns e+1 .. e+h (entry at close e); NaN if missing."""
    if e + h >= len(r):
        return np.nan
    s = r[e + 1:e + h + 1]
    return np.nan if np.isnan(s).any() else float(np.prod(1 + s) - 1)


def analyse(x, R, elig, sig, rng):
    pool = R[elig]
    vals = R[elig & sig]
    out = {"n_eligible": int(elig.sum()), "n_signal": int((elig & sig).sum())}
    if len(vals) == 0:
        out.update({"mean_signal": None, "mean_eligible": float(pool.mean()) if len(pool) else None, "p_upper": None})
        return out
    obs = float(vals.mean())
    draws = np.array([rng.choice(pool, size=len(vals), replace=False).mean() for _ in range(N_PERM)])
    out.update({"mean_signal": obs, "mean_eligible": float(pool.mean()),
                "p_upper": float((1 + np.sum(draws >= obs)) / (1 + N_PERM)),
                "share_positive": float(np.mean(vals > 0))})
    return out


def trade(entries, R, elig, sig, ends, h):
    net, last_exit = [], -1
    for t in np.where(elig & sig)[0]:
        e = entries[t]
        if e <= last_exit:
            continue
        net.append(R[t] - COST - BORROW * h / 252)
        last_exit = e + h
    net = np.array(net)
    et = np.where(elig)[0]
    years = (ends[et[-1]] - ends[et[0]]).days / 365.25 if len(et) else float("nan")
    if len(net) == 0:
        return {"trades": 0}
    return {"trades": int(len(net)), "share_profitable": float(np.mean(net > 0)), "mean_net": float(net.mean()),
            "median_net": float(np.median(net)),
            "t_mean": float(net.mean() / (net.std(ddof=1) / np.sqrt(len(net)))) if len(net) > 1 else None,
            "worst": float(net.min()), "sum_net_per_year": float(net.sum() / years)}


def build(days, ret, leg, keys, wk, ends, frozen, h):
    pos = {d: i for i, d in enumerate(days)}
    x = wk[leg] - wk["QQQ"]
    T = len(keys)
    entries = np.array([pos[ends[t]] + 1 for t in range(T)])
    R = np.array([fwd(ret[leg], entries[t], h) - fwd(ret["QQQ"], entries[t], h) for t in range(T)])
    raw = np.zeros(T, bool)
    complete = np.zeros(T, bool)
    for t in range(WIN, T):
        hst = x[t - WIN:t]
        if np.isnan(hst).any() or np.isnan(x[t]):
            continue
        complete[t] = True
        raw[t] = x[t] <= np.quantile(hst, PCT)
    near = np.array([any(abs((ends[t] - f).days) <= GAP for f in frozen) for t in range(T)])
    elig = complete & ~np.isnan(R) & ~near
    return x, R, raw, elig, entries


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, ret = c2.load_bench(os.path.join(a.bench, "bench.csv"))
    ret["W"], _ = k2.legs_b(a.data_b, days, a.bench)
    keys, wk = c2.weekly(days, ret)
    ends = k2.week_ends(days)
    frozen = [e["week_end"] for e in c2.load_eps(a.episodes)]
    res = {}
    x, R, sig, elig, ent = build(days, ret, "GVIP", keys, wk, ends, frozen, 20)
    res.update(analyse(x, R, elig, sig, np.random.default_rng(SEED)))
    res["verdict"] = ("INSUFFICIENT" if res["n_signal"] < MIN_SIG else
                      "SUPPORTED" if res["p_upper"] <= 0.05 else "NOT SUPPORTED")
    xb, Rb, sigb, eligb, entb = build(days, ret, "W", keys, wk, ends, frozen, 20)
    res["basket"] = analyse(xb, Rb, eligb, sigb, np.random.default_rng(SEED))
    for hz in (5, 10):
        _, Rh, sh, eh, _ = build(days, ret, "GVIP", keys, wk, ends, frozen, hz)
        res[f"h{hz}"] = analyse(None, Rh, eh, sh, np.random.default_rng(SEED))
    prev = np.array([sig[max(0, t - 4):t].any() for t in range(len(sig))])
    res["declustered"] = analyse(x, R, elig, sig & ~prev, np.random.default_rng(SEED))
    res["trade_gvip"] = trade(ent, R, elig, sig, ends, 20)
    res["trade_basket"] = trade(entb, Rb, eligb, sigb, ends, 20)
    et = np.where(elig)[0]
    res["first_eligible"], res["last_eligible"] = ends[et[0]].isoformat(), ends[et[-1]].isoformat()
    print(json.dumps(res, indent=1, default=str))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results_rebound.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
