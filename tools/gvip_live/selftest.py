"""Self-test for the GVIP test (PREREG section 4): the imported VIP regression self-test, and the
96-month threshold on a synthetic bench.csv."""
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
rc = subprocess.call([sys.executable, os.path.join(HERE, "..", "vip_premium", "selftest.py")])
fails = [] if rc == 0 else ["vip regression self-test"]


def synth(d, months, alpha):
    rng = np.random.default_rng(9)
    start = dt.date(2026, 9, 30) - dt.timedelta(days=int(months * 30.44) + 20)
    days, x = [], start
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    f = rng.normal(0.0003, 0.01, (n, 6))
    rfd = np.full(n, 0.0001)
    g = alpha / 252 + f @ np.array([1.1, 0.1, -0.2, 0.0, 0.0, 0.1]) + rfd + rng.normal(0, 0.004, n)
    lvl = lambda r: 100 * np.cumprod(1 + r)
    with open(os.path.join(d, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "SPY", "QQQ", "RSP"])
        G, S, Q, R = lvl(g), lvl(f[:, 0] + rfd), lvl(f[:, 0] * 1.2 + rfd), lvl(f[:, 0] + rfd)
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat(), G[i], S[i], Q[i], R[i]])
    with open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for i, dd in enumerate(days):
            if dd <= dt.date(2026, 9, 30):
                w.writerow([dd.isoformat()] + list(100 * f[i, :5]) + [100 * rfd[i]])
    with open(os.path.join(d, "mom_daily.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "Mom"])
        for i, dd in enumerate(days):
            if dd <= dt.date(2026, 9, 30):
                w.writerow([dd.isoformat(), 100 * f[i, 5]])


for months, alpha, want in ((110, 0.10, "PASS"), (80, 0.10, "INSUFFICIENT")):
    with tempfile.TemporaryDirectory() as d:
        synth(d, months, alpha)
        subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
        r = json.load(open(os.path.join(d, "results.json")))
        ok = r["verdict"] == want
        print(("ok   " if ok else "FAIL ") + f"{months} months, planted {alpha:.0%}: {r['verdict']} (n {r['n_months']}, t {r['t']:.2f})")
        if not ok:
            fails.append(f"{months} months")
if fails:
    print("SELFTEST FAILED:", fails)
    sys.exit(1)
print("SELFTEST PASSED")
