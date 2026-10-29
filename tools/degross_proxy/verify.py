#!/usr/bin/env python3
"""Independent second implementation of PREREG.md (degross proxy), sections 3 to 6.

Written from the specification alone. Standard library and numpy only.

Usage: python verify.py --data DATA_DIR --out OUT_DIR
"""
import argparse
import csv
import datetime as dt
import json
import math
import os

import numpy as np

SEED = 20261029
N_PERM = 10000
REFERENCES = ["2021-01-29", "2026-05-01", "2026-10-16"]


# ---------------------------------------------------------------- input
def _read_csv(path):
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    body = [r for r in rows[1:] if r and r[0].strip()]
    return header, body


def _val(s):
    s = s.strip()
    if s == "" or s == ".":
        return None
    return float(s)


def load_french(data_dir):
    _, mom = _read_csv(os.path.join(data_dir, "mom10_daily.csv"))
    _, ff = _read_csv(os.path.join(data_dir, "ff3_daily.csv"))
    m_by_date = {}
    for r in ff:
        mkt, rf = _val(r[1]), _val(r[4])
        if mkt is None or rf is None:
            continue
        m_by_date[r[0].strip()] = (mkt + rf) / 100.0
    dates, L, W, M = [], [], [], []
    for r in mom:
        d = r[0].strip()
        lo, hi = _val(r[1]), _val(r[-1])  # first and last value columns, by position
        if lo is None or hi is None or d not in m_by_date:
            continue
        dates.append(dt.date.fromisoformat(d))
        L.append(lo / 100.0)
        W.append(hi / 100.0)
        M.append(m_by_date[d])
    order = np.argsort(np.array([d.toordinal() for d in dates]), kind="stable")
    dates = [dates[i] for i in order]
    return dates, np.array(L)[order], np.array(W)[order], np.array(M)[order]


def load_ndx(data_dir):
    _, body = _read_csv(os.path.join(data_dir, "ndx.csv"))
    dates, vals = [], []
    for r in body:
        v = _val(r[1])
        if v is None:
            continue
        dates.append(dt.date.fromisoformat(r[0].strip()))
        vals.append(v)
    order = np.argsort(np.array([d.toordinal() for d in dates]), kind="stable")
    return [dates[i] for i in order], np.array(vals, dtype=float)[order]


# ---------------------------------------------------------------- section 3
def weekly(dates, L, W, M):
    """Group French days by ISO (year, week); compound; week end = last day."""
    keys = [d.isocalendar()[:2] for d in dates]
    weeks = []  # list of (end_date, end_day_index, start_idx, end_idx)
    start = 0
    for i in range(1, len(dates) + 1):
        if i == len(dates) or keys[i] != keys[start]:
            weeks.append((start, i))
            start = i
    n = len(weeks)
    Wt, Lt, Mt = np.empty(n), np.empty(n), np.empty(n)
    e, eidx = [], np.empty(n, dtype=int)
    for t, (a, b) in enumerate(weeks):
        Wt[t] = np.prod(1.0 + W[a:b]) - 1.0
        Lt[t] = np.prod(1.0 + L[a:b]) - 1.0
        Mt[t] = np.prod(1.0 + M[a:b]) - 1.0
        e.append(dates[b - 1])
        eidx[t] = b - 1
    return e, eidx, Wt, Lt, Mt


def _slope(x, y):
    xm, ym = x.mean(), y.mean()
    return float(np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2))


