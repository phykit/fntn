"""Self-test of the covered-call pair simulation (PREREG section 11). Exits non-zero on failure.

Six checks on the implementation's own functions: the Black-Scholes code against a hand value,
the closed form at mu = r, a small simulation against the closed form, common random numbers,
the jump arm's moments, and the drawdown function against a hand-computed path. None of these
is a registered figure; they exist so that a defect in the machinery is caught before the run.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

FAILS = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("ok   " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


# i) Black-Scholes premium at m = 1, v = 0.2, dt = 1, r = 0 equals N(0.1) - N(-0.1).
want = run.ncdf(0.1) - run.ncdf(-0.1)
have = run.bs_call(1.0, 0.2, r=0.0, dt=1.0)
check("bs_call hand value", abs(have - want) <= 1e-12, f"{have:.12f} vs {want:.12f}")

# ii) Closed-form E[y] is zero when mu = r and v = sigma, at both moneyness values.
for m in run.M_GRID:
    ey = run.expected_overlay(m, run.SIGMA, mu=run.R)
    check(f"E[y] = 0 at mu = r, m = {m:.2f}", abs(ey) <= 1e-12, f"{ey:.3e}")

# iii) Small simulation: control arm, rho = 0.5, m = 1.05, leg mean within 3 SE of closed form.
d = run.draws(n_paths=400, t=120, seed=7)
g1, g2 = run.base_returns(d, 0.5)
st, ybar, y1, y2 = run.cell_stats(g1, g2, 1.05, run.SIGMA)
ey = run.expected_overlay(1.05, run.SIGMA)
for name, yl in (("leg 1", y1), ("leg 2", y2)):
    se = yl.std(ddof=1) / math.sqrt(yl.size)
    z = (yl.mean() - ey) / se
    check(f"small simulation {name} within 3 SE of closed form", abs(z) <= 3.0, f"z = {z:+.2f}")

# iv) Common random numbers: leg 1 identical at rho = 0.0 and rho = 0.9.
a1, _ = run.base_returns(d, 0.0)
b1, _ = run.base_returns(d, 0.9)
check("leg 1 identical across rho", np.array_equal(a1, b1))

# v) Jump arm at rho_d = 0, rho_j = 0: log-return variance within 3% of SIGMA^2 DT, gross mean
#    within 3 SE of exp(MU DT).
j1, j2, both = run.jump_returns(d, 0.0, 0.0)
x = np.log(j1)
target_var = run.SIGMA ** 2 * run.DT
check("jump arm variance", abs(x.var(ddof=1) / target_var - 1.0) <= 0.03,
      f"ratio {x.var(ddof=1) / target_var:.4f}")
se = j1.std(ddof=1) / math.sqrt(j1.size)
z = (j1.mean() - math.exp(run.MU * run.DT)) / se
check("jump arm gross mean", abs(z) <= 3.0, f"z = {z:+.2f}")

# vi) Maximum drawdown of [+0.10, -0.20, +0.05, -0.10] is -0.244.
mdd = run.max_drawdown_per_path(np.array([[0.10, -0.20, 0.05, -0.10]]))[0]
check("max drawdown hand value", abs(mdd - (-0.244)) <= 1e-12, f"{mdd:.12f}")

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
