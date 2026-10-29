"""Self-test for study 2e: persistence planted (AR(1) phi 0.3 in GVIP minus QQQ) is SUPPORTED and
absent persistence is not; a planted E-1 lag of 3% in ten new episodes is SUPPORTED; frozen-episode
weeks are excluded from 2e-ii."""
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


def world(d, phi, lag, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2016, 11, 14)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    q = rng.normal(0.0006, 0.012, n)
    keys = [dd.isocalendar()[:2] for dd in days]
    wk = sorted(set(keys))
    e = rng.normal(0, 0.012, len(wk))
    s = np.zeros(len(wk))
    for i in range(len(wk)):
        s[i] = (phi * s[i - 1] if i else 0) + e[i]
    fr = [dd for dd in days if dd.weekday() == 4 and dd.year >= 2019]
    pick = sorted(rng.choice(len(fr), 19, replace=False))
    frozen, new = [fr[i] for i in pick[:9]], [fr[i] for i in pick[9:]]
    wpos = {k: i for i, k in enumerate(wk)}
    for ne in new:
        s[wpos[ne.isocalendar()[:2]] - 1] -= lag
    daily = np.array([s[wpos[k]] / 5 for k in keys])
    g = q + daily
    lvl = lambda r: 100 * np.cumprod(1 + r)
    G, Q = lvl(g), lvl(q)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "SPY", "QQQ", "RSP", "W", "L"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i], Q[i], Q[i], Q[i], g[i], q[i]])
    for name, lst in (("frozen.csv", frozen), ("new.csv", new), ("other.csv", [])):
        with open(os.path.join(d, name), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["episode_id", "class", "week_end"])
            for i, ee in enumerate(lst):
                w.writerow([f"E{i:02d}", "D", ee.isoformat()])
    subprocess.check_call([sys.executable, os.path.join(HERE, "crowd2e.py"), "--bench", d, "--data-b", "bench",
                           "--episodes", os.path.join(d, "frozen.csv"), "--new", os.path.join(d, "new.csv"),
                           "--new-other", os.path.join(d, "other.csv"), "--out", d], stdout=subprocess.DEVNULL)
    r = json.load(open(os.path.join(d, "results_crowd2e.json")))
    return r["verdicts"]["2e-i"]["verdict"], r["verdicts"]["2e-ii"]["verdict"]


for phi, lag, seed, want in ((0.3, 0.03, 1, ("SUPPORTED", "SUPPORTED")),
                             (0.0, 0.0, 2, ("NOT SUPPORTED", "NOT SUPPORTED")),
                             (0.0, 0.0, 3, ("NOT SUPPORTED", "NOT SUPPORTED"))):
    with tempfile.TemporaryDirectory() as d:
        v = world(d, phi, lag, seed)
    ok = v == want
    print(("ok   " if ok else "FAIL ") + f"phi {phi}, lag {lag:.0%}, seed {seed}: {v}")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
