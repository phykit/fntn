"""Self-test: a planted winter premium must PASS; none must FAIL."""
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


def world(d, plant, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(1985, 10, 1)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    r = np.array([rng.normal(0.0003 + (plant / 21 if dd.month in (11, 12, 1, 2, 3, 4) else 0.0), 0.012) for dd in days])
    lvl = 100 * np.cumprod(1 + r)
    with open(os.path.join(d, "ndx.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["observation_date", "NASDAQ100"])
        for dd, v in zip(days, lvl):
            w.writerow([dd.isoformat(), v])
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for dd in days:
            if dd <= dt.date(2026, 9, 30):
                w.writerow([dd.isoformat(), 0, 0, 0, 0, 0, 0.01])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


null_pass = 0
for plant, seed, want in ((0.012, 1, "PASS"), (0.012, 2, "PASS")) + tuple((0.0, s, "FAIL") for s in range(3, 9)):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, plant, seed)
    ok = r["last_oos"] == "2026-09" and r["first_oos"] == "2003-01" and (r["verdict"] == want if plant else True)
    if not plant and r["verdict"] == "PASS":
        null_pass += 1
    print(("ok   " if ok else "FAIL ") + f"plant {plant}, seed {seed}: {r['verdict']} (n {r['n_oos']}, c {r['c']:+.4f} t {r['c_t']:.2f}; pairs {r['n_winter_summer_pairs']}, {r['first_oos']} to {r['last_oos']})")
    if not ok:
        FAILS.append(seed)
print(f"null worlds passing: {null_pass} of 6 (at most 1 allowed: the one-sided t >= 2 rule passes about 2% of nulls)")
if null_pass > 1:
    FAILS.append("null-rate")
if FAILS:
    print("SELFTEST FAILED:", FAILS); sys.exit(1)
print("SELFTEST PASSED")
