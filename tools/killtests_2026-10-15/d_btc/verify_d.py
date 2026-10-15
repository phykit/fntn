#!/usr/bin/env python3
"""Independent second implementation of pre-registration D (PREREG.md, sections 3, 4, 5, 7).

Written from PREREG.md alone, without sight of run_d.py or kt.py, so that every criterion figure
can be compared on the runner. Standard library and numpy only.

Usage: python verify_d.py --data data --out out

Readings taken where the specification admits more than one (the most literal reading is used):

  A1. Section 5's out-of-sample positions (t >= 750, fit on 0..t-5 inclusive) are counted WITHIN
      the aligned sample of {M, n1, n5, n20, R_5}, as section 5 now states explicitly (amended
      before freezing). An earlier draft of this script read them as joint-calendar positions;
      that reading is withdrawn.
  A2. r_t is undefined where no numeric tbill RATE exists on or before date_t; M_t is then
      undefined and the day drops out of every aligned sample. No rate is assumed.
  A3. Expiry months run from the first joint date's month to the month after the last joint
      date's month inclusive. The exclusion window k_X-4..k_X+1 is clipped to 0..N-1.
  A4. The rotation regresses y on x rotated circularly by k positions (np.roll); the shift set
      21..m-21 is symmetric under k -> m-k, so the direction of rotation does not matter. The
      rotated slope uses the same closed-form OLS slope as the observed one.
  A5. Newey-West S is the unnormalised sum Gamma_0 + sum_l w_l (Gamma_l + Gamma_l'), which with
      the unnormalised (X'X)^-1 on either side is the stated sandwich with no d.o.f. correction.
      The Clark-West t is the Newey-West t of the mean (regression on a constant).
  A6. Halves, size and the primary slope all use the h = 5 aligned sample of {M, R_5}.
  A7. When s = 0, Dq = 0 as stated; Q and n_top are still reported as computed on s x M.
  A8. UNSCORABLE (m_5 - 41 < 100) sets every criterion to false; the statistics are still
      reported where computable.
  A9. A day is on the joint calendar only if both CLOSE fields parse as finite numbers; empty,
      "." or unparseable fields are missing. Duplicate dates in an input file raise.
"""

import argparse
import calendar
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np


# ---------------------------------------------------------------- input

def _num(s):
    s = (s or "").strip()
    if s == "" or s == ".":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def read_series(path, field):
    out = {}
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames is None or "DATE" not in rd.fieldnames or field not in rd.fieldnames:
            raise SystemExit(f"{path}: header must contain DATE and {field}, got {rd.fieldnames}")
        for row in rd:
            ds = (row["DATE"] or "").strip()
            if not ds:
                continue
            d = dt.date.fromisoformat(ds[:10])
            if d in out:
                raise SystemExit(f"{path}: duplicate date {d}")
            out[d] = _num(row[field])
    return out


# ---------------------------------------------------------------- calendar

def last_friday(y, mth):
    last = dt.date(y, mth, calendar.monthrange(y, mth)[1])
    return last - dt.timedelta(days=(last.weekday() - 4) % 7)


def build(spot, fut, bill):
    dates = sorted(d for d in spot if spot[d] is not None and d in fut and fut[d] is not None)
    N = len(dates)
    S = np.array([spot[d] for d in dates], float)
    F = np.array([fut[d] for d in dates], float)

    # rate: latest numeric RATE on or before date_t
    bd = sorted(d for d in bill if bill[d] is not None)
    r = np.full(N, np.nan)
    j, cur = 0, None
    for i, d in enumerate(dates):
        while j < len(bd) and bd[j] <= d:
            cur = bill[bd[j]]
            j += 1
        if cur is not None:
            r[i] = cur / 100.0

    # expiries
    y, mth = dates[0].year, dates[0].month
    ly, lm = dates[-1].year, dates[-1].month
    ly, lm = (ly + 1, 1) if lm == 12 else (ly, lm + 1)
    expiries = []
    while (y, mth) <= (ly, lm):
        expiries.append(last_friday(y, mth))
        y, mth = (y + 1, 1) if mth == 12 else (y, mth + 1)

    ords = np.array([d.toordinal() for d in dates])
    kX = {}
    for X in expiries:
        k = int(np.searchsorted(ords, X.toordinal(), side="right")) - 1
        kX[X] = k if k >= 0 else None

    kept = np.ones(N, bool)
    for X, k in kX.items():
        if k is None:
            continue
        kept[max(0, k - 4):min(N - 1, k + 1) + 1] = False

    last = dates[-1]
    Xt = [None] * N
    tau = np.full(N, np.nan)
    for i, d in enumerate(dates):
        if not kept[i]:
            continue
        for X in expiries:
            if X > d and (kX[X] is not None or X > last):
                Xt[i] = X
                tau[i] = (X - d).days / 365.0
                break

    M = np.full(N, np.nan)
    ok = kept & np.isfinite(r) & np.isfinite(tau)
    M[ok] = 100.0 * (F[ok] / (S[ok] * np.exp(r[ok] * tau[ok])) - 1.0)

    lS = np.log(S)

    def back(n):
        v = np.full(N, np.nan)
        v[n:] = 100.0 * (lS[n:] - lS[:-n])
        return v

    def fwd(h):
        v = np.full(N, np.nan)
        v[:-h] = 100.0 * (lS[h:] - lS[:-h])
        return v

    return dict(dates=dates, N=N, S=S, F=F, r=r, kept=kept, Xt=Xt, tau=tau, M=M,
                n1=back(1), n5=back(5), n20=back(20), R={h: fwd(h) for h in (1, 5, 20)},
                expiries=expiries, kX=kX)


