"""Self-test: a world where a persistent credit factor leads QQQ must PASS; a world with no lead must
not; the rule must exit at least once in a planted credit slump."""
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


def world(d, lead, seed):
    rng = np.random.default_rng(seed)
    n = 4800
    z = np.zeros(n)
    for t in range(1, n):
        z[t] = 0.995 * z[t - 1] + rng.normal(0, 0.1)
    c = 0.0004 * z + rng.normal(0, 0.003, n)
    q = 0.0004 + lead * 0.0008 * np.concatenate([[0, 0], z[:-2]]) + rng.normal(0, 0.012, n)
    i = rng.normal(0.0001, 0.004, n)
    h = i + c
    days, x = [], dt.date(2007, 4, 11)
    while len(days) < n:
        if x.weekday() < 5:
            days.append(x)
        x += dt.timedelta(days=1)
    lv = lambda r: 100 * np.exp(np.cumsum(r))
    H, I, Q = lv(h), lv(i), lv(q)
    with open(os.path.join(d, "prices.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "HYG", "IEF", "QQQ"])
        for k in range(n):
            w.writerow([days[k].isoformat(), H[k], I[k], Q[k]])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for lead, seed, want in ((1.0, 1, {"PASS"}), (0.0, 2, {"FAIL", "WEAK"}), (0.0, 3, {"FAIL", "WEAK"})):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, lead, seed)
    ok = r["verdict"] in want and (lead == 0 or r["rule"]["exits"] >= 1)
    print(("ok   " if ok else "FAIL ") + f"lead {lead}, seed {seed}: {r['verdict']} (b {r['b']:.4f}, p {r['p_shift']:.4f}, exits {r['rule']['exits']})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
