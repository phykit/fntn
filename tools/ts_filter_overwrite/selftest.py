"""Self-test of the term-structure filter test (PREREG section 6.1). Exits non-zero on failure."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
N = 204


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def verdict(h, y, W, b=500):
    kA, kF = h + y, h + W * y
    D = run.delta(kF, kA, np.arange(N))
    boots, _ = run.bootstrap(kF, kA, N, b)
    rs = run.random_skip(h, y, kA, int((~W).sum()), r=b)
    ok = D > 0 and np.percentile(boots, run.PCT) > 0 and D > np.percentile(rs, 99)
    return "SUPPORTED" if ok else "NOT SUPPORTED"


def world(seed, m_con, m_back):
    rng = np.random.default_rng(seed)
    h = rng.normal(0.009, 0.045, N)
    W = rng.random(N) >= 0.15
    y = np.where(W, m_con, m_back) - 0.4 * np.maximum(h, 0) + rng.normal(0, 0.01, N)
    return h, y, W


h0 = sum(verdict(*world(5000 + s, 0.003, 0.003)) == "SUPPORTED" for s in range(40))
check("null: SUPPORTED in at most 2 of 40", h0 <= 2, f"{h0} of 40")
h1 = sum(verdict(*world(6000 + s, 0.003, -0.03)) == "SUPPORTED" for s in range(8))
check("planted: SUPPORTED in 8 of 8", h1 == 8, f"{h1} of 8")
check("Sh([1, 2, 3]) = 2", abs(run.sh(np.array([1.0, 2.0, 3.0])) - 2.0) < 1e-15)
s = 0.2 / math.sqrt(run.WIN / 252.0)
check("ATM premium hand value", abs(run.atm_call(s) - (run.ncdf(0.1) - run.ncdf(-0.1))) < 1e-12)
h, y, W = world(11, 0.0, 0.0)
b1, _ = run.bootstrap(h + W * y, h + y, N, 40)
b2, _ = run.bootstrap(h + W * y, h + y, N, 40)
check("same seed, identical Delta*", np.array_equal(b1, b2))

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
