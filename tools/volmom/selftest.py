"""Self-test: a momentum world with volatility clustering and crashes in high-volatility months
must PASS out of sample; a constant-volatility world must not PASS; the bootstrap and the complete-
month rule are exercised on the way."""
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


def world(d, clustered, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(1990, 1, 2)
    while x <= dt.date(2026, 9, 30):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    if clustered:
        # regime volatility: calm 0.6%/day with +0.05% drift; stormy 2.5%/day with -0.3% drift
        storm = np.zeros(n, bool)
        k = 0
        while k < n:
            L = rng.integers(120, 400)
            storm[k:k + L] = rng.random() < 0.15
            k += L
        mu = np.where(storm, -0.003, 0.0005)
        sd = np.where(storm, 0.025, 0.006)
    else:
        mu, sd = np.full(n, 0.0004), np.full(n, 0.012)
    r = mu + sd * rng.normal(size=n)
    with open(os.path.join(d, "mom_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mom"])
        for dd, v in zip(days, r):
            w.writerow([dd.isoformat(), 100 * v])
    spy = 100 * np.cumprod(1 + rng.normal(0.0004, 0.01, n))
    mt = spy * np.cumprod(1 + r * 0.5)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "MTUM", "SPY"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), mt[i] if dd >= dt.date(2013, 4, 18) else "", spy[i]])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for clustered, seed, want in ((True, 1, {"PASS"}), (True, 2, {"PASS"}), (False, 3, {"FAIL", "WEAK"}), (False, 4, {"FAIL", "WEAK"})):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, clustered, seed)
    ok = r["verdict"] in want and r["n_oos"] == 129 and r["oos_last"] == "2026-09"
    print(("ok   " if ok else "FAIL ") + f"clustered {clustered}, seed {seed}: {r['verdict']} (n_oos {r['n_oos']}, alpha t {r.get('oos_alpha_t', float('nan')):.2f}, "
          f"Sharpe {r.get('oos_sharpe_raw', float('nan')):.2f} -> {r.get('oos_sharpe_managed', float('nan')):.2f}, p {r.get('p_boot', float('nan')):.4f}; mtum {r['mtum']['verdict']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
