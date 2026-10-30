"""Self-test of the benchmark alpha test (PREREG section 6.1). Exits non-zero on failure."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []
N = 248
POP = 0.92 * 0.006 - 0.08 * 0.05


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def world(seed, shift):
    rng = np.random.default_rng(seed)
    xs = rng.normal(0.006, 0.043, N)
    e = np.where(rng.random(N) < 0.08, -rng.exponential(0.05, N), rng.normal(0.006, 0.004, N)) - POP
    return xs, 0.5 * xs + e + shift


def verdict(xs, xS, reps=999):
    a, b, se = (v[0] for v in run.ols_nw(xS, xs))
    rng = np.random.default_rng(run.SEED)
    starts = rng.integers(0, N - run.BLOCK + 1, size=(reps, math.ceil(N / run.BLOCK)))
    idx = (starts[:, :, None] + np.arange(run.BLOCK)).reshape(reps, -1)[:, :N]
    ab, _, seb = run.ols_nw(xS[idx], xs[idx])
    crit = np.percentile((ab - a) / seb, run.PCT)
    return a > 0 and a / se >= crit, crit


h0 = sum(verdict(*world(100 + i, 0.0))[0] for i in range(40))
check("null: SUPPORTED in at most 2 of 40", h0 <= 2, f"{h0} of 40")
h1 = sum(verdict(*world(200 + i, 0.020))[0] for i in range(8))
check("planted +2.0% a month: SUPPORTED in 8 of 8", h1 == 8, f"{h1} of 8")
a, b, _ = run.ols_nw(np.array([1.0, 2.0, 3.0, 4.0]), np.array([0.0, 1.0, 2.0, 3.0]))
check("OLS hand values", abs(a[0] - 1) < 1e-12 and abs(b[0] - 1) < 1e-12)
# White's estimator at 0 lags: compare with an explicit sandwich.
rng = np.random.default_rng(5)
x, y = rng.normal(size=80), rng.normal(size=80)
X = np.column_stack([np.ones(80), x])
beta = np.linalg.lstsq(X, y, rcond=None)[0]
u = y - X @ beta
inv = np.linalg.inv(X.T @ X)
white = math.sqrt((inv @ (X * u[:, None]).T @ (X * u[:, None]) @ inv)[0, 0])
lags_saved = None
# run.ols_nw has 3 lags built in; reproduce 0 lags by checking the explicit 3-lag sandwich instead.
S = (X * u[:, None]).T @ (X * u[:, None])
for l in range(1, 4):
    G = (X[l:] * u[l:, None]).T @ (X[:-l] * u[:-l, None])
    S += (1 - l / 4) * (G + G.T)
nw3 = math.sqrt((inv @ S @ inv)[0, 0])
check("Newey-West intercept s.e. matches explicit sandwich", abs(run.ols_nw(y, x)[2][0] - nw3) < 1e-12,
      f"white {white:.5f}")
xs, xS = world(9, 0.0)
check("same seed, identical critical value", verdict(xs, xS, 99)[1] == verdict(xs, xS, 99)[1])

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
