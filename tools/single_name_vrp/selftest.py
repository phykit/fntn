"""Self-test of the single-name premium test (PREREG section 5.1). Exits non-zero on failure.

A planted idiosyncratic premium must be found in 8 of 8 synthetic worlds; with none planted (but
a systematic premium present, so that the split is exercised) it may be found in at most 4 of 40.
Plus hand checks of the Newey-West, Black-Scholes and 3-name rules."""
from __future__ import annotations

import datetime as dt
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
BETAS = [0.8, 1.0, 1.2, 1.4, 0.9]
S_M, S_E = 0.18, 0.25


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def world(seed: int, k: float, n: int = 4000):
    rng = np.random.default_rng(seed)
    d0 = dt.date(2010, 1, 4)
    dates = []
    d = d0
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += dt.timedelta(days=1)
    rm = rng.normal(0, S_M / math.sqrt(252), n)
    px = {"SPY": 100 * np.exp(np.cumsum(rm))}
    ivm2 = S_M ** 2 * 1.3
    vx = {"MKT": np.full(n, 100 * math.sqrt(ivm2))}
    for name, b in zip(run.NAMES, BETAS):
        ri = b * rm + rng.normal(0, S_E / math.sqrt(252), n)
        px[name] = 50 * np.exp(np.cumsum(ri))
        vx[name] = np.full(n, 100 * math.sqrt(b * b * ivm2 + S_E ** 2 * (1 + k)))
    return dates, px, vx


hits = sum(run.analyse(*world(100 + s, 0.3))["verdict"] == "SUPPORTED" for s in range(8))
check("planted idiosyncratic premium found", hits == 8, f"{hits} of 8")
hits0 = sum(run.analyse(*world(500 + s, 0.0))["verdict"] == "SUPPORTED" for s in range(40))
check("no planted premium: false positives", hits0 <= 4, f"{hits0} of 40")

rng = np.random.default_rng(3)
x = rng.normal(size=60)
m, se, _ = run.nw_t(x)
e = x - x.mean()
saved = run.NW_LAGS
run.NW_LAGS = 0
_, se0, _ = run.nw_t(x)
run.NW_LAGS = saved
check("Newey-West at 0 lags equals White", abs(se0 - math.sqrt((e * e).sum()) / 60) < 1e-15)

sig = 0.2 / math.sqrt(run.WIN / 252.0)
want = run.ncdf(0.1) - run.ncdf(-0.1)
check("ATM call hand value", abs(run.atm_call(sig) - want) < 1e-12, f"{run.atm_call(sig):.12f}")

dates, px, vx = world(7, 0.0)
base = run.analyse(dates, px, vx)["n_months"]
# Blank three names' implied volatility on one formation day: that month has 2 names and drops.
j = next(i for i, d in enumerate(dates) if d.startswith("2014-03"))
for name in ("AAPL", "AMZN", "GOOG"):
    vx[name] = vx[name].copy()
    vx[name][j] = float("nan")
check("month with 2 used names is dropped", run.analyse(dates, px, vx)["n_months"] == base - 1)

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
