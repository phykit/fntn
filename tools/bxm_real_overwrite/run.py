"""Index overwrite at real option prices: BXM against SPY (tools/bxm_real_overwrite/PREREG.md).
Frozen implementation; every rule is the pre-registration's."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

LAST = "2026-09"
SPLIT = "2010-12"
RECON_FROM = "2011-02"
SEED = 20261104
B = 2000
BLOCK = 12
MIN_N = 120
MAX_DISCARD = 20
PCT = 1


def monthly(path: str):
    """Calendar-month returns from the last date in each month with BXM and SPY both present."""
    with open(path) as f:
        rows = list(csv.reader(f))
    head = rows[0]
    bi, si = head.index("BXM"), head.index("SPY")
    last = {}
    for r in rows[1:]:
        if len(r) <= max(bi, si) or r[bi].strip() == "" or r[si].strip() == "":
            continue
        last[r[0][:7]] = (r[0], float(r[bi]), float(r[si]))  # rows are date-sorted, so the last wins
    ms = sorted(last)
    months, rb, rs = [], [], []
    for prev, cur in zip(ms, ms[1:]):
        py, pm = int(prev[:4]), int(prev[5:7])
        cy, cm = int(cur[:4]), int(cur[5:7])
        if (cy * 12 + cm) - (py * 12 + pm) != 1 or cur > LAST:
            continue  # a month without the previous calendar month's value has no return
        months.append(cur)
        rb.append(last[cur][1] / last[prev][1] - 1.0)
        rs.append(last[cur][2] / last[prev][2] - 1.0)
    return months, np.array(rb), np.array(rs)


def sh(x) -> float:
    return float(x.mean() / x.std(ddof=1))


def delta(b, s, idx) -> float:
    x, y = b[idx], s[idx]
    if x.std(ddof=1) == 0 or y.std(ddof=1) == 0:
        raise ZeroDivisionError
    return sh(x) - sh(y)


def maxdd(x) -> float:
    eq = np.concatenate([[1.0], np.cumprod(1.0 + x)])
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def downside(x) -> float:
    return float(x.mean() / math.sqrt(np.mean(np.minimum(x, 0.0) ** 2)))


def nw_t(x) -> float:
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for l in range(1, 4):
        s += 2.0 * (1.0 - l / 4.0) * float((e[l:] * e[:-l]).sum())
    return float(x.mean() / (math.sqrt(s) / n))


def bootstrap(b, s, n, reps=B, seed=SEED):
    rng = np.random.default_rng(seed)
    out, disc = [], 0
    for _ in range(reps):
        starts = rng.integers(0, n - BLOCK + 1, size=math.ceil(n / BLOCK))
        idx = np.concatenate([np.arange(st, st + BLOCK) for st in starts])[:n]
        try:
            out.append(delta(b, s, idx))
        except ZeroDivisionError:
            disc += 1
    return np.array(out), disc


def analyse(months, rb, rs, reps: int = B) -> dict:
    n = len(months)
    res = {"n": n, "first_month": months[0] if n else None, "last_month": months[-1] if n else None}
    if n < BLOCK:
        res["verdict"] = "INSUFFICIENT"
        return res
    res["Delta"] = delta(rb, rs, np.arange(n))
    boots, disc = bootstrap(rb, rs, n, reps)
    res.update({"discarded": disc, "lower": float(np.percentile(boots, PCT)),
                "boot_mean": float(boots.mean()), "boot_p05": float(np.percentile(boots, 5)),
                "boot_p95": float(np.percentile(boots, 95))})
    if n < MIN_N:
        res["verdict"] = "INSUFFICIENT"
    elif disc > MAX_DISCARD:
        res["verdict"] = "REFUSED"
    elif res["Delta"] > 0 and res["lower"] > 0:
        res["verdict"] = "SUPPORTED"
    else:
        res["verdict"] = "NOT SUPPORTED"
    res["sh_bxm"], res["sh_spy"] = sh(rb), sh(rs)
    res["ann"] = {k: {"mean": float(12 * x.mean()), "vol": float(math.sqrt(12) * x.std(ddof=1)),
                      "sharpe": sh(x) * math.sqrt(12), "maxdd": maxdd(x), "downside_ratio": downside(x)}
                  for k, x in (("BXM", rb), ("SPY", rs))}
    m = np.array(months)
    pre, post = m <= SPLIT, m > SPLIT
    res["delta_pre2011"] = delta(rb, rs, np.where(pre)[0])
    res["delta_from2011"] = delta(rb, rs, np.where(post)[0])
    d = rb - rs
    res["diff_mean_pct"], res["diff_t"] = float(100 * d.mean()), nw_t(d)
    res["diff_mean_pct_from2011"], res["diff_t_from2011"] = float(100 * d[post].mean()), nw_t(d[post])
    rec = m >= RECON_FROM
    res["recon_mean_pct"] = float(100 * d[rec].mean())
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(*monthly(os.path.join(a.data, "series.csv")))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