def signals(Wt, Lt, Mt):
    n = len(Wt)
    nan = np.full(n, np.nan)
    rW, rL, P = nan.copy(), nan.copy(), nan.copy()
    for t in range(52, n):
        bW = _slope(Mt[t - 52:t], Wt[t - 52:t])
        bL = _slope(Mt[t - 52:t], Lt[t - 52:t])
        rW[t] = Wt[t] - bW * Mt[t]
        rL[t] = Lt[t] - bL * Mt[t]
        P[t] = rW[t] - rL[t]
    z = nan.copy()
    for t in range(n):
        if t - 156 < 0 or np.isnan(P[t]):
            continue
        win = P[t - 156:t]
        if np.isnan(win).any():
            continue
        sd = np.std(win, ddof=1)
        if sd > 0:
            z[t] = (P[t] - win.mean()) / sd
    S = nan.copy()
    for t in range(n):
        if t - 26 < 0:
            continue
        win = P[t - 26:t]
        if not np.isnan(win).any():
            S[t] = win.sum()
    Cdef = np.zeros(n, dtype=bool)
    C = np.zeros(n, dtype=bool)
    for t in range(n):
        if t - 260 < 0 or np.isnan(S[t]):
            continue
        win = S[t - 260:t]
        if np.isnan(win).any():
            continue
        Cdef[t] = True
        C[t] = bool(S[t] >= np.percentile(win, 90))
    sig_eval = (~np.isnan(z)) & Cdef
    # Amended spec (section 3, section 9 item 5): sign conditions on RAW weekly returns,
    # so that a rebound week (winners up but lagging beta) cannot pass via a negative residual.
    with np.errstate(invalid="ignore"):
        D_full = (z <= -2.0) & (Wt < 0) & (Lt > 0)
        D_z = z <= -2.0
    D_full &= sig_eval
    D_z &= sig_eval
    return dict(rW=rW, rL=rL, P=P, z=z, S=S, C=C, sig_eval=sig_eval,
                D_full=D_full, D_z=D_z)


# ---------------------------------------------------------------- section 4
def gate(e, sig, last_french):
    refs = [dt.date.fromisoformat(r) for r in REFERENCES]
    available = [r for r in refs if r <= last_french]
    se = sig["sig_eval"]
    D = sig["D_full"]
    dweeks = [e[t] for t in range(len(e)) if se[t] and D[t]]
    matched = [r for r in available
               if any(abs((d - r).days) <= 7 for d in dweeks)]
    n_se = int(se.sum())
    b = float(D[se].mean()) if n_se else float("nan")
    if len(available) < 2:
        status = "UNTESTABLE"
    elif len(matched) >= 2 and b <= 0.05:
        status = "PASS"
    else:
        status = "FAIL"
    # information only: P(at least observed matches | random D at rate b, 3-week windows)
    chance = None
    if n_se and available:
        q = 1.0 - (1.0 - b) ** 3
        na, m = len(available), len(matched)
        chance = sum(math.comb(na, k) * q ** k * (1 - q) ** (na - k)
                     for k in range(m, na + 1))
    return {"status": status,
            "available": [r.isoformat() for r in available],
            "matched": [r.isoformat() for r in matched],
            "base_rate": b,
            "n_signal_evaluable": n_se,
            "last_french_date": last_french.isoformat(),
            "chance_info_only": chance}


# ---------------------------------------------------------------- section 3/5
def drawdown(N, i, H):
    seg = N[i:i + H + 1]
    runmax = np.maximum.accumulate(seg)
    return float(np.min(seg[1:] / runmax[1:]) - 1.0)


