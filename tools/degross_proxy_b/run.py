"""Frozen test, Version B: the de-gross proxy built from hedge-fund 13F baskets.

NON-EVIDENTIARY side test outside the FNTN funnel. PREREG.md in this directory governs, with
Version A's PREREG.md where it carries rules over. gate() and outcome_test() are Version A's code
verbatim (apart from the gate's date-field name); the windows and the basket returns are B's. The
gate is written before any outcome is computed, and on anything but PASS no outcome is computed.

Usage: python run.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

SEED = 20261029
N_PERM = 10_000
REFS = [dt.date(2021, 1, 29), dt.date(2026, 5, 1), dt.date(2026, 10, 16)]
BETA_WIN = 52
Z_WIN = 104
S_WIN = 13
PCT_WIN = 104
EPISODE_GAP = 63


def load_prices(data):
    with open(os.path.join(data, "prices.csv"), newline="") as fh:
        rows = list(csv.reader(fh))
    head = rows[0][1:]
    days, vals = [], []
    for r in rows[1:]:
        if not r[1].strip():
            continue
        days.append(dt.date.fromisoformat(r[0]))
        vals.append([float(v) if v.strip() else np.nan for v in r[1:]])
    return days, {s: i for i, s in enumerate(head)}, np.array(vals)


def load_baskets(data):
    bk = {}
    with open(os.path.join(data, "baskets.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            e = dt.date.fromisoformat(r["effective"])
            bk.setdefault(e, {"long": [], "short": []})[r["leg"]].append(r["symbol"])
    return bk


def load_ndx(data):
    with open(os.path.join(data, "ndx.csv"), newline="") as fh:
        rows = list(csv.reader(fh))[1:]
    pairs = sorted((dt.date.fromisoformat(r[0]), float(r[1])) for r in rows if r[1].strip())
    return [p[0] for p in pairs], np.array([p[1] for p in pairs])


def daily_legs(days, col, px, bk):
    """Section 4: equal-weighted daily basket returns; NaN where no basket earns."""
    n = len(days)
    ret = px[1:] / px[:-1] - 1  # ret[k] is the return on day k+1
    W = np.full(n, np.nan)
    L = np.full(n, np.nan)
    M = np.full(n, np.nan)
    M[1:] = ret[:, col["SPY"]]
    effs = sorted(bk)
    pos = {d: i for i, d in enumerate(days)}
    coverage = []
    for k, e in enumerate(effs):
        if e not in pos:
            continue
        i0 = pos[e]
        i1 = pos[effs[k + 1]] if k + 1 < len(effs) and effs[k + 1] in pos else n - 1
        cov = {"effective": e.isoformat()}
        for leg, arr in (("long", W), ("short", L)):
            syms = [s for s in bk[e][leg] if s in col and not np.isnan(px[i0, col[s]])]
            cov[f"{leg}_listed"] = len(bk[e][leg])
            cov[f"{leg}_entered"] = len(syms)
            if not syms:
                continue
            idx = [col[s] for s in syms]
            for d in range(i0 + 1, i1 + 1):
                r = ret[d - 1, idx]
                r = r[~np.isnan(r)]
                if len(r):
                    arr[d] = r.mean()
        coverage.append(cov)
    return W, L, M, coverage


def to_weekly(days, W, L, M):
    keys = [d.isocalendar()[:2] for d in days]
    ends, Ww, Lw, Mw = [], [], [], []
    i, n = 0, len(days)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        sl = slice(i, j + 1)
        if np.isnan(W[sl]).any() or np.isnan(L[sl]).any() or np.isnan(M[sl]).any():
            Ww.append(np.nan); Lw.append(np.nan); Mw.append(np.nan)
        else:
            Ww.append(np.prod(1 + W[sl]) - 1)
            Lw.append(np.prod(1 + L[sl]) - 1)
            Mw.append(np.prod(1 + M[sl]) - 1)
        ends.append(days[j])
        i = j + 1
    return ends, np.array(Ww), np.array(Lw), np.array(Mw)


def _slope(y, x):
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef[1]


def signals(Ww, Lw, Mw):
    n = len(Ww)
    nan = np.full(n, np.nan)
    rW, rL, P, z, S = nan.copy(), nan.copy(), nan.copy(), nan.copy(), nan.copy()
    for t in range(BETA_WIN, n):
        w, l, m = Ww[t - BETA_WIN:t], Lw[t - BETA_WIN:t], Mw[t - BETA_WIN:t]
        if np.isnan(w).any() or np.isnan(l).any() or np.isnan(m).any() or np.isnan(Ww[t]) or np.isnan(Lw[t]) or np.isnan(Mw[t]):
            continue
        bw, bl = _slope(w, m), _slope(l, m)
        rW[t] = Ww[t] - bw * Mw[t]
        rL[t] = Lw[t] - bl * Mw[t]
        P[t] = rW[t] - rL[t]
    for t in range(n):
        if t - Z_WIN >= 0:
            win = P[t - Z_WIN:t]
            if not np.isnan(win).any() and not np.isnan(P[t]):
                z[t] = (P[t] - win.mean()) / win.std(ddof=1)
        if t - S_WIN >= 0:
            win = P[t - S_WIN:t]
            if not np.isnan(win).any():
                S[t] = win.sum()
    C = np.zeros(n, bool)
    c_def = np.zeros(n, bool)
    for t in range(n):
        if t - PCT_WIN >= 0 and not np.isnan(S[t]):
            win = S[t - PCT_WIN:t]
            if not np.isnan(win).any():
                c_def[t] = True
                C[t] = S[t] >= np.percentile(win, 90)
    sig_eval = c_def & ~np.isnan(z)
    zl = np.where(np.isnan(z), np.inf, z)
    D = sig_eval & (zl <= -2.0) & (np.nan_to_num(Ww, nan=0.0) < 0) & (np.nan_to_num(Lw, nan=0.0) > 0)
    D_nosign = sig_eval & (zl <= -2.0)
    return {"rW": rW, "rL": rL, "P": P, "z": z, "S": S, "C": C & sig_eval,
            "sig_eval": sig_eval, "D": D, "D_nosign": D_nosign}


# ---------------------------------------------------------------- gate (Version A verbatim)

def gate(ends, D, sig_eval, last_week_end):
    available = [r for r in REFS if r <= last_week_end]
    d_dates = [ends[t] for t in range(len(ends)) if D[t]]
    matched = [r for r in available if any(abs((e - r).days) <= 7 for e in d_dates)]
    n_eval = int(sig_eval.sum())
    b = float(D.sum() / n_eval) if n_eval else float("nan")
    if len(available) < 2:
        status = "UNTESTABLE"
    elif len(matched) >= 2 and b <= 0.05:
        status = "PASS"
    else:
        status = "FAIL"
    q = 1 - (1 - b) ** 3 if n_eval else float("nan")
    a, m = len(available), len(matched)
    chance = sum(math.comb(a, k) * q ** k * (1 - q) ** (a - k) for k in range(m, a + 1)) if a else float("nan")
    return {"status": status, "available": [r.isoformat() for r in available],
            "matched": [r.isoformat() for r in matched], "base_rate": b,
            "n_signal_evaluable": n_eval, "last_week_end": last_week_end.isoformat(),
            "chance_of_at_least_matched": chance}


# ---------------------------------------------------------------- outcome and test (Version A verbatim)

def outcome_test(ends, trig, sig_eval, px_days, px, window, thresh, seed=SEED, n_perm=N_PERM):
    """Section 3 outcome, episodes and section 5 permutation on one price series."""
    ords = np.array([d.toordinal() for d in px_days])
    n = len(ends)
    first = px_days[0]
    i_t = np.full(n, -1)
    E = np.zeros(n, bool)
    DD = np.full(n, np.nan)
    R21 = np.full(n, np.nan)
    oe = np.zeros(n, bool)
    for t in range(n):
        if not sig_eval[t] or ends[t] < first:
            continue
        i = int(np.searchsorted(ords, ends[t].toordinal(), side="right") - 1)
        if i < 0 or i + EPISODE_GAP >= len(px) or i + window >= len(px) or i < 21:
            continue
        seg = px[i:i + window + 1]
        runmax = np.maximum.accumulate(seg)
        DD[t] = float(np.min(seg[1:] / runmax[1:]) - 1)
        E[t] = DD[t] <= thresh
        R21[t] = px[i] / px[i - 21] - 1
        i_t[t] = i
        oe[t] = True
    # episodes
    episodes = []
    start_i = None
    for t in range(n):
        if oe[t] and trig[t]:
            if start_i is None or i_t[t] - start_i > EPISODE_GAP:
                episodes.append(t)
                start_i = i_t[t]
    untrig = np.where(oe & ~trig)[0]
    E_O = float(E[untrig].mean()) if len(untrig) else float("nan")
    ne = len(episodes)
    res = {"n_episodes": ne, "n_outcome_evaluable": int(oe.sum()),
           "E_O": E_O, "episodes": [{"date": ends[t].isoformat(), "E": bool(E[t]), "DD": float(DD[t])}
                                     for t in episodes]}
    if ne == 0:
        res.update({"E_T": float("nan"), "delta": float("nan"), "p": float("nan"), "verdict": "INSUFFICIENT"})
        return res
    E_T = float(E[episodes].mean())
    delta = E_T - E_O
    vals = R21[oe]
    c1, c2 = np.percentile(vals, 100 / 3), np.percentile(vals, 200 / 3)

    def stratum(x):
        return 0 if x < c1 else (2 if x >= c2 else 1)

    strata = np.array([stratum(R21[t]) for t in untrig])
    pools = {s: untrig[strata == s] for s in (0, 1, 2)}
    ep_strata = [stratum(R21[t]) for t in episodes]
    need = {s: ep_strata.count(s) for s in (0, 1, 2)}
    for s in (0, 1, 2):
        if need[s] > len(pools[s]):
            raise RuntimeError(f"stratum {s} runs out: need {need[s]}, have {len(pools[s])}")
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        tot = 0
        for s in (0, 1, 2):
            if need[s]:
                pick = rng.choice(pools[s], size=need[s], replace=False)
                tot += int(E[pick].sum())
        if tot / ne - E_O >= delta:
            count += 1
    p = (1 + count) / (1 + n_perm)
    if ne < 8:
        verdict = "INSUFFICIENT"
    elif p <= 0.05 and delta >= 0.10:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    res.update({"E_T": E_T, "delta": delta, "p": p, "verdict": verdict,
                "tercile_cuts": [float(c1), float(c2)]})
    return res


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    days, col, px = load_prices(a.data)
    bk = load_baskets(a.data)
    W, L, M, coverage = daily_legs(days, col, px, bk)
    ends, Ww, Lw, Mw = to_weekly(days, W, L, M)
    sg = signals(Ww, Lw, Mw)
    print(f"spy days {len(days)}, weeks {len(ends)}, baskets {len(bk)}, signal-evaluable weeks {int(sg['sig_eval'].sum())}")
    first_eval = next((ends[t] for t in range(len(ends)) if sg["sig_eval"][t]), None)
    g = gate(ends, sg["D"], sg["sig_eval"], ends[-1])
    g["first_signal_evaluable_week"] = first_eval.isoformat() if first_eval else None
    g["z_near_refs"] = {
        r.isoformat(): [[ends[t].isoformat(), None if np.isnan(sg["z"][t]) else round(float(sg["z"][t]), 3),
                         None if np.isnan(Ww[t]) else round(float(Ww[t]), 5),
                         None if np.isnan(Lw[t]) else round(float(Lw[t]), 5)]
                        for t in range(len(ends)) if abs((ends[t] - r).days) <= 10]
        for r in REFS}
    out = {"gate": g, "coverage": coverage, "primary": None, "secondary_21d_5pct": None,
           "secondary_no_sign_filter": None}
    print("GATE:", json.dumps({k: g[k] for k in ("status", "available", "matched", "base_rate", "n_signal_evaluable")}))
    for r, v in g["z_near_refs"].items():
        print("  near", r, v)
    with open(os.path.join(a.out, "gate.json"), "w") as fh:
        json.dump(g, fh, indent=1)
    if g["status"] != "PASS":
        out["verdict"] = f"CLOSED (gate {g['status']})"
        print("VERDICT:", out["verdict"], "- no outcome computed")
        with open(os.path.join(a.out, "results.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        return 0
    ndays, npx = load_ndx(a.data)
    T = sg["D"] & sg["C"]
    out["primary"] = outcome_test(ends, T, sg["sig_eval"], ndays, npx, 63, -0.10)
    out["secondary_21d_5pct"] = outcome_test(ends, T, sg["sig_eval"], ndays, npx, 21, -0.05)
    out["secondary_no_sign_filter"] = outcome_test(ends, sg["D_nosign"] & sg["C"], sg["sig_eval"], ndays, npx, 63, -0.10)
    out["verdict"] = out["primary"]["verdict"]
    for k in ("primary", "secondary_21d_5pct", "secondary_no_sign_filter"):
        r = out[k]
        print(f"{k}: n={r['n_episodes']} E_T={r['E_T']} E_O={r['E_O']:.4f} delta={r['delta']} p={r['p']} verdict={r['verdict']}")
    print("VERDICT:", out["verdict"])
    with open(os.path.join(a.out, "results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
