"""Term-structure filter on the index overwrite (tools/ts_filter_overwrite/PREREG.md). Frozen
implementation; every rule is the pre-registration's."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

WIN = 21
CUTOFF = "2026-09-01"
SEED = 20261102
B = 2000
BLOCK = 12
MIN_N = 120
MAX_DISCARD = 20
PCT = 1
SEED_RAND = 20261103
R = 2000
STEEP = 0.95
SKEW = 0.9


def ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def atm_call(s: float) -> float:
    d1 = s * math.sqrt(WIN / 252.0) / 2.0
    return ncdf(d1) - ncdf(-d1)


def read_csv(path):
    with open(path) as f:
        rows = list(csv.reader(f))
    head = rows[0]
    out = {c: {} for c in head[1:]}
    for r in rows[1:]:
        for j, c in enumerate(head[1:], start=1):
            if j < len(r) and r[j].strip() != "":
                out[c][r[0]] = float(r[j])
    return out


def extract(data_dir: str):
    """Monthly arrays over U (section 3)."""
    px = read_csv(os.path.join(data_dir, "prices.csv"))["SPY"]
    vx = read_csv(os.path.join(data_dir, "vx.csv"))
    dates = sorted(px)
    p = np.array([px[d] for d in dates])
    seen, months, G, V, V3 = set(), [], [], [], []
    for j, d in enumerate(dates):
        if d[:7] in seen:
            continue
        seen.add(d[:7])
        if j + WIN > len(dates) - 1 or d > CUTOFF:
            continue
        if d not in vx["MKT"] or d not in vx["M3"]:
            continue
        months.append(d)
        G.append(p[j + WIN] / p[j])
        V.append(vx["MKT"][d])
        V3.append(vx["M3"][d])
    return months, np.array(G), np.array(V), np.array(V3)


def legs(G, V, V3, steep: float | None = None, skew: float = 1.0):
    h = G - 1.0
    c = np.array([atm_call(skew * v / 100.0) for v in V])
    y = c - np.maximum(G - 1.0, 0.0)
    W = (V / V3 < steep) if steep is not None else (V < V3)
    return h, y, h + y, h + W * y, W


def sh(x) -> float:
    return float(x.mean() / x.std(ddof=1))


def delta(kF, kA, idx) -> float:
    a, b = kF[idx], kA[idx]
    if a.std(ddof=1) == 0 or b.std(ddof=1) == 0:
        raise ZeroDivisionError
    return sh(a) - sh(b)


def nw_t(x) -> float:
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for l in range(1, 4):
        s += 2.0 * (1.0 - l / 4.0) * float((e[l:] * e[:-l]).sum())
    return float(x.mean() / (math.sqrt(s) / n))


def bootstrap(kF, kA, n, b=B, seed=SEED):
    rng = np.random.default_rng(seed)
    out, disc = [], 0
    for _ in range(b):
        starts = rng.integers(0, n - BLOCK + 1, size=math.ceil(n / BLOCK))
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        try:
            out.append(delta(kF, kA, idx))
        except ZeroDivisionError:
            disc += 1
    return np.array(out), disc


def random_skip(h, y, kA, n_back: int, r: int = R, seed: int = SEED_RAND) -> np.ndarray:
    """Section 4 benchmark: skip n_back months chosen at random, so that the verdict asks whether
    the term structure picks better months to skip than chance does."""
    rng = np.random.default_rng(seed)
    n = h.size
    out = np.empty(r)
    base = sh(kA)
    for i in range(r):
        W = np.ones(n, dtype=bool)
        W[rng.choice(n, size=n_back, replace=False)] = False
        out[i] = sh(h + W * y) - base
    return out


def analyse(months, G, V, V3, b: int = B, r: int = R) -> dict:
    n = len(months)
    res = {"n": n, "first_month": months[0] if n else None, "last_month": months[-1] if n else None}
    if n < BLOCK:
        res["verdict"] = "INSUFFICIENT"
        return res
    h, y, kA, kF, W = legs(G, V, V3)
    allidx = np.arange(n)
    res["Delta"] = delta(kF, kA, allidx)
    boots, disc = bootstrap(kF, kA, n, b)
    res.update({"discarded": disc, "lower": float(np.percentile(boots, PCT)),
                "boot_mean": float(boots.mean()), "boot_p05": float(np.percentile(boots, 5)),
                "boot_p95": float(np.percentile(boots, 95))})
    back = ~W
    rs = random_skip(h, y, kA, int(back.sum()), r)
    res.update({"rand_mean": float(rs.mean()), "rand_p99": float(np.percentile(rs, 99)),
                "rand_share_ge": float((rs >= res["Delta"]).mean())})
    if n < MIN_N:
        res["verdict"] = "INSUFFICIENT"
    elif disc > MAX_DISCARD:
        res["verdict"] = "REFUSED"
    elif res["Delta"] > 0 and res["lower"] > 0 and res["Delta"] > res["rand_p99"]:
        res["verdict"] = "SUPPORTED"
    else:
        res["verdict"] = "NOT SUPPORTED"
    res["n_back"] = int(back.sum())
    res["back_dates"] = [m for m, w in zip(months, W) if not w]
    res["y_con_mean_pct"] = float(100 * y[W].mean())
    res["y_con_sd_pct"] = float(100 * y[W].std(ddof=1))
    res["y_back_mean_pct"] = float(100 * y[back].mean()) if back.any() else None
    res["y_back_sd_pct"] = float(100 * y[back].std(ddof=1)) if back.sum() > 1 else None
    res.update({"sh_h": sh(h), "sh_kA": sh(kA), "sh_kF": sh(kF)})
    res["sh_kF_minus_h"] = res["sh_kF"] - res["sh_h"]
    res["ann"] = {k: res[f"sh_{k}"] * math.sqrt(12) for k in ("h", "kA", "kF")}
    d = kF - kA
    res["diff_mean_pct"] = float(100 * d.mean())
    res["diff_t"] = nw_t(d)
    res["annret"] = {"h": float(12 * h.mean()), "kA": float(12 * kA.mean()), "kF": float(12 * kF.mean())}
    _, _, kA2, kF2, _ = legs(G, V, V3, steep=STEEP)
    res["Delta_steep"] = delta(kF2, kA2, allidx)
    _, _, kA3, kF3, _ = legs(G, V, V3, skew=SKEW)
    res["Delta_skew"] = delta(kF3, kA3, allidx)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(*extract(a.data))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
