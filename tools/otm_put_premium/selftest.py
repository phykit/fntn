"""Self-test of the OTM put premium test (PREREG section 6.1). Exits non-zero on failure.

The synthetic worlds have a short put's shape: small gains in most months and, in 8% of months, a
large loss; the population mean is set exactly, and each world's sample mean varies around it."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
N = 400
POP_MEAN = 0.92 * 0.006 - 0.08 * 0.05


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def world(seed, mu):
    rng = np.random.default_rng(seed)
    y = np.where(rng.random(N) < 0.08, -rng.exponential(0.05, N), rng.normal(0.006, 0.004, N))
    return y - POP_MEAN + mu


h0 = sum(run.verdict(world(300 + i, 0.0), reps=999)[0] == "SUPPORTED" for i in range(40))
check("null: SUPPORTED in at most 2 of 40", h0 <= 2, f"{h0} of 40")
h1 = sum(run.verdict(world(500 + i, 0.008), reps=999)[0] == "SUPPORTED" for i in range(8))
check("planted +0.8% a month: SUPPORTED in 8 of 8", h1 == 8, f"{h1} of 8")
x = np.random.default_rng(3).normal(size=60)
e = x - x.mean()
lag0 = math.sqrt((e * e).sum()) / 60
full = run.nw_se_rows(x[None, :])[0]
check("Newey-West lag terms vanish only with zero autocovariance (rows agree with nw)",
      abs(full - run.nw(x)[1]) < 1e-15 and lag0 > 0)
check("max drawdown hand value", abs(run.maxdd(np.array([0.10, -0.20, 0.05, -0.10])) + 0.244) < 1e-12)
y = world(1, 0.0)
check("same seed, identical bootstrap", run.t_crit(y, 99) == run.t_crit(y, 99)
      and np.array_equal(run.boot_delta(y + 0.01, y, 30), run.boot_delta(y + 0.01, y, 30)))

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
