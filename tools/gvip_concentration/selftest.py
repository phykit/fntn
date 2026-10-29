"""Self-test: GVIP - QQQ = 1.0 x (QQQE - QQQ) + noise gives CONCENTRATION EXPLAINS; an independent
-0.5% a month shortfall gives RESIDUAL SHORTFALL; a start before 2016-12 is excluded."""
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
FAILS = []


def world(d, mode, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2012, 3, 21)
    while x <= dt.date(2026, 10, 29):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    q = rng.normal(0.0007, 0.012, n)
    conc = rng.normal(0.0002, 0.004, n)          # QQQ minus equal-weight: concentration premium
    e = q - conc
    spy = q * 0.8 + rng.normal(0, 0.003, n)
    rsp = spy - conc * 0.6 + rng.normal(0, 0.002, n)
    if mode == "conc":
        g = e + rng.normal(0, 0.003, n)          # GVIP tracks equal-weight
    else:
        g = q - 0.005 / 21 + rng.normal(0, 0.003, n)  # GVIP = QQQ less a steady shortfall
    lvl = lambda r: 100 * np.cumprod(1 + r)
    G, Q, E, R, S = lvl(g), lvl(q), lvl(e), lvl(rsp), lvl(spy)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "QQQ", "QQQE", "RSP", "SPY"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i] if dd >= dt.date(2016, 11, 11) else "", Q[i], E[i], R[i], S[i]])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for mode, seed, want in (("conc", 1, "CONCENTRATION EXPLAINS"), ("conc", 2, "CONCENTRATION EXPLAINS"),
                         ("short", 3, "RESIDUAL SHORTFALL"), ("short", 4, "RESIDUAL SHORTFALL")):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, mode, seed)
    ok = r["verdict"] == want and r["first_month"] == "2016-12" and r["last_month"] == "2026-09"
    print(("ok   " if ok else "FAIL ") + f"{mode}, seed {seed}: {r['verdict']} (n {r['n_months']}, a t {r['a_t']:.2f}, b {r['b']:.2f} t {r['b_t']:.2f}, {r['first_month']} to {r['last_month']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