def outcome_test(e, sig, D, idx_dates, N, i_of_week, H, thr, start_date=None):
    """Generic section 5 test.

    idx_dates: dates of the outcome index; N: its levels;
    i_of_week(t) -> index position or None.
    """
    n_idx = len(N)
    T = D & sig["C"] & sig["sig_eval"]
    rows = []  # (t, i, E, DD, R21, T)
    for t in range(len(e)):
        if not sig["sig_eval"][t]:
            continue
        if start_date is not None and e[t] < start_date:
            continue
        if e[t] < idx_dates[0]:
            continue
        i = i_of_week(t)
        if i is None or i + 63 >= n_idx:  # N(i+63) must exist (outcome-evaluable)
            continue
        if i + H >= n_idx:
            continue
        if i < 21:  # R21 undefined: dropped from the outcome test
            continue
        dd = drawdown(N, i, H)
        rows.append((t, i, dd <= thr, dd, N[i] / N[i - 21] - 1.0, bool(T[t])))
    if not rows:
        return None
    R21 = np.array([r[4] for r in rows])
    Ev = np.array([r[2] for r in rows], dtype=float)
    Tv = np.array([r[5] for r in rows])
    c1, c2 = np.percentile(R21, [100.0 / 3.0, 200.0 / 3.0])
    strat = np.where(R21 < c1, 0, np.where(R21 >= c2, 2, 1))

    # episodes
    episodes = []  # row indices of first trigger
    i_start = None
    for k, r in enumerate(rows):
        if not r[5]:
            continue
        if i_start is not None and r[1] - i_start <= 63:
            continue
        episodes.append(k)
        i_start = r[1]
    n = len(episodes)
    others = ~Tv
    E_O = float(Ev[others].mean()) if others.any() else float("nan")
    E_T = float(Ev[episodes].mean()) if n else float("nan")
    delta = E_T - E_O if n else float("nan")

    p = None
    if n:
        rng = np.random.default_rng(SEED)
        pools = {s: Ev[others & (strat == s)].tolist() for s in (0, 1, 2)}
        ep_strata = [int(strat[k]) for k in episodes]
        count = 0
        for _ in range(N_PERM):
            avail = {s: list(v) for s, v in pools.items()}
            tot = 0.0
            for s in ep_strata:
                pool = avail[s]
                if not pool:
                    raise RuntimeError("stratum %d ran out of placebo weeks" % s)
                j = int(rng.integers(len(pool)))
                tot += pool[j]
                pool[j] = pool[-1]
                pool.pop()
            if tot / n - E_O >= delta:
                count += 1
        p = (1 + count) / (1 + N_PERM)

    if n < 8:
        verdict = "INSUFFICIENT"
    elif p <= 0.05 and delta >= 0.10:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"n_episodes": n, "E_T": E_T, "E_O": E_O, "delta": delta, "p": p,
            "verdict": verdict,
            "n_outcome_evaluable": len(rows),
            "n_triggered_weeks": int(Tv.sum()),
            "tercile_cuts": [float(c1), float(c2)],
            "episodes": [{"date": e[rows[k][0]].isoformat(), "E": bool(rows[k][2]),
                          "DD": rows[k][3], "stratum": int(strat[k])}
                         for k in episodes]}


def run(data_dir, force_gate=False):
    dates, L, W, M = load_french(data_dir)
    e, eidx, Wt, Lt, Mt = weekly(dates, L, W, M)
    sig = signals(Wt, Lt, Mt)
    g = gate(e, sig, dates[-1])
    out = {"gate": g, "primary": None, "secondary_21d_5pct": None,
           "secondary_no_sign_filter": None, "secondary_french_market": None}
    if g["status"] != "PASS" and not force_gate:
        return out, sig, e
    if force_gate:
        out["gate_forced"] = True

    ndx_dates, N = load_ndx(data_dir)
    ndx_ord = np.array([d.toordinal() for d in ndx_dates])

    def i_ndx(t):
        i = int(np.searchsorted(ndx_ord, e[t].toordinal(), side="right")) - 1
        return i if i >= 0 else None

    out["primary"] = outcome_test(e, sig, sig["D_full"], ndx_dates, N, i_ndx, 63, -0.10)
    out["secondary_21d_5pct"] = outcome_test(e, sig, sig["D_full"], ndx_dates, N, i_ndx,
                                             21, -0.05)
    out["secondary_no_sign_filter"] = outcome_test(e, sig, sig["D_z"], ndx_dates, N,
                                                   i_ndx, 63, -0.10)
    F = np.cumprod(1.0 + M)
    out["secondary_french_market"] = outcome_test(
        e, sig, sig["D_full"], dates, F, lambda t: int(eidx[t]), 63, -0.10,
        start_date=dt.date(1927, 1, 1))
    return out, sig, e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--force-gate", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    out, _, _ = run(a.data, a.force_gate)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: (v if k == "gate" else (None if v is None else
                     {kk: v[kk] for kk in ("n_episodes", "E_T", "E_O", "delta", "p", "verdict")}))
                      for k, v in out.items() if k != "gate_forced"}, indent=1))


if __name__ == "__main__":
    main()
