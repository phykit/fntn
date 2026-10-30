"""Index overwrite against single-stock overwrite (tools/index_vs_single_overwrite/PREREG.md).

Frozen implementation. Data loading and the at-the-money premium come from the frozen
tools/single_name_vrp/run.py, loaded under its own name, so the per-name excess is run 3's."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("single_name_vrp_run",
                                               os.path.join(HERE, "..", "single_name_vrp", "run.py"))
snv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snv)

NAMES = snv.NAMES
CUTOFF = "2026-09-01"
SEED = 20261101
B = 2000
BLOCK = 12
MIN_N = 120
MAX_DISCARD = 20
SKEW_I, SKEW_N = 0.9, 0.95


def extract(dates, px, vx):
    """Monthly arrays over U: per-name G and implied vol, SPY's G and the VIX (section 2)."""
    n = len(dates)
    r = {}
    for k, p in px.items():
        rr = np.full(n, np.nan)
        rr[1:] = np.log(p[1:] / p[:-1])
        r[k] = rr
    seen, t0s = set(), []
    for j, d in enumerate(dates):
        if d[:7] in seen:
            continue
        seen.add(d[:7])
        if j + snv.WIN <= n - 1:
            t0s.append(j)
    months, G, V = [], {k: [] for k in NAMES + ["SPY"]}, {k: [] for k in NAMES + ["MKT"]}
    for j in t0s:
        if dates[j] > CUTOFF or j - snv.BETA_N + 1 < 1:
            continue
        bw, hw = slice(j - snv.BETA_N + 1, j + 1), slice(j + 1, j + snv.WIN + 1)
        rm = r["SPY"]
        if np.isnan(rm[bw]).any() or np.isnan(rm[hw]).any() or not (vx["MKT"][j] == vx["MKT"][j]):
            continue
        if rm[bw].var() == 0:
            continue  # beta undefined, so no name-month is used (single_name_vrp section 3)
        if not all(vx[i][j] == vx[i][j] and not np.isnan(r[i][bw]).any() and not np.isnan(r[i][hw]).any()
                   for i in NAMES):
            continue
        months.append(dates[j])
        for k in NAMES + ["SPY"]:
            G[k].append(px[k][j + snv.WIN] / px[k][j])
        for k in NAMES + ["MKT"]:
            V[k].append(vx[k][j] / 100.0)
    return months, {k: np.array(v) for k, v in G.items()}, {k: np.array(v) for k, v in V.items()}


def legs(G, V, fi: float = 1.0, fn: float = 1.0):
    """Monthly h, y, k for the index and the basket (section 2); fi, fn scale the implied vols."""
    c = np.vectorize(snv.atm_call)
    hI = G["SPY"] - 1.0
    yI = c(fi * V["MKT"]) - np.maximum(G["SPY"] - 1.0, 0.0)
    ys = [c(fn * V[i]) - np.maximum(G[i] - 1.0, 0.0) for i in NAMES]
    hB = np.mean([G[i] for i in NAMES], axis=0) - 1.0
    yB = np.mean(ys, axis=0)
    return hI, yI, hI + yI, hB, yB, hB + yB


def sh(x) -> float:
    return float(x.mean() / x.std(ddof=1))


def delta(L, idx) -> float:
    hI, yI, kI, hB, yB, kB = (a[idx] for a in L)
    for a in (hI, kI, hB, kB):
        if a.std(ddof=1) == 0:
            raise ZeroDivisionError
    return (sh(kI) - sh(hI)) - (sh(kB) - sh(hB))


def nw_t(x) -> float:
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for l in range(1, 4):
        s += 2.0 * (1.0 - l / 4.0) * float((e[l:] * e[:-l]).sum())
    return float(x.mean() / (math.sqrt(s) / n))


def analyse(months, G, V, b: int = B) -> dict:
    n = len(months)
    res = {"n": n, "first_month": months[0] if n else None, "last_month": months[-1] if n else None}
    if n < BLOCK:
        res["verdict"] = "INSUFFICIENT"
        return res
    L = legs(G, V)
    hI, yI, kI, hB, yB, kB = L
    res["Delta"] = delta(L, np.arange(n))
    rng = np.random.default_rng(SEED)
    boots, disc = [], 0
    for _ in range(b):
        starts = rng.integers(0, n - BLOCK + 1, size=math.ceil(n / BLOCK))
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        try:
            boots.append(delta(L, idx))
        except ZeroDivisionError:
            disc += 1
    boots = np.array(boots)
    res.update({"discarded": disc, "lower": float(np.percentile(boots, 5)),
                "boot_mean": float(boots.mean()), "boot_p95": float(np.percentile(boots, 95))})
    if n < MIN_N:
        res["verdict"] = "INSUFFICIENT"
    elif disc > MAX_DISCARD:
        res["verdict"] = "REFUSED"
    elif res["Delta"] > 0 and res["lower"] > 0:
        res["verdict"] = "SUPPORTED"
    else:
        res["verdict"] = "NOT SUPPORTED"
    res.update({"sh_hI": sh(hI), "sh_kI": sh(kI), "sh_hB": sh(hB), "sh_kB": sh(kB)})
    res["impr_I"] = res["sh_kI"] - res["sh_hI"]
    res["impr_B"] = res["sh_kB"] - res["sh_hB"]
    for tag, y in (("yI", yI), ("yB", yB)):
        res[f"{tag}_mean_pct"] = float(100 * y.mean())
        res[f"{tag}_sd_pct"] = float(100 * y.std(ddof=1))
        res[f"{tag}_ir"] = sh(y)
    d = yI - yB
    res["diff_mean_pct"] = float(100 * d.mean())
    res["diff_t"] = nw_t(d)
    res["Delta_skew"] = delta(legs(G, V, SKEW_I, SKEW_N), np.arange(n))
    res["ann"] = {k: res[k] * math.sqrt(12) for k in ("sh_hI", "sh_kI", "sh_hB", "sh_kB")}
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
