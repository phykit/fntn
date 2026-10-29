"""Frozen test: a price-implied de-grossing proxy as a warning of Nasdaq 100 drawdowns.

NON-EVIDENTIARY side test outside the FNTN funnel. The specification is PREREG.md in this
directory and it governs; this file implements it and nothing else. The gate (PREREG section 4) is
evaluated and written BEFORE any outcome is computed, and on anything but a gate PASS no outcome is
computed at all, because an outcome read after a failed gate would be an outcome read on a proxy
already shown not to measure the mechanism.

Usage: python run.py --data DATA_DIR --out OUT_DIR
Writes OUT_DIR/results.json. Prints derived statistics only, never an input value.
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
Z_WIN = 156
S_WIN = 26
PCT_WIN = 260
EPISODE_GAP = 63


# ---------------------------------------------------------------- loading

def _read(path):
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def _num(s):
    s = s.strip()
    return float(s) if s != "" else None


def load_french(data):
    """Daily L, W, M as fractions, on days where all three are present."""
    _, mrows = _read(os.path.join(data, "mom10_daily.csv"))
    _, frows = _read(os.path.join(data, "ff3_daily.csv"))
    mom = {}
    for r in mrows:
        lo, hi = _num(r[1]), _num(r[-1])
        mom[r[0]] = (lo, hi)
    ff = {}
    for r in frows:
        mkt, rf = _num(r[1]), _num(r[4])
        ff[r[0]] = (mkt, rf)
    days, L, W, M = [], [], [], []
    for d in sorted(set(mom) & set(ff)):
        lo, hi = mom[d]
        mkt, rf = ff[d]
        if lo is None or hi is None or mkt is None or rf is None:
            continue
        days.append(dt.date.fromisoformat(d))
        L.append(lo / 100.0)
        W.append(hi / 100.0)
        M.append((mkt + rf) / 100.0)
    return days, np.array(W), np.array(L), np.array(M)


def load_ndx(data):
    _, rows = _read(os.path.join(data, "ndx.csv"))
    days, px = [], []
    for r in rows:
        v = _num(r[1])
        if v is None:
            continue
        days.append(dt.date.fromisoformat(r[0]))
        px.append(v)
    order = np.argsort(np.array([d.toordinal() for d in days]))
    return [days[i] for i in order], np.array(px)[order]


# ---------------------------------------------------------------- weekly signals

def to_weekly(days, W, L, M):
    keys = [d.isocalendar()[:2] for d in days]
    ends, Ww, Lw, Mw = [], [], [], []
    i = 0
    n = len(days)
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        sl = slice(i, j + 1)
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
        bw = _slope(Ww[t - BETA_WIN:t], Mw[t - BETA_WIN:t])
        bl = _slope(Lw[t - BETA_WIN:t], Mw[t - BETA_WIN:t])
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
    D = sig_eval & (zl <= -2.0) & (Ww < 0) & (Lw > 0)
    D_nosign = sig_eval & (zl <= -2.0)
    return {"rW": rW, "rL": rL, "P": P, "z": z, "S": S, "C": C & sig_eval,
            "sig_eval": sig_eval, "D": D, "D_nosign": D_nosign}


# ---------------------------------------------------------------- gate

def gate(ends, D, sig_eval, last_french):
    available = [r for r in REFS if r <= last_french]
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
            "n_signal_evaluable": n_eval, "last_french_date": last_french.isoformat(),
            "chance_of_at_least_matched": chance}


# ---------------------------------------------------------------- outcome and test

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

    days, W, L, M = load_french(a.data)
    ends, Ww, Lw, Mw = to_weekly(days, W, L, M)
    sg = signals(Ww, Lw, Mw)
    print(f"french days {len(days)}, weeks {len(ends)}, first {days[0]}, last {days[-1]}")
    g = gate(ends, sg["D"], sg["sig_eval"], days[-1])
    out = {"gate": g, "primary": None, "secondary_21d_5pct": None,
           "secondary_no_sign_filter": None, "secondary_french_market": None}
    print("GATE:", json.dumps(g))
    # D weeks near each reference, for the record
    out["gate"]["d_weeks_near_refs"] = {
        r.isoformat(): [ends[t].isoformat() for t in range(len(ends))
                        if sg["sig_eval"][t] and abs((ends[t] - r).days) <= 21 and sg["D"][t]]
        for r in REFS}
    out["gate"]["z_near_refs"] = {
        r.isoformat(): [[ends[t].isoformat(), round(float(sg["z"][t]), 3),
                         round(float(sg["rW"][t]), 5), round(float(sg["rL"][t]), 5)]
                        for t in range(len(ends)) if sg["sig_eval"][t] and abs((ends[t] - r).days) <= 10]
        for r in REFS}
    with open(os.path.join(a.out, "gate.json"), "w") as fh:
        json.dump(out["gate"], fh, indent=1)
    if g["status"] != "PASS":
        out["verdict"] = f"CLOSED (gate {g['status']})"
        print("VERDICT:", out["verdict"], "- no outcome computed")
        with open(os.path.join(a.out, "results.json"), "w") as fh:
            json.dump(out, fh, indent=1)
        return 0

    ndays, npx = load_ndx(a.data)
    print(f"ndx days {len(ndays)}, first {ndays[0]}, last {ndays[-1]}")
    T = sg["D"] & sg["C"]
    out["primary"] = outcome_test(ends, T, sg["sig_eval"], ndays, npx, 63, -0.10)
    out["secondary_21d_5pct"] = outcome_test(ends, T, sg["sig_eval"], ndays, npx, 21, -0.05)
    T2 = sg["D_nosign"] & sg["C"]
    out["secondary_no_sign_filter"] = outcome_test(ends, T2, sg["sig_eval"], ndays, npx, 63, -0.10)
    mkt = np.cumprod(1 + M)
    out["secondary_french_market"] = outcome_test(ends, T, sg["sig_eval"], days, mkt, 63, -0.10)
    out["verdict"] = out["primary"]["verdict"]
    for k in ("primary", "secondary_21d_5pct", "secondary_no_sign_filter", "secondary_french_market"):
        r = out[k]
        print(f"{k}: n={r['n_episodes']} E_T={r['E_T']:.4f} E_O={r['E_O']:.4f} "
              f"delta={r['delta']:.4f} p={r['p']:.4f} verdict={r['verdict']}")
    print("VERDICT:", out["verdict"])
    with open(os.path.join(a.out, "results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
