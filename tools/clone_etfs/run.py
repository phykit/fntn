"""Follow-up study 4 (PREREG.md governs): six-factor alpha of 13F-copycat ETFs and their
equal-weighted composite, by the frozen analyse() and ols() of tools/vip_premium/run.py.

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

FUNDS = ("GURU", "ACTX", "GURI", "ALFA", "ALFI", "IBLN")
MIN_FUND_MONTHS = 36
MIN_COMPOSITE_MONTHS = 60
FCOLS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]


def month_returns(data):
    rows = [r for r in csv.DictReader(open(os.path.join(data, "funds.csv"), newline="")) if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    n = len(days)
    ff = vp.read_daily(os.path.join(data, "ff5_daily.csv"), FCOLS)
    mom = vp.read_daily(os.path.join(data, "mom_daily.csv"), ["Mom"])
    last_factor = max(d for d in ff if d in mom)
    fac = {f: np.array([ff[d][j] / 100 if d in ff else np.nan for d in days]) for j, f in enumerate(FCOLS)}
    fac["Mom"] = np.array([mom[d][0] / 100 if d in mom else np.nan for d in days])
    fok = np.ones(n, bool)
    for v in fac.values():
        fok &= ~np.isnan(v)
    mon = {}
    for k, v in fac.items():
        mon[k] = vp.monthly(days, np.nan_to_num(v), fok)
    for s in FUNDS + ("GVIP", "SPY", "QQQ", "RSP"):
        p = np.array([float(r[s]) if r[s].strip() else np.nan for r in rows])
        r = np.full(n, np.nan)
        r[1:] = p[1:] / p[:-1] - 1
        ok = fok & ~np.isnan(r)
        mon[s] = vp.monthly(days, np.nan_to_num(r), ok)
    # the last factor month must be full
    last_spy = max(d for d in days if (d.year, d.month) == (last_factor.year, last_factor.month))
    end = (last_factor.year, last_factor.month)
    if last_factor < last_spy:
        end = (last_factor.year - (last_factor.month == 1), (last_factor.month - 2) % 12 + 1)
    return mon, end


def run_one(mon, keys, x_by_month):
    ret = {k: np.array([mon[k][m] for m in keys]) for k in ("SPY", "QQQ", "RSP", "RF")}
    ret["basket"] = np.array([x_by_month[m] for m in keys])
    rf = ret["RF"]
    F = np.column_stack([np.array([mon[f][m] for m in keys]) for f in vp.FACTORS])
    res = vp.analyse(keys, ret["basket"] - rf, F, ret, rf)
    res.pop("verdict", None)  # analyse()'s 120-month rule is the VIP test's, not this one's
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    mon, end = month_returns(a.data)
    base = ["SPY", "QQQ", "RSP", "RF"] + vp.FACTORS

    def base_ok(m):
        return m <= end and all(mon[k].get(m) is not None for k in base)

    res = {"factor_end": f"{end[0]}-{end[1]:02d}", "funds": {}, "admitted": []}
    live = {}
    for s in FUNDS + ("GVIP",):
        keys = sorted(m for m, v in mon[s].items() if v is not None and base_ok(m))
        res["funds"][s] = {"months": len(keys)}
        if len(keys) < MIN_FUND_MONTHS:
            res["funds"][s]["admitted"] = False
            print(f"{s}: {len(keys)} complete months, not admitted")
            continue
        res["funds"][s]["admitted"] = True
        res["funds"][s].update(run_one(mon, keys, mon[s]))
        live[s] = {m: mon[s][m] for m in keys}
        r = res["funds"][s]
        print(f"{s}: {len(keys)} months {r['first_month']} to {r['last_month']}, alpha {r['alpha_annual']:+.4f} (t {r['t']:.2f}), "
              f"vs QQQ {r['excess_vs']['QQQ']['annual']:+.4f}, vs SPY {r['excess_vs']['SPY']['annual']:+.4f}")
    res["admitted"] = [s for s in FUNDS if s in live]

    def composite(members):
        months = sorted({m for s in members for m in live[s]})
        return months, {m: float(np.mean([live[s][m] for s in members if m in live[s]])) for m in months}

    if len(res["admitted"]) < 2:
        res["composite"] = {"n_funds": len(res["admitted"])}
        res["verdict"] = "INSUFFICIENT"
    else:
        keys, cx = composite(res["admitted"])
        c = run_one(mon, keys, cx)
        c["n_funds"] = len(res["admitted"])
        res["composite"] = c
        if len(keys) < MIN_COMPOSITE_MONTHS:
            res["verdict"] = "INSUFFICIENT"
        elif c["t"] >= 2.0 and c["alpha_annual"] >= 0.02:
            res["verdict"] = "PASS"
        else:
            res["verdict"] = "FAIL"
        print(f"composite of {c['n_funds']}: {c['n_months']} months, alpha {c['alpha_annual']:+.4f} (t {c['t']:.2f}), "
              f"vs QQQ {c['excess_vs']['QQQ']['annual']:+.4f} (t {c['excess_vs']['QQQ']['t']:.2f})")
    if "GVIP" in live and res["admitted"]:
        keys, cx = composite(res["admitted"] + ["GVIP"])
        res["composite_with_gvip"] = run_one(mon, keys, cx)
    print("admitted:", res["admitted"])
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
