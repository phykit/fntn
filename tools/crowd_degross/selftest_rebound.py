"""Self-test for study R: a planted rebound (half the bad week's loss returned over the next 20
trading days) is SUPPORTED; no rebound is not."""
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


def world(d, k, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2013, 1, 2)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    q = rng.normal(0.0006, 0.012, n)
    e = rng.normal(0, 0.006, n)
    keys = [dd.isocalendar()[:2] for dd in days]
    for i in range(5, n - 25):
        if keys[i] != keys[i + 1]:  # last day of a week
            j = i
            while j > 0 and keys[j - 1] == keys[i]:
                j -= 1
            wk = e[j:i + 1].sum()
            if wk < -0.02:
                e[i + 2:i + 22] += -k * wk / 20
    g = q + e
    lvl = lambda r: 100 * np.cumprod(1 + r)
    G, Q = lvl(g), lvl(q)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "SPY", "QQQ", "RSP", "W", "L"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i], Q[i], Q[i], Q[i], g[i], q[i]])
    with open(os.path.join(d, "eps.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["episode_id", "class", "week_end"])
        w.writerow(["E01", "D", "2024-06-14"])
    subprocess.check_call([sys.executable, os.path.join(HERE, "rebound.py"), "--bench", d, "--data-b", "bench",
                           "--episodes", os.path.join(d, "eps.csv"), "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results_rebound.json")))


for k, seed, want in ((0.5, 1, "SUPPORTED"), (0.0, 2, "NOT SUPPORTED"), (0.0, 3, "NOT SUPPORTED")):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, k, seed)
    ok = r["verdict"] == want
    print(("ok   " if ok else "FAIL ") + f"rebound {k}, seed {seed}: {r['verdict']} (n {r['n_signal']}, mean {r['mean_signal']:+.4f} vs {r['mean_eligible']:+.4f}, p {r['p_upper']:.4f}; trades {r['trade_gvip']['trades']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
