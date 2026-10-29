"""Self-test for follow-up study 4: planted 10% alpha in the composite PASSES, a null composite
FAILS, one admitted fund is INSUFFICIENT, and a fund with under 36 months is not admitted."""
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
FUNDS = ("GURU", "ACTX", "GURI", "ALFA", "ALFI", "IBLN")
FAILS = []


def world(d, alpha, spans, seed):
    rng = np.random.default_rng(seed)
    days, x = [], dt.date(2012, 1, 2)
    while x <= dt.date(2026, 10, 28):
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    n = len(days)
    f = rng.normal(0.0003, 0.01, (n, 6))
    rfd = np.full(n, 0.0001)
    lvl = lambda r: 100 * np.cumprod(1 + r)
    cols = {"SPY": lvl(f[:, 0] + rfd), "QQQ": lvl(1.2 * f[:, 0] + rfd), "RSP": lvl(f[:, 0] + rfd)}
    cols["GVIP"] = lvl(f @ np.array([1.1, 0.1, -0.2, 0, 0, 0.1]) + rfd + rng.normal(0, 0.004, n))
    for s in FUNDS:
        cols[s] = np.full(n, np.nan)
    for s, (y0, y1) in spans.items():
        m = np.array([dt.date(y0, 1, 1) <= dd <= dt.date(y1, 12, 31) for dd in days])
        r = alpha / 252 + f @ np.array([1.0, 0.2, 0.1, 0, 0, 0.0]) + rfd + rng.normal(0, 0.004, n)
        p = lvl(r)
        cols[s] = np.where(m, p, np.nan)
    with open(os.path.join(d, "funds.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        order = FUNDS + ("GVIP", "SPY", "QQQ", "RSP")
        w.writerow(["DATE", *order])
        for i, dd in enumerate(days):
            w.writerow([dd.isoformat()] + ["" if np.isnan(cols[s][i]) else cols[s][i] for s in order])
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
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


cases = [(0.10, {"GURU": (2013, 2026), "ALFA": (2015, 2020)}, 1, "PASS"),
         (0.0, {"GURU": (2013, 2026), "ALFA": (2015, 2020)}, 2, "FAIL"),
         (0.10, {"GURU": (2013, 2026), "IBLN": (2016, 2017)}, 3, "INSUFFICIENT")]
for alpha, spans, seed, want in cases:
    with tempfile.TemporaryDirectory() as d:
        r = world(d, alpha, spans, seed)
    ok = r["verdict"] == want
    if seed == 3:
        ok = ok and r["funds"]["IBLN"]["admitted"] is False
    print(("ok   " if ok else "FAIL ") + f"alpha {alpha:.0%}, {list(spans)}: {r['verdict']} (admitted {r['admitted']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
