"""Self-test: a planted negative relation between the detrended short interest index and next
month's NDX excess return must PASS; no relation must not PASS; a short sample is INSUFFICIENT; the
parser reads YYYYMM, YYYY-MM and M/D/YYYY months."""
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


def world(d, beta, seed, months=600, fmt="yyyymm"):
    rng = np.random.default_rng(seed)
    y0, m0 = 1973, 1
    keys = []
    y, m = y0, m0
    for _ in range(months):
        keys.append((y, m))
        y, m = y + (m == 12), m % 12 + 1
    e = np.zeros(months)
    for i in range(1, months):
        e[i] = 0.9 * e[i - 1] + rng.normal(0, 0.1)
    sii = 0.002 * np.arange(months) + e          # trend plus persistent cycle
    rets = np.zeros(months)
    for i in range(months - 1):
        rets[i + 1] = 0.008 + beta * e[i] + rng.normal(0, 0.06)
    with open(os.path.join(d, "sii.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Month", "SII"])
        for k, v in zip(keys, sii):
            lab = {"yyyymm": f"{k[0]}{k[1]:02d}", "iso": f"{k[0]}-{k[1]:02d}", "us": f"{k[1]}/1/{k[0]}"}[fmt]
            w.writerow([lab, v])
    # NDX from 1986 only, daily rows, month-end level consistent with rets
    lvl = 100.0
    with open(os.path.join(d, "ndx.csv"), "w", newline="") as fh, open(os.path.join(d, "ff5_daily.csv"), "w", newline="") as fr:
        w = csv.writer(fh); w.writerow(["observation_date", "NASDAQ100"])
        wr = csv.writer(fr); wr.writerow(["DATE", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
        for k, r in zip(keys, rets):
            if k < (1985, 10):
                continue
            lvl *= np.exp(r)
            last = dt.date(k[0] + (k[1] == 12), k[1] % 12 + 1, 1) - dt.timedelta(days=1)
            w.writerow([last.isoformat(), lvl])
            wr.writerow([last.isoformat(), 0, 0, 0, 0, 0, 0.01])
    subprocess.check_call([sys.executable, os.path.join(HERE, "run.py"), "--data", d, "--out", d], stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(d, "results.json")))


for beta, seed, months, fmt, want in ((-0.10, 1, 600, "yyyymm", {"PASS"}), (-0.10, 2, 600, "iso", {"PASS"}),
                                      (0.0, 3, 600, "us", {"FAIL", "WEAK"}), (0.0, 4, 600, "yyyymm", {"FAIL", "WEAK"}),
                                      (-0.06, 5, 300, "yyyymm", {"INSUFFICIENT"})):
    with tempfile.TemporaryDirectory() as d:
        r = world(d, beta, seed, months, fmt)
    ok = r["verdict"] in want
    print(("ok   " if ok else "FAIL ") + f"beta {beta}, seed {seed}, {months} SII months, {fmt}: {r['verdict']} (n {r['n']}, "
          f"b/sd {r.get('b_per_sd', float('nan')):+.4f}, p {r.get('p_shift', float('nan')):.4f}, R2oos {r.get('r2_oos', float('nan')):+.4f}, CW {r.get('clark_west_t', float('nan')):.2f})")
    if not ok:
        FAILS.append(seed)
if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
