#!/usr/bin/env python3
"""Independent second implementation of pre-registration C (VIX term-structure basis).

Written from PREREG.md sections 2, 3, 4, 5 and 7 alone, without sight of run_c.py or kt.py,
so that every criterion figure can be compared on the runner. Standard library and numpy only.

Usage: python verify_c.py --data data --out out

Readings taken where the specification is open (most literal reading in each case):
 1. Joint calendar: the intersection of dates on which vix.CLOSE, vix3m.CLOSE and etp.OPEN,
    etp.CLOSE, etp.ADJCLOSE all parse as finite floats. Positions are taken on that calendar, so
    n1, n5, n20 and R_h step over joint positions, not over each file's own rows.
 2. n5_t = 100 ln(V_t / V_(t-5)), n20_t = 100 ln(V_t / V_(t-20)), by analogy with n1.
 3. Rotation: x is rotated circularly against y, x_k[i] = x[(i - k) mod m]; the shift set
    {21, ..., m-21} is symmetric under k -> m-k, so the direction does not matter. Rotated and
    observed slopes are computed by the same formula and compared exactly (no tolerance).
 4. MDE = 2.80 x Newey-West s.e. of the slope at that horizon (L = h + 5).
 5. Halves are taken on the h = 5 aligned sample (that of b_5).
 6. OOS positions are positions within the aligned sample of {B, lv, n1, n5, n20, R_5}; for each
    t >= 750 both models (each with an intercept, per section 4) are fitted on aligned positions
    0..t-5 inclusive and forecast R_5 at t from that day's regressors.
    Clark-West: f_t = e_base^2 - (e_aug^2 - (yhat_base - yhat_aug)^2); its mean and the
    Newey-West t of the mean (regression on a constant, L = 10).
 7. Size: Q and n_top are computed literally even when s = 0; only Dq is set to 0 then.
    n_top counts days with s x B >= Q.
 8. A statistic that cannot be formed (too few observations, singular design) is reported as
    null and any criterion reading it is false; this is not a reason for UNSCORABLE, which the
    rule confines to fewer than 100 rotation shifts at h = 5.
 9. Non-positive prices are not excluded from the calendar (the rule names numeric values only);
    they would make a logarithm undefined and that day's derived quantities are then undefined.
"""
import argparse
import csv
import json
import math
import os
import sys

import numpy as np


# ----------------------------------------------------------------------------- input

def _num(s):
    s = (s or "").strip()
    if s == "" or s == ".":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def read_csv(path, fields):
    out = {}
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        hdr = [h.strip() for h in (rdr.fieldnames or [])]
        rdr.fieldnames = hdr
        missing = [f for f in ["DATE"] + fields if f not in hdr]
        if missing:
            raise SystemExit(f"{path}: missing columns {missing}")
        for row in rdr:
            d = (row["DATE"] or "").strip()
            if not d:
                continue
            vals = [_num(row[f]) for f in fields]
            if d in out:
                raise SystemExit(f"{path}: duplicate date {d}")
            out[d] = vals
    return out


# ----------------------------------------------------------------------------- estimators

def ols(y, X):
    """OLS of y on X (X already carries the intercept column)."""
    XtX = X.T @ X
    beta = np.linalg.solve(XtX, X.T @ y)
    return beta, XtX


def newey_west(y, X, L):
    """Returns (beta, NW covariance). Bartlett w_l = 1 - l/(L+1); no dof correction."""
    beta, XtX = ols(y, X)
    u = y - X @ beta
    Z = X * u[:, None]
    S = Z.T @ Z
    n = len(y)
    for l in range(1, L + 1):
        if l >= n:
            break
        w = 1.0 - l / (L + 1.0)
        G = Z[l:].T @ Z[:-l]
        S += w * (G + G.T)
    Xi = np.linalg.inv(XtX)
    V = Xi @ S @ Xi
    return beta, V


def sign(v):
    if v is None:
        return None
    return 1 if v > 0 else (-1 if v < 0 else 0)


def slope_formula(x, y):
    xc = x - x.mean()
    yc = y - y.mean()
    return float(np.dot(xc, yc) / np.dot(xc, xc))


