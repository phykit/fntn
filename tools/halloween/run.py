"""Frozen test (PREREG.md governs): the Halloween effect on the Nasdaq 100, out of sample from 2003.

Inputs under --data: ndx.csv (observation_date,NASDAQ100) and ff5_daily.csv (French daily, RF %).
Choices fixed before any data was seen: a month's NDX close is its last observation; monthly return
needs the prior calendar month's close; monthly RF compounds the French rows dated in the month and
a month with none is dropped; the replication sample is the first full month after the NDX start
to December 2002; "winter beats summer" compares each OOS winter's cumulative NDX return (Nov to Apr)
with the cumulative return of the summer that follows it (May to Oct), winters with a complete
following summer only.

Usage: python run.py --data DATA_DIR --out OUT_DIR
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
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_volmom", os.path.join(HERE, "..", "volmom", "run.py"))
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
complete_months, sharpe_fn, maxdd = _vm.complete_months, _vm.sharpe, _vm.maxdd

OOS_START, REP_END, MIN_MONTHS = (2003, 1), (2002, 12), 120
WINTER = {11, 12, 1, 2, 3, 4}


def load_ndx(path):
    rows = list(csv.reader(open(path, newline="")))[1:]
    days, px = [], []
    for r in rows:
        if r[1].strip():
            days.append(dt.date.fromisoformat(r[0])); px.append(float(r[1]))
    return days, np.array(px)


def load_rf(path):
    rf = {}
    for r in csv.DictReader(open(path, newline="")):
        if r["RF"].strip():
            d = dt.date.fromisoformat(r["DATE"]); k = (d.year, d.month)
            rf[k] = rf.get(k, 1.0) * (1 + float(r["RF"]) / 100)
    return {k: v - 1 for k, v in rf.items()}


def nxt(k):
    return (k[0] + (k[1] == 12), k[1] % 12 + 1)


def stats(tot, rfv):
    n = len(tot)
    return {"ann_return": float(np.prod(1 + tot) ** (12 / n) - 1), "ann_vol": float(math.sqrt(12) * tot.std(ddof=1)),
            "sharpe": sharpe_fn(tot - rfv), "max_drawdown": maxdd(tot)}


def reg(e, w):
    b, se = vp.ols(e, w[:, None])
    return {"n": int(len(e)), "a": float(b[0]), "c": float(b[1]), "c_t": float(b[1] / se[1])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, px = load_ndx(os.path.join(a.data, "ndx.csv"))
    rf = load_rf(os.path.join(a.data, "ff5_daily.csv"))
    last = {}
    for d, p in zip(days, px):
        last[(d.year, d.month)] = p
    comp = set(complete_months(days))
    months = [k for k in sorted(last) if k in comp and (k[0] - (k[1] == 1), (k[1] - 2) % 12 + 1) in last and k in rf]
    ret = np.array([last[k] / last[(k[0] - (k[1] == 1), (k[1] - 2) % 12 + 1)] - 1 for k in months])
    rfv = np.array([rf[k] for k in months])
    e = ret - rfv
    w = np.array([1.0 if k[1] in WINTER else 0.0 for k in months])
    oos = np.array([k >= OOS_START for k in months])
    rep = np.array([k <= REP_END for k in months])
    res = {"n_oos": int(oos.sum()), "first_oos": f"{months[np.argmax(oos)][0]}-{months[np.argmax(oos)][1]:02d}",
           "last_oos": f"{months[-1][0]}-{months[-1][1]:02d}"}
    r = reg(e[oos], w[oos])
    res.update({"c": r["c"], "c_t": r["c_t"], "a": r["a"]})
    res["criteria"] = {"primary": bool(r["c"] > 0 and r["c_t"] >= 2.0)}
    res["verdict"] = "INSUFFICIENT" if res["n_oos"] < MIN_MONTHS else ("PASS" if res["criteria"]["primary"] else "FAIL")
    res["mean_winter"], res["mean_summer"] = float(e[oos & (w == 1)].mean()), float(e[oos & (w == 0)].mean())
    res["full"] = {k: v for k, v in reg(e, w).items() if k in ("n", "c", "c_t")}
    res["replication"] = {k: v for k, v in reg(e[rep], w[rep]).items() if k in ("n", "c", "c_t")} if rep.sum() >= 24 else {"n": int(rep.sum())}
    # winters beating the following summer, OOS
    wins, beats = 0, 0
    for i, k in enumerate(months):
        if k[1] == 11 and oos[i] and i + 11 < len(months) and months[i + 11] == (k[0] + 1, 10):
            wn = np.prod(1 + ret[i:i + 6]) - 1
            sm = np.prod(1 + ret[i + 6:i + 12]) - 1
            wins += 1; beats += wn > sm
    res["share_winter_beats_summer"] = beats / wins if wins else None
    res["n_winter_summer_pairs"] = wins
    strat = np.where(w == 1, ret, rfv)
    res["strategy"] = stats(strat[oos], rfv[oos])
    res["held"] = stats(ret[oos], rfv[oos])
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
