"""Synthetic data for test C2 (self-test and cross-check). Touches no real observation.
Usage: python synth_c2.py null|planted <seed> <outdir>"""
import csv
import datetime as dt
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import cal  # noqa: E402
from fetch_c2 import vx_expiry  # noqa: E402


def world(kind, seed, dd):
    rng = np.random.default_rng(seed)
    days = [d for d in (dt.date(2013, 1, 2) + dt.timedelta(days=i) for i in range(5050)) if cal.is_business_day(d)]
    N = len(days)
    lv = np.full(N, np.log(18.0))
    for t in range(1, N):
        lv[t] = np.log(18) + 0.97 * (lv[t - 1] - np.log(18)) + rng.normal(0, 0.06)
    V = np.exp(lv)
    exps = sorted(set(vx_expiry(y, m) for (y, m) in cal.months_between(days[0], days[-1] + dt.timedelta(days=120))))
    Bt = np.full(N, 8.0)
    for t in range(1, N):
        Bt[t] = 8 + 0.9 * (Bt[t - 1] - 8) + rng.normal(0, 2)
    rows = []
    B30 = np.zeros(N)
    for t, d in enumerate(days):
        fut = [x for x in exps if x > d]
        x1, x2 = fut[0], fut[1]
        t1, t2 = (x1 - d).days, (x2 - d).days
        f1 = V[t] * (1 + Bt[t] / 100 * t1 / 30)
        f2 = V[t] * (1 + Bt[t] / 100 * t2 / 30)
        w = min(max((t2 - 30) / (t2 - t1), 0), 1)
        F30 = w * f1 + (1 - w) * f2
        B30[t] = 100 * (F30 / V[t] - 1)
        for x, f in ((x1, f1), (x2, f2), (fut[2], V[t] * (1 + Bt[t] / 100 * (fut[2] - d).days / 30))):
            rows.append((d.isoformat(), x.isoformat(), float(f)))
    ret = rng.normal(-0.1, 3.5, N)
    if kind == "planted":
        for lag in range(1, 6):
            ret[lag:] += -0.08 * (B30[:-lag] - 8)
    on = rng.normal(0, 1, N)
    lC, lO = np.zeros(N), np.zeros(N)
    prev = np.log(100)
    for t in range(N):
        lO[t] = prev + on[t] / 100
        lC[t] = lO[t] + ret[t] / 100
        prev = lC[t]
    os.makedirs(dd, exist_ok=True)
    with open(os.path.join(dd, "vx.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "EXPIRY", "SETTLE"])
        for r in rows:
            w.writerow([r[0], r[1], repr(r[2])])
    with open(os.path.join(dd, "vix.csv"), "w") as fh:
        fh.write("DATE,CLOSE\n" + "".join(f"{d},{V[t]:.6f}\n" for t, d in enumerate(days)))
    with open(os.path.join(dd, "etp.csv"), "w") as fh:
        fh.write("DATE,OPEN,CLOSE,ADJCLOSE\n" + "".join(f"{d},{math.exp(lO[t]):.6f},{math.exp(lC[t]):.6f},{math.exp(lC[t]) * 0.5:.6f}\n"
                                                       for t, d in enumerate(days) if t % 97 != 5))


if __name__ == "__main__":
    world(sys.argv[1], int(sys.argv[2]), sys.argv[3])
