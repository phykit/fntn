"""Covered calls on a two-stock pair: Monte Carlo theory check (tools/covered_call_pair_mc/PREREG.md).

Frozen implementation. Every constant, the draw order, the statistics and the checks are those of
the pre-registration, section by section; where a choice is made here it is because the
pre-registration made it first. The simulation is given its expected return by construction (the
volatility premium of section 4), so nothing it reports is a fact about markets.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

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
# Section 5: governor.
GOVERNOR = 0.9
# Section 6: jump arm.
P_J = 1.0 / 12.0
MU_J = -0.10
S_J = 0.05
RHO_D_GRID = [0.0, 0.3, 0.6, 0.9]
RHO_J_GRID = [0.0, 1.0]
# Section 7: size and seed.
N_PATHS = 2000
T = 120
SEED = 20261030
# Section 9: the halt and prediction threshold, in standard errors.
Z_BAR = 3.0


def ncdf(x: float) -> float:
    """Standard normal distribution function, N(x) = 0.5 * erfc(-x / sqrt(2)) (PREREG section 3)."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bs_call(m: float, v: float, r: float = R, dt: float = DT) -> float:
    """Black-Scholes call premium per unit of spot at strike m, vol v, rate r, time dt."""
    sq = v * math.sqrt(dt)
    d1 = (math.log(1.0 / m) + (r + 0.5 * v * v) * dt) / sq
    d2 = d1 - sq
    return ncdf(d1) - m * math.exp(-r * dt) * ncdf(d2)


def expected_payoff(m: float, mu: float = MU, sigma: float = SIGMA, dt: float = DT) -> float:
    """E[max(G - m, 0)] for lognormal G with E[G] = exp(mu dt) and log-sd sigma sqrt(dt) (section 3)."""
    sq = sigma * math.sqrt(dt)
    d1s = (math.log(1.0 / m) + (mu + 0.5 * sigma * sigma) * dt) / sq
    d2s = d1s - sq
    return math.exp(mu * dt) * ncdf(d1s) - m * ncdf(d2s)


def expected_overlay(m: float, v: float, mu: float = MU, sigma: float = SIGMA, r: float = R,
                     dt: float = DT) -> float:
    """Closed-form E[y] = c exp(r dt) - E[max(G - m, 0)]; independent of rho (section 3)."""
    return bs_call(m, v, r, dt) * math.exp(r * dt) - expected_payoff(m, mu, sigma, dt)


def implied_vol(arm: str, rho: float) -> float:
    """Section 4: what the market is assumed to charge, by arm."""
    if arm == "control":
        return SIGMA
    if arm == "A":
        return SIGMA * math.sqrt(1.0 + KAPPA)
    if arm == "B":
        return SIGMA * math.sqrt(1.0 + KAPPA * abs(rho))
    raise ValueError(arm)


def draws(n_paths: int = N_PATHS, t: int = T, seed: int = SEED) -> dict:
    """Section 7: the draws, in this order and these shapes, made once and reused by every cell.

    Draws 3 to 6 serve the jump arm only but are made regardless so that the stream is fixed."""
    rng = np.random.default_rng(seed)
    shape = (n_paths, t)
    d = {}
    d["Z1"] = rng.standard_normal(shape)
    d["Z2"] = rng.standard_normal(shape)
    d["U_MIX"] = rng.random(shape)
    d["U_C"] = rng.random(shape)
    d["J_C"] = rng.normal(MU_J, S_J, shape)
    d["U_1"] = rng.random(shape)
    d["J_1"] = rng.normal(MU_J, S_J, shape)
    d["U_2"] = rng.random(shape)
    d["J_2"] = rng.normal(MU_J, S_J, shape)
    return d


def base_returns(d: dict, rho: float) -> tuple[np.ndarray, np.ndarray]:
    """Section 2: gross monthly returns of the two legs at correlation rho, common random numbers."""
    eps1 = d["Z1"]
    eps2 = rho * d["Z1"] + math.sqrt(1.0 - rho * rho) * d["Z2"]
    drift = (MU - 0.5 * SIGMA * SIGMA) * DT
    scale = SIGMA * math.sqrt(DT)
    return np.exp(drift + scale * eps1), np.exp(drift + scale * eps2)


