"""Frozen test: six-factor alpha of the live GVIP ETF (PREREG.md governs).

Regression code imported from tools/vip_premium/run.py (frozen). NON-EVIDENTIARY side test.

Usage: python run.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import run as vp  # noqa: E402

MIN_MONTHS = 96


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(a.data, "bench.csv"), newline="")))
    rows = [r for r in rows if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {s: np.array([float(r[s]) if r[s].strip() else np.nan for r in rows]) for s in ("GVIP", "SPY", "QQQ", "RSP")}
    n = len(days)
    series = {}
    for s, v in px.items():
        r = np.full(n, np.nan)
        r[1:] = v[1:] / v[:-1] - 1
        series["basket" if s == "GVIP" else s] = r
    ff = vp.read_daily(os.path.join(a.data, "ff5_daily.csv"), ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
    mom = vp.read_daily(os.path.join(a.data, "mom_daily.csv"), ["Mom"])
    for j, f in enumerate(["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]):
        series[f] = np.array([ff[d][j] / 100 if d in ff else np.nan for d in days])
    series["Mom"] = np.array([mom[d][0] / 100 if d in mom else np.nan for d in days])
    ok = np.ones(n, bool)
    for v in series.values():
        ok &= ~np.isnan(v)
    first_px = days[int(np.argmax(~np.isnan(px["GVIP"])))]
    start = (first_px.year + (first_px.month == 12), first_px.month % 12 + 1)
    last_factor = max(d for d in ff if d in mom)
    mon = {k: vp.monthly(days, np.nan_to_num(v), ok) for k, v in series.items()}
    keys = sorted(k for k in mon["basket"] if start <= k <= (last_factor.year, last_factor.month)
                  and all(mon[s][k] is not None for s in mon))
    ret = {k: np.array([mon[k][m] for m in keys]) for k in mon}
    rf = ret["RF"]
    x = ret["basket"] - rf
    F = np.column_stack([ret[f] for f in vp.FACTORS])
    res = vp.analyse(keys, x, F, ret, rf)
    # this test's minimum sample (PREREG section 3 item 2)
    if len(keys) < MIN_MONTHS:
        res["verdict"] = "INSUFFICIENT"
    elif res["t"] >= 2.0 and res["alpha_annual"] >= 0.02:
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
    h = len(keys) // 2
    res["halves"] = []
    for sl in (slice(0, h), slice(h, None)):
        sub = keys[sl]
        b, se = vp.ols(x[sl], F[sl])
        res["halves"].append({"first_month": f"{sub[0][0]}-{sub[0][1]:02d}", "last_month": f"{sub[-1][0]}-{sub[-1][1]:02d}",
                              "alpha_annual": float(12 * b[0]), "t": float(b[0] / se[0])})
    res["gvip_first_price"] = first_px.isoformat()
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
