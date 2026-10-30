"""Frozen test (PREREG.md governs): intra-week persistence of the crowded-long spread. Does a bad
first two days of the week (GVIP against QQQ; MTUM against SPY) continue into the rest of the week?

Inputs: --data DIR holding bench.csv (DATE,GVIP,QQQ,MTUM,SPY, blanks where missing); --episodes the
frozen Goldman episode file (week_end column). Writes results.json to --out.

Choices where the PREREG is silent, fixed before any figure was computed: the ISO week of a date is
`date.isocalendar()[:2]`; weeks are ordered by their first trading day; the reference set of a week
is formed over admissible weeks only (an inadmissible week is simply absent from the series); the
one-day signal uses its own reference sets of S' over the same prior admissible weeks; the shift
test's rotations use numpy.roll on the indicator over the eligible weeks in date order; the t of the
trade mean uses the sample standard deviation (ddof = 1); the Newey-West regressions include a
constant and report the slope's t.

Usage: python run.py --data DATA_DIR --episodes FILE --out OUT_DIR
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

PAIRS = {"P1": ("GVIP", "QQQ"), "P2": ("MTUM", "SPY")}
REF, REF_MIN, MIN_DAYS, SHIFT_MIN, NW_L = 104, 52, 4, 5, 5
MIN_SIGNAL = 40
COST = {"P1": 0.004, "P2": 0.001}
BORROW = 0.005


def load_bench(path):
    rows = list(csv.reader(open(path, newline="")))
    hdr = rows[0]
    days = [dt.date.fromisoformat(r[0]) for r in rows[1:]]
    px = {}
    for j, name in enumerate(hdr[1:], start=1):
        px[name] = np.array([float(r[j]) if r[j].strip() else np.nan for r in rows[1:]])
    return days, px


def spread(first, second):
    s = np.full(len(first), np.nan)
    s[1:] = (first[1:] / first[:-1] - 1) - (second[1:] / second[:-1] - 1)
    return s


def nw_slope(x, y, L=NW_L):
    """OLS of y on a constant and x; the slope and its Newey-West t (Bartlett, lag L, no correction)."""
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    XtX = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, L + 1):
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += (1 - l / (L + 1)) * (G + G.T)
    se = np.sqrt(np.diag(XtX @ S @ XtX))
    return float(b[1]), float(b[1] / se[1]), int(len(x))


def shift_p(R, I, lower=True):
    """d = mean R on signal weeks minus mean on the others; one-sided circular-shift p over k = 5 .. n-5."""
    d = float(R[I].mean() - R[~I].mean())
    n = len(R)
    cnt = 0
    for k in range(SHIFT_MIN, n - SHIFT_MIN + 1):
        Ik = np.roll(I, k)
        dk = R[Ik].mean() - R[~Ik].mean()
        if (dk <= d) if lower else (dk >= d):
            cnt += 1
    return d, float((1 + cnt) / (1 + (n - 2 * SHIFT_MIN + 1))), n - 2 * SHIFT_MIN + 1


def weeks_of(days):
    """Trading weeks as lists of row indices, in order of first day, keyed by ISO (year, week)."""
    out, order = {}, []
    for i, d in enumerate(days):
        k = d.isocalendar()[:2]
        if k not in out:
            out[k] = []
            order.append(k)
        out[k].append(i)
    return [(k, out[k]) for k in order]


def analyse(pair, days, s, weeks, episode_keys):
    adm = []  # admissible weeks: dict with key, label, days (list of s), S, R, S1, R1
    for k, idx in weeks:
        vals = s[idx]
        if len(idx) >= MIN_DAYS and not np.isnan(vals).any():
            adm.append({"key": k, "label": days[idx[-1]].isoformat(), "s": vals, "S": float(vals[0] + vals[1]),
                        "R": float(vals[2:].sum()), "S1": float(vals[0]), "R1": float(vals[1:].sum()), "n": len(idx)})
    res = {"legs": list(pair), "n_admissible": len(adm)}
    # reference sets and eligibility
    for j, w in enumerate(adm):
        ref = adm[max(0, j - REF):j]
        w["ref_S"] = np.array([r["S"] for r in ref])
        w["ref_S1"] = np.array([r["S1"] for r in ref])
        w["has_ref"] = len(ref) >= REF_MIN
        w["episode"] = w["key"] in episode_keys
        w["eligible"] = w["has_ref"] and not w["episode"]
    el = [w for w in adm if w["eligible"]]
    res.update({"n_eligible": len(el), "first_eligible": el[0]["label"] if el else None, "last_eligible": el[-1]["label"] if el else None})
    R = np.array([w["R"] for w in el])
    S = np.array([w["S"] for w in el])
    I = np.array([w["S"] <= np.percentile(w["ref_S"], 10) for w in el])
    res["n_signal"] = int(I.sum())
    d, p, ns = shift_p(R, I, lower=True)
    res.update({"mean_R_signal": float(R[I].mean()), "mean_R_other": float(R[~I].mean()), "d": d, "p_shift": p, "n_shifts": ns,
                "share_R_negative_signal": float(np.mean(R[I] < 0))})
    It = np.array([w["S"] >= np.percentile(w["ref_S"], 90) for w in el])
    dt_, pt, _ = shift_p(R, It, lower=False)
    res["top"] = {"n_signal": int(It.sum()), "d": dt_, "p_shift": pt}
    R1 = np.array([w["R1"] for w in el])
    I1 = np.array([w["S1"] <= np.percentile(w["ref_S1"], 10) for w in el])
    d1, p1, _ = shift_p(R1, I1, lower=True)
    res["one_day"] = {"n_signal": int(I1.sum()), "d": d1, "p_shift": p1}
    # daily autocorrelation, no week boundaries
    ok1 = ~np.isnan(s[:-1]) & ~np.isnan(s[1:])
    sl1, t1, n1 = nw_slope(s[:-1][ok1], s[1:][ok1])
    x = s[:-4] + s[1:-3]
    y = s[2:-2] + s[3:-1] + s[4:]
    ok2 = ~np.isnan(x) & ~np.isnan(y)
    sl2, t2, n2 = nw_slope(x[ok2], y[ok2])
    res["daily"] = {"slope1": sl1, "t1": t1, "n1": n1, "slope23": sl2, "t23": t2, "n23": n2}
    # the frozen episode weeks
    ep = [w for w in adm if w["episode"]]
    by_day = [[w["s"][i] for w in ep if w["n"] > i] for i in range(5)]
    with_ref = [w for w in ep if w["has_ref"]]
    res["episodes"] = {"n": len(ep), "mean_by_day": [float(np.mean(v)) if v else None for v in by_day],
                       "mean_S": float(np.mean([w["S"] for w in ep])) if ep else None,
                       "mean_R": float(np.mean([w["R"] for w in ep])) if ep else None,
                       "hit_rate": float(np.mean([w["S"] <= np.percentile(w["ref_S"], 10) for w in with_ref])) if with_ref else None,
                       "n_with_reference": len(with_ref)}
    # the trade
    net = np.array([-w["R"] - COST[pair_id(pair)] - BORROW * (w["n"] - 2) / 252 for w, sig in zip(el, I) if sig])
    nt = len(net)
    tr = {"n": nt, "share_profitable": float(np.mean(net > 0)), "mean": float(net.mean()), "median": float(np.median(net)),
          "t": float(net.mean() / (net.std(ddof=1) / math.sqrt(nt))) if nt > 1 else None, "worst": float(net.min()),
          "net_per_year": float(net.sum() / (len(el) / 52))}
    tr["trade_passes"] = bool(tr["mean"] > 0 and tr["t"] is not None and tr["t"] >= 2.0 and nt >= MIN_SIGNAL)
    res["trade"] = tr
    return res


def pair_id(pair):
    return next(k for k, v in PAIRS.items() if v == pair)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, px = load_bench(os.path.join(a.data, "bench.csv"))
    episode_keys = {dt.date.fromisoformat(r["week_end"]).isocalendar()[:2] for r in csv.DictReader(open(a.episodes, newline=""))}
    weeks = weeks_of(days)
    res = {"pairs": {}}
    for pid, pair in PAIRS.items():
        s = spread(px[pair[0]], px[pair[1]])
        res["pairs"][pid] = analyse(pair, days, s, weeks, episode_keys)
    P1, P2 = res["pairs"]["P1"], res["pairs"]["P2"]
    c1 = bool(P1["d"] < 0 and P1["p_shift"] <= 0.025 and P1["n_signal"] >= MIN_SIGNAL)
    c2 = bool(P2["d"] < 0 and P2["p_shift"] <= 0.05 and P2["n_signal"] >= MIN_SIGNAL)
    res["criteria"] = {"p1": c1, "p2": c2}
    res["p1_alone"] = bool(c1 and not c2)
    res["verdict"] = "INSUFFICIENT" if P1["n_signal"] < MIN_SIGNAL else ("SUPPORTED" if c1 and c2 else "NOT SUPPORTED")
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
