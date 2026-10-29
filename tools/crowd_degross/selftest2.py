"""Self-test for studies 2a to 2d: a world with all four effects planted in nine episode weeks must
be SUPPORTED (2d: SEES) on all four after Holm; a null world must support none; Holm must be exact
on a known vector."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crowd2  # noqa: E402

FAILS = []
adj = crowd2.holm([0.01, 0.04, 0.03, 0.5])
ok = np.allclose(adj, [0.04, 0.09, 0.09, 0.5])
print(("ok   " if ok else "FAIL ") + f"Holm {adj}")
if not ok:
    FAILS.append("holm")


def world(d, plant, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2016, 11, 14)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    qd = rng.normal(0.0006, 0.012, n)
    g = qd + rng.normal(0, 0.004, n)
    W = qd + rng.normal(0, 0.004, n)
    L = qd + rng.normal(0, 0.006, n)
    mom = rng.normal(0.0002, 0.006, n)
    fac = rng.normal(0, 0.005, (n, 5))
    fr = [dd for dd in days if dd.weekday() == 4 and dd.year >= 2021]
    epd = [fr[i] for i in sorted(rng.choice(len(fr), 9, replace=False))]
    ek = {e.isocalendar()[:2] for e in epd}
    for k, dd in enumerate(days):
        if dd.isocalendar()[:2] in ek:
            g[k] -= plant / 5
            L[k] += plant / 5
            mom[k] -= plant / 5
    lvl = lambda r: 100 * np.cumprod(1 + r)
    G, Q = lvl(g), lvl(qd)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "SPY", "QQQ", "RSP", "W", "L"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i], Q[i], Q[i], Q[i], W[i], L[i]])
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat()] + list(100 * fac[i]) + [0.01])
    with open(os.path.join(d, "mom_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mom"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), 100 * mom[i]])
    with open(os.path.join(d, "ndx.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["observation_date", "NASDAQ100"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), Q[i]])
    with open(os.path.join(d, "eps.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["episode_id", "class", "week_end"])
        for i, e in enumerate(epd):
            w.writerow([f"E{i:02d}", "D", e.isoformat()])
    subprocess.check_call([sys.executable, os.path.join(HERE, "crowd2.py"), "--bench", d, "--data-b", "bench",
                           "--ndx", os.path.join(d, "ndx.csv"), "--episodes", os.path.join(d, "eps.csv"), "--out", d],
                          stdout=subprocess.DEVNULL)
    return {k: v["verdict"] for k, v in json.load(open(os.path.join(d, "results_crowd2.json")))["holm"].items()}


for plant, seed, want in ((0.05, 1, {"2a": "SUPPORTED", "2b": "SUPPORTED", "2c": "SUPPORTED", "2d": "SEES"}),
                          (0.0, 2, {"2a": "NOT SUPPORTED", "2b": "NOT SUPPORTED", "2c": "NOT SUPPORTED", "2d": "DOES NOT SEE"}),
                          (0.0, 3, {"2a": "NOT SUPPORTED", "2b": "NOT SUPPORTED", "2c": "NOT SUPPORTED", "2d": "DOES NOT SEE"})):
    with tempfile.TemporaryDirectory() as d:
        v = world(d, plant, seed)
    ok = v == want
    print(("ok   " if ok else "FAIL ") + f"plant {plant:.0%}, seed {seed}: {v}")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
