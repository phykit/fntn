"""Self-test: a planted announcement-day premium must PASS; none must FAIL; fewer than 60 OOS
announcements must be INSUFFICIENT."""
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


def world(d, plant, seed, ann_per_year=8):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(1990, 1, 2)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    # announcement days: ann_per_year per year from 1994, roughly every 252/ann_per_year days
    anns = []
    for y in range(1994, 2027):
        yd = [dd for dd in days if dd.year == y]
        step = max(1, len(yd) // ann_per_year)
        anns += [yd[i] for i in range(step // 2, len(yd), step)][:ann_per_year]
    aset = set(anns)
    r = rng.normal(0.0004, 0.013, n) + np.array([plant if dd in aset else 0.0 for dd in days])
    lvl = 100 * np.cumprod(1 + r)
    with open(os.path.join(d, "ndx.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["observation_date", "NASDAQ100"])
        for dd, v in zip(days, lvl):
            w.writerow([dd.isoformat(), v])
    with open(os.path.join(d, "qqq.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["DATE", "QQQ"])
        for dd, v in zip(days, lvl):
            if dd >= dt.date(1999, 3, 10):
                w.writerow([dd.isoformat(), v])
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for dd in days:
            w.writerow([dd.isoformat(), 0, 0, 0, 0, 0, 0.01])
    with open(os.path.join(d, "dates.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["year", "meeting_start", "meeting_end", "announcement_day", "source_url"])
        for ad in anns:
            w.writerow([ad.year, (ad - dt.timedelta(days=1)).isoformat(), ad.isoformat(), ad.isoformat(), "synthetic"])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--dates", os.path.join(d, "dates.csv"), "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for plant, seed, apy, want in ((0.006, 1, 8, "PASS"), (0.006, 2, 8, "PASS"), (0.0, 3, 8, "FAIL"), (0.0, 4, 8, "FAIL"), (0.006, 5, 4, "INSUFFICIENT")):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, plant, seed, apy)
    ok = r["verdict"] == want
    print(("ok   " if ok else "FAIL ") + f"plant {plant}, seed {seed}, {apy}/yr: {r['verdict']} (ann {r['n_oos_announcements']}, d {1e4*r['d_oos']:+.1f} bp, p {r['p_shift_oos']:.4f}, t {r['nw_t_oos']:.2f}, strat {r['strategy']['ann_return']:.3f})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS); sys.exit(1)
print("SELFTEST PASSED")