def jump_constants() -> tuple[float, float]:
    """Section 6: diffusive scale SD and level A such that total variance and mean are preserved."""
    vj = P_J * (S_J * S_J + MU_J * MU_J) - P_J * P_J * MU_J * MU_J
    vd = SIGMA * SIGMA * DT - vj
    sd = math.sqrt(vd)
    a = MU * DT - 0.5 * vd - math.log(1.0 - P_J + P_J * math.exp(MU_J + 0.5 * S_J * S_J))
    return sd, a


def jump_returns(d: dict, rho_d: float, rho_j: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Section 6: gross returns with a jump component; returns (G1, G2, both_jump)."""
    sd, a = jump_constants()
    eps1 = d["Z1"]
    eps2 = rho_d * d["Z1"] + math.sqrt(1.0 - rho_d * rho_d) * d["Z2"]
    mix = d["U_MIX"] < rho_j
    b_c = d["U_C"] < P_J
    b_1 = d["U_1"] < P_J
    b_2 = d["U_2"] < P_J
    jump1 = np.where(mix, b_c * d["J_C"], b_1 * d["J_1"])
    jump2 = np.where(mix, b_c * d["J_C"], b_2 * d["J_2"])
    both = np.where(mix, b_c, b_1 & b_2)
    g1 = np.exp(a + sd * eps1 + jump1)
    g2 = np.exp(a + sd * eps2 + jump2)
    return g1, g2, both


def max_drawdown_per_path(g: np.ndarray) -> np.ndarray:
    """Most negative drawdown of the compounded series from equity 1, against its running maximum."""
    equity = np.cumprod(1.0 + g, axis=1)
    peak = np.maximum.accumulate(np.maximum(equity, 1.0), axis=1)
    dd = equity / peak - 1.0
    return dd.min(axis=1)


def governor_mask(g_pair: np.ndarray, stock_pair: np.ndarray) -> np.ndarray:
    """Section 5, V2: written in month t iff E_(t-1) >= 0.9 P_(t-1); month 1 always written.

    The loop is over months only; paths are vectorised. The rule reads the joint history, which is
    the point of including it: under i.i.d. months the current month's returns are independent of
    the decision, so the mean over written months cannot depend on rho."""
    n_paths, t = g_pair.shape
    equity = np.ones(n_paths)
    peak = np.ones(n_paths)
    written = np.zeros((n_paths, t), dtype=bool)
    for k in range(t):
        w = equity >= GOVERNOR * peak if k > 0 else np.ones(n_paths, dtype=bool)
        written[:, k] = w
        q = np.where(w, g_pair[:, k], stock_pair[:, k])
        equity = equity * (1.0 + q)
        peak = np.maximum(peak, equity)
    return written


def cell_stats(g1: np.ndarray, g2: np.ndarray, m: float, v: float, written: np.ndarray | None = None,
               both_jump: np.ndarray | None = None) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    """Section 8 statistics for one cell. Returns (stats, ybar per path, y1, y2)."""
    c = bs_call(m, v) * math.exp(R * DT)
    y1 = c - np.maximum(g1 - m, 0.0)
    y2 = c - np.maximum(g2 - m, 0.0)
    y = 0.5 * (y1 + y2)
    gg1 = (g1 - 1.0) + y1
    gg2 = (g2 - 1.0) + y2
    g = 0.5 * (gg1 + gg2)
    n = y.size
    st = {
        "mean_y": float(y.mean()),
        "sd_y": float(y.std(ddof=1)),
        "mean_y1": float(y1.mean()),
        "mean_y2": float(y2.mean()),
        "mean_g": float(g.mean()),
        "sd_g": float(g.std(ddof=1)),
        "worst_g": float(g.min()),
        "assign_1": float((g1 > m).mean()),
        "assign_2": float((g2 > m).mean()),
        "assign_both": float(((g1 > m) & (g2 > m)).mean()),
        "n": int(n),
    }
    st["se_y"] = st["sd_y"] / math.sqrt(n)
    st["sharpe_y"] = st["mean_y"] / st["sd_y"]
    if written is None:
        mdd = max_drawdown_per_path(g)
        ybar = y.mean(axis=1)
    else:
        # V2: the equity path uses the plain pair stock return in unwritten months.
        stock_pair = 0.5 * ((g1 - 1.0) + (g2 - 1.0))
        q = np.where(written, g, stock_pair)
        mdd = max_drawdown_per_path(q)
        nw = int(written.sum())
        yw = y[written]
        st["frac_written"] = float(written.mean())
        st["n_written"] = nw
        st["mean_y_written"] = float(yw.mean())
        st["sd_y_written"] = float(yw.std(ddof=1))
        st["se_y_written"] = st["sd_y_written"] / math.sqrt(nw)
        # The per-path written-month mean is a ratio whose denominator depends on later writing
        # decisions; it is reported without weight (PREREG check 2 annotation).
        ybar = (y * written).sum(axis=1) / written.sum(axis=1)
    st["mdd_median"] = float(np.median(mdd))
    st["mdd_p05"] = float(np.percentile(mdd, 5))
    if both_jump is not None:
        st["frac_both_jump"] = float(both_jump.mean())
    return st, ybar, y1, y2


def paired(ybar_hi: np.ndarray, ybar_lo: np.ndarray) -> tuple[float, float, float]:
    """Section 9: D, SE_D, z_D from the per-path difference d_k = ybar_k(hi) - ybar_k(lo)."""
    dk = ybar_hi - ybar_lo
    D = float(dk.mean())
    se = float(dk.std(ddof=1) / math.sqrt(dk.size))
    return D, se, D / se


def ols_slope(x: list[float], yv: list[float]) -> float:
    xa = np.array(x)
    ya = np.array(yv)
    xc = xa - xa.mean()
    return float((xc * (ya - ya.mean())).sum() / (xc * xc).sum())


def analytic_ok(st: dict, m: float, v: float, written: np.ndarray | None, y1: np.ndarray,
                y2: np.ndarray) -> tuple[bool, str]:
    """Check 1: each leg's pooled mean within 3 SE of the closed form (over written months for V2)."""
    ey = expected_overlay(m, v)
    out = []
    ok = True
    for name, yl in (("y1", y1), ("y2", y2)):
        vals = yl[written] if written is not None else yl.ravel()
        se = vals.std(ddof=1) / math.sqrt(vals.size)
        z = (vals.mean() - ey) / se
        out.append(f"{name} z={z:+.2f}")
        ok = ok and abs(z) <= Z_BAR
    return ok, f"E[y]={ey:.6f} " + " ".join(out)


def simulate(out_dir: str) -> dict:
    d = draws()
    params = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float, list))}
    cells = []
    paired_list = []
    checks = {
        "check1_analytic": {"pass": True, "detail": []},
        "check2_theorem": {"pass": True, "detail": []},
        "check3_armB": {"pass": True, "detail": []},
        "check4_variance": {"pass": True, "detail": []},
        "check5_jump": {"pass": True, "detail": []},
    }
    thesis_hits = []
    # Base returns at each rho, computed once.
    base = {rho: base_returns(d, rho) for rho in RHO_GRID}
    for arm in ("control", "A", "B"):
        for m in M_GRID:
            for variant in ("V1", "V2"):
                if variant == "V2" and arm == "B":
                    continue
                ybars = {}
                means = []
                sds = []
                pooled_w = {}
                for rho in RHO_GRID:
                    g1, g2 = base[rho]
                    v = implied_vol(arm, rho)
                    written = None
                    if variant == "V2":
                        # The governor reads the written-every-month pair series to decide; its
                        # decision uses only past months, as section 5 defines.
                        c = bs_call(m, v) * math.exp(R * DT)
                        g_pair = 0.5 * (((g1 - 1.0) + c - np.maximum(g1 - m, 0.0))
                                        + ((g2 - 1.0) + c - np.maximum(g2 - m, 0.0)))
                        stock_pair = 0.5 * ((g1 - 1.0) + (g2 - 1.0))
                        written = governor_mask(g_pair, stock_pair)
                    st, ybar, y1, y2 = cell_stats(g1, g2, m, v, written)
                    ok, detail = analytic_ok(st, m, v, written, y1, y2)
                    tag = f"{arm} m={m:.2f} {variant} rho={rho:+.1f}"
                    checks["check1_analytic"]["detail"].append(f"{tag}: {detail}")
                    if not ok:
                        checks["check1_analytic"]["pass"] = False
                    cell = {"arm": arm, "m": m, "variant": variant, "rho": rho, "v": v}
                    cell.update(st)
                    cells.append(cell)
                    ybars[rho] = ybar
                    means.append(st["mean_y"])
                    sds.append(st["sd_y"])
                    if variant == "V2":
                        pooled_w[rho] = (st["mean_y_written"], st["se_y_written"])
                D, se, z = paired(ybars[1.0], ybars[-0.3])
                slope = ols_slope(RHO_GRID, means)
                entry = {"arm": arm, "m": m, "variant": variant, "D": D, "SE_D": se, "z_D": z,
                         "slope_y": slope}
                tag = f"{arm} m={m:.2f} {variant}"
                if variant == "V2":
                    # Check 2 under V2: the pooled written-month difference, with a standard
                    # error that ignores the common random numbers and so overstates the noise.
                    D2 = pooled_w[1.0][0] - pooled_w[-0.3][0]
                    SE2 = math.sqrt(pooled_w[1.0][1] ** 2 + pooled_w[-0.3][1] ** 2)
                    z2 = D2 / SE2
                    entry.update({"D2": D2, "SE2": SE2, "z2": z2})
                    hit = z2 <= -Z_BAR
                    if arm in ("control", "A"):
                        checks["check2_theorem"]["detail"].append(
                            f"{tag}: z2={z2:+.2f} (per-path z_D={z:+.2f}, no weight)")
                        if abs(z2) > Z_BAR:
                            checks["check2_theorem"]["pass"] = False
                else:
                    hit = z <= -Z_BAR
                    if arm in ("control", "A"):
                        checks["check2_theorem"]["detail"].append(f"{tag}: z_D={z:+.2f}")
                        if abs(z) > Z_BAR:
                            checks["check2_theorem"]["pass"] = False
                paired_list.append(entry)
                if arm == "B" and variant == "V1":
                    checks["check3_armB"]["detail"].append(f"{tag}: z_D={z:+.2f}")
                    if z < Z_BAR:
                        checks["check3_armB"]["pass"] = False
                if variant == "V1":
                    inc = all(sds[i] < sds[i + 1] for i in range(len(sds) - 1))
                    checks["check4_variance"]["detail"].append(
                        f"{tag}: sd_y " + " < ".join(f"{s:.5f}" for s in sds) + (" ok" if inc else " NOT increasing"))
                    if not inc:
                        checks["check4_variance"]["pass"] = False
                if hit:
                    thesis_hits.append(tag)
    # Jump arm.
    v_a = implied_vol("A", 1.0)
    for m in M_GRID:
        ybars = {}
        by_cell = {}
        for rho_d in RHO_D_GRID:
            for rho_j in RHO_J_GRID:
                g1, g2, both = jump_returns(d, rho_d, rho_j)
                st, ybar, _, _ = cell_stats(g1, g2, m, v_a, None, both)
                cell = {"arm": "jump", "m": m, "variant": "V1", "rho_d": rho_d, "rho_j": rho_j, "v": v_a}
                cell.update(st)
                cells.append(cell)
                ybars[(rho_d, rho_j)] = ybar
                by_cell[(rho_d, rho_j)] = st
        D, se, z = paired(ybars[(0.9, 1.0)], ybars[(0.0, 0.0)])
        paired_list.append({"arm": "jump", "m": m, "variant": "V1", "D": D, "SE_D": se, "z_D": z})
        tag = f"jump m={m:.2f}"
        checks["check5_jump"]["detail"].append(f"{tag}: z_J={z:+.2f}")
        if abs(z) > Z_BAR:
            checks["check5_jump"]["pass"] = False
            checks["check5_jump"]["detail"].append(f"{tag}: HALT, theorem violated")
        for rho_d in RHO_D_GRID:
            a0, a1 = by_cell[(rho_d, 0.0)], by_cell[(rho_d, 1.0)]
            worse = a1["mdd_p05"] <= a0["mdd_p05"] and a1["worst_g"] <= a0["worst_g"]
            checks["check5_jump"]["detail"].append(
                f"{tag} rho_d={rho_d:.1f}: mdd_p05 {a0['mdd_p05']:+.4f} -> {a1['mdd_p05']:+.4f}, "
                f"worst_g {a0['worst_g']:+.4f} -> {a1['worst_g']:+.4f}" + ("" if worse else " NOT worse"))
            if not worse:
                checks["check5_jump"]["pass"] = False
    halt = not (checks["check1_analytic"]["pass"] and checks["check2_theorem"]["pass"])
    halt = halt or any("HALT" in s for s in checks["check5_jump"]["detail"])
    if halt:
        verdict = "HALTED"
    elif thesis_hits:
        verdict = "SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"
    for k in checks:
        checks[k]["detail"] = "; ".join(checks[k]["detail"])
    res = {"params": params, "cells": cells, "paired": paired_list, "checks": checks,
           "verdict": verdict, "thesis_hits": thesis_hits}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    return res


