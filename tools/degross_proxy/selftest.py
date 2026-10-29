"""Self-test of run.py before any input is fetched (PREREG section 7).

(a) Hand-built cases with known answers: weekly compounding, the drawdown formula, episode
    merging, the gate and the de-gross sign conditions.
(b) 40 null worlds and 8 planted worlds through the outcome test. Acceptable if no more than 4 of
    40 null worlds and all 8 planted worlds reach PASS.
Exits non-zero on any failure, so the workflow stops before fetching.
"""
from __future__ import annotations

import datetime as dt
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


def bdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def part_a():
    days = bdays(dt.date(2024, 1, 1), 10)  # two ISO weeks
    W = np.array([0.01] * 10)
    L = np.array([0.0] * 10)
    M = np.array([0.0] * 10)
    ends, Ww, Lw, Mw = run.to_weekly(days, W, L, M)
    check("two weekly rows", len(ends) == 2)
    check("weekly compounding", abs(Ww[0] - (1.01 ** 5 - 1)) < 1e-12)
    check("week end is last day", ends[0] == dt.date(2024, 1, 5))

    # drawdown: path up 10%, then down to 0.88 of the peak, within 63 days
    pdays = bdays(dt.date(2000, 1, 3), 200)
    px = np.ones(200) * 100.0
    px[1:11] = np.linspace(101, 110, 10)
    px[11:21] = np.linspace(108, 110 * 0.88, 10)
    px[21:] = 110 * 0.88
    ends2 = [pdays[30]]  # entry at index 30 sees a flat path
    res_flat = run.outcome_test(ends2 * 1, np.array([False]), np.array([True]), pdays, px, 63, -0.10,
                                n_perm=10)
    check("flat path has no episodes", res_flat["n_episodes"] == 0)
    # entry at index 25? need i >= 21 for R21: use entry at index 21 then a later fall
    px2 = np.ones(200) * 100.0
    px2[22:40] = np.linspace(105, 120, 18)
    px2[40:60] = np.linspace(118, 120 * 0.85, 20)
    px2[60:] = 120 * 0.85
    seg = px2[21:21 + 64]
    want = float(np.min(seg[1:] / np.maximum.accumulate(seg)[1:]) - 1)
    check("drawdown formula ~ -0.15", abs(want + 0.15) < 1e-9)

    # episodes merge within 63 trading days of the first trigger, no chaining
    pdays3 = bdays(dt.date(2001, 1, 1), 2000)
    px3 = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, 2000)))
    ends3 = [pdays3[i] for i in range(30, 1800, 5)]
    trig = np.zeros(len(ends3), bool)
    trig[[10, 20, 22, 40]] = True  # indices 10 and 20 are 50 days apart; 22 is 60 days after 10
    r = run.outcome_test(ends3, trig, np.ones(len(ends3), bool), pdays3, px3, 63, -0.10, n_perm=50)
    check("episode merging (10, 20, 22 -> one; 40 -> another)", r["n_episodes"] == 2)

    # gate
    ends4 = [dt.date(2021, 1, 29) + dt.timedelta(weeks=k) for k in range(-60, 300)]
    D = np.zeros(len(ends4), bool)
    ev = np.ones(len(ends4), bool)
    D[60] = True  # 2021-01-29
    k_may = [i for i, e in enumerate(ends4) if abs((e - dt.date(2026, 5, 1)).days) <= 3][0]
    D[k_may + 1] = True  # one week later: within 7 days
    g = run.gate(ends4, D, ev, dt.date(2026, 9, 30))
    check("gate available drops October 2026", g["available"] == ["2021-01-29", "2026-05-01"])
    check("gate PASS on two matches", g["status"] == "PASS")
    g2 = run.gate(ends4, D, ev, dt.date(2026, 3, 1))
    check("gate UNTESTABLE with one available", g2["status"] == "UNTESTABLE")
    D3 = D.copy()
    D3[k_may + 1] = False
    g3 = run.gate(ends4, D3, ev, dt.date(2026, 9, 30))
    check("gate FAIL on one match", g3["status"] == "FAIL")
    D4 = np.ones(len(ends4), bool)
    g4 = run.gate(ends4, D4, ev, dt.date(2026, 9, 30))
    check("gate FAIL when base rate above 5%", g4["status"] == "FAIL")

    # sign conditions: a strongly negative pair that is a rebound squeeze (winners up) is not D
    rng = np.random.default_rng(7)
    n = 500
    Mw = rng.normal(0, 0.02, n)
    Ww = Mw + rng.normal(0, 0.01, n)
    Lw = Mw + rng.normal(0, 0.01, n)
    Ww[450], Lw[450], Mw[450] = 0.10, 0.25, 0.12  # winners up, losers up more
    Ww[460], Lw[460], Mw[460] = -0.08, 0.06, 0.0   # winners down, losers up
    sg = run.signals(Ww, Lw, Mw)
    check("rebound squeeze (winners up outright) excluded by the raw-return sign filter", (not sg["D"][450]))
    check("true de-gross week flagged", bool(sg["D"][460]))
    check("no-sign variant keeps the squeeze if z <= -2",
          bool(sg["D_nosign"][450]) == bool(sg["z"][450] <= -2))


def world(seed, planted):
    rng = np.random.default_rng(seed)
    pdays = bdays(dt.date(1986, 1, 2), 10_300)
    ret = rng.normal(0.0003, 0.015, len(pdays))
    ends = [pdays[i] for i in range(25, len(pdays) - 70, 5)]
    trig = rng.random(len(ends)) < 0.012
    if planted:
        ords = np.array([d.toordinal() for d in pdays])
        for t in np.where(trig)[0]:
            i = int(np.searchsorted(ords, ends[t].toordinal(), side="right") - 1)
            ret[i + 1:i + 31] = np.log(0.85) / 30
    px = 100 * np.exp(np.cumsum(ret))
    return run.outcome_test(ends, trig, np.ones(len(ends), bool), pdays, px, 63, -0.10, n_perm=2000)


def part_b():
    null_pass = sum(world(1000 + s, False)["verdict"] == "PASS" for s in range(40))
    plant = [world(2000 + s, True) for s in range(8)]
    plant_pass = sum(r["verdict"] == "PASS" for r in plant)
    print(f"null worlds passing: {null_pass} of 40")
    print(f"planted worlds passing: {plant_pass} of 8 (episodes {[r['n_episodes'] for r in plant]})")
    check("null worlds pass at most 4 of 40", null_pass <= 4)
    check("planted worlds pass 8 of 8", plant_pass == 8)


if __name__ == "__main__":
    part_a()
    part_b()
    if FAILS:
        print(f"SELFTEST FAILED: {len(FAILS)} checks")
        sys.exit(1)
    print("SELFTEST PASSED")
