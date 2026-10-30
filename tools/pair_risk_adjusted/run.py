"""Covered-call excess per unit of risk, by pair correlation (tools/pair_risk_adjusted/PREREG.md).

Frozen implementation. Data loading and the at-the-money premium are imported from the frozen
tools/single_name_vrp/run.py so that the per-name excess is run 3's, not a re-derivation of it."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys

import importlib.util

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# Loaded under its own name: both modules are called run.py, and a plain import would resolve to
# this file.
_spec = importlib.util.spec_from_file_location("single_name_vrp_run",
                                               os.path.join(HERE, "..", "single_name_vrp", "run.py"))
snv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snv)

NAMES = snv.NAMES
PAIRS = list(itertools.combinations(NAMES, 2))
CUTOFF = "2026-09-01"
SEED = 20261031
B = 2000
BLOCK = 12
MIN_N = 120
MAX_DISCARD = 20


def extract(dates, px, vx):
    """Per-name y and G and per-pair trailing correlation over U (PREREG sections 2 and 3)."""
    n = len(dates)
    r = {}
    for k, p in px.items():
        rr = np.full(n, np.nan)
        rr[1:] = np.log(p[1:] / p[:-1])
        r[k] = rr
    seen = set()
    t0s = []
    for j, d in enumerate(dates):
        if d[:7] in seen:
            continue
        seen.add(d[:7])
        if j + snv.WIN <= n - 1:
            t0s.append(j)
    U, Y, G, C = [], {i: [] for i in NAMES}, {i: [] for i in NAMES}, {p: [] for p in PAIRS}
    for j in t0s:
        if dates[j] > CUTOFF or j - snv.BETA_N + 1 < 1:
            continue
        bw = slice(j - snv.BETA_N + 1, j + 1)
        hw = slice(j + 1, j + snv.WIN + 1)
        if np.isnan(r["SPY"][bw]).any() or np.isnan(r["SPY"][hw]).any() or not (vx["MKT"][j] == vx["MKT"][j]):
            continue
        ok = all(vx[i][j] == vx[i][j] and not np.isnan(r[i][bw]).any() and not np.isnan(r[i][hw]).any()
                 for i in NAMES)
        if not ok:
            continue  # U requires all five names used (section 3)
        U.append(j)
        for i in NAMES:
            g = px[i][j + snv.WIN] / px[i][j]
            Y[i].append(snv.atm_call(vx[i][j] / 100.0) - max(g - 1.0, 0.0))
            G[i].append(g)
        for a, b in PAIRS:
            C[(a, b)].append(float(np.corrcoef(r[a][bw], r[b][bw])[0, 1]))
    return ([dates[j] for j in U], {i: np.array(v) for i, v in Y.items()},
            {i: np.array(v) for i, v in G.items()}, {p: np.array(v) for p, v in C.items()})


def ir(x: np.ndarray) -> float:
    return float(x.mean() / x.std(ddof=1))


def split(c: np.ndarray):
    med = float(np.median(c))
    return c < med, c >= med  # a value equal to the median goes to H (section 4)


def D_of(Y, C, idx) -> float:
    """Mean over pairs of IR(low) - IR(high) on the month positions idx (duplicates count)."""
    ds = []
    for a, b in PAIRS:
        y = 0.5 * (Y[a][idx] + Y[b][idx])
        lo, hi = split(C[(a, b)][idx])
        sl, sh = y[lo].std(ddof=1), y[hi].std(ddof=1)
        if sl == 0 or sh == 0:
            raise ZeroDivisionError
        ds.append(y[lo].mean() / sl - y[hi].mean() / sh)
    return float(np.mean(ds))


def bootstrap(Y, C, n: int, b: int = B, seed: int = SEED):
    rng = np.random.default_rng(seed)
    nb = math.ceil(n / BLOCK)
    out, discarded = [], 0
    for _ in range(b):
        starts = rng.integers(0, n - BLOCK + 1, size=nb)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        try:
            out.append(D_of(Y, C, idx))
        except ZeroDivisionError:
            discarded += 1
    return np.array(out), discarded


def spearman(x, y) -> float:
    def rank(v):
        v = np.asarray(v, float)
        order = v.argsort(kind="mergesort")
        rk = np.empty(len(v))
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            rk[order[i:j + 1]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return rk
    return float(np.corrcoef(rank(x), rank(y))[0, 1])


def analyse(months, Y, G, C, b: int = B) -> dict:
    n = len(months)
    res = {"n": n, "first_month": months[0] if n else None, "last_month": months[-1] if n else None}
    if n < BLOCK:
        res["verdict"] = "INSUFFICIENT"  # too short even to draw one bootstrap block
        return res
    allidx = np.arange(n)
    res["D"] = D_of(Y, C, allidx)
    boot, disc = bootstrap(Y, C, n, b)
    res["discarded"] = disc
    res["lower"] = float(np.percentile(boot, 5))
    res["boot_mean"] = float(boot.mean())
    res["boot_p05"] = res["lower"]
    res["boot_p95"] = float(np.percentile(boot, 95))
    # Figures are computed and reported below the 120-month floor too; only the verdict refuses.
    if n < MIN_N:
        res["verdict"] = "INSUFFICIENT"
    elif disc > MAX_DISCARD:
        res["verdict"] = "REFUSED"
    elif res["D"] > 0 and res["lower"] > 0:
        res["verdict"] = "SUPPORTED"
    else:
        res["verdict"] = "NOT SUPPORTED"
    pairs, mc, irs, drs, mdiff, sdiff = {}, [], [], [], [], []
    pooled_c, pooled_y = [], []
    for a, b2 in PAIRS:
        y = 0.5 * (Y[a] + Y[b2])
        h = 0.5 * (G[a] + G[b2]) - 1.0
        k = h + y
        c = C[(a, b2)]
        lo, hi = split(c)
        d = {"mean_c": float(c.mean()), "mean_y": float(y.mean()), "sd_y": float(y.std(ddof=1)), "ir": ir(y),
             "mean_y_low": float(y[lo].mean()), "sd_y_low": float(y[lo].std(ddof=1)), "ir_low": ir(y[lo]),
             "mean_y_high": float(y[hi].mean()), "sd_y_high": float(y[hi].std(ddof=1)), "ir_high": ir(y[hi]),
             "div_ratio": float(y.std(ddof=1) / ((Y[a].std(ddof=1) + Y[b2].std(ddof=1)) / 2.0)),
             "sharpe_held": ir(h), "sharpe_covered": ir(k)}
        d["delta"] = d["ir_low"] - d["ir_high"]
        d["sharpe_diff"] = d["sharpe_covered"] - d["sharpe_held"]
        pairs[f"{a}-{b2}"] = d
        mc.append(d["mean_c"]); irs.append(d["ir"]); drs.append(d["div_ratio"])
        mdiff.append(d["mean_y_low"] - d["mean_y_high"]); sdiff.append(d["sd_y_low"] - d["sd_y_high"])
        pooled_c.append(c); pooled_y.append(y)
    res["pairs"] = pairs
    res["names"] = {i: {"mean_y": float(Y[i].mean()), "sd_y": float(Y[i].std(ddof=1)), "ir": ir(Y[i])} for i in NAMES}
    res["spearman_c_ir"] = spearman(mc, irs)
    res["spearman_c_divratio"] = spearman(mc, drs)
    res["decomp_mean_diff"] = float(np.mean(mdiff))
    res["decomp_sd_diff"] = float(np.mean(sdiff))
    for key in ("sharpe_held", "sharpe_covered", "sharpe_diff"):
        res[f"{key}_mean"] = float(np.mean([p[key] for p in pairs.values()]))
    pc, py = np.concatenate(pooled_c), 100.0 * np.concatenate(pooled_y)
    med = float(np.median(pc))
    res["recon_low_pct"] = float(py[pc < med].mean())
    res["recon_high_pct"] = float(py[pc >= med].mean())
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(*extract(*snv.load(a.data)))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
