"""Premium in selling 5% out-of-the-money S&P 500 puts at traded prices: S&P total return less PPUT
(tools/otm_put_premium/PREREG.md). Frozen implementation; every rule is the pre-registration's."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

LAST = "2026-09"
SPLIT = "2016-05"
SEED = 20261105
B = 2000
BLOCK = 12
MIN_N = 120
T_BAR = 2.326


def monthly(path: str):
    """Calendar-month returns on the last date in each month with PPUT and SPY both present;
    PUT and BXM are read on that same date (section 3)."""
    with open(path) as f:
        rows = list(csv.reader(f))
    head = rows[0]
    ix = {c: head.index(c) for c in ("PPUT", "SPY", "PUT", "BXM")}

    def val(r, c):
        """A blank, non-numeric or non-finite cell stays missing (section 2)."""
        j = ix[c]
        if j >= len(r):
            return None
        try:
            v = float(r[j])
        except ValueError:
            return None
        return v if math.isfinite(v) else None

    last = {}
    for r in sorted(rows[1:], key=lambda r: r[0]):
        if val(r, "PPUT") is None or val(r, "SPY") is None:
            continue
        last[r[0][:7]] = {c: val(r, c) for c in ix}
    ms = sorted(last)
    out = {"months": [], "PPUT": [], "SPY": [], "PUT": [], "BXM": []}
    for prev, cur in zip(ms, ms[1:]):
        py, pm, cy, cm = int(prev[:4]), int(prev[5:7]), int(cur[:4]), int(cur[5:7])
        if (cy * 12 + cm) - (py * 12 + pm) != 1 or cur > LAST:
            continue
        out["months"].append(cur)
        for c in ix:
            a, b = last[prev][c], last[cur][c]
            out[c].append(b / a - 1.0 if a is not None and b is not None else np.nan)
    return {k: (v if k == "months" else np.array(v)) for k, v in out.items()}


def nw(x):
    """Mean, Newey-West standard error (3 lags, Bartlett, no small-sample correction), t."""
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for l in range(1, 4):
        if l < n:
            s += 2.0 * (1.0 - l / 4.0) * float((e[l:] * e[:-l]).sum())
    se = math.sqrt(s) / n
    return float(x.mean()), se, float(x.mean() / se)


def sh(x) -> float:
    return float(x.mean() / x.std(ddof=1))


def maxdd(x) -> float:
    eq = np.concatenate([[1.0], np.cumprod(1.0 + x)])
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def ann(x, downside: bool = True) -> dict:
    d = {"mean": float(12 * x.mean()), "vol": float(math.sqrt(12) * x.std(ddof=1)),
         "sharpe": sh(x) * math.sqrt(12), "maxdd": maxdd(x)}
    if downside:
        d["downside_ratio"] = float(x.mean() / math.sqrt(np.mean(np.minimum(x, 0.0) ** 2)))
    return d


def boot_delta(k, s, reps=B, seed=SEED):
    n = k.size
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        starts = rng.integers(0, n - BLOCK + 1, size=math.ceil(n / BLOCK))
        idx = np.concatenate([np.arange(st, st + BLOCK) for st in starts])[:n]
        out.append(sh(k[idx]) - sh(s[idx]))
    return np.array(out)


SEED_T = 20261106
B_T = 1999
PCT_T = 99


def nw_se_rows(Y):
    """Newey-West standard error of the mean, row by row (the same estimator as nw)."""
    n = Y.shape[-1]
    e = Y - Y.mean(-1, keepdims=True)
    s = (e * e).sum(-1)
    for l in range(1, 4):
        s = s + 2.0 * (1.0 - l / 4.0) * (e[..., l:] * e[..., :-l]).sum(-1)
    return np.sqrt(s) / n


def t_crit(y, reps: int = B_T, seed: int = SEED_T) -> float:
    """Block-bootstrap t critical value (section 4 amendment): the normal 2.326 over-rejects on
    negatively skewed data such as a short put's, so the critical value is taken from the data."""
    n = y.size
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n - BLOCK + 1, size=(reps, math.ceil(n / BLOCK)))
    idx = (starts[:, :, None] + np.arange(BLOCK)).reshape(reps, -1)[:, :n]
    Y = y[idx]
    tstar = (Y.mean(1) - y.mean()) / nw_se_rows(Y)
    return float(np.percentile(tstar, PCT_T))


def verdict(y, reps: int = B_T) -> tuple[str, float, float, float, str]:
    m, _, t = nw(y)
    tc = t_crit(y, reps)
    if y.size < MIN_N:
        return "INSUFFICIENT", m, t, tc, "INSUFFICIENT"
    v = "SUPPORTED" if m > 0 and t >= tc else "NOT SUPPORTED"
    vn = "SUPPORTED" if m > 0 and t >= T_BAR else "NOT SUPPORTED"
    return v, m, t, tc, vn


def analyse(D: dict, reps: int = B) -> dict:
    months = np.array(D["months"])
    y = D["SPY"] - D["PPUT"]
    n = y.size
    res = {"n": int(n), "first_month": str(months[0]) if n else None, "last_month": str(months[-1]) if n else None}
    if n < BLOCK:
        res["verdict"] = "INSUFFICIENT"
        return res
    res["verdict"], res["mean_y"], res["t"], res["t_crit"], res["verdict_normal"] = verdict(y)
    for tag, mask in (("pre", months <= SPLIT), ("post", months > SPLIT)):
        m, _, t = nw(y[mask])
        res[f"mean_y_{tag}"], res[f"t_{tag}"], res[f"n_{tag}"] = m, t, int(mask.sum())
    e = y - y.mean()
    pos = y[y > 0].sum()
    res["y_stats"] = {"ann_mean": float(12 * y.mean()), "sd": float(y.std(ddof=1)), "ratio": sh(y),
                      "skew": float(np.mean(e ** 3) / y.std(ddof=0) ** 3), "worst": float(y.min()),
                      "share_neg": float((y < 0).mean()),
                      "worst5_over_pos": float(np.sort(y)[:5].sum() / pos)}
    k, s = D["SPY"] + y, D["SPY"]
    bd = boot_delta(k, s, reps)
    res["overlay"] = {"k": ann(k), "spy": ann(s), "delta_k": sh(k) - sh(s),
                      "boot_p05": float(np.percentile(bd, 5)), "boot_p95": float(np.percentile(bd, 95))}
    ok = ~np.isnan(D["PUT"]) & ~np.isnan(D["BXM"])
    res["atm"] = {"n": int(ok.sum()), "PUT": ann(D["PUT"][ok], False), "BXM": ann(D["BXM"][ok], False),
                  "SPY": ann(D["SPY"][ok], False)}
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(monthly(os.path.join(a.data, "series.csv")))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
