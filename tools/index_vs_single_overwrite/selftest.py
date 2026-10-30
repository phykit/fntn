"""Self-test of the index against single-stock overwrite test (PREREG section 5.1).

Synthetic held returns and excesses are fed to run.delta and the verdict logic through a small
wrapper that bypasses extract; the bootstrap is the module's own."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
N = 187


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def verdict(L, b=500):
    n = L[0].size
    D = run.delta(L, np.arange(n))
    rng = np.random.default_rng(run.SEED)
    boots = []
    for _ in range(b):
        starts = rng.integers(0, n - run.BLOCK + 1, size=math.ceil(n / run.BLOCK))
        idx = np.concatenate([np.arange(s, s + run.BLOCK) for s in starts])[:n]
        boots.append(run.delta(L, idx))
    return "SUPPORTED" if D > 0 and np.percentile(boots, 5) > 0 else "NOT SUPPORTED", boots


def world(seed, mI, mB):
    """Index and basket held returns share one distribution, so with mI == mB the two legs are
    identically distributed and Delta has expectation zero (the PREREG's null)."""
    rng = np.random.default_rng(seed)
    hI = rng.normal(0.009, 0.045, N)
    hB = rng.normal(0.009, 0.045, N)
    # Excess negatively related to the held return, as a short call's is.
    yI = mI - 0.4 * np.maximum(hI, 0) + rng.normal(0, 0.01, N)
    yB = mB - 0.4 * np.maximum(hB, 0) + rng.normal(0, 0.01, N)
    return hI, yI, hI + yI, hB, yB, hB + yB


h0 = sum(verdict(world(3000 + s, 0.008, 0.008))[0] == "SUPPORTED" for s in range(40))
check("null: SUPPORTED in at most 4 of 40", h0 <= 4, f"{h0} of 40")
h1 = sum(verdict(world(4000 + s, 0.008 + 0.005, 0.008 - 0.005))[0] == "SUPPORTED" for s in range(8))
check("planted: SUPPORTED in 8 of 8", h1 == 8, f"{h1} of 8")
check("Sh([1, 2, 3]) = 2", abs(run.sh(np.array([1.0, 2.0, 3.0])) - 2.0) < 1e-15)
_, b1 = verdict(world(9, 0.0, 0.0), b=40)
_, b2 = verdict(world(9, 0.0, 0.0), b=40)
check("same seed, identical Delta*", b1 == b2)

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
