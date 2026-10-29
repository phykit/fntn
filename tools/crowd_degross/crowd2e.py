"""Study 2e (PREREG_2e.md governs): 2e-i, GVIP minus QQQ in the week before new de-gross episodes;
2e-ii, persistence of crowded-long weakness outside the frozen episode weeks. Holm across the two.

Usage: python crowd2e.py --bench DIR --data-b DIR --episodes FROZEN_CSV --out DIR
                         [--new GOLDMAN_EXT_CSV --new-other OTHER_PB_CSV]
Without --new, 2e-i is not run and is reported as PENDING.
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
sys.path.insert(0, HERE)
import crowd2 as k2  # noqa: E402  studies 2a to 2d (frozen)
import run as c2  # noqa: E402  study 2 (frozen)

SEED = 20261029
N_PERM = 10_000
WIN, PCT, GAP = 104, 0.10, 14
MIN_NEW, MIN_SIG = 8, 20


def nw_slope(y, x, lags=3):
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    XtX = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += w * (G + G.T)
    se = np.sqrt(np.diag(XtX @ S @ XtX))
    return float(b[1]), float(b[1] / se[1])


def persistence(x, ends, frozen_dates, rng):
    T = len(x)
    near = np.array([any(abs((ends[t] - f).days) <= GAP for f in frozen_dates) for t in range(T)])
    sig, elig, elig2 = np.zeros(T, bool), np.zeros(T, bool), np.zeros(T, bool)
    for t in range(WIN, T - 1):
        h = x[t - WIN:t]
        if np.isnan(h).any() or np.isnan(x[t]) or np.isnan(x[t + 1]) or near[t] or near[t + 1]:
            continue
        elig[t] = True
        sig[t] = x[t] <= np.quantile(h, PCT)
        if t + 2 < T and not np.isnan(x[t + 2]) and not near[t + 2]:
            elig2[t] = True
    nxt = np.full(T, np.nan)
    nxt[:-1] = x[1:]
    vals, pool = nxt[elig & sig], nxt[elig]
    out = {"eligible_weeks": int(elig.sum()), "signal_weeks": int((elig & sig).sum())}
    if len(vals) == 0:
        out["n"] = 0
        return out
    obs = float(vals.mean())
    draws = np.array([rng.choice(pool, size=len(vals), replace=False).mean() for _ in range(N_PERM)])
    out.update({"n": int(len(vals)), "mean_next": obs, "unconditional_next": float(pool.mean()),
                "p_lower": float((1 + np.sum(draws <= obs)) / (1 + N_PERM)),
                "share_next_negative": float(np.mean(vals < 0)), "unconditional_share_negative": float(np.mean(pool < 0))})
    ii = np.where(elig)[0]
    out["slope_next_on_this"], out["slope_t"] = nw_slope(x[ii + 1], x[ii])
    two = np.full(T, np.nan)
    two[:-2] = x[1:-1] + x[2:]
    v2, p2 = two[elig2 & sig], two[elig2]
    if len(v2):
        o2 = float(v2.mean())
        d2 = np.array([rng.choice(p2, size=len(v2), replace=False).mean() for _ in range(N_PERM)])
        out["two_week"] = {"n": int(len(v2)), "mean": o2, "unconditional": float(p2.mean()),
                           "p_lower": float((1 + np.sum(d2 <= o2)) / (1 + N_PERM))}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--new")
    ap.add_argument("--new-other")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, ret = c2.load_bench(os.path.join(a.bench, "bench.csv"))
    ret["W"], ret["L"] = k2.legs_b(a.data_b, days, a.bench)
    keys, wk = c2.weekly(days, ret)
    ends = k2.week_ends(days)
    kidx = {k: t for t, k in enumerate(keys)}
    frozen = c2.load_eps(a.episodes)
    fdates = [e["week_end"] for e in frozen]
    g = wk["GVIP"] - wk["QQQ"]
    wq = wk["W"] - wk["QQQ"]
    res = {"weeks": len(keys)}

    # 2e-ii
    res["2e-ii GVIP-QQQ (primary)"] = persistence(g, ends, fdates, np.random.default_rng(SEED))
    res["2e-ii basket-QQQ (no weight)"] = persistence(wq, ends, fdates, np.random.default_rng(SEED))

    # 2e-i
    if a.new:
        new = [e for e in c2.load_eps(a.new) if e["cls"] == "D"]
        oth = [e for e in c2.load_eps(a.new_other) if e["cls"] == "D"
               and all(abs((e["week_end"] - f).days) > GAP for f in fdates)]
        eps = new + oth
        idx0 = [kidx.get(e["week_end"].isocalendar()[:2]) for e in eps]
        idxm1 = [t - 1 if t is not None and t > 0 else None for t in idx0]
        rng = np.random.default_rng(SEED)
        r = {"episodes": [{"id": e["id"], "week_end": e["week_end"].isoformat(),
                           "E-1": None if t is None or np.isnan(g[t]) else float(g[t]),
                           "E0": None if t0 is None or np.isnan(g[t0]) else float(g[t0])}
                          for e, t, t0 in zip(eps, idxm1, idx0)],
             "E-1 GVIP-QQQ (primary)": k2.stat(g, idxm1, rng),
             "E-1 basket-QQQ (no weight)": k2.stat(wq, idxm1, rng),
             "E0 GVIP-QQQ (no weight)": k2.stat(g, idx0, rng)}
        fN = [kidx.get(e["week_end"].isocalendar()[:2]) for e in frozen if e["cls"] == "N"]
        r["frozen N E-1 GVIP-QQQ (no weight)"] = k2.stat(g, [t - 1 if t else None for t in fN], rng)
        res["2e-i"] = r
        p_i, n_i = r["E-1 GVIP-QQQ (primary)"].get("p_lower", float("nan")), r["E-1 GVIP-QQQ (primary)"].get("n", 0)
    else:
        res["2e-i"] = "PENDING: new episode lists not yet frozen"
        p_i, n_i = float("nan"), 0

    pii, nii = res["2e-ii GVIP-QQQ (primary)"].get("p_lower", float("nan")), res["2e-ii GVIP-QQQ (primary)"].get("n", 0)
    if n_i >= MIN_NEW:
        adj = k2.holm([p_i, pii])
        v_i = "SUPPORTED" if adj[0] <= 0.05 else "NOT SUPPORTED"
        p_ii_used = adj[1]
    else:
        v_i = "INSUFFICIENT" if a.new else "PENDING"
        p_ii_used = pii
    v_ii = "INSUFFICIENT" if nii < MIN_SIG else ("SUPPORTED" if p_ii_used <= 0.05 else "NOT SUPPORTED")
    res["verdicts"] = {"2e-i": {"p_raw": p_i, "n": n_i, "verdict": v_i},
                       "2e-ii": {"p_raw": pii, "p_used": p_ii_used, "n": nii, "verdict": v_ii}}

    for name in ("2e-ii GVIP-QQQ (primary)", "2e-ii basket-QQQ (no weight)"):
        r = res[name]
        if r.get("n"):
            print(f"{name}: eligible {r['eligible_weeks']}, signal {r['signal_weeks']}, next-week mean {r['mean_next']:+.4f} "
                  f"vs {r['unconditional_next']:+.4f}, p_lower {r['p_lower']:.4f}, share neg {r['share_next_negative']:.2f} "
                  f"vs {r['unconditional_share_negative']:.2f}; slope {r['slope_next_on_this']:+.3f} (t {r['slope_t']:.2f})")
            if "two_week" in r:
                tw = r["two_week"]
                print(f"   two-week: n {tw['n']}, mean {tw['mean']:+.4f} vs {tw['unconditional']:+.4f}, p_lower {tw['p_lower']:.4f}")
    if isinstance(res["2e-i"], dict):
        for kk, s in res["2e-i"].items():
            if isinstance(s, dict) and s.get("n"):
                print(f"2e-i {kk}: n {s['n']}, mean {s['mean']:+.4f} vs {s['unconditional_mean']:+.4f}, p_lower {s['p_lower']:.4f}")
        for e in res["2e-i"]["episodes"]:
            print("  ", e)
    else:
        print("2e-i:", res["2e-i"])
    print("verdicts:", json.dumps(res["verdicts"]))
    json.dump(res, open(os.path.join(a.out, "results_crowd2e.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