def report(res: dict) -> None:
    print(f"{'arm':8}{'m':>6}{'var':>4}{'rho':>6}{'v':>7}{'mean_y':>10}{'sd_y':>9}{'sharpe':>8}"
          f"{'mean_g':>9}{'mdd_med':>9}{'mdd_p05':>9}{'written':>9}")
    for c in res["cells"]:
        if c["arm"] == "jump":
            continue
        print(f"{c['arm']:8}{c['m']:6.2f}{c['variant']:>4}{c['rho']:6.1f}{c['v']:7.4f}{c['mean_y']:10.5f}"
              f"{c['sd_y']:9.5f}{c['sharpe_y']:8.4f}{c['mean_g']:9.5f}{c['mdd_median']:9.4f}{c['mdd_p05']:9.4f}"
              f"{c.get('frac_written', float('nan')):9.3f}")
    print(f"{'jump':8}{'m':>6}{'rho_d':>6}{'rho_j':>6}{'mean_y':>10}{'sd_y':>9}{'worst_g':>9}{'mdd_p05':>9}{'both':>7}")
    for c in res["cells"]:
        if c["arm"] != "jump":
            continue
        print(f"{'':8}{c['m']:6.2f}{c['rho_d']:6.1f}{c['rho_j']:6.1f}{c['mean_y']:10.5f}{c['sd_y']:9.5f}"
              f"{c['worst_g']:9.4f}{c['mdd_p05']:9.4f}{c['frac_both_jump']:7.4f}")
    print("paired differences, rho 1.0 minus rho -0.3 (jump: (0.9,1) minus (0,0)):")
    for p in res["paired"]:
        print(f"  {p['arm']:8} m={p['m']:.2f} {p['variant']}  D={p['D']:+.6f}  SE={p['SE_D']:.6f}  z_D={p['z_D']:+.2f}"
              + (f"  slope_y={p['slope_y']:+.6f}" if "slope_y" in p else "")
              + (f"  pooled D2={p['D2']:+.6f} z2={p['z2']:+.2f}" if "z2" in p else ""))
    for k, v in res["checks"].items():
        print(("ok   " if v["pass"] else "FAIL ") + k + ": " + v["detail"])
    print("VERDICT:", res["verdict"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = simulate(a.out)
    report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
