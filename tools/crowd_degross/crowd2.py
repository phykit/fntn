"""Studies 2a to 2d (PREREG_2.md governs): short side, momentum, rally-matched control and a
real-time nowcast, with a Holm adjustment across the four primary p-values.

Inputs: --bench (bench.csv, ff5_daily.csv, mom_daily.csv as written by tools/gvip_live/fetch.py),
--data-b (Version B's prices.csv and baskets.csv, or "none"), --ndx (FRED NASDAQ100 CSV), --episodes.

Usage: python crowd2.py --bench DIR --data-b DIR --ndx CSV --episodes CSV --out DIR
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
sys.path.insert(0, HERE)
import run as c2  # noqa: E402  study 2's frozen run.py

SEED = 20261029
N_PERM = 10_000
MIN_EP = 8
Z_WIN, Z_TH = 104, -2.0
FAC = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]


def read_fac(path, cols):
    out = {}
    for r in csv.DictReader(open(path, newline="")):
        v = [r[c].strip() for c in cols]
        if all(v):
            out[dt.date.fromisoformat(r["DATE"])] = [float(x) / 100 for x in v]
    return out


def legs_b(data_b, days, bench_dir=None):
    if data_b == "bench":  # self-test only: W and L daily returns as columns of bench.csv
        rows = {r["DATE"]: r for r in csv.DictReader(open(os.path.join(bench_dir, "bench.csv"), newline=""))}
        return tuple(np.array([float(rows[d.isoformat()][c]) if d.isoformat() in rows and rows[d.isoformat()][c] else np.nan
                               for d in days]) for c in ("W", "L"))
    if data_b == "none":
        return np.full(len(days), np.nan), np.full(len(days), np.nan)
    sys.path.insert(0, os.path.join(HERE, "..", "degross_proxy_b"))
    import run as vb  # noqa: E402
    bd, col, px = vb.load_prices(data_b)
    W, L, _, _ = vb.daily_legs(bd, col, px, vb.load_baskets(data_b))
    mw, ml = dict(zip(bd, W)), dict(zip(bd, L))
    return np.array([mw.get(d, np.nan) for d in days]), np.array([ml.get(d, np.nan) for d in days])


def week_ends(days):
    keys = [d.isocalendar()[:2] for d in days]
    return [days[i] for i in range(len(days)) if i + 1 == len(days) or keys[i + 1] != keys[i]]


def ndx_pre10(path, keys):
    rows = list(csv.reader(open(path, newline="")))[1:]
    pairs = sorted((dt.date.fromisoformat(r[0]), float(r[1])) for r in rows if r[1].strip())
    nd, px = [p[0] for p in pairs], np.array([p[1] for p in pairs])
    last = {}
    for i, d in enumerate(nd):
        last[d.isocalendar()[:2]] = i
    out = np.full(len(keys), np.nan)
    for t, k in enumerate(keys):
        i = last.get(k)
        if i is not None and i >= 10:
            out[t] = px[i] / px[i - 10] - 1
    return out


def perm(vals, pool, rng):
    obs = float(np.mean(vals))
    draws = np.array([rng.choice(pool, size=len(vals), replace=False).mean() for _ in range(N_PERM)])
    return obs, float((1 + np.sum(draws <= obs)) / (1 + N_PERM)), float((1 + np.sum(draws >= obs)) / (1 + N_PERM))


def at(arr, idx):
    return np.array([arr[t] for t in idx if t is not None and not np.isnan(arr[t])])


def stat(arr, idx, rng):
    vals, pool = at(arr, idx), arr[~np.isnan(arr)]
    if len(vals) == 0:
        return {"n": 0}
    obs, pl, pu = perm(vals, pool, rng)
    return {"n": int(len(vals)), "mean": obs, "unconditional_mean": float(pool.mean()), "p_lower": pl, "p_upper": pu,
            "share_negative": float(np.mean(vals < 0))}


def window14(f, b):
    T = len(f)
    return np.array([c2.window(f, t, 1, 4) - c2.window(b, t, 1, 4) for t in range(T)])


def holm(ps):
    m = len(ps)
    order = sorted(range(m), key=lambda i: (math.isnan(ps[i]), ps[i]))
    adj, run_max = [float("nan")] * m, 0.0
    for r, i in enumerate(order):
        if math.isnan(ps[i]):
            continue
        run_max = max(run_max, min(1.0, (m - r) * ps[i]))
        adj[i] = run_max
    return adj


def binom_tail(k, n, q):
    return sum(math.comb(n, j) * q ** j * (1 - q) ** (n - j) for j in range(k, n + 1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--ndx", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, ret = c2.load_bench(os.path.join(a.bench, "bench.csv"))
    ret["W"], ret["L"] = legs_b(a.data_b, days, a.bench)
    ff = read_fac(os.path.join(a.bench, "ff5_daily.csv"), FAC)
    mo = read_fac(os.path.join(a.bench, "mom_daily.csv"), ["Mom"])
    for j, f in enumerate(FAC):
        ret[f] = np.array([ff[d][j] if d in ff else np.nan for d in days])
    ret["Mom"] = np.array([mo[d][0] if d in mo else np.nan for d in days])
    keys, wk = c2.weekly(days, ret)
    ends = week_ends(days)
    kidx = {k: t for t, k in enumerate(keys)}
    eps_all = c2.load_eps(a.episodes)
    epsD = [e for e in eps_all if e["cls"] == "D"]
    idx = [kidx.get(e["week_end"].isocalendar()[:2]) for e in epsD]
    res, prim = {"weeks": len(keys)}, {}

    # 2a short side
    rng = np.random.default_rng(SEED)
    s_e0 = wk["L"] - wk["QQQ"]
    res["2a"] = {"L-QQQ E0": stat(s_e0, idx, rng),
                 "L-QQQ E1_4 (no weight)": stat(window14(wk["L"], wk["QQQ"]), idx, rng),
                 "W-L E0 (no weight)": stat(wk["W"] - wk["L"], idx, rng)}
    prim["2a"] = (res["2a"]["L-QQQ E0"], "p_upper")

    # 2b momentum and other factors
    rng = np.random.default_rng(SEED)
    res["2b"] = {"Mom E0": stat(wk["Mom"], idx, rng)}
    for f in FAC[1:]:
        s = stat(wk[f], idx, rng)
        if s.get("n"):
            s["p_two_sided"] = min(1.0, 2 * min(s["p_lower"], s["p_upper"]))
        res["2b"][f"{f} E0 (no weight)"] = s
    prim["2b"] = (res["2b"]["Mom E0"], "p_lower")

    # 2c rally-matched control
    rng = np.random.default_rng(SEED)
    g = wk["GVIP"] - wk["QQQ"]
    pre = ndx_pre10(a.ndx, keys)
    ok = ~np.isnan(g) & ~np.isnan(pre)
    cuts = np.quantile(pre[ok], [0.2, 0.4, 0.6, 0.8])
    quint = np.where(ok, np.searchsorted(cuts, pre, side="right"), -1)
    ep = [t for t in idx if t is not None and ok[t]]
    if len(ep) == 0:
        res["2c"] = {"n": 0}
        prim["2c"] = ({"n": 0}, "p_lower")
    else:
        obs = float(np.mean(g[ep]))
        pools = {q: np.where(quint == q)[0] for q in range(5)}
        need = {q: sum(quint[t] == q for t in ep) for q in range(5)}
        draws = np.empty(N_PERM)
        for k in range(N_PERM):
            tot = 0.0
            for q, m in need.items():
                if m:
                    tot += g[rng.choice(pools[q], size=m, replace=False)].sum()
            draws[k] = tot / len(ep)
        res["2c"] = {"n": len(ep), "mean": obs, "matched_null_mean": float(draws.mean()),
                     "p_lower": float((1 + np.sum(draws <= obs)) / (1 + N_PERM)),
                     "episode_quintiles": [int(quint[t]) for t in ep], "quintile_cuts": [float(c) for c in cuts]}
        prim["2c"] = (res["2c"], "p_lower")

    # 2d nowcast
    T = len(keys)
    z = np.full(T, np.nan)
    for t in range(Z_WIN, T):
        h = g[t - Z_WIN:t]
        if np.isnan(h).any() or np.isnan(g[t]):
            continue
        sd = h.std(ddof=1)
        if sd > 0:
            z[t] = (g[t] - h.mean()) / sd
    defined = ~np.isnan(z)
    sig = defined & (z <= Z_TH)
    b = float(sig.sum() / defined.sum()) if defined.any() else float("nan")
    q = 1 - (1 - b) ** 3
    dts = [ends[t] for t in range(T) if defined[t]]
    lo, hi = (min(dts), max(dts)) if dts else (None, None)
    sweeks = [ends[t] for t in range(T) if sig[t]]
    scored = [e for e in epsD if lo and lo <= e["week_end"] <= hi]
    hit = [e["id"] for e in scored if any(abs((s - e["week_end"]).days) <= 7 for s in sweeks)]
    n, k = len(scored), len(hit)
    p = binom_tail(k, n, q) if n else float("nan")
    near = [s for s in sweeks if any(abs((s - e["week_end"]).days) <= 7 for e in eps_all)]
    rng = np.random.default_rng(SEED)
    idx_m1 = [t - 1 if t is not None and t > 0 else None for t in idx]
    res["2d"] = {"n": n, "hits": k, "hit_ids": hit, "hit_rate": k / n if n else float("nan"), "signal_rate": b,
                 "chance_per_episode": q, "p": p, "signal_weeks": len(sweeks),
                 "precision (no weight)": len(near) / len(sweeks) if sweeks else float("nan"),
                 "episode_z": {e["id"]: (None if t is None or np.isnan(z[t]) else float(z[t])) for e, t in zip(epsD, idx)},
                 "E-1 GVIP-QQQ (no weight)": stat(g, idx_m1, rng)}
    prim["2d"] = ({"n": n, "p": p}, "p")

    # Holm
    names = ["2a", "2b", "2c", "2d"]
    raw = [prim[s][0].get(prim[s][1], float("nan")) if prim[s][0].get("n", 0) else float("nan") for s in names]
    adj = holm(raw)
    res["holm"] = {}
    for s, pr, pa in zip(names, raw, adj):
        n_s = prim[s][0].get("n", 0)
        if n_s < MIN_EP:
            v = "INSUFFICIENT"
        elif s == "2d":
            v = "SEES" if (res["2d"]["hit_rate"] >= 0.5 and pa <= 0.05) else "DOES NOT SEE"
        else:
            v = "SUPPORTED" if pa <= 0.05 else "NOT SUPPORTED"
        res["holm"][s] = {"p_raw": pr, "p_holm": pa, "verdict": v}

    def show(lbl, s):
        if s.get("n"):
            print(f"  {lbl}: n {s['n']}, mean {s['mean']:+.4f} vs {s['unconditional_mean']:+.4f}, "
                  f"p_lower {s['p_lower']:.4f}, p_upper {s['p_upper']:.4f}, share neg {s['share_negative']:.2f}")
    print("2a short side")
    for kk, s in res["2a"].items():
        show(kk, s)
    print("2b factors")
    for kk, s in res["2b"].items():
        show(kk, s)
    if res["2c"].get("n"):
        r = res["2c"]
        print(f"2c matched: n {r['n']}, mean {r['mean']:+.4f} vs matched null {r['matched_null_mean']:+.4f}, p_lower {r['p_lower']:.4f}, quintiles {r['episode_quintiles']}")
    r = res["2d"]
    print(f"2d nowcast: scored {r['n']}, hits {r['hits']} {r['hit_ids']}, signal rate {r['signal_rate']:.3f}, chance {r['chance_per_episode']:.3f}, "
          f"p {r['p']:.4f}, signal weeks {r['signal_weeks']}, precision {r['precision (no weight)']:.2f}")
    print("  episode z:", {kk: (None if v is None else round(v, 2)) for kk, v in r["episode_z"].items()})
    show("E-1 GVIP-QQQ", r["E-1 GVIP-QQQ (no weight)"])
    for s, h in res["holm"].items():
        print(f"{s}: p raw {h['p_raw']:.4f}, Holm {h['p_holm']:.4f}, {h['verdict']}")
    json.dump(res, open(os.path.join(a.out, "results_crowd2.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
