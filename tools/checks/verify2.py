"""Independent second implementation of follow-up study 2 (tools/crowd_degross/PREREG.md).

Written from the pre-registration and the input formats alone, under Check 1 of
tools/checks/PREREG.md. The first implementation (tools/crowd_degross/run.py) was not read;
agreement is only evidence if the two were written apart.

Usage:
    python verify2.py --bench DIR --data-b DIR --episodes CSV --out DIR

--data-b none makes the reconstructed basket all-NaN (used for synthetic testing).

Resolutions of points the pre-registration leaves open are stated beside the code that takes
them, so that a disagreement with the first implementation can be traced to a reading rather
than to a bug.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import os
import sys

import numpy as np

SEED = 20261029
N_PERM = 10_000
BETA_LEN = 52
BETA_LAG = 4
BETA_MIN = 40
VERDICT_MIN_N = 8
ALPHA = 0.05
SERIES = ["GVIP-QQQ", "basket-QQQ", "GVIP-SPY", "GVIP-resid-QQQ"]
WINDOWS = ["E0", "E1_4"]
CLASSES = ["D", "N"]

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


# ---------------------------------------------------------------- inputs

def load_bench(bench_dir):
    """bench.csv: DATE plus adjusted closes on SPY trading days; blank is missing."""
    path = bench_dir if bench_dir.endswith(".csv") else os.path.join(bench_dir, "bench.csv")
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {}
    for c in ("GVIP", "SPY", "QQQ", "RSP"):
        px[c] = np.array([float(r[c]) if r.get(c, "").strip() else np.nan for r in rows])
    order = np.argsort(np.array([d.toordinal() for d in days]))
    days = [days[i] for i in order]
    px = {c: v[order] for c, v in px.items()}
    return days, px


def daily_returns(p):
    """Close-to-close on consecutive bench rows; NaN if either close is missing."""
    r = np.full(len(p), np.nan)
    r[1:] = p[1:] / p[:-1] - 1
    return r


def basket_daily(data_b, bench_days):
    """Version B's long leg W, by B's frozen daily_legs, re-indexed onto the bench calendar.

    A bench day absent from B's price calendar is missing for the basket. The short leg is
    set empty as instructed.
    """
    out = np.full(len(bench_days), np.nan)
    if data_b is None or data_b.lower() == "none":
        return out
    path = os.path.join(REPO, "tools", "degross_proxy_b", "run.py")
    spec = importlib.util.spec_from_file_location("_verify2_proxy_b_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    days, col, px = mod.load_prices(data_b)
    bk = mod.load_baskets(data_b)
    bk = {e: {"long": list(v.get("long", [])), "short": []} for e, v in bk.items()}
    W, _L, _M, _cov = mod.daily_legs(days, col, px, bk)
    pos = {d: i for i, d in enumerate(days)}
    for k, d in enumerate(bench_days):
        if d in pos:
            out[k] = W[pos[d]]
    return out


def load_episodes(path):
    eps = []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            eps.append({"episode_id": r["episode_id"], "class": r["class"].strip(),
                        "week_end": dt.date.fromisoformat(r["week_end"].strip())})
    return eps


# ---------------------------------------------------------------- weekly

def monday(d):
    return d - dt.timedelta(days=d.weekday())


def weekly(days, daily_by_name):
    """ISO-week compounding. The week grid is every calendar ISO week from the first to the last
    bench date, so k steps along it are k calendar weeks. A week is undefined for a leg if any
    bench day in it has a missing daily return, or if it has no bench day at all.

    Consequence (stated): the first week of any instrument is undefined, because its first day has
    no prior close; this is what 'from GVIP's first full week' is read to mean.
    """
    m0, m1 = monday(days[0]), monday(days[-1])
    nweeks = (m1 - m0).days // 7 + 1
    weeks = [m0 + dt.timedelta(days=7 * i) for i in range(nweeks)]
    members = [[] for _ in range(nweeks)]
    for i, d in enumerate(days):
        members[(monday(d) - m0).days // 7].append(i)
    out = {}
    for name, r in daily_by_name.items():
        w = np.full(nweeks, np.nan)
        for k, idx in enumerate(members):
            if not idx:
                continue
            x = r[idx]
            if np.isnan(x).any():
                continue
            w[k] = np.prod(1 + x) - 1
        out[name] = w
    return weeks, out


def residual_weekly(g, q):
    """GVIP minus beta x QQQ per week. Beta: OLS slope with intercept over the 52 calendar weeks
    t-55..t-4 inclusive ('ending 4 weeks before'), using the weeks where both legs are defined,
    at least 40 of them. The intercept is estimated but not subtracted: the PREREG defines the
    residual as GVIP minus beta x QQQ.
    """
    n = len(g)
    res = np.full(n, np.nan)
    beta = np.full(n, np.nan)
    for t in range(n):
        hi = t - BETA_LAG
        lo = hi - BETA_LEN + 1
        if lo < 0:
            continue
        y, x = g[lo:hi + 1], q[lo:hi + 1]
        ok = ~np.isnan(y) & ~np.isnan(x)
        if ok.sum() < BETA_MIN:
            continue
        xv, yv = x[ok], y[ok]
        xc = xv - xv.mean()
        den = (xc * xc).sum()
        if den == 0:
            continue
        b = (xc * (yv - yv.mean())).sum() / den
        beta[t] = b
        if not (np.isnan(g[t]) or np.isnan(q[t])):
            res[t] = g[t] - b * q[t]
    return res, beta


def window_values(wk, series):
    """For every anchor week t, the series' E0 and E+1..4 values.

    Differenced series: each leg compounded over the window, then differenced. Residual series:
    weekly residuals summed. Undefined if any constituent week is undefined.
    """
    n = len(wk["QQQ"])

    def comp(x, a, b):
        if a < 0 or b >= n:
            return np.nan
        seg = x[a:b + 1]
        if np.isnan(seg).any():
            return np.nan
        return np.prod(1 + seg) - 1

    out = {}
    for s in SERIES:
        e0 = np.full(n, np.nan)
        e14 = np.full(n, np.nan)
        if s == "GVIP-resid-QQQ":
            r = series["resid"]
            for t in range(n):
                e0[t] = r[t]
                if t + 4 < n:
                    seg = r[t + 1:t + 5]
                    if not np.isnan(seg).any():
                        e14[t] = seg.sum()
        else:
            a, b = {"GVIP-QQQ": ("GVIP", "QQQ"), "basket-QQQ": ("BASKET", "QQQ"),
                    "GVIP-SPY": ("GVIP", "SPY")}[s]
            for t in range(n):
                e0[t] = comp(wk[a], t, t) - comp(wk[b], t, t)
                e14[t] = comp(wk[a], t + 1, t + 4) - comp(wk[b], t + 1, t + 4)
        out[s] = {"E0": e0, "E1_4": e14}
    return out


# ---------------------------------------------------------------- test

def perm(rng, pool, obs, n):
    """One-sided permutation p-values: 10,000 means of n distinct pool values, drawn without
    replacement; p = (1 + #draws at or beyond observed) / (1 + 10,000)."""
    draws = np.empty(N_PERM)
    for i in range(N_PERM):
        draws[i] = rng.choice(pool, size=n, replace=False).mean()
    lo = (1 + int((draws <= obs).sum())) / (1 + N_PERM)
    hi = (1 + int((draws >= obs).sum())) / (1 + N_PERM)
    return lo, hi


def run_class(eps, weeks, vals):
    """One fresh rng per class, consumed series-major then window. A cell with no defined
    episode, or more episodes than pool weeks, consumes no draws (stated resolution)."""
    rng = np.random.default_rng(SEED)
    widx = {w: i for i, w in enumerate(weeks)}
    out = {}
    for s in SERIES:
        cell = {}
        per_ep = []
        for e in eps:
            k = widx.get(monday(e["week_end"]))
            rec = {"episode_id": e["episode_id"], "week_end": e["week_end"].isoformat()}
            for w in WINDOWS:
                v = np.nan if k is None else vals[s][w][k]
                rec[w] = None if np.isnan(v) else float(v)
            per_ep.append(rec)
        for w in WINDOWS:
            pool = vals[s][w][~np.isnan(vals[s][w])]
            obs_v = np.array([r[w] for r in per_ep if r[w] is not None])
            n = len(obs_v)
            c = {"n": n, "n_episodes": len(eps), "pool_weeks": int(len(pool)),
                 "unconditional_mean": float(pool.mean()) if len(pool) else None,
                 "mean": float(obs_v.mean()) if n else None,
                 "share_negative": float((obs_v < 0).mean()) if n else None,
                 "p_lower": None, "p_upper": None}
            if n and n <= len(pool):
                c["p_lower"], c["p_upper"] = perm(rng, pool, obs_v.mean(), n)
            cell[w] = c
        cell["episodes"] = per_ep
        out[s] = cell
    return out


def verdict(prim):
    if prim["n"] < VERDICT_MIN_N:
        return "INSUFFICIENT"
    if prim["p_lower"] is not None and prim["p_lower"] <= ALPHA:
        return "SUPPORTED"
    return "NOT SUPPORTED"


def leave_one_out(eps_d, weeks, vals):
    """Check 1: the primary statistic recomputed with each Class D episode removed, a fresh
    default_rng(20261029) each time, the pool unchanged (all defined weeks)."""
    widx = {w: i for i, w in enumerate(weeks)}
    e0 = vals["GVIP-QQQ"]["E0"]
    pool = e0[~np.isnan(e0)]
    rows = []
    for drop in eps_d:
        keep = [e for e in eps_d if e is not drop]
        v = []
        for e in keep:
            k = widx.get(monday(e["week_end"]))
            if k is not None and not np.isnan(e0[k]):
                v.append(e0[k])
        v = np.array(v)
        row = {"omitted": drop["episode_id"], "n": len(v),
               "mean": float(v.mean()) if len(v) else None, "p_lower": None}
        if len(v) and len(v) <= len(pool):
            row["p_lower"], _ = perm(np.random.default_rng(SEED), pool, v.mean(), len(v))
        rows.append(row)
    ps = [r for r in rows if r["p_lower"] is not None]
    worst = max(ps, key=lambda r: r["p_lower"]) if ps else None
    return {"rows": rows, "max_p_lower": worst["p_lower"] if worst else None,
            "max_p_omitted": worst["omitted"] if worst else None}


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    days, px = load_bench(a.bench)
    daily = {c: daily_returns(px[c]) for c in ("GVIP", "SPY", "QQQ")}
    daily["BASKET"] = basket_daily(a.data_b, days)
    weeks, wk = weekly(days, daily)
    resid, _beta = residual_weekly(wk["GVIP"], wk["QQQ"])
    vals = window_values(wk, {"resid": resid})

    eps = load_episodes(a.episodes)
    res = {}
    for c in CLASSES:
        res[f"class_{c}"] = run_class([e for e in eps if e["class"] == c], weeks, vals)
    prim = res["class_D"]["GVIP-QQQ"]["E0"]
    res["verdict_H_crowd"] = verdict(prim)
    res["leave_one_out"] = leave_one_out([e for e in eps if e["class"] == "D"], weeks, vals)
    res["meta"] = {"seed": SEED, "n_perm": N_PERM, "bench_first": days[0].isoformat(),
                   "bench_last": days[-1].isoformat(), "weeks": len(weeks),
                   "data_b": a.data_b, "implementation": "tools/checks/verify2.py"}

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify2.json"), "w") as fh:
        json.dump(res, fh, indent=2)

    f = lambda x, d=5: "n/a" if x is None else f"{x:+.{d}f}"
    g = lambda x: "n/a" if x is None else f"{x:.4f}"
    print(f"verify2: bench {days[0]} to {days[-1]}, {len(weeks)} ISO weeks")
    for c in CLASSES:
        print(f"\nClass {c}")
        print(f"  {'series':<16}{'win':<6}{'n':>3}{'mean':>11}{'uncond':>11}{'p_low':>8}{'p_up':>8}{'neg':>6}")
        for s in SERIES:
            for w in WINDOWS:
                x = res[f"class_{c}"][s][w]
                print(f"  {s:<16}{w:<6}{x['n']:>3}{f(x['mean']):>11}{f(x['unconditional_mean']):>11}"
                      f"{g(x['p_lower']):>8}{g(x['p_upper']):>8}"
                      f"{'n/a' if x['share_negative'] is None else format(x['share_negative'], '.2f'):>6}")
    print("\nPrimary per-episode E0 (Class D, GVIP-QQQ):")
    for r in res["class_D"]["GVIP-QQQ"]["episodes"]:
        print(f"  {r['episode_id']} {r['week_end']}  {f(r['E0'])}")
    print(f"\nPrimary: n={prim['n']} mean={f(prim['mean'])} uncond={f(prim['unconditional_mean'])} "
          f"p_lower={g(prim['p_lower'])}")
    print(f"Verdict H-crowd: {res['verdict_H_crowd']}")
    loo = res["leave_one_out"]
    print("\nLeave-one-out (descriptive):")
    for r in loo["rows"]:
        print(f"  without {r['omitted']}: n={r['n']} mean={f(r['mean'])} p_lower={g(r['p_lower'])}")
    print(f"  largest p_lower {g(loo['max_p_lower'])} on omitting {loo['max_p_omitted']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
