"""Follow-up study 2 (PREREG.md governs): crowded longs against the Nasdaq 100 in Goldman-reported
de-gross weeks.

Inputs: --bench, a directory holding the GVIP test's bench.csv (DATE,GVIP,SPY,QQQ,RSP); --data-b,
Version B's data directory (prices.csv, baskets.csv), for the reconstructed basket; --episodes, an
episodes CSV in the frozen format. Writes results.json to --out.

Window returns: each leg is compounded over the window and the legs are differenced, so an E+1..4
excess is (product of 1 + fund) - (product of 1 + benchmark). The residual series is summed.

Usage: python run.py --bench DIR --data-b DIR --episodes CSV --out DIR [--tag NAME]
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
SEED = 20261029
N_PERM = 10_000
MIN_EP = 8
BETA_WIN, BETA_GAP, BETA_MIN = 52, 4, 40


def load_bench(path):
    rows = [r for r in csv.DictReader(open(path, newline="")) if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {s: np.array([float(r[s]) if r[s].strip() else np.nan for r in rows]) for s in ("GVIP", "SPY", "QQQ")}
    ret = {}
    for s, v in px.items():
        r = np.full(len(days), np.nan)
        r[1:] = v[1:] / v[:-1] - 1
        ret[s] = r
    return days, ret


def basket_daily(data_b, days):
    """Version B's long leg W, by B's frozen daily_legs, re-indexed to the bench days."""
    sys.path.insert(0, os.path.join(HERE, "..", "degross_proxy_b"))
    import run as vb  # noqa: E402
    bd, col, px = vb.load_prices(data_b)
    bk = vb.load_baskets(data_b)
    bk = {e: {"long": v["long"], "short": []} for e, v in bk.items() if v["long"]}
    W, _, _, _ = vb.daily_legs(bd, col, px, bk)
    m = dict(zip(bd, W))
    return np.array([m.get(d, np.nan) for d in days])


def weekly(days, daily):
    """Compound each daily series over ISO weeks; a week with any missing day is NaN."""
    keys = [d.isocalendar()[:2] for d in days]
    out_keys, out = [], {k: [] for k in daily}
    i, n = 0, len(days)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        for k, v in daily.items():
            s = v[i:j + 1]
            out[k].append(np.nan if np.isnan(s).any() else float(np.prod(1 + s) - 1))
        out_keys.append(keys[i])
        i = j + 1
    return out_keys, {k: np.array(v) for k, v in out.items()}


def window(a, t, k0, k1):
    """Compounded return of weekly series a over weeks t+k0 .. t+k1; NaN if any missing."""
    if t + k0 < 0 or t + k1 >= len(a):
        return np.nan
    s = a[t + k0:t + k1 + 1]
    return np.nan if np.isnan(s).any() else float(np.prod(1 + s) - 1)


def residual(f, b):
    """f - beta * b, beta from OLS with intercept on weeks t-55 .. t-4 (52 weeks), >= 40 defined."""
    n = len(f)
    out = np.full(n, np.nan)
    for t in range(n):
        lo, hi = t - BETA_GAP - BETA_WIN + 1, t - BETA_GAP
        if lo < 0 or np.isnan(f[t]) or np.isnan(b[t]):
            continue
        y, x = f[lo:hi + 1], b[lo:hi + 1]
        ok = ~np.isnan(y) & ~np.isnan(x)
        if ok.sum() < BETA_MIN:
            continue
        beta = np.polyfit(x[ok], y[ok], 1)[0]
        out[t] = f[t] - beta * b[t]
    return out


def series_set(wk):
    s = {}
    s["GVIP-QQQ"] = (wk["GVIP"], wk["QQQ"])
    s["basket-QQQ"] = (wk["W"], wk["QQQ"])
    s["GVIP-SPY"] = (wk["GVIP"], wk["SPY"])
    return s


def perm(vals, pool, rng):
    n = len(vals)
    obs = float(np.mean(vals))
    draws = np.array([rng.choice(pool, size=n, replace=False).mean() for _ in range(N_PERM)])
    return obs, float((1 + np.sum(draws <= obs)) / (1 + N_PERM)), float((1 + np.sum(draws >= obs)) / (1 + N_PERM))


def evaluate(keys, wk, eps, rng):
    kidx = {k: t for t, k in enumerate(keys)}
    res = {}
    resid = residual(wk["GVIP"], wk["QQQ"])
    defs = dict(series_set(wk))
    for name in list(defs) + ["GVIP-resid-QQQ"]:
        T = len(keys)
        if name == "GVIP-resid-QQQ":
            e0 = resid.copy()
            e14 = np.array([np.nansum(resid[t + 1:t + 5]) if t + 4 < T and not np.isnan(resid[t + 1:t + 5]).any() else np.nan for t in range(T)])
        else:
            f, b = defs[name]
            e0 = f - b
            e14 = np.array([window(f, t, 1, 4) - window(b, t, 1, 4) for t in range(T)])
        out = {"episodes": []}
        for e in eps:
            t = kidx.get(e["week_end"].isocalendar()[:2])
            out["episodes"].append({"id": e["id"], "week_end": e["week_end"].isoformat(),
                                    "E0": None if t is None or np.isnan(e0[t]) else float(e0[t]),
                                    "E1_4": None if t is None or np.isnan(e14[t]) else float(e14[t])})
        for w, arr in (("E0", e0), ("E1_4", e14)):
            vals = np.array([r[w] for r in out["episodes"] if r[w] is not None])
            pool = arr[~np.isnan(arr)]
            if len(vals) == 0:
                out[w] = {"n": 0}
                continue
            obs, pl, pu = perm(vals, pool, rng)
            out[w] = {"n": int(len(vals)), "mean": obs, "median": float(np.median(vals)),
                      "unconditional_mean": float(pool.mean()), "n_unconditional": int(len(pool)),
                      "p_lower": pl, "p_upper": pu, "share_negative": float(np.mean(vals < 0)),
                      "unconditional_share_negative": float(np.mean(pool < 0))}
        res[name] = out
    return res


def load_eps(path):
    out = []
    for r in csv.DictReader(open(path, newline="")):
        out.append({"id": r["episode_id"], "cls": r["class"].strip().upper(),
                    "week_end": dt.date.fromisoformat(r["week_end"])})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="frozen21")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, ret = load_bench(os.path.join(a.bench, "bench.csv"))
    ret["W"] = basket_daily(a.data_b, days) if a.data_b != "none" else np.full(len(days), np.nan)
    keys, wk = weekly(days, ret)
    eps = load_eps(a.episodes)
    res = {"tag": a.tag, "weeks": len(keys)}
    for cls in ("D", "N"):
        rng = np.random.default_rng(SEED)
        res[f"class_{cls}"] = evaluate(keys, wk, [e for e in eps if e["cls"] == cls], rng)
    p = res["class_D"]["GVIP-QQQ"]["E0"]
    if p.get("n", 0) < MIN_EP:
        res["verdict_H_crowd"] = "INSUFFICIENT"
    else:
        res["verdict_H_crowd"] = "SUPPORTED" if p["p_lower"] <= 0.05 else "NOT SUPPORTED"
    for cls in ("D", "N"):
        for name, v in res[f"class_{cls}"].items():
            for w in ("E0", "E1_4"):
                s = v[w]
                if s.get("n"):
                    print(f"{a.tag} class {cls} {name} {w}: n {s['n']}, mean {s['mean']:+.4f} vs {s['unconditional_mean']:+.4f}, "
                          f"p_lower {s['p_lower']:.4f}, p_upper {s['p_upper']:.4f}, share neg {s['share_negative']:.2f}")
    for r in res["class_D"]["GVIP-QQQ"]["episodes"]:
        print(f"  {r['id']} {r['week_end']} E0 {r['E0']} E1_4 {r['E1_4']}")
    print("H-crowd:", res["verdict_H_crowd"])
    json.dump(res, open(os.path.join(a.out, f"results_{a.tag}.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
