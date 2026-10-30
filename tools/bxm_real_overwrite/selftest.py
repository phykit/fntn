"""Self-test of the BXM real-price test (PREREG section 6.1). Exits non-zero on failure."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
N = 290


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def verdict(b, s, reps=500):
    D = run.delta(b, s, np.arange(N))
    boots, _ = run.bootstrap(b, s, N, reps)
    return "SUPPORTED" if D > 0 and np.percentile(boots, run.PCT) > 0 else "NOT SUPPORTED"


def world(seed, sharpe_gap):
    """Two correlated monthly series (correlation 0.9) with Sharpe ratios 0.20 and 0.20 + gap."""
    rng = np.random.default_rng(seed)
    z1 = rng.normal(size=N)
    z2 = 0.9 * z1 + np.sqrt(1 - 0.81) * rng.normal(size=N)
    s = 0.009 + 0.045 * z1
    b = 0.03 * (0.20 + sharpe_gap) + 0.03 * z2
    return b, s


h0 = sum(verdict(*world(7000 + i, 0.0)) == "SUPPORTED" for i in range(40))
check("null: SUPPORTED in at most 2 of 40", h0 <= 2, f"{h0} of 40")
h1 = sum(verdict(*world(8000 + i, 0.15)) == "SUPPORTED" for i in range(8))
check("planted: SUPPORTED in 8 of 8", h1 == 8, f"{h1} of 8")
check("Sh([1, 2, 3]) = 2", abs(run.sh(np.array([1.0, 2.0, 3.0])) - 2.0) < 1e-15)
check("max drawdown hand value", abs(run.maxdd(np.array([0.10, -0.20, 0.05, -0.10])) + 0.244) < 1e-12)
b, s = world(1, 0.0)
b1, _ = run.bootstrap(b, s, N, 40)
b2, _ = run.bootstrap(b, s, N, 40)
check("same seed, identical Delta*", np.array_equal(b1, b2))

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
