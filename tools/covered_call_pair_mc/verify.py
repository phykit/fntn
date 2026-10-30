#!/usr/bin/env python3
"""Independent second implementation of the covered-call pair Monte Carlo.

Written from PREREG.md alone (sections 2 to 10), without sight of run.py,
selftest.py or compare.py, so that agreement between results.json and
verify.json is evidence that the pre-registration document, and not the first
implementation's private reading of it, determines the figures. A second
implementation that had read the first would only confirm that the first was
copied correctly.

Dependencies: numpy and the standard library only. Float64 throughout. All
simulated quantities are (N_PATHS, T) arrays and every operation on them is
vectorised, save the V2 governor, which is sequential in months by its nature
and is looped over T with the paths vectorised.

Reading decisions taken where the document leaves room, stated here so that a
disagreement with run.py can be traced to its cause rather than hunted for:

i)   Under V2 the pair total return of a month in which the calls are not
     written is the plain stock return (G_1 + G_2) / 2 - 1, which is the q_t
     of section 5; in a written month it is g_t. The g series used for
     mean_g, sd_g, worst_g and the drawdown figures is therefore q_t, and its
     compounded path from 1 is exactly the strategy equity E_t that the
     governor reads. The overlay figures mean_y, sd_y, se_y, sharpe_y,
     mean_y1 and mean_y2 are taken over all path-months of y as defined in
     section 3, that is the overlay as if written, so that they are the same
     random variable as under V1; the written-only figures are reported
     separately as mean_y_written, sd_y_written, se_y_written and n_written.
     The analytic check uses written months only, as check 1 requires. The
     assignment fractions are over all path-months, since G_i > m does not
     depend on whether a call was sold.
ii)  Check 5's theorem part halts the run "as in check 2", so a failure there
     yields the HALTED verdict even though the verdict paragraph of section 9
     names only checks 1 and 2.
iii) Check 5's pass flag is the conjunction of its theorem part and its
     predicted (drawdown) part; the detail string reports each separately.
iv)  The thesis hit of section 9 is z_D <= -3 in any V1 base cell (control,
     A or B) or z2 <= -3 in any V2 cell. The jump arm's z_J and the per-path
     z_D under V2 are not thesis hits; a value of z_J beyond 3 in either
     direction halts under check 5 before the verdict is reached.
v)   Check 2 under V2 is the pooled z2 of the amended section 9, with
     se_w = sd_y_written / sqrt(n_written) at each end of the grid. The
     per-path z_D under V2 is computed and written to the paired object
     without weight, as the document asks, and is not read by any check.
vi)  The running maximum used for every drawdown includes the starting
     equity of 1, as section 5's P_(t-1) includes E_0.

Usage: python3 verify.py --out DIR   (writes DIR/verify.json)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Constants, every one of them taken from PREREG.md. None is fitted to anything.
# ---------------------------------------------------------------------------

# Section 2: model.
SIGMA = 0.30
MU = 0.06
R = 0.04
DT = 1.0 / 12.0
RHO_GRID = [-0.3, 0.0, 0.3, 0.6, 0.9, 1.0]

# Section 3: strategy.
M_GRID = [1.00, 1.05]

# Section 4: arms.
KAPPA = 0.21
V_CONTROL = SIGMA
V_ARM_A = SIGMA * math.sqrt(1.0 + KAPPA)

# Section 5: V2 drawdown governor threshold.
GOVERNOR = 0.9

# Section 6: jump arm. The jump variance is removed from the diffusive variance
# so that the total monthly log-return variance stays at SIGMA^2 * DT, and the
# constant A is chosen so that E[exp(x)] = exp(MU * DT) exactly.
P_J = 1.0 / 12.0
MU_J = -0.10
S_J = 0.05
VJ = P_J * (S_J ** 2 + MU_J ** 2) - P_J ** 2 * MU_J ** 2
VD = SIGMA ** 2 * DT - VJ
SD = math.sqrt(VD)
A_JUMP = MU * DT - VD / 2.0 - math.log(1.0 - P_J + P_J * math.exp(MU_J + S_J ** 2 / 2.0))
RHO_D_GRID = [0.0, 0.3, 0.6, 0.9]
RHO_J_GRID = [0.0, 1.0]

# Section 7: simulation size and seed.
N_PATHS = 2000
T = 120
SEED = 20261030

# Section 9: the halting and direction threshold on z statistics.
Z_LIMIT = 3.0

ARMS = ["control", "A", "B"]
VARIANTS = ["V1", "V2"]

RHO_LOW = RHO_GRID[0]    # -0.3, the lower end of the paired difference
RHO_HIGH = RHO_GRID[-1]  # 1.0, the upper end of the paired difference


# ---------------------------------------------------------------------------
# Closed forms (section 3).
# ---------------------------------------------------------------------------

def norm_cdf(x: float) -> float:
    """Standard normal distribution function, N(x) = 0.5 * erfc(-x / sqrt(2)).

    The document fixes this form so that two implementations agree to the last
    bit rather than to a library's tolerance.
    """
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bs_call(m: float, v: float, r: float = R, dt: float = DT) -> float:
    """Black-Scholes premium as a fraction of the start price, strike m, rate r,
    time dt, implied volatility v (section 3)."""
    vs = v * math.sqrt(dt)
    d1 = (math.log(1.0 / m) + (r + v * v / 2.0) * dt) / vs
    d2 = d1 - vs
    return norm_cdf(d1) - m * math.exp(-r * dt) * norm_cdf(d2)


def expected_call_payoff(m: float) -> float:
    """E[max(G - m, 0)] under the section 2 dynamics (closed form of section 3).

    Uses the real drift MU and the realised volatility SIGMA, not the implied
    volatility, because it is the expectation of the realised payoff."""
    ss = SIGMA * math.sqrt(DT)
    d1s = (math.log(1.0 / m) + (MU + SIGMA ** 2 / 2.0) * DT) / ss
    d2s = d1s - ss
    return math.exp(MU * DT) * norm_cdf(d1s) - m * norm_cdf(d2s)


def expected_overlay_excess(m: float, v: float) -> float:
    """Closed form E[y] = c * exp(R * DT) - E[max(G - m, 0)].

    This does not involve rho, which is the whole of the analyst's prior: a
    leg's overlay excess depends on that leg's own return and its own premium.
    """
    return bs_call(m, v) * math.exp(R * DT) - expected_call_payoff(m)


def implied_vol(arm: str, rho: float) -> float:
    """Section 4: what the market is assumed to charge in each arm."""
    if arm == "control":
        return V_CONTROL
    if arm == "A":
        return V_ARM_A
    if arm == "B":
        # Premium on the systematic share of variance only; in the symmetric
        # one-factor reading that share is abs(rho).
        return SIGMA * math.sqrt(1.0 + KAPPA * abs(rho))
    raise ValueError(f"unknown arm {arm!r}")


# ---------------------------------------------------------------------------
# Random numbers (section 7).
# ---------------------------------------------------------------------------

def draw_random_numbers() -> dict:
    """All draws, in the order and shapes of section 7, made once.

    The jump-arm draws (3 to 6) are made even though the base design never
    reads them, so that the stream is fixed and a second implementation that
    follows the same order lands on the same numbers.
    """
    rng = np.random.default_rng(SEED)
    shape = (N_PATHS, T)
    draws = {}
    draws["Z1"] = rng.standard_normal(shape)
    draws["Z2"] = rng.standard_normal(shape)
    draws["U_MIX"] = rng.random(shape)
    draws["U_C"] = rng.random(shape)
    draws["J_C"] = rng.normal(MU_J, S_J, shape)
    draws["U_1"] = rng.random(shape)
    draws["J_1"] = rng.normal(MU_J, S_J, shape)
    draws["U_2"] = rng.random(shape)
    draws["J_2"] = rng.normal(MU_J, S_J, shape)
    return draws


def correlated_eps(Z1: np.ndarray, Z2: np.ndarray, rho: float):
    """Common random numbers: eps_1 = Z1, eps_2 = rho * Z1 + sqrt(1 - rho^2) * Z2.

    Leg 1 is identical across the grid by construction; only the dependence
    moves, which is what makes the paired difference of section 9 sharp.
    """
    return Z1, rho * Z1 + math.sqrt(1.0 - rho * rho) * Z2


def base_gross_returns(Z1: np.ndarray, Z2: np.ndarray, rho: float):
    """Section 2: gross monthly returns G_1, G_2 of the two legs at correlation rho."""
    e1, e2 = correlated_eps(Z1, Z2, rho)
    drift = (MU - SIGMA ** 2 / 2.0) * DT
    scale = SIGMA * math.sqrt(DT)
    return np.exp(drift + scale * e1), np.exp(drift + scale * e2)


def jump_gross_returns(draws: dict, rho_d: float, rho_j: float):
    """Section 6: gross returns with a jump component and correlated arrival.

    Returns (G_1, G_2, B_1, B_2) where B_i is the effective arrival indicator
    of leg i after mixing. With Mix = 1 both legs take the common (B_c, J_c);
    with Mix = 0 each leg takes its own draw. Each leg's marginal is the same
    at every rho_j because the common and own draws have the same law.
    """
    e1, e2 = correlated_eps(draws["Z1"], draws["Z2"], rho_d)
    mix = draws["U_MIX"] < rho_j
    b_c = draws["U_C"] < P_J
    b_1 = draws["U_1"] < P_J
    b_2 = draws["U_2"] < P_J
    b1 = np.where(mix, b_c, b_1)
    b2 = np.where(mix, b_c, b_2)
    j1 = np.where(mix, draws["J_C"], draws["J_1"])
    j2 = np.where(mix, draws["J_C"], draws["J_2"])
    x1 = A_JUMP + SD * e1 + np.where(b1, j1, 0.0)
    x2 = A_JUMP + SD * e2 + np.where(b2, j2, 0.0)
    return np.exp(x1), np.exp(x2), b1, b2


# ---------------------------------------------------------------------------
# Strategy arithmetic (sections 3 and 5).
# ---------------------------------------------------------------------------

def overlay_excess(G: np.ndarray, m: float, c: float) -> np.ndarray:
    """y = c * exp(R * DT) - max(G - m, 0): the premium, accrued at R for the
    month, less the call payoff surrendered. Cash settled, stock kept."""
    return c * math.exp(R * DT) - np.maximum(G - m, 0.0)


def run_governor(G1: np.ndarray, G2: np.ndarray, y1: np.ndarray, y2: np.ndarray) -> np.ndarray:
    """Section 5 V2: the drawdown governor, returning the boolean (N_PATHS, T)
    array of months in which the calls are written.

    Sequential in t because the decision for month t reads E_(t-1) and
    P_(t-1), which depend on every earlier month's decision. Month 1 is always
    written. In an unwritten month the strategy earns the plain pair stock
    return. The rule reads the joint history of both legs, which is why it is
    the one place a portfolio-level rule could let rho into the mean if the
    theorem were wrong; the check is that it does not.
    """
    stock = (G1 + G2) / 2.0 - 1.0
    g_written = stock + (y1 + y2) / 2.0
    equity = np.ones(N_PATHS)
    peak = np.ones(N_PATHS)
    written = np.zeros((N_PATHS, T), dtype=bool)
    for t in range(T):
        if t == 0:
            w = np.ones(N_PATHS, dtype=bool)
        else:
            w = equity >= GOVERNOR * peak
        written[:, t] = w
        q = np.where(w, g_written[:, t], stock[:, t])
        equity = equity * (1.0 + q)
        peak = np.maximum(peak, equity)
    return written


def max_drawdown(g: np.ndarray) -> np.ndarray:
    """Per-path maximum drawdown of the equity compounded from 1 along the
    monthly total returns g, measured against the running maximum (which
    starts at the initial equity of 1), the most negative value taken."""
    equity = np.cumprod(1.0 + g, axis=1)
    peak = np.maximum(np.maximum.accumulate(equity, axis=1), 1.0)
    return (equity / peak - 1.0).min(axis=1)


def cell_statistics(y1: np.ndarray, y2: np.ndarray, G1: np.ndarray, G2: np.ndarray, m: float,
                    written: np.ndarray | None = None) -> dict:
    """Section 8 statistics over all path-months of one cell.

    y1 and y2 are the per-leg overlay excesses as defined in section 3, that
    is as if written in every month. Under V2 the caller passes the boolean
    array of written months; the total return g is then the strategy return
    q_t of section 5 (the overlay counted only in written months), so that the
    compounded g is the equity E_t the governor reads, whilst the y figures
    remain over every path-month of the overlay as if written.
    """
    y = (y1 + y2) / 2.0
    stock = (G1 + G2) / 2.0 - 1.0
    if written is None:
        g = stock + y
    else:
        g = np.where(written, stock + y, stock)
    n = y.size
    sd_y = float(y.std(ddof=1))
    mean_y = float(y.mean())
    a1 = G1 > m
    a2 = G2 > m
    mdd = max_drawdown(g)
    return {
        "mean_y": mean_y,
        "sd_y": sd_y,
        "se_y": sd_y / math.sqrt(n),
        "sharpe_y": mean_y / sd_y,
        "mean_y1": float(y1.mean()),
        "mean_y2": float(y2.mean()),
        "mean_g": float(g.mean()),
        "sd_g": float(g.std(ddof=1)),
        "worst_g": float(g.min()),
        "assign_1": float(a1.mean()),
        "assign_2": float(a2.mean()),
        "assign_both": float((a1 & a2).mean()),
        "mdd_median": float(np.median(mdd)),
        "mdd_p05": float(np.percentile(mdd, 5)),
    }


# ---------------------------------------------------------------------------
# Paired statistics (section 9).
# ---------------------------------------------------------------------------

def paired_difference(ybar_high: np.ndarray, ybar_low: np.ndarray) -> dict:
    """D = mean(d_k), SE_D = sd(d_k, ddof 1) / sqrt(N_PATHS), z_D = D / SE_D,
    with d_k the per-path difference of mean overlay excess between the two
    ends of the grid. The common random numbers make d_k a within-path
    contrast, which is why its standard error is far smaller than the cell
    standard errors."""
    d = ybar_high - ybar_low
    D = float(d.mean())
    SE_D = float(d.std(ddof=1)) / math.sqrt(N_PATHS)
    return {"D": D, "SE_D": SE_D, "z_D": D / SE_D}


def ols_slope(xs: list, ys: list) -> float:
    """Ordinary least-squares slope of ys on xs, no weights, no intercept
    constraint (section 9's slope_y)."""
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    xc = x - x.mean()
    return float((xc * (y - y.mean())).sum() / (xc * xc).sum())


# ---------------------------------------------------------------------------
# The run.
# ---------------------------------------------------------------------------

def simulate() -> dict:
    draws = draw_random_numbers()
    Z1, Z2 = draws["Z1"], draws["Z2"]

    # The base dynamics depend on rho only, so build them once per grid point.
    base_G = {rho: base_gross_returns(Z1, Z2, rho) for rho in RHO_GRID}

    cells = []
    paired = []
    leg_checks = []          # one record per (cell, leg) for check 1
    sd_by_design = {}        # (arm, m) -> [sd_y along RHO_GRID] under V1, for check 4

    # ---- Base design: arm, m, variant, rho. ----
    for arm in ARMS:
        for m in M_GRID:
            for variant in VARIANTS:
                if variant == "V2" and arm == "B":
                    continue  # V2 runs on the control arm and Arm A only (section 5)
                ybars = {}
                mean_ys = []
                sd_ys = []
                written_stats = {}
                for rho in RHO_GRID:
                    G1, G2 = base_G[rho]
                    v = implied_vol(arm, rho)
                    c = bs_call(m, v)
                    y1 = overlay_excess(G1, m, c)
                    y2 = overlay_excess(G2, m, c)
                    if variant == "V2":
                        w = run_governor(G1, G2, y1, y2)
                        stats = cell_statistics(y1, y2, G1, G2, m, written=w)
                        y_pair = (y1 + y2) / 2.0
                        n_written = int(w.sum())
                        yw = y_pair[w]
                        sd_w = float(yw.std(ddof=1))
                        stats["frac_written"] = float(w.mean())
                        stats["mean_y_written"] = float(yw.mean())
                        stats["sd_y_written"] = sd_w
                        stats["se_y_written"] = sd_w / math.sqrt(n_written)
                        stats["n_written"] = n_written
                        written_stats[rho] = stats
                        # Per-path mean over written months only (section 9).
                        ybars[rho] = (np.where(w, y_pair, 0.0)).sum(axis=1) / w.sum(axis=1)
                        leg1_pool = y1[w]
                        leg2_pool = y2[w]
                    else:
                        stats = cell_statistics(y1, y2, G1, G2, m)
                        y_pair = (y1 + y2) / 2.0
                        ybars[rho] = y_pair.mean(axis=1)
                        leg1_pool = y1.ravel()
                        leg2_pool = y2.ravel()

                    # Check 1 material: each leg against the closed form at this
                    # cell's m and v, over the leg's pooled (written) path-months.
                    ey = expected_overlay_excess(m, v)
                    for leg, pool in ((1, leg1_pool), (2, leg2_pool)):
                        se = float(pool.std(ddof=1)) / math.sqrt(pool.size)
                        dev = float(pool.mean()) - ey
                        leg_checks.append({
                            "arm": arm, "m": m, "variant": variant, "rho": rho, "leg": leg,
                            "dev": dev, "se": se, "ratio": abs(dev) / se,
                            "pass": abs(dev) <= Z_LIMIT * se,
                        })

                    cells.append({"arm": arm, "m": float(m), "variant": variant, "rho": float(rho), **stats})
                    mean_ys.append(stats["mean_y"])
                    sd_ys.append(stats["sd_y"])

                pd = paired_difference(ybars[RHO_HIGH], ybars[RHO_LOW])
                entry = {
                    "arm": arm, "m": float(m), "variant": variant,
                    "D": pd["D"], "SE_D": pd["SE_D"], "z_D": pd["z_D"],
                    "slope_y": ols_slope(RHO_GRID, mean_ys),
                }
                if variant == "V2":
                    # Check 2 under V2 (amended section 9): the pooled
                    # written-month difference, with a standard error that
                    # ignores the common random numbers and so overstates.
                    hi = written_stats[RHO_HIGH]
                    lo = written_stats[RHO_LOW]
                    D2 = hi["mean_y_written"] - lo["mean_y_written"]
                    SE2 = math.sqrt(hi["se_y_written"] ** 2 + lo["se_y_written"] ** 2)
                    entry["D2"] = D2
                    entry["SE2"] = SE2
                    entry["z2"] = D2 / SE2
                paired.append(entry)
                if variant == "V1":
                    sd_by_design[(arm, m)] = sd_ys

    # ---- Jump arm: m, rho_d, rho_j; priced under Arm A; V1 only. ----
    jump_G = {(rd, rj): jump_gross_returns(draws, rd, rj) for rd in RHO_D_GRID for rj in RHO_J_GRID}
    jump_cells_by_key = {}
    for m in M_GRID:
        c = bs_call(m, V_ARM_A)
        ybars = {}
        for rho_d in RHO_D_GRID:
            for rho_j in RHO_J_GRID:
                G1, G2, b1, b2 = jump_G[(rho_d, rho_j)]
                y1 = overlay_excess(G1, m, c)
                y2 = overlay_excess(G2, m, c)
                stats = cell_statistics(y1, y2, G1, G2, m)
                stats["frac_both_jump"] = float((b1 & b2).mean())
                y_pair = (y1 + y2) / 2.0
                ybars[(rho_d, rho_j)] = y_pair.mean(axis=1)
                cell = {"arm": "jump", "m": float(m), "variant": "V1",
                        "rho_d": float(rho_d), "rho_j": float(rho_j), **stats}
                cells.append(cell)
                jump_cells_by_key[(m, rho_d, rho_j)] = cell
        pd = paired_difference(ybars[(0.9, 1.0)], ybars[(0.0, 0.0)])
        paired.append({"arm": "jump", "m": float(m), "variant": "V1",
                       "D": pd["D"], "SE_D": pd["SE_D"], "z_D": pd["z_D"]})

    checks = run_checks(paired, leg_checks, sd_by_design, jump_cells_by_key)
    verdict = decide_verdict(checks, paired)

    params = {
        "SIGMA": SIGMA, "MU": MU, "R": R, "DT": DT, "RHO_GRID": RHO_GRID,
        "M_GRID": M_GRID, "KAPPA": KAPPA, "V_CONTROL": V_CONTROL, "V_ARM_A": V_ARM_A,
        "GOVERNOR": GOVERNOR,
        "P_J": P_J, "MU_J": MU_J, "S_J": S_J, "VJ": VJ, "VD": VD, "SD": SD, "A": A_JUMP,
        "RHO_D_GRID": RHO_D_GRID, "RHO_J_GRID": RHO_J_GRID,
        "N_PATHS": N_PATHS, "T": T, "SEED": SEED, "Z_LIMIT": Z_LIMIT,
    }
    return {"params": params, "cells": cells, "paired": paired, "checks": checks, "verdict": verdict}


# ---------------------------------------------------------------------------
# Checks and verdict (section 9), fixed before the run.
# ---------------------------------------------------------------------------

def run_checks(paired: list, leg_checks: list, sd_by_design: dict, jump_cells: dict) -> dict:
    checks = {}

    # Check 1: analytic. Every base cell, each leg, within 3 se of the closed
    # form. A failure is a code defect, not a result, because the closed form
    # is exact under the model.
    fails = [r for r in leg_checks if not r["pass"]]
    worst = max(leg_checks, key=lambda r: r["ratio"])
    detail = (f"{len(leg_checks)} leg checks over {len(leg_checks) // 2} base cells; "
              f"max |dev|/se = {worst['ratio']:.3f} at arm={worst['arm']} m={worst['m']} "
              f"{worst['variant']} rho={worst['rho']} leg {worst['leg']}; "
              f"{len(fails)} failure(s)")
    if fails:
        detail += ": " + "; ".join(
            f"arm={r['arm']} m={r['m']} {r['variant']} rho={r['rho']} leg {r['leg']} "
            f"dev={r['dev']:.3e} se={r['se']:.3e}" for r in fails)
    checks["check1_analytic"] = {"pass": not fails, "detail": detail}

    # Check 2: theorem. Control and Arm A, both m. Under V1 |z_D| <= 3,
    # because E[d_k] = 0 exactly when the premium does not depend on rho.
    # Under V2 the pooled |z2| <= 3 (amended section 9); the per-path z_D under
    # V2 is a biased ratio estimator and is not read here.
    theorem = [p for p in paired if p["arm"] in ("control", "A")]

    def theorem_z(p):
        return p["z_D"] if p["variant"] == "V1" else p["z2"]

    def theorem_label(p):
        return "z_D" if p["variant"] == "V1" else "z2"

    fails = [p for p in theorem if abs(theorem_z(p)) > Z_LIMIT]
    detail = "; ".join(f"{p['arm']} m={p['m']} {p['variant']}: {theorem_label(p)}={theorem_z(p):.3f}"
                       for p in theorem)
    checks["check2_theorem"] = {"pass": not fails,
                                "detail": f"{len(fails)} of {len(theorem)} exceed |z|={Z_LIMIT:g}. " + detail}

    # Check 3: Arm B direction. Predicted z_D >= 3 because the premium rises
    # with abs(rho). Failure is recorded, not halting.
    arm_b = [p for p in paired if p["arm"] == "B" and p["variant"] == "V1"]
    fails = [p for p in arm_b if not (p["z_D"] >= Z_LIMIT)]
    detail = "; ".join(f"m={p['m']}: z_D={p['z_D']:.3f}" for p in arm_b)
    checks["check3_armB"] = {"pass": not fails,
                             "detail": f"{len(fails)} of {len(arm_b)} below z={Z_LIMIT:g}. " + detail}

    # Check 4: variance effect. sd_y strictly increasing along RHO_GRID in
    # every arm under V1, both m. Predicted; failure recorded.
    fails = []
    parts = []
    for arm in ARMS:
        for m in M_GRID:
            sds = sd_by_design[(arm, m)]
            increasing = bool(np.all(np.diff(np.asarray(sds)) > 0.0))
            parts.append(f"{arm} m={m}: " + ("increasing" if increasing else "NOT increasing")
                         + " [" + ", ".join(f"{s:.5f}" for s in sds) + "]")
            if not increasing:
                fails.append((arm, m))
    checks["check4_variance"] = {"pass": not fails,
                                 "detail": f"{len(fails)} of {len(parts)} designs fail. " + "; ".join(parts)}

    # Check 5: jump arm. Theorem part |z_J| <= 3 (halts on failure, as check 2);
    # then at each (m, rho_d) the drawdown figures at rho_j = 1 are no better
    # than at rho_j = 0: mdd_p05 and worst_g both no greater. Predicted;
    # failure of the second part is recorded.
    jump_pairs = [p for p in paired if p["arm"] == "jump"]
    theorem_fails = [p for p in jump_pairs if abs(p["z_D"]) > Z_LIMIT]
    theorem_ok = not theorem_fails
    dd_fails = []
    for m in M_GRID:
        for rho_d in RHO_D_GRID:
            c0 = jump_cells[(m, rho_d, 0.0)]
            c1 = jump_cells[(m, rho_d, 1.0)]
            if c1["mdd_p05"] > c0["mdd_p05"]:
                dd_fails.append(f"m={m} rho_d={rho_d} mdd_p05 {c1['mdd_p05']:.5f} > {c0['mdd_p05']:.5f}")
            if c1["worst_g"] > c0["worst_g"]:
                dd_fails.append(f"m={m} rho_d={rho_d} worst_g {c1['worst_g']:.5f} > {c0['worst_g']:.5f}")
    predicted_ok = not dd_fails
    detail = ("theorem part " + ("PASS" if theorem_ok else "FAIL (halts)") + ": "
              + "; ".join(f"m={p['m']}: z_J={p['z_D']:.3f}" for p in jump_pairs)
              + ". predicted part " + ("PASS" if predicted_ok else "FAIL (recorded)")
              + f": {len(dd_fails)} of {2 * len(M_GRID) * len(RHO_D_GRID)} comparisons better at rho_j=1"
              + ("; " + "; ".join(dd_fails) if dd_fails else ""))
    checks["check5_jump"] = {"pass": theorem_ok and predicted_ok, "detail": detail,
                             "theorem_pass": theorem_ok, "predicted_pass": predicted_ok}

    return checks


def decide_verdict(checks: dict, paired: list) -> str:
    """Section 9's verdict on H-CC.

    HALTED when check 1 or 2 fails, or when check 5's theorem part fails (it
    halts "as in check 2"). Otherwise SUPPORTED if there is a thesis hit,
    z_D <= -3 in any V1 base design or z2 <= -3 in any V2 design, and NOT
    SUPPORTED if there is none. The document predicts NOT SUPPORTED and says a
    SUPPORTED verdict would itself be a defect to diagnose; this function
    reports what the figures say and leaves that diagnosis to the reader.
    """
    if not checks["check1_analytic"]["pass"] or not checks["check2_theorem"]["pass"]:
        return "HALTED"
    if not checks["check5_jump"]["theorem_pass"]:
        return "HALTED"
    base = [p for p in paired if p["arm"] != "jump"]
    hit = any(p["z_D"] <= -Z_LIMIT for p in base if p["variant"] == "V1") or \
        any(p["z2"] <= -Z_LIMIT for p in base if p["variant"] == "V2")
    if hit:
        return "SUPPORTED"
    return "NOT SUPPORTED"


# ---------------------------------------------------------------------------
# Output.
# ---------------------------------------------------------------------------

def to_builtin(obj):
    """Recursively convert numpy scalars and arrays into JSON-serialisable
    Python objects; json.dump will not take numpy types."""
    if isinstance(obj, dict):
        return {k: to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [to_builtin(v) for v in obj.tolist()]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def print_report(results: dict) -> None:
    cells = results["cells"]
    print("Cells (base design, then jump arm)")
    hdr = (f"{'arm':8s} {'m':>5s} {'var':4s} {'rho':>5s} {'rho_j':>5s} "
           f"{'mean_y':>10s} {'sd_y':>9s} {'sharpe':>8s} {'mean_g':>10s} "
           f"{'mdd_med':>9s} {'mdd_p05':>9s} {'worst_g':>9s} {'written':>8s}")
    print(hdr)
    for c in cells:
        rho = c.get("rho", c.get("rho_d"))
        rho_j = c.get("rho_j")
        rho_j_s = f"{rho_j:5.1f}" if rho_j is not None else f"{'':5s}"
        fw = c.get("frac_written")
        fw_s = f"{fw:8.4f}" if fw is not None else f"{'':8s}"
        print(f"{c['arm']:8s} {c['m']:5.2f} {c['variant']:4s} {rho:5.1f} {rho_j_s} "
              f"{c['mean_y']:10.6f} {c['sd_y']:9.6f} {c['sharpe_y']:8.4f} {c['mean_g']:10.6f} "
              f"{c['mdd_median']:9.5f} {c['mdd_p05']:9.5f} {c['worst_g']:9.5f} {fw_s}")
    print()
    print("Paired differences, rho = 1.0 less rho = -0.3 (jump: (0.9, 1.0) less (0.0, 0.0))")
    print(f"{'arm':8s} {'m':>5s} {'var':4s} {'D':>12s} {'SE_D':>12s} {'z_D':>8s} {'slope_y':>12s}")
    for p in results["paired"]:
        slope = p.get("slope_y")
        slope_s = f"{slope:12.3e}" if slope is not None else f"{'n/a':>12s}"
        print(f"{p['arm']:8s} {p['m']:5.2f} {p['variant']:4s} {p['D']:12.3e} {p['SE_D']:12.3e} "
              f"{p['z_D']:8.3f} {slope_s}")
    print()
    print("Checks")
    for name, chk in results["checks"].items():
        print(f"  {name:18s} {'PASS' if chk['pass'] else 'FAIL'}  {chk['detail']}")
    print()
    print(f"Verdict on H-CC: {results['verdict']}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Second implementation of the covered-call pair "
                                                 "Monte Carlo, from PREREG.md alone.")
    parser.add_argument("--out", required=True, help="directory to receive verify.json")
    args = parser.parse_args(argv)

    results = simulate()
    # The two auxiliary flags on check 5 are kept out of the file so that the
    # checks object has exactly the shape section 10 specifies.
    out = to_builtin(results)
    out["checks"]["check5_jump"] = {"pass": out["checks"]["check5_jump"]["pass"],
                                    "detail": out["checks"]["check5_jump"]["detail"]}

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "verify.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    print_report(results)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