def rotation(x, y):
    m = len(x)
    ks = range(21, m - 21 + 1)
    K = m - 41
    if K <= 0:
        return None, None, None, max(K, 0)
    xc = x - x.mean()
    yc = y - y.mean()
    den = float(np.dot(xc, xc))
    obs = float(np.dot(xc, yc) / den)
    ge = le = 0
    for k in ks:
        r = float(np.dot(np.roll(xc, k), yc) / den)
        if r >= obs:
            ge += 1
        if r <= obs:
            le += 1
    pp = (1 + ge) / (1 + K)
    pm = (1 + le) / (1 + K)
    return pp, pm, min(1.0, 2 * min(pp, pm)), K


def fnum(v):
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    vix = read_csv(os.path.join(a.data, "vix.csv"), ["CLOSE"])
    v3m = read_csv(os.path.join(a.data, "vix3m.csv"), ["CLOSE"])
    etp = read_csv(os.path.join(a.data, "etp.csv"), ["OPEN", "CLOSE", "ADJCLOSE"])

    def ok(rec, d):
        return d in rec and all(v is not None for v in rec[d])

    dates = sorted(d for d in vix if ok(vix, d) and ok(v3m, d) and ok(etp, d))
    N = len(dates)
    print(f"joint days N={N}" + (f" {dates[0]}..{dates[-1]}" if N else ""))

    V = np.array([vix[d][0] for d in dates], dtype=float)
    V3 = np.array([v3m[d][0] for d in dates], dtype=float)
    O = np.array([etp[d][0] for d in dates], dtype=float)
    C = np.array([etp[d][1] for d in dates], dtype=float)
    A = np.array([etp[d][2] for d in dates], dtype=float)

    with np.errstate(all="ignore"):
        adj = A / C
        B = 100.0 * (V3 / V - 1.0)
        lnV = np.log(V)
        lv = lnV.copy()

        def mom(k):
            out = np.full(N, np.nan)
            if N > k:
                out[k:] = 100.0 * (lnV[k:] - lnV[:-k])
            return out

        n1, n5, n20 = mom(1), mom(5), mom(20)

        def outcome(h):
            out = np.full(N, np.nan)
            for t in range(0, N - h):
                num = C[t + h] * adj[t + h]
                den = O[t + 1] * adj[t + 1]
                out[t] = 100.0 * math.log(num / den) if num > 0 and den > 0 else np.nan
            return out

        R = {h: outcome(h) for h in (1, 5, 20)}

    fin = np.isfinite
    res = {"horizons": {}}

    # ---- per-horizon slopes
    hz = {}
    for h in (1, 5, 20):
        msk = fin(B) & fin(R[h])
        x, y = B[msk], R[h][msk]
        m = len(x)
        entry = {"n": m, "b": None, "nw_t": None, "p_plus": None, "p_minus": None,
                 "p2": None, "mde": None}
        K = max(m - 41, 0)
        if m >= 3 and np.var(x) > 0:
            X = np.column_stack([np.ones(m), x])
            beta, Vc = newey_west(y, X, h + 5)
            se = math.sqrt(Vc[1, 1])
            entry["b"] = fnum(beta[1])
            entry["nw_t"] = fnum(beta[1] / se) if se > 0 else None
            entry["mde"] = fnum(2.80 * se)
            pp, pm, p2, K = rotation(x, y)
            entry["p_plus"], entry["p_minus"], entry["p2"] = pp, pm, p2
        entry["_K"] = K
        hz[h] = (entry, x, y)
        print(f"h={h:>2} n={m} b={entry['b']} t={entry['nw_t']} p+={entry['p_plus']} "
              f"p-={entry['p_minus']} p2={entry['p2']} mde={entry['mde']} K={K}")

    b5 = hz[5][0]["b"]
    s = sign(b5) if b5 is not None else 0
    res["s"] = s

    # ---- halves (h = 5 aligned sample)
    _, x5, y5 = hz[5]
    m5 = len(x5)
    hf = m5 // 2

    def sl(xx, yy):
        if len(xx) < 2 or np.var(xx) == 0:
            return None
        X = np.column_stack([np.ones(len(xx)), xx])
        return fnum(ols(yy, X)[0][1])

    res["halves"] = {"n_first": hf, "b_first": sl(x5[:hf], y5[:hf]),
                     "n_rest": m5 - hf, "b_rest": sl(x5[hf:], y5[hf:])}
    print(f"halves {res['halves']}")

    # ---- incremental
    msk = fin(B) & fin(lv) & fin(n1) & fin(n5) & fin(n20) & fin(R[5])
    Xf = np.column_stack([np.ones(int(msk.sum())), B[msk], lv[msk], n1[msk], n5[msk], n20[msk]])
    yf = R[5][msk]
    inc = {"n": int(msk.sum()), "g": None, "nw_t": None}
    try:
        beta, Vc = newey_west(yf, Xf, 10)
        inc["g"] = fnum(beta[1])
        inc["nw_t"] = fnum(beta[1] / math.sqrt(Vc[1, 1]))
    except (np.linalg.LinAlgError, ValueError):
        pass
    res["incremental"] = inc
    print(f"incremental {inc}")

    # ---- out of sample (positions within the aligned sample)
    mA = len(yf)
    Xb = Xf[:, [0, 2, 3, 4, 5]]
    Xa = Xf
    eb, ea, fb, fa, ys = [], [], [], [], []
    for t in range(750, mA):
        e = t - 5 + 1  # rows 0..t-5 inclusive
        if e < Xa.shape[1]:
            continue
        try:
            bb = np.linalg.lstsq(Xb[:e], yf[:e], rcond=None)[0]
            ba = np.linalg.lstsq(Xa[:e], yf[:e], rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        pb = float(Xb[t] @ bb)
        pa = float(Xa[t] @ ba)
        fb.append(pb); fa.append(pa); ys.append(yf[t])
    oos = {"n_forecasts": len(ys), "r2_os": None, "cw_mean": None, "cw_nw_t": None}
    if ys:
        ys = np.array(ys); fb = np.array(fb); fa = np.array(fa)
        e_b = ys - fb
        e_a = ys - fa
        sse_b = float(e_b @ e_b); sse_a = float(e_a @ e_a)
        oos["r2_os"] = fnum(1.0 - sse_a / sse_b) if sse_b > 0 else None
        cw = e_b ** 2 - (e_a ** 2 - (fb - fa) ** 2)
        oos["cw_mean"] = fnum(cw.mean())
        if len(cw) >= 2:
            beta, Vc = newey_west(cw, np.ones((len(cw), 1)), 10)
            oos["cw_nw_t"] = fnum(beta[0] / math.sqrt(Vc[0, 0])) if Vc[0, 0] > 0 else None
    res["oos"] = oos
    print(f"oos {oos}")

    # ---- size (h = 5 aligned sample)
    size = {"Q": None, "n_top": None, "Dq": None}
    if m5 > 0:
        sx = s * x5
        Q = float(np.percentile(sx, 80))  # numpy default method is linear
        top = sx >= Q
        size["Q"] = fnum(Q)
        size["n_top"] = int(top.sum())
        size["Dq"] = 0.0 if s == 0 else fnum(y5[top].mean() - y5.mean())
    res["size"] = size
    print(f"size {size}")

    # ---- horizons into JSON
    for h in (1, 5, 20):
        e = dict(hz[h][0]); e.pop("_K")
        res["horizons"][str(h)] = e

    # ---- criteria and verdict
    h1, h5, h20 = hz[1][0], hz[5][0], hz[20][0]
    crit = {}
    crit["a"] = bool(b5 is not None and b5 != 0 and h5["p2"] is not None and h5["p2"] <= 0.025)
    crit["b"] = bool(h1["b"] is not None and h20["b"] is not None
                     and sign(h1["b"]) == s and sign(h20["b"]) == s)
    hv = res["halves"]
    crit["c"] = bool(hv["b_first"] is not None and hv["b_rest"] is not None
                     and sign(hv["b_first"]) == s and sign(hv["b_rest"]) == s)
    crit["d"] = bool(inc["g"] is not None and inc["nw_t"] is not None
                     and sign(inc["g"]) == s and abs(inc["nw_t"]) >= 2.0)
    crit["e"] = bool(oos["r2_os"] is not None and oos["r2_os"] > 0)
    crit["f"] = bool(size["Dq"] is not None and size["Dq"] >= 0.157)
    res["criteria"] = crit

    if hz[5][0]["_K"] < 100:
        verdict = "UNSCORABLE"
    elif all(crit.values()):
        verdict = "PASS"
    elif crit["a"]:
        verdict = "WEAK"
    else:
        verdict = "FAIL"
    res["verdict"] = verdict
    print(f"criteria {crit}")
    print(f"verdict {verdict} s={s}")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify_c.json"), "w") as fh:
        json.dump(res, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())