# ---------------------------------------------------------------- estimators

def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta


def nw_cov(X, e, L):
    XtX_inv = np.linalg.inv(X.T @ X)
    u = X * e[:, None]
    S = u.T @ u
    for l in range(1, L + 1):
        if l >= len(e):
            break
        G = u[l:].T @ u[:-l]
        S += (1.0 - l / (L + 1.0)) * (G + G.T)
    return XtX_inv @ S @ XtX_inv


def slope(x, y):
    xc = x - x.mean()
    return float(np.dot(xc, y - y.mean()) / np.dot(xc, xc))


def sgn(v):
    if v is None or not np.isfinite(v):
        return None
    return int(np.sign(v))


def simple_reg(x, y, L):
    m = len(y)
    X = np.column_stack([np.ones(m), x])
    beta, e = ols(X, y)
    b = slope(x, y)
    V = nw_cov(X, e, L)
    se = math.sqrt(V[1, 1])
    return b, se, b / se


def rotation(x, y, b_obs):
    m = len(y)
    shifts = range(21, m - 20)  # 21..m-21 inclusive
    K = len(shifts)
    if K <= 0:
        return K, None, None, None
    xc = x - x.mean()
    yc = y - y.mean()
    den = float(np.dot(xc, xc))
    rs = np.array([np.dot(np.roll(xc, k), yc) / den for k in shifts])
    pp = (1 + int(np.sum(rs >= b_obs))) / (1 + K)
    pm = (1 + int(np.sum(rs <= b_obs))) / (1 + K)
    return K, pp, pm, min(1.0, 2.0 * min(pp, pm))


def aligned(*arrs):
    mask = np.ones(len(arrs[0]), bool)
    for a in arrs:
        mask &= np.isfinite(a)
    return np.nonzero(mask)[0]


def fin(v):
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------- OOS

