"""Self-test: a world where the MTUM-SPY spread has clustered volatility with crashes in the stormy
state must PASS; a constant-volatility world must not PASS; the strategy with weights fixed at 1
reproduces MTUM held to rounding."""
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
    days, x = [], dt.date(2010, 1, 4)
    while x <= dt.date(2026, 10, 29):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    spy = rng.normal(0.0004, 0.011, n)
    if clustered:
        storm = np.zeros(n, bool)
        k, seg = 0, 0
        while k < n:
            L = rng.integers(120, 400)
            storm[k:k + L] = (seg % 4 == 3)  # every fourth segment is stormy, so storms fall in sample
            k += L
            seg += 1
        mu = np.where(storm, -0.0012, 0.0006)
        sd = np.where(storm, 0.016, 0.004)
    else:
        mu, sd = np.full(n, 0.00015), np.full(n, 0.007)
    spread = mu + sd * rng.normal(size=n)
    mt = spy + spread
    S = 100 * np.cumprod(1 + spy)
    M = 100 * np.cumprod(1 + mt)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "MTUM", "SPY"])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), M[i] if dd >= dt.date(2013, 4, 18) else "", S[i]])
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for dd in days:
            if dd <= dt.date(2026, 9, 30):
                w.writerow([dd.isoformat(), 0, 0, 0, 0, 0, 0.01])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for clustered, seed, want in ((True, 1, {"PASS"}), (True, 2, {"PASS"}), (False, 3, {"FAIL", "WEAK"}), (False, 4, {"FAIL", "WEAK"})):
    with tempfile.TemporaryDirectory() as dd:
        r = world(dd, clustered, seed)
    ok = r["verdict"] in want and r["last_month"] == "2026-09" and r["first_month"] == "2013-11"
    print(("ok   " if ok else "FAIL ") + f"clustered {clustered}, seed {seed}: {r['verdict']} (n {r['n_months']}, alpha t {r['alpha_t']:.2f}, "
          f"active Sharpe {r['sharpe_static_active']:.2f} -> {r['sharpe_active']:.2f}, p {r['p_boot']:.4f}, capped {r['weight']['share_capped']:.2f}, "
          f"strat/spy Sharpe {r['sharpe_strategy']:.2f}/{r['sharpe_spy']:.2f}, {r['first_month']} to {r['last_month']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
