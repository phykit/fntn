"""Self-test: 200 synthetic tickers, half quarterly payers; a planted premium in predicted months must
PASS; none must FAIL."""
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
    days, x = [], dt.date(1999, 1, 4)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    T = 200
    tick = [f"T{i:02d}" for i in range(T)]
    payer = np.array([i % 2 == 0 for i in range(T)])
    phase = rng.integers(0, 3, T)  # pay in months phase, phase+3, ...
    ex = []
    for j in range(T):
        if payer[j]:
            for y in range(1999, 2027):
                for q in range(4):
                    m = phase[j] + 1 + 3 * q
                    ex.append((tick[j], dt.date(y, m, 15).isoformat(), 0.5))
    exset = {(t, dt.date.fromisoformat(e).year, dt.date.fromisoformat(e).month) for t, e, _ in ex}
    px = np.zeros((n, T))
    lvl = np.full(T, 100.0)
    mkt = rng.normal(0.0003, 0.01, n)
    for i, dd in enumerate(days):
        bump = np.array([plant / 21 if (tick[j], dd.year, dd.month) in exset else 0.0 for j in range(T)])
        lvl *= 1 + mkt[i] + rng.normal(0, 0.012, T) + bump
        px[i] = lvl
    with open(os.path.join(d, "prices.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["DATE"] + tick)
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat()] + ["" if (j % 7 == 0 and dd < dt.date(2004, 1, 1)) else px[i, j] for j in range(T)])
    with open(os.path.join(d, "dividends.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["ticker", "ex_date", "amount"]); w.writerows(ex)
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for dd in days:
            if dd <= dt.date(2026, 9, 30):
                w.writerow([dd.isoformat(), 0, 0, 0, 0, 0, 0.01])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for plant, seed, want in ((0.01, 1, "PASS"), (0.01, 2, "PASS"), (0.0, 3, "FAIL"), (0.0, 4, "FAIL")):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, plant, seed)
    ok = r["verdict"] == want and r["first_oos"] == "2010-01" and r["last_oos"] == "2026-09"
    print(("ok   " if ok else "FAIL ") + f"plant {plant}, seed {seed}: {r['verdict']} (n {r['n_oos']}, D {1e4*r['mean_D']:+.1f} bp t {r['t_D']:.2f}, S t {r['t_S']:.2f}; P {r['counts']['mean_P']:.0f} of {r['counts']['mean_U']:.0f}; turnover {r['strategy']['mean_turnover']:.2f})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS); sys.exit(1)
print("SELFTEST PASSED")
