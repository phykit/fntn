"""Self-test of the VIP test's regression code (PREREG section 5): planted alpha must PASS 8 of 8,
no alpha must PASS no more than 4 of 40; plus a Newey-West hand check. Exits non-zero on failure."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def world(seed, alpha):
    rng = np.random.default_rng(seed)
    n = 150
    F = rng.normal(0.005, 0.03, (n, 6))
    beta = np.array([1.1, 0.2, -0.3, 0.1, -0.1, 0.2])
    x = alpha + F @ beta + rng.normal(0, 0.015, n)
    months = [(2013 + (i + 8) // 12, (i + 8) % 12 + 1) for i in range(n)]
    ret = {k: rng.normal(0.01, 0.04, n) for k in ("basket", "SPY", "QQQ", "RSP")}
    return run.analyse(months, x, F, ret, np.zeros(n))


# Newey-West with zero lags equals White's estimator
rng = np.random.default_rng(3)
X = np.column_stack([np.ones(50), rng.normal(size=50)])
e = rng.normal(size=50)
white = np.sqrt(np.diag(np.linalg.inv(X.T @ X) @ (X * e[:, None]).T @ (X * e[:, None]) @ np.linalg.inv(X.T @ X)))
check("Newey-West with 0 lags equals White", np.allclose(run.nw_se(X, e, lags=0), white))
check("monthly compounding", abs(run.monthly([__import__("datetime").date(2020, 1, 2), __import__("datetime").date(2020, 1, 3)],
                                              np.array([0.1, 0.1]), np.array([True, True]))[(2020, 1)] - 0.21) < 1e-12)
null = sum(world(100 + s, 0.0)["verdict"] == "PASS" for s in range(40))
plant = sum(world(200 + s, 0.01)["verdict"] == "PASS" for s in range(8))
print(f"null worlds passing {null} of 40; planted (12% a year) passing {plant} of 8")
check("null worlds pass at most 4 of 40", null <= 4)
check("planted worlds pass 8 of 8", plant == 8)
if FAILS:
    print(f"SELFTEST FAILED: {len(FAILS)}")
    sys.exit(1)
print("SELFTEST PASSED")
