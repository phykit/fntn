"""Self-test of the pair risk-adjusted test (PREREG section 7.1). Exits non-zero on failure.

Synthetic per-name y and G and per-pair correlation arrays over 187 months, built so that each
pair's y_p has a planted mean in the low and high halves (or none), feed run.analyse directly."""
from __future__ import annotations

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


def world(seed: int, effect: float):
    """To plant a per-pair effect while the pairs share names, every pair is given one common
    correlation path, so the low and high months are the same for all pairs. (The cross-pair
    Spearman figures are then undefined, which is harmless here: they carry no weight.)"""
    rng = np.random.default_rng(seed)
    c_common = rng.uniform(0.1, 0.7, N)
    lo = c_common < np.median(c_common)
    C = {p: c_common.copy() for p in run.PAIRS}
    mean = np.where(lo, effect, -effect)
    Y = {i: mean + rng.normal(0, 0.03, N) for i in run.NAMES}
    G = {i: 1.0 + rng.normal(0.01, 0.06, N) for i in run.NAMES}
    months = [f"{2011 + m // 12}-{m % 12 + 1:02d}-01" for m in range(N)]
    return months, Y, G, C


hits0 = sum(run.analyse(*world(1000 + s, 0.0), b=500)["verdict"] == "SUPPORTED" for s in range(40))
check("null: SUPPORTED in at most 4 of 40", hits0 <= 4, f"{hits0} of 40")
hits = sum(run.analyse(*world(2000 + s, 0.005), b=500)["verdict"] == "SUPPORTED" for s in range(8))
check("planted: SUPPORTED in 8 of 8", hits == 8, f"{hits} of 8")
check("IR of [1, 2, 3] is 2", abs(run.ir(np.array([1.0, 2.0, 3.0])) - 2.0) < 1e-15)
lo, hi = run.split(np.array([1.0, 2.0, 3.0]))
check("value equal to median goes to H", bool(hi[1]) and not bool(lo[1]))
m, Y, G, C = world(5, 0.0)
b1, _ = run.bootstrap(Y, C, N, 50)
b2, _ = run.bootstrap(Y, C, N, 50)
check("same seed, identical D*", np.array_equal(b1, b2))

if FAILS:
    print("SELFTEST FAILED:", FAILS)
    sys.exit(1)
print("SELFTEST PASSED")
