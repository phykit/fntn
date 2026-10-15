#!/usr/bin/env python3
"""verify_c2.py: independent second implementation of pre-registration C2.

Written from PREREG.md (sections 2, 3, 4, 5 and 7) alone, without sight of
run_c2.py, kt.py or any other file in the repository, so that a figure on
which the two implementations agree was reached twice and not copied once.

Usage: python verify_c2.py --data data --out out

Standard library and numpy only. Writes <out>/verify_c2.json and prints a
compact log.

Readings of the specification where it admits more than one, resolved by the
most literal reading (the reason is stated so that a disagreement with
run_c2.py can be traced to a reading rather than to an error):

 R1  Missing: an empty field, ".", or any token float() cannot read as a
     finite number. A SETTLE of exactly zero is also missing (section 2).
 R2  Duplicate keys (the same DATE twice in vix.csv or etp.csv, the same
     DATE and EXPIRY twice in vx.csv): the first row is kept and the count
     of discarded rows is logged. The specification says one row per key.
 R3  Joint calendar: "numeric values for every field" is read as numeric,
     not positive. A non-positive price makes a logarithm undefined; that
     quantity is then undefined (NaN) at that position and drops out of
     every aligned sample needing it, but the date stays in the calendar.
 R4  Lags n1, n5, n20 and leads in R_h are taken over joint-calendar
     POSITIONS, not trading days of any one file (section 3: "over 5 and
     20 positions").
 R5  Every OLS fit, including the baseline and augmented models of the
     out-of-sample test, carries an intercept (section 4: "OLS with an
     intercept").
 R6  The Newey-West t of the Clark-West mean is the regression of the
     Clark-West series on a constant, through the same estimator (L = 10).
     The Clark-West term is e_base^2 - (e_aug^2 - (f_base - f_aug)^2).
 R7  The rotation shifts x against y cyclically, x_rot[i] = x[(i+k) mod m];
     the set k = 21..m-21 is closed under k -> m-k, so the direction of
     rotation does not change the p-values.
 R8  Size when s = 0: Q and n_top are computed literally on 0 x B30 (so Q
     is 0 and every day is in the top group) and Dq is set to 0 as stated.
 R9  A criterion whose statistic cannot be computed (too few points, a
     singular design, no out-of-sample forecasts) is NOT met, and the
     statistic is reported as null. A not-computable statistic is never
     read as a pass.
 R10 Criteria (b), (c), (d) compare signs with s literally: when s = 0 they
     require a slope of sign 0.
 R11 UNSCORABLE is tested first: K = m - 41 at h = 5 below 100.
 R12 coverage.n_contracts is the number of distinct EXPIRY values in
     vx.csv (contracts found), whether or not any of their settles is
     usable.
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

HORIZONS = (1, 5, 20)
ALPHA2 = 0.025
DQ_MIN = 0.157
OOS_START = 750
EMBARGO = 5          # fit on positions 0..t-5 inclusive
MDE_MULT = 2.80
NW_L_INCR = 10
ROT_MIN = 21


# ----------------------------------------------------------------- reading

def parse_num(tok):
    """Return a finite float, or None for missing (R1)."""
    if tok is None:
        return None
    tok = tok.strip()
    if tok == "" or tok == ".":
        return None
    try:
        v = float(tok)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    return v


def parse_date(tok):
    tok = (tok or "").strip()
    if tok == "":
        return None
    return dt.date.fromisoformat(tok[:10])


def read_csv(path, fields):
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        hdr = {h.strip().upper(): h for h in (rdr.fieldnames or [])}
        missing = [f for f in fields if f not in hdr]
        if missing:
            raise SystemExit(f"{path}: missing columns {missing}; header {rdr.fieldnames}")
        rows = []
        for r in rdr:
            rows.append({f: r.get(hdr[f]) for f in fields})
    return rows


def load_vx(path):
    rows = read_csv(path, ["DATE", "EXPIRY", "SETTLE"])
    seen = {}
    dup = 0
    expiries = set()
    for r in rows:
        d = parse_date(r["DATE"])
        e = parse_date(r["EXPIRY"])
        if d is None or e is None:
            continue
        expiries.add(e)
        key = (d, e)
        if key in seen:
            dup += 1
            continue
        s = parse_num(r["SETTLE"])
        if s is not None and s == 0.0:
            s = None
        seen[key] = s
    # futures calendar (section 3)
    by_date = {}
    for (d, e), s in seen.items():
        by_date.setdefault(d, [])
        if s is not None and e > d:
            by_date[d].append((e, s))
    cal = {}
    for d, lst in by_date.items():
        lst.sort()
        if len(lst) >= 2:
            (e1, f1), (e2, f2) = lst[0], lst[1]
            cal[d] = (f1, f2, (e1 - d).days, (e2 - d).days)
    return cal, len(expiries), len(by_date), dup


def load_series(path, fields):
    rows = read_csv(path, ["DATE"] + fields)
    out = {}
    dup = 0
    for r in rows:
        d = parse_date(r["DATE"])
        if d is None:
            continue
        if d in out:
            dup += 1
            continue
        out[d] = tuple(parse_num(r[f]) for f in fields)
    return out, dup


# --------------------------------------------------------------- estimators

def safe_log(x):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(np.where(x > 0, x, np.nan))
    return r


def ols_nw(y, X, L):
    """OLS (X must already carry its intercept column) with the Newey-West
    covariance (X'X)^-1 S (X'X)^-1, Bartlett w_l = 1 - l/(L+1), no
    degrees-of-freedom correction. Returns (beta, se) or (None, None)."""
    n, k = X.shape
    if n <= k:
        return None, None
    XtX = X.T @ X
    try:
        XtXi = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        return None, None
    if not np.all(np.isfinite(XtXi)) or np.linalg.cond(XtX) > 1e14:
        return None, None
    beta = XtXi @ (X.T @ y)
    u = y - X @ beta
    xu = X * u[:, None]
    S = xu.T @ xu
    for l in range(1, min(L, n - 1) + 1):
        wl = 1.0 - l / (L + 1.0)
        G = xu[l:].T @ xu[:-l]
        S += wl * (G + G.T)
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.maximum(np.diag(V), 0.0))
    return beta, se


def simple_slope(x, y):
    xc = x - x.mean()
    sxx = float(xc @ xc)
    if sxx == 0.0:
        return None
    return float(xc @ (y - y.mean())) / sxx


def rotation_p(x, y, b_obs):
    """Section 4: shifts k = 21..m-21 of x against y, K = m - 41."""
    m = len(x)
    K = m - 2 * ROT_MIN + 1
    if K <= 0:
        return K, None, None, None
    xc = x - x.mean()
    yc = y - y.mean()
    sxx = float(xc @ xc)
    ge = le = 0
    for k in range(ROT_MIN, m - ROT_MIN + 1):
        bk = float(np.roll(xc, -k) @ yc) / sxx
        if bk >= b_obs:
            ge += 1
        if bk <= b_obs:
            le += 1
    pp = (1 + ge) / (1 + K)
    pm = (1 + le) / (1 + K)
    return K, pp, pm, min(1.0, 2.0 * min(pp, pm))


def sgn(v):
    if v is None:
        return None
    return 1 if v > 0 else (-1 if v < 0 else 0)


def nz(v):
    """JSON-safe float."""
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cal, n_contracts, n_vx_dates, dup_vx = load_vx(os.path.join(a.data, "vx.csv"))
    vix, dup_vix = load_series(os.path.join(a.data, "vix.csv"), ["CLOSE"])
    etp, dup_etp = load_series(os.path.join(a.data, "etp.csv"), ["OPEN", "CLOSE", "ADJCLOSE"])

    # joint calendar (section 3)
    dates = sorted(
        d for d in cal
        if d in vix and d in etp
        and all(v is not None for v in vix[d])
        and all(v is not None for v in etp[d])
    )
    N = len(dates)
    etp_ok = [d for d in etp if all(v is not None for v in etp[d])]
    no_pair = sum(1 for d in etp_ok if d not in cal)
    print(f"vx: {n_contracts} contracts, {n_vx_dates} dates, {len(cal)} with a pair, "
          f"{dup_vx} duplicate rows dropped")
    print(f"vix: {len(vix)} rows ({dup_vix} dup); etp: {len(etp)} rows ({dup_etp} dup); "
          f"etp days with no futures pair: {no_pair}")
    print(f"joint calendar N = {N}" + (f" ({dates[0]} .. {dates[-1]})" if N else ""))

    F1 = np.array([cal[d][0] for d in dates], float)
    F2 = np.array([cal[d][1] for d in dates], float)
    t1 = np.array([cal[d][2] for d in dates], float)
    t2 = np.array([cal[d][3] for d in dates], float)
    V = np.array([vix[d][0] for d in dates], float)
    O = np.array([etp[d][0] for d in dates], float)
    C = np.array([etp[d][1] for d in dates], float)
    A = np.array([etp[d][2] for d in dates], float)

    with np.errstate(divide="ignore", invalid="ignore"):
        w = np.clip((t2 - 30.0) / (t2 - t1), 0.0, 1.0)
        F30 = w * F1 + (1.0 - w) * F2
        B30 = 100.0 * (F30 / V - 1.0)
        B30[~np.isfinite(B30)] = np.nan
        lnV = safe_log(V)
        lv = lnV.copy()

        def lagdiff(k):
            r = np.full(N, np.nan)
            if N > k:
                r[k:] = 100.0 * (lnV[k:] - lnV[:-k])
            return r

        n1, n5, n20 = lagdiff(1), lagdiff(5), lagdiff(20)
        a_ = A / C
        a_[~np.isfinite(a_)] = np.nan
        lnTop = safe_log(C * a_)          # ln(C_t a_t)
        lnOpen = safe_log(O * a_)         # ln(O_t a_t)
        R = {}
        for h in HORIZONS:
            r = np.full(N, np.nan)
            if N > h:
                # R_h(t) = 100 ln(C_{t+h} a_{t+h} / (O_{t+1} a_{t+1})), t = 0..N-1-h
                r[: N - h] = 100.0 * (lnTop[h:] - lnOpen[1: N - h + 1])
            R[h] = r

    out = {"horizons": {}}
    res = {}

    # ---- per-horizon slopes (section 5)
    for h in HORIZONS:
        msk = np.isfinite(B30) & np.isfinite(R[h])
        x, y = B30[msk], R[h][msk]
        m = len(x)
        rec = {"n": m, "b": None, "nw_t": None, "p_plus": None, "p_minus": None,
               "p2": None, "mde": None}
        K = m - 2 * ROT_MIN + 1
        if m >= 3:
            X = np.column_stack([np.ones(m), x])
            beta, se = ols_nw(y, X, h + 5)
            if beta is not None:
                b = float(beta[1])
                rec["b"] = b
                rec["nw_t"] = nz(b / se[1]) if se[1] > 0 else None
                rec["mde"] = nz(MDE_MULT * se[1])
                b_rot = simple_slope(x, y)
                Kr, pp, pm, p2 = rotation_p(x, y, b_rot)
                rec["p_plus"], rec["p_minus"], rec["p2"] = pp, pm, p2
        res[h] = (rec, K, msk)
        out["horizons"][str(h)] = {k: nz(v) if isinstance(v, float) else v for k, v in rec.items()}

    b5 = res[5][0]["b"]
    s = sgn(b5) if b5 is not None else 0
    out["s"] = s

    # ---- halves
    msk5 = res[5][2]
    x5, y5 = B30[msk5], R[5][msk5]
    m5 = len(x5)
    hf = m5 // 2

    def slope_ic(xx, yy):
        if len(xx) < 2:
            return None
        return simple_slope(xx, yy)

    b_first, b_rest = slope_ic(x5[:hf], y5[:hf]), slope_ic(x5[hf:], y5[hf:])
    out["halves"] = {"n_first": hf, "b_first": nz(b_first), "n_rest": m5 - hf, "b_rest": nz(b_rest)}

    # ---- incremental
    mi = np.isfinite(B30) & np.isfinite(lv) & np.isfinite(n1) & np.isfinite(n5) \
        & np.isfinite(n20) & np.isfinite(R[5])
    mI = int(mi.sum())
    g = g_t = None
    if mI > 6:
        Xi = np.column_stack([np.ones(mI), B30[mi], lv[mi], n1[mi], n5[mi], n20[mi]])
        beta, se = ols_nw(R[5][mi], Xi, NW_L_INCR)
        if beta is not None:
            g = float(beta[1])
            g_t = nz(g / se[1]) if se[1] > 0 else None
    out["incremental"] = {"n": mI, "g": nz(g), "nw_t": g_t}

    # ---- out of sample (positions within the aligned sample of section 5)
    yb = R[5][mi]
    Xb = np.column_stack([np.ones(mI), lv[mi], n1[mi], n5[mi], n20[mi]])
    Xa = np.column_stack([Xb, B30[mi]])
    eb, ea, cw = [], [], []
    for t in range(OOS_START, mI):
        nfit = t - EMBARGO + 1          # positions 0..t-5 inclusive
        if nfit <= Xa.shape[1]:
            continue
        bb, *_ = np.linalg.lstsq(Xb[:nfit], yb[:nfit], rcond=None)
        ba, *_ = np.linalg.lstsq(Xa[:nfit], yb[:nfit], rcond=None)
        fb, fa = float(Xb[t] @ bb), float(Xa[t] @ ba)
        e_b, e_a = yb[t] - fb, yb[t] - fa
        eb.append(e_b)
        ea.append(e_a)
        cw.append(e_b ** 2 - (e_a ** 2 - (fb - fa) ** 2))
    nf = len(cw)
    r2os = cw_mean = cw_t = None
    if nf > 0:
        sse_b = float(np.sum(np.square(eb)))
        sse_a = float(np.sum(np.square(ea)))
        r2os = 1.0 - sse_a / sse_b if sse_b > 0 else None
        cwa = np.array(cw)
        cw_mean = float(cwa.mean())
        if nf > 1:
            beta, se = ols_nw(cwa, np.ones((nf, 1)), NW_L_INCR)
            if beta is not None and se[0] > 0:
                cw_t = float(beta[0] / se[0])
    out["oos"] = {"n_forecasts": nf, "r2_os": nz(r2os), "cw_mean": nz(cw_mean), "cw_nw_t": nz(cw_t)}

    # ---- size
    Q = n_top = Dq = None
    if m5 > 0:
        z = s * x5
        Q = float(np.percentile(z, 80, method="linear"))
        top = z >= Q
        n_top = int(top.sum())
        Dq = 0.0 if s == 0 else float(y5[top].mean() - y5.mean())
    out["size"] = {"Q": nz(Q), "n_top": n_top, "Dq": nz(Dq)}

    # ---- verdict (section 7)
    r1, r5, r20 = res[1][0], res[5][0], res[20][0]
    crit = {
        "a": bool(r5["b"] is not None and r5["b"] != 0 and r5["p2"] is not None
                  and r5["p2"] <= ALPHA2),
        "b": bool(r1["b"] is not None and r20["b"] is not None
                  and sgn(r1["b"]) == s and sgn(r20["b"]) == s),
        "c": bool(b_first is not None and b_rest is not None
                  and sgn(b_first) == s and sgn(b_rest) == s),
        "d": bool(g is not None and g_t is not None and sgn(g) == s and abs(g_t) >= 2.0),
        "e": bool(r2os is not None and r2os > 0),
        "f": bool(Dq is not None and Dq >= DQ_MIN),
    }
    out["criteria"] = crit
    K5 = res[5][1]
    if K5 < 100:
        verdict = "UNSCORABLE"
    elif all(crit.values()):
        verdict = "PASS"
    elif crit["a"]:
        verdict = "WEAK"
    else:
        verdict = "FAIL"
    out["verdict"] = verdict
    out["coverage"] = {"n_joint": N, "n_contracts": n_contracts}

    # ---- log
    for h in HORIZONS:
        r = out["horizons"][str(h)]
        print(f"h={h:>2}: n={r['n']} b={_f(r['b'])} t={_f(r['nw_t'])} "
              f"p+={_f(r['p_plus'])} p-={_f(r['p_minus'])} p2={_f(r['p2'])} mde={_f(r['mde'])}")
    print(f"s={s}  K5={K5}  halves {hf}/{m5 - hf}: {_f(b_first)} / {_f(b_rest)}")
    print(f"incremental n={mI} g={_f(g)} t={_f(g_t)}")
    print(f"oos n={nf} R2_OS={_f(r2os)} CW mean={_f(cw_mean)} t={_f(cw_t)}")
    print(f"size Q={_f(Q)} n_top={n_top} Dq={_f(Dq)}")
    print("criteria " + " ".join(f"{k}={'Y' if v else 'n'}" for k, v in crit.items())
          + f"  VERDICT {verdict} (s={s})")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify_c2.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    return 0


def _f(v):
    return "n/a" if v is None else f"{v:.4g}"


if __name__ == "__main__":
    sys.exit(main())
