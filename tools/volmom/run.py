"""Frozen test (PREREG.md governs): volatility-managed momentum out of sample, 2016 to 2026, by the
Barroso and Santa-Clara scaling, judged by the Moreira-Muir alpha and the Sharpe ratio.

Inputs under --data: mom_daily.csv (DATE,Mom in per cent) and bench.csv (DATE,MTUM,SPY adjusted
closes). Writes results.json to --out.

Choices where the PREREG is silent, fixed before any data was seen: the 126-day window is the 126
file rows immediately preceding the month's first row; the Sharpe ratio uses ddof = 1; the worst-
month list is by raw OOS return ascending; the MTUM spread's realised variance uses the daily
spread d = r_MTUM - r_SPY over rows where both are defined, and a month is used only if every row
in it has both closes and the prior close.

Usage: python run.py --data DATA_DIR --out OUT_DIR
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402  frozen: ols() with Newey-West L = 3

SEED = 20261029
N_BOOT = 10_000
WIN, SCALE, BLOCK = 126, 21, 12
S_T = 0.12 / math.sqrt(12)
MIN_OOS = 96
OOS_START = (2016, 1)


def last_weekday(y, m):
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def complete_months(days):
    keys = sorted({(d.year, d.month) for d in days})
    last = days[-1]
    out = []
    for k in keys:
        if k < (last.year, last.month) or last == last_weekday(*k):
            out.append(k)
    return out


def monthly_series(days, r):
    """Monthly compounded return and the 126-row realised monthly variance before each month."""
    keys = [(d.year, d.month) for d in days]
    out = {}
    i, n = 0, len(days)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        seg = r[i:j + 1]
        R = float(np.prod(1 + seg) - 1) if not np.isnan(seg).any() else np.nan
        if i >= WIN and not np.isnan(r[i - WIN:i]).any():
            v = SCALE / WIN * float(np.sum(r[i - WIN:i] ** 2))
        else:
            v = np.nan
        out[keys[i]] = (R, v)
        i = j + 1
    return out


def sharpe(x):
    return float(math.sqrt(12) * x.mean() / x.std(ddof=1))


def maxdd(x):
    w = np.concatenate([[1.0], np.cumprod(1 + x)])
    return float(np.min(w / np.maximum.accumulate(w)) - 1)


def boot_p(raw, man, rng):
    n = len(raw)
    nb = math.ceil(n / BLOCK)
    le = 0
    for _ in range(N_BOOT):
        starts = rng.integers(0, n, size=nb)
        idx = np.concatenate([(s + np.arange(BLOCK)) % n for s in starts])[:n]
        if sharpe(man[idx]) - sharpe(raw[idx]) <= 0:
            le += 1
    return (1 + le) / (1 + N_BOOT)


def evaluate(months, R, V, rng):
    w = S_T / np.sqrt(V)
    M = w * R
    res = {"n": int(len(R)), "first": f"{months[0][0]}-{months[0][1]:02d}", "last": f"{months[-1][0]}-{months[-1][1]:02d}"}
    b, se = vp.ols(M, R[:, None])
    res.update({"alpha_monthly": float(b[0]), "alpha_t": float(b[0] / se[0]), "b": float(b[1])})
    res["sharpe_raw"], res["sharpe_managed"] = sharpe(R), sharpe(M)
    res["sharpe_ratio"] = res["sharpe_managed"] / res["sharpe_raw"] if res["sharpe_raw"] > 0 else float("nan")
    res["p_boot"] = boot_p(R, M, rng)
    ca = res["alpha_monthly"] > 0 and res["alpha_t"] >= 2.0
    # (b) as "at least 1.2 x" when the raw Sharpe is positive; with a raw Sharpe at or below zero the
    # ratio is meaningless, so the same margin is applied as an improvement of 0.2 x |raw|.
    gain = res["sharpe_managed"] - res["sharpe_raw"]
    cb = gain >= 0.2 * abs(res["sharpe_raw"]) and res["p_boot"] <= 0.05
    res["criteria"] = {"a": bool(ca), "b": bool(cb)}
    if len(R) < MIN_OOS:
        res["verdict"] = "INSUFFICIENT"
    else:
        res["verdict"] = "PASS" if (ca and cb) else ("WEAK" if (ca or cb) else "FAIL")
    res["maxdd_raw"], res["maxdd_managed"] = maxdd(R), maxdd(M)
    res["weight_min"], res["weight_median"], res["weight_max"] = float(w.min()), float(np.median(w)), float(w.max())
    res["weight_share_above_2"] = float(np.mean(w > 2))
    order = np.argsort(R)[:5]
    res["worst_raw_months"] = [{"month": f"{months[i][0]}-{months[i][1]:02d}", "raw": float(R[i]), "managed": float(M[i])} for i in order]
    res["ann_return_managed"] = float(np.prod(1 + M) ** (12 / len(M)) - 1)
    res["cost_estimate_annual"] = float(0.002 * np.sum(np.abs(np.diff(w))) / (len(w) / 12))
    return res


def load_mom(path):
    d = vp.read_daily(path, ["Mom"])
    days = sorted(d)
    return days, np.array([d[x][0] / 100 for x in days])


def load_bench(path):
    rows = [r for r in csv.DictReader(open(path, newline="")) if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {k: np.array([float(r[k]) if r[k].strip() else np.nan for r in rows]) for k in ("MTUM", "SPY")}
    ret = {}
    for k, v in px.items():
        x = np.full(len(days), np.nan)
        x[1:] = v[1:] / v[:-1] - 1
        ret[k] = x
    return days, ret


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, r = load_mom(os.path.join(a.data, "mom_daily.csv"))
    ms = monthly_series(days, r)
    comp = [k for k in complete_months(days) if k in ms and not np.isnan(ms[k][0]) and not np.isnan(ms[k][1])]
    is_m = [k for k in comp if k < OOS_START]
    oos = [k for k in comp if k >= OOS_START]
    res = {}
    if oos:
        o = evaluate(oos, np.array([ms[k][0] for k in oos]), np.array([ms[k][1] for k in oos]), np.random.default_rng(SEED))
        res.update({"n_oos": o["n"], "oos_first": o["first"], "oos_last": o["last"], "oos_alpha_monthly": o["alpha_monthly"],
                    "oos_alpha_t": o["alpha_t"], "oos_b": o["b"], "oos_sharpe_raw": o["sharpe_raw"],
                    "oos_sharpe_managed": o["sharpe_managed"], "oos_sharpe_ratio": o["sharpe_ratio"], "p_boot": o["p_boot"],
                    "criteria": o["criteria"], "verdict": o["verdict"], "oos_maxdd_raw": o["maxdd_raw"],
                    "oos_maxdd_managed": o["maxdd_managed"], "weight_min": o["weight_min"], "weight_median": o["weight_median"],
                    "weight_max": o["weight_max"], "weight_share_above_2": o["weight_share_above_2"],
                    "worst_raw_months": o["worst_raw_months"]})
    else:
        res.update({"n_oos": 0, "verdict": "INSUFFICIENT"})
    if is_m:
        i = evaluate(is_m, np.array([ms[k][0] for k in is_m]), np.array([ms[k][1] for k in is_m]), np.random.default_rng(SEED))
        res.update({"n_is": i["n"], "is_first": i["first"], "is_sharpe_raw": i["sharpe_raw"], "is_sharpe_managed": i["sharpe_managed"],
                    "is_alpha_monthly": i["alpha_monthly"], "is_alpha_t": i["alpha_t"]})
    else:
        res["n_is"] = 0
    # implementable version: long MTUM, short SPY
    bdays, bret = load_bench(os.path.join(a.data, "bench.csv"))
    ok = ~np.isnan(bret["MTUM"]) & ~np.isnan(bret["SPY"])
    d = np.where(ok, bret["MTUM"] - bret["SPY"], np.nan)
    keys = [(x.year, x.month) for x in bdays]
    spread, var = {}, {}
    i, n = 0, len(bdays)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        if ok[i:j + 1].all():
            spread[keys[i]] = float(np.prod(1 + bret["MTUM"][i:j + 1]) - np.prod(1 + bret["SPY"][i:j + 1]))
        if i >= WIN and not np.isnan(d[i - WIN:i]).any():
            var[keys[i]] = SCALE / WIN * float(np.sum(d[i - WIN:i] ** 2))
        i = j + 1
    mk = [k for k in complete_months(bdays) if k in spread and k in var]
    if mk:
        m = evaluate(mk, np.array([spread[k] for k in mk]), np.array([var[k] for k in mk]), np.random.default_rng(SEED))
        res["mtum"] = {k: m[k] for k in ("n", "first", "last", "alpha_monthly", "alpha_t", "sharpe_raw", "sharpe_managed",
                                          "sharpe_ratio", "p_boot", "verdict", "ann_return_managed", "cost_estimate_annual",
                                          "maxdd_raw", "maxdd_managed")}
    else:
        res["mtum"] = {"n": 0, "verdict": "INSUFFICIENT"}
    print(json.dumps(res, indent=1, default=str))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
