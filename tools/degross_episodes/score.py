"""Studies 2 and 3 (PREREG.md governs): proxy hit rates against Goldman-reported de-gross episodes,
and Nasdaq 100 timing around them.

Version A's and Version B's de-gross weeks are recomputed by importing their frozen run.py files.
Requires, under DATA_A, Version A's inputs (mom10_daily.csv, ff3_daily.csv, ndx.csv) and, under
DATA_B, Version B's (prices.csv, baskets.csv). episodes.csv is this directory's committed list.

Usage: python score.py --data-a DATA_A --data-b DATA_B --out OUT_DIR
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
SEED = 20261029
N_PERM = 10_000


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def episodes(path):
    out = []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            out.append({"id": r["episode_id"], "cls": r["class"].strip().upper(),
                        "week_end": dt.date.fromisoformat(r["week_end"]),
                        "first_public": dt.date.fromisoformat(r["first_public"])})
    return out


def binom_tail(k, n, q):
    return sum(math.comb(n, j) * q ** j * (1 - q) ** (n - j) for j in range(k, n + 1))


def hits(eps, ends, D, sig_eval, cls):
    ev = [ends[t] for t in range(len(ends)) if sig_eval[t]]
    lo, hi = min(ev), max(ev)
    dweeks = [ends[t] for t in range(len(ends)) if D[t]]
    b = float(D.sum() / sig_eval.sum())
    q = 1 - (1 - b) ** 3
    scored = [e for e in eps if e["cls"] in cls and lo <= e["week_end"] <= hi]
    hit = [e["id"] for e in scored if any(abs((d - e["week_end"]).days) <= 7 for d in dweeks)]
    n, k = len(scored), len(hit)
    p = binom_tail(k, n, q) if n else float("nan")
    rate = k / n if n else float("nan")
    if n < 8:
        verdict = "INSUFFICIENT"
    elif rate >= 0.5 and p <= 0.05:
        verdict = "SEES"
    else:
        verdict = "DOES NOT SEE"
    return {"n_scored": n, "hits": k, "hit_rate": rate, "base_rate": b, "chance_per_episode": q,
            "p": p, "verdict": verdict, "hit_ids": hit, "scored_ids": [e["id"] for e in scored],
            "range": [lo.isoformat(), hi.isoformat()]}


def proxy_a(data_a):
    A = load_module("run_a", os.path.join(HERE, "..", "degross_proxy", "run.py"))
    days, W, L, M = A.load_french(data_a)
    ends, Ww, Lw, Mw = A.to_weekly(days, W, L, M)
    sg = A.signals(Ww, Lw, Mw)
    return ends, sg["D"], sg["sig_eval"]


def proxy_b(data_b):
    B = load_module("run_b", os.path.join(HERE, "..", "degross_proxy_b", "run.py"))
    days, col, px = B.load_prices(data_b)
    bk = B.load_baskets(data_b)
    W, L, M, _ = B.daily_legs(days, col, px, bk)
    ends, Ww, Lw, Mw = B.to_weekly(days, W, L, M)
    sg = B.signals(Ww, Lw, Mw)
    return ends, sg["D"], sg["sig_eval"]


def load_ndx(path):
    rows = list(csv.reader(open(path, newline="")))[1:]
    pairs = sorted((dt.date.fromisoformat(r[0]), float(r[1])) for r in rows if r[1].strip())
    return [p[0] for p in pairs], np.array([p[1] for p in pairs])


def timing(eps, nd, npx):
    ords = np.array([d.toordinal() for d in nd])

    def on_or_before(d):
        return int(np.searchsorted(ords, d.toordinal(), side="right") - 1)

    def on_or_after(d):
        return int(np.searchsorted(ords, d.toordinal(), side="left"))

    def win(i, a, b):
        if i + a < 0 or i + b >= len(npx) or i < 0:
            return None
        return npx[i + b] / npx[i + a] - 1

    D = [e for e in eps if e["cls"] == "D"]
    rows = []
    for e in D:
        i = on_or_before(e["week_end"])
        j = on_or_after(e["first_public"])
        rows.append({"id": e["id"], "week_end": e["week_end"].isoformat(), "pre10": win(i, -10, 0),
                     "post21_pub": win(j, 0, 21), "post63_pub": win(j, 0, 63)})
    # unconditional: last NDX day of every ISO week from 2016-01-01
    keys = [d.isocalendar()[:2] for d in nd]
    week_idx = [k for k in range(len(nd)) if nd[k] >= dt.date(2016, 1, 1) and (k + 1 == len(nd) or keys[k + 1] != keys[k])]
    unc = {"pre10": np.array([v for v in (win(k, -10, 0) for k in week_idx) if v is not None]),
           "post21_pub": np.array([v for v in (win(k, 0, 21) for k in week_idx) if v is not None]),
           "post63_pub": np.array([v for v in (win(k, 0, 63) for k in week_idx) if v is not None])}
    out = {"episodes": rows, "n_unconditional": {k: int(len(v)) for k, v in unc.items()}}
    rng = np.random.default_rng(SEED)
    for k in ("pre10", "post21_pub", "post63_pub"):
        vals = np.array([r[k] for r in rows if r[k] is not None])
        n = len(vals)
        if n == 0:
            out[k] = {"n": 0}
            continue
        obs = float(vals.mean())
        draws = np.array([rng.choice(unc[k], size=n, replace=False).mean() for _ in range(N_PERM)])
        p_low = float((1 + np.sum(draws <= obs)) / (1 + N_PERM))
        out[k] = {"n": n, "mean": obs, "median": float(np.median(vals)), "unconditional_mean": float(unc[k].mean()),
                  "p_lower": p_low, "share_negative": float(np.mean(vals < 0)),
                  "unconditional_share_negative": float(np.mean(unc[k] < 0))}
    n_pre = out["pre10"].get("n", 0)
    if n_pre < 8:
        out["verdict_H_lag"] = "INSUFFICIENT"
    else:
        out["verdict_H_lag"] = "SUPPORTED" if out["pre10"]["p_lower"] <= 0.05 else "NOT SUPPORTED"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-a", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    eps = episodes(os.path.join(HERE, "episodes.csv"))
    print(f"episodes: {len(eps)} (D {sum(e['cls'] == 'D' for e in eps)}, N {sum(e['cls'] == 'N' for e in eps)})")
    res = {"study2": {}, "study3": None}
    for name, fn, data in (("A_momentum", proxy_a, a.data_a), ("B_13f", proxy_b, a.data_b)):
        ends, D, ev = fn(data)
        res["study2"][name] = {"class_D": hits(eps, ends, D, ev, {"D"}),
                               "class_N (no weight)": hits(eps, ends, D, ev, {"N"}),
                               "class_D_and_N (no weight)": hits(eps, ends, D, ev, {"D", "N"})}
        r = res["study2"][name]["class_D"]
        print(f"{name}: scored {r['n_scored']}, hits {r['hits']}, rate {r['hit_rate']:.2f}, chance {r['chance_per_episode']:.3f}, p {r['p']:.4f}, {r['verdict']}")
    nd, npx = load_ndx(os.path.join(a.data_a, "ndx.csv"))
    res["study3"] = timing(eps, nd, npx)
    s3 = res["study3"]
    for k in ("pre10", "post21_pub", "post63_pub"):
        if s3[k].get("n"):
            print(f"{k}: n {s3[k]['n']}, mean {s3[k]['mean']:.4f} vs unconditional {s3[k]['unconditional_mean']:.4f}, p_lower {s3[k]['p_lower']:.4f}")
    print("H-lag:", s3["verdict_H_lag"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
