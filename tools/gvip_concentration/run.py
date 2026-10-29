"""Frozen test (PREREG.md governs): is GVIP's shortfall against QQQ a concentration exposure?
Monthly GVIP - QQQ regressed on QQQE - QQQ, Newey-West L = 3.

Input: --data DIR with bench.csv (DATE,GVIP,QQQ,QQQE,RSP,SPY adjusted closes on SPY days).
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
import run as vp  # noqa: E402  frozen ols() with Newey-West L = 3
import importlib.util  # noqa: E402  volmom's run.py by path: "run" is already the VIP module

_spec = importlib.util.spec_from_file_location("run_volmom", os.path.join(HERE, "..", "volmom", "run.py"))
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
complete_months = _vm.complete_months

TICK = ("GVIP", "QQQ", "QQQE", "RSP", "SPY")
START = (2016, 12)
MIN_MONTHS = 96


def monthly(days, ret):
    keys = [(d.year, d.month) for d in days]
    out = {}
    i, n = 0, len(days)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        seg = {k: v[i:j + 1] for k, v in ret.items()}
        if all(not np.isnan(s).any() for s in seg.values()):
            out[keys[i]] = {k: float(np.prod(1 + s) - 1) for k, s in seg.items()}
        i = j + 1
    return out


def reg(y, x):
    b, se = vp.ols(y, x[:, None])
    X = np.column_stack([np.ones(len(y)), x])
    e = y - X @ b
    r2 = 1 - float(e @ e) / float(((y - y.mean()) ** 2).sum())
    return {"a_monthly": float(b[0]), "a_t": float(b[0] / se[0]), "b": float(b[1]), "b_t": float(b[1] / se[1]), "r2": r2}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    rows = [r for r in csv.DictReader(open(os.path.join(a.data, "bench.csv"), newline="")) if r["SPY"].strip()]
    days = [dt.date.fromisoformat(r["DATE"]) for r in rows]
    px = {k: np.array([float(r[k]) if r[k].strip() else np.nan for r in rows]) for k in TICK}
    ret = {}
    for k, v in px.items():
        x = np.full(len(days), np.nan)
        x[1:] = v[1:] / v[:-1] - 1
        ret[k] = x
    mon = monthly(days, ret)
    keys = [k for k in complete_months(days) if k in mon and k >= START]
    n = len(keys)
    g = np.array([mon[k]["GVIP"] for k in keys])
    q = np.array([mon[k]["QQQ"] for k in keys])
    e = np.array([mon[k]["QQQE"] for k in keys])
    rsp = np.array([mon[k]["RSP"] for k in keys])
    spy = np.array([mon[k]["SPY"] for k in keys])
    y, x = g - q, e - q
    res = {"n_months": n, "first_month": f"{keys[0][0]}-{keys[0][1]:02d}", "last_month": f"{keys[-1][0]}-{keys[-1][1]:02d}"}
    res.update(reg(y, x))
    if n < MIN_MONTHS:
        v = "INSUFFICIENT"
    elif res["a_t"] <= -2.0:
        v = "RESIDUAL SHORTFALL"
    elif res["b"] >= 0.5 and res["b_t"] >= 2.0 and res["a_t"] > -2.0:
        v = "CONCENTRATION EXPLAINS"
    else:
        v = "INDETERMINATE"
    res["verdict"] = v
    d = g - e
    bb, ss = vp.ols(d, None)
    res["gvip_minus_qqqe_annual"], res["gvip_minus_qqqe_t"] = float(12 * bb[0]), float(bb[0] / ss[0])
    res["rsp"] = reg(y, rsp - spy)
    h = n // 2
    res["halves"] = []
    for sl in (slice(0, h), slice(h, None)):
        sub = keys[sl]
        r = reg(y[sl], x[sl])
        res["halves"].append({"first_month": f"{sub[0][0]}-{sub[0][1]:02d}", "last_month": f"{sub[-1][0]}-{sub[-1][1]:02d}",
                              "a_monthly": r["a_monthly"], "a_t": r["a_t"], "b": r["b"], "b_t": r["b_t"]})
    print(json.dumps(res, indent=1))
    print("VERDICT:", v)
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