def oos(pos_label, y, Zb, Za, start):
    """pos_label: the position used for the t >= start and 0..t-5 rule, one per aligned row."""
    eb, ea, cw = [], [], []
    for i in range(len(y)):
        t = pos_label[i]
        if t < start:
            continue
        tr = pos_label <= t - 5
        if tr.sum() <= Za.shape[1]:
            continue
        bb, _ = ols(Zb[tr], y[tr])
        ba, _ = ols(Za[tr], y[tr])
        fb = float(Zb[i] @ bb)
        fa = float(Za[i] @ ba)
        eb.append(y[i] - fb)
        ea.append(y[i] - fa)
        cw.append((y[i] - fb) ** 2 - ((y[i] - fa) ** 2 - (fb - fa) ** 2))
    n = len(cw)
    if n == 0:
        return dict(n_forecasts=0, r2_os=None, cw_mean=None, cw_nw_t=None)
    eb, ea, cw = np.array(eb), np.array(ea), np.array(cw)
    r2 = 1.0 - float(np.dot(ea, ea)) / float(np.dot(eb, eb))
    cm = float(cw.mean())
    t = None
    if n >= 2:
        X = np.ones((n, 1))
        V = nw_cov(X, cw - cm, 10)
        t = cm / math.sqrt(V[0, 0]) if V[0, 0] > 0 else None
    return dict(n_forecasts=n, r2_os=r2, cw_mean=cm, cw_nw_t=t)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    spot = read_series(os.path.join(a.data, "btc_spot.csv"), "CLOSE")
    fut = read_series(os.path.join(a.data, "btc_fut.csv"), "CLOSE")
    bill = read_series(os.path.join(a.data, "tbill.csv"), "RATE")
    D = build(spot, fut, bill)
    M, R = D["M"], D["R"]
    N = D["N"]
    print(f"joint days N={N} {D['dates'][0]}..{D['dates'][-1]}; kept={int(D['kept'].sum())}; "
          f"M defined={int(np.isfinite(M).sum())}; expiries={len(D['expiries'])}")

    out = {"horizons": {}}
    m5 = 0
    for h in (1, 5, 20):
        idx = aligned(M, R[h])
        m = len(idx)
        x, y = M[idx], R[h][idx]
        rec = dict(n=m, b=None, nw_t=None, p_plus=None, p_minus=None, p2=None, mde=None,
                   b_per_sd=None, K=None)
        if m >= 3:
            b, se, t = simple_reg(x, y, h + 5)
            K, pp, pm, p2 = rotation(x, y, b)
            rec.update(b=b, nw_t=t, p_plus=pp, p_minus=pm, p2=p2, mde=2.80 * se,
                       b_per_sd=b * float(np.std(x)), K=K)
        out["horizons"][str(h)] = {k: fin(v) if k not in ("n", "K") else v for k, v in rec.items()}
        if h == 5:
            m5 = m
            idx5, x5, y5 = idx, x, y
        print(f"h={h:2d} n={m} b={rec['b']} t={rec['nw_t']} p+={rec['p_plus']} "
              f"p-={rec['p_minus']} p2={rec['p2']} mde={rec['mde']}")

    b5 = out["horizons"]["5"]["b"]
    s = sgn(b5) if b5 is not None else 0
    out["s"] = s

    # halves
    hm = m5 // 2
    bf = slope(x5[:hm], y5[:hm]) if hm >= 2 else None
    br = slope(x5[hm:], y5[hm:]) if m5 - hm >= 2 else None
    out["halves"] = dict(n_first=hm, b_first=fin(bf), n_rest=m5 - hm, b_rest=fin(br))

    # incremental
    idxI = aligned(M, D["n1"], D["n5"], D["n20"], R[5])
    mi = len(idxI)
    yI = R[5][idxI]
    Zb = np.column_stack([np.ones(mi), D["n1"][idxI], D["n5"][idxI], D["n20"][idxI]])
    Za = np.column_stack([Zb, M[idxI]])
    g = gt = None
    if mi > 5:
        beta, e = ols(Za, yI)
        V = nw_cov(Za, e, 10)
        g, gt = float(beta[4]), float(beta[4] / math.sqrt(V[4, 4]))
    out["incremental"] = dict(n=mi, g=fin(g), nw_t=fin(gt))

    # out of sample (A1: positions counted within the aligned sample, per amended section 5)
    out["oos"] = {k: fin(v) if k != "n_forecasts" else v
                  for k, v in oos(np.arange(mi), yI, Zb, Za, 750).items()}

    # size
    sM = s * x5
    Q = float(np.percentile(sM, 80)) if m5 else None
    top = sM >= Q if m5 else np.zeros(0, bool)
    ntop = int(top.sum())
    Dq = 0.0 if s == 0 else (float(y5[top].mean() - y5.mean()) if ntop else None)
    out["size"] = dict(Q=fin(Q), n_top=ntop, Dq=fin(Dq))

    # criteria
    unscorable = (m5 - 41) < 100
    H = out["horizons"]
    p2_5 = H["5"]["p2"]
    crit = dict(
        a=b5 is not None and b5 != 0 and p2_5 is not None and p2_5 <= 0.025,
        b=sgn(H["1"]["b"]) == s and sgn(H["20"]["b"]) == s,
        c=sgn(bf) == s and sgn(br) == s,
        d=g is not None and sgn(g) == s and gt is not None and abs(gt) >= 2.0,
        e=out["oos"]["r2_os"] is not None and out["oos"]["r2_os"] > 0,
        f=Dq is not None and Dq >= 0.157,
    )
    if unscorable:
        crit = {k: False for k in crit}
        verdict = "UNSCORABLE"
    elif not crit["a"]:
        verdict = "FAIL"
    elif all(crit.values()):
        verdict = "PASS"
    else:
        verdict = "WEAK"
    out["criteria"] = crit
    out["verdict"] = verdict

    print(f"s={s} halves={out['halves']}")
    print(f"incremental={out['incremental']}")
    print(f"oos={out['oos']}")
    print(f"size={out['size']}")
    print(f"criteria={crit} verdict={verdict} (direction s={s})")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify_d.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())
