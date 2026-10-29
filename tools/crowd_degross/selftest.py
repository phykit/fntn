"""Self-test for follow-up study 2: a planted underperformance of 3% in nine episode weeks must be
SUPPORTED, a null world must not, and fewer than 8 episodes must be INSUFFICIENT."""
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


def world(d, plant, n_eps, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2017, 1, 2)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    q = rng.normal(0.0006, 0.012, n)
    s = 0.8 * q + rng.normal(0, 0.004, n)
    g = q + rng.normal(0, 0.006, n)
    fridays = [dd for dd in days if dd.weekday() == 4 and dd.year >= 2018]
    eps = sorted(rng.choice(len(fridays), size=n_eps, replace=False))
    epd = [fridays[i] for i in eps]
    for e in epd:
        for k, dd in enumerate(days):
            if dd.isocalendar()[:2] == e.isocalendar()[:2]:
                g[k] -= plant / 5
    lvl = lambda r: 100 * np.cumprod(1 + r)
    G, S, Q = lvl(g), lvl(s), lvl(q)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "SPY", "QQQ", "RSP"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i], S[i], Q[i], S[i]])
    with open(os.path.join(d, "eps.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["episode_id", "class", "week_end"])
        for i, e in enumerate(epd):
            w.writerow([f"E{i:02d}", "D", e.isoformat()])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--bench", d, "--data-b", "none",
                           "--episodes", os.path.join(d, "eps.csv"), "--out", d, "--tag", "t"], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results_t.json")))["verdict_H_crowd"]


for plant, n_eps, seed, want in ((0.03, 9, 1, {"SUPPORTED"}), (0.03, 9, 2, {"SUPPORTED"}),
                                 (0.0, 9, 3, {"NOT SUPPORTED"}), (0.0, 9, 4, {"NOT SUPPORTED"}),
                                 (0.03, 6, 5, {"INSUFFICIENT"})):
    with tempfile.TemporaryDirectory() as d:
        v = world(d, plant, n_eps, seed)
    ok = v in want
    print(("ok   " if ok else "FAIL ") + f"plant {plant:.0%}, {n_eps} episodes, seed {seed}: {v}")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
