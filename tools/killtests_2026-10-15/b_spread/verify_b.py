#!/usr/bin/env python3
"""Independent second implementation of pre-registration B (spot residual as a
predictor of the front-to-second natural gas calendar spread).

Written from b_spread/PREREG.md (sections 3, 4, 5 and 7) and a_expiry/PREREG.md
(sections 2 and 3, incorporated by reference for the business-day calendar, the
expiry rule and the switch convention) alone, without sight of run_b.py or kt.py.
The reason it exists is that a statistic computed once is a statistic nobody has
checked; every criterion figure is compared against run_b.py on the runner.

Usage: python verify_b.py --data data --out out

Standard library and numpy only. Ambiguities in the specification are resolved by
the most literal reading; each resolution is listed in AMBIGUITIES below and in the
stdout log, so that a disagreement with run_b.py can be traced to a reading rather
than hunted for in arithmetic.
"""

import argparse
import bisect
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

AMBIGUITIES = [
    "A1 Saturday holidays move to the preceding Friday and Sunday holidays to the "
    "following Monday, except New Year's Day on a Saturday, which is not observed "
    "(A section 3 as amended before freezing: the exchanges trade on that 31 "
    "December). A Sunday New Year is observed on Monday 2 January.",
    "A2 No closures other than the listed holidays (e.g. national days of mourning, "
    "11 to 14 September 2001, Hurricane Sandy) are treated as non-business days.",
    "A3 'Numeric' means a value that parses as a finite float; empty, '.', and "
    "anything unparseable are missing. A quantity whose logarithm has a non-positive "
    "argument is undefined on that day (the day stays in the joint calendar).",
    "A4 Expiries are generated for delivery months from the first joint date's month "
    "to the month after the last joint date's month (A section 3). A's amended rule "
    "that only expiries on or before the last joint date are used governs A's "
    "windows and is NOT applied here: B section 3 uses the full list for X(t) and the "
    "exclusions (coordinator's confirmation of 15 October 2026). A kept day with "
    "no expiry strictly after it in that list has X(t) undefined, so M, tau and every "
    "same-contract quantity are undefined there.",
    "A5 The qualifier 'with k_X defined or X after the last joint date' in X(t) is "
    "always satisfied for an expiry strictly after date_t (date_t itself is a joint "
    "date on or before X), so X(t) is simply the first listed expiry strictly after "
    "date_t.",
    "A6 Exclusion positions k_X-4..k_X+1 are clipped to 0..N-1. Expiries with k_X "
    "undefined exclude nothing.",
    "A7 n1 and n5 (spot momentum) require only that positions t-1 / t-5 exist in the "
    "joint calendar; the 'both ends kept and in the same contract' condition is read "
    "as attaching to dSp1 and dSp5 only. They are taken on kept days t (the test "
    "sample), with the lagged end free to be excluded.",
    "A8 Lags and leads (t+h, t-1, t-5) are joint-calendar positions; Newey-West lags, "
    "halves, rotations and the out-of-sample positions (t >= 1000, fit on 0..t-5) are "
    "positions within the statistic's own aligned sample.",
    "A9 Out-of-sample positions are counted within the aligned sample of {M, Sp, dSp1, "
    "dSp5, n1, n5, D_5} (now explicit in B section 5); for each t >= 1000 both models "
    "are fitted on positions 0..t-5 inclusive (t-4 rows). "
    "Both models include an intercept (section 4: "
    "'OLS with an intercept'). Clark-West adjusted loss f_t = e_base^2 - (e_aug^2 - "
    "(yhat_base - yhat_aug)^2); its Newey-West t is that of the mean (regression on a "
    "constant), L = 10.",
    "A10 Rotation: x_rot = x shifted circularly by k (np.roll); the slope set is "
    "symmetric in direction because k and m-k are both in 21..m-21. Observed and "
    "rotated slopes are computed by the same closed form for the p-value comparison. "
    "UNSCORABLE when K = m - 41 < 100 at h = 5.",
    "A11 Size: Q and n_top are computed literally on s x M even when s = 0, and Dq is "
    "then forced to 0. Criterion (e) is False when R2_OS is undefined (fewer than "
    "1001 aligned days or a singular fit).",
    "A12 Duplicate dates within one input file: the first occurrence is kept.",
]


# ---------------------------------------------------------------- input


def parse_value(s):
    if s is None:
        return None
    s = s.strip()
    if s == "" or s == ".":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    return v


def read_series(path, field):
    out = {}
    dups = 0
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames is None or "DATE" not in rd.fieldnames or field not in rd.fieldnames:
            raise SystemExit(f"{path}: header must contain DATE and {field}; got {rd.fieldnames}")
        for row in rd:
            ds = (row.get("DATE") or "").strip()
            if not ds:
                continue
            d = dt.date.fromisoformat(ds)
            if d in out:
                dups += 1
                continue
            out[d] = parse_value(row.get(field))
    return out, dups


# ---------------------------------------------------------------- calendar


def easter(y):
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(y, month, day)


def nth_weekday(y, month, weekday, n):
    d = dt.date(y, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def last_weekday(y, month, weekday):
    nxt = dt.date(y + (month == 12), month % 12 + 1, 1)
    d = nxt - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def observed(d):
    if d.weekday() == 5:
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:
        return d + dt.timedelta(days=1)
    return d


def holidays_for_year(y):
    h = set()
    ny = dt.date(y, 1, 1)
    if ny.weekday() != 5:  # a Saturday New Year is not observed on 31 December
        h.add(observed(ny))
    if y >= 1998:
        h.add(nth_weekday(y, 1, 0, 3))  # MLK
    h.add(nth_weekday(y, 2, 0, 3))  # Presidents' Day
    h.add(easter(y) - dt.timedelta(days=2))  # Good Friday
    h.add(last_weekday(y, 5, 0))  # Memorial Day
    if y >= 2022:
        h.add(observed(dt.date(y, 6, 19)))  # Juneteenth
    h.add(observed(dt.date(y, 7, 4)))
    h.add(nth_weekday(y, 9, 0, 1))  # Labor Day
    h.add(nth_weekday(y, 11, 3, 4))  # Thanksgiving
    h.add(observed(dt.date(y, 12, 25)))
    return h


class BusinessCalendar:
    def __init__(self):
        self._cache = {}

    def holidays(self, y):
        if y not in self._cache:
            self._cache[y] = holidays_for_year(y)
        return self._cache[y]

    def is_business(self, d):
        if d.weekday() >= 5:
            return False
        # an observed holiday can fall in the adjacent calendar year
        return not (d in self.holidays(d.year) or d in self.holidays(d.year + 1)
                    or d in self.holidays(d.year - 1))


def ng_expiry(cal, delivery_year, delivery_month):
    """Third business day counting back from the last day of the preceding month,
    that last day counting as the first if it is a business day."""
    d = dt.date(delivery_year, delivery_month, 1) - dt.timedelta(days=1)
    count = 0
    while True:
        if cal.is_business(d):
            count += 1
            if count == 3:
                return d
        d -= dt.timedelta(days=1)


def month_range(y0, m0, y1, m1):
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


# ---------------------------------------------------------------- estimators


def ols_nw(X, y, L):
    """OLS coefficients and Newey-West standard errors, Bartlett weights
    1 - l/(L+1), no degrees-of-freedom correction. Returns (beta, se) or
    (None, None) if X'X is singular."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    XtX = X.T @ X
    try:
        XtXi = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        return None, None
    if not np.all(np.isfinite(XtXi)) or np.linalg.matrix_rank(XtX) < X.shape[1]:
        return None, None
    beta = XtXi @ (X.T @ y)
    u = y - X @ beta
    Z = X * u[:, None]
    S = Z.T @ Z
    n = len(y)
    for l in range(1, min(L, n - 1) + 1):
        w = 1.0 - l / (L + 1.0)
        G = Z[l:].T @ Z[:-l]
        S += w * (G + G.T)
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.maximum(np.diag(V), 0.0))
    return beta, se


def slope_cf(x, y):
    xc = x - x.mean()
    yc = y - y.mean()
    den = float(xc @ xc)
    if den == 0.0:
        return float("nan")
    return float(xc @ yc) / den


def rotation_p(x, y):
    m = len(x)
    K = m - 41
    if K <= 0:
        return K, None, None, None
    obs = slope_cf(x, y)
    xc = x - x.mean()
    yc = y - y.mean()
    den = float(xc @ xc)
    ge = le = 0
    for k in range(21, m - 20):
        r = float(np.roll(xc, k) @ yc) / den
        if r >= obs:
            ge += 1
        if r <= obs:
            le += 1
    pp = (1 + ge) / (1 + K)
    pm = (1 + le) / (1 + K)
    return K, pp, pm, min(1.0, 2.0 * min(pp, pm))


def sgn(v):
    if v is None or not np.isfinite(v):
        return None
    return int(np.sign(v))


def simple_reg(x, y, L):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(x)), x])
    beta, se = ols_nw(X, y, L)
    if beta is None:
        return None, None, None
    b = float(beta[1])
    t = b / float(se[1]) if se[1] > 0 else float("nan")
    return b, t, float(se[1])


# ---------------------------------------------------------------- main


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return f if math.isfinite(f) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    spot, d1 = read_series(os.path.join(a.data, "ng_spot.csv"), "VALUE")
    c1, d2 = read_series(os.path.join(a.data, "ng_c1.csv"), "CLOSE")
    c2, d3 = read_series(os.path.join(a.data, "ng_c2.csv"), "CLOSE")
    tb, d4 = read_series(os.path.join(a.data, "tbill.csv"), "RATE")

    dates = sorted(d for d in spot
                   if spot.get(d) is not None and c1.get(d) is not None and c2.get(d) is not None)
    N = len(dates)
    if N == 0:
        raise SystemExit("empty joint calendar")
    S = np.array([spot[d] for d in dates])
    F1 = np.array([c1[d] for d in dates])
    F2 = np.array([c2[d] for d in dates])

    tb_dates = sorted(d for d, v in tb.items() if v is not None)
    tb_vals = [tb[d] for d in tb_dates]
    r = np.full(N, np.nan)
    for i, d in enumerate(dates):
        j = bisect.bisect_right(tb_dates, d) - 1
        if j >= 0:
            r[i] = tb_vals[j] / 100.0

    cal = BusinessCalendar()
    first, last = dates[0], dates[-1]
    ly, lm = (last.year + 1, 1) if last.month == 12 else (last.year, last.month + 1)
    expiries = [ng_expiry(cal, y, m) for y, m in month_range(first.year, first.month, ly, lm)]

    excluded = np.zeros(N, bool)
    n_kx = 0
    for X in expiries:
        k = bisect.bisect_right(dates, X) - 1
        if k < 0:
            continue
        n_kx += 1
        excluded[max(0, k - 4):min(N - 1, k + 1) + 1] = True
    kept = ~excluded

    Xt = [None] * N
    for i, d in enumerate(dates):
        if kept[i]:
            j = bisect.bisect_right(expiries, d)
            Xt[i] = expiries[j] if j < len(expiries) else None

    def logratio(a_, b_):
        with np.errstate(divide="ignore", invalid="ignore"):
            out = np.where((a_ > 0) & (b_ > 0), 100.0 * np.log(np.where(a_ > 0, a_, 1.0) / np.where(b_ > 0, b_, 1.0)), np.nan)
        return out

    NaN = float("nan")
    M = np.full(N, NaN)
    for i in range(N):
        if kept[i] and Xt[i] is not None and np.isfinite(r[i]):
            tau = (Xt[i] - dates[i]).days / 365.0
            fstar = S[i] * math.exp(r[i] * tau)
            if fstar != 0:
                M[i] = 100.0 * (F1[i] / fstar - 1.0)
    Sp = logratio(F2, F1)

    def same(i, j):
        return (0 <= i < N and 0 <= j < N and kept[i] and kept[j]
                and Xt[i] is not None and Xt[i] == Xt[j])

    D = {}
    for h in (1, 3, 5):
        arr = np.full(N, NaN)
        for t in range(N):
            if same(t, t + h):
                arr[t] = Sp[t + h] - Sp[t]
        D[h] = arr
    dSp1 = np.full(N, NaN)
    dSp5 = np.full(N, NaN)
    n1 = np.full(N, NaN)
    n5 = np.full(N, NaN)
    lS = logratio(S, np.ones(N))  # 100 ln S
    for t in range(N):
        if not kept[t]:
            continue
        if same(t - 1, t):
            dSp1[t] = Sp[t] - Sp[t - 1]
        if same(t - 5, t):
            dSp5[t] = Sp[t] - Sp[t - 5]
        if t - 1 >= 0:
            n1[t] = lS[t] - lS[t - 1]
        if t - 5 >= 0:
            n5[t] = lS[t] - lS[t - 5]
    SpK = np.where(kept, Sp, NaN)

    def aligned(*cols):
        mask = kept.copy()
        for c in cols:
            mask &= np.isfinite(c)
        return np.nonzero(mask)[0]

    log = []
    P = log.append
    P(f"joint days N={N} {first}..{last}; kept={int(kept.sum())}; expiries listed={len(expiries)}, with k_X={n_kx}")
    P(f"duplicates skipped spot/c1/c2/tbill = {d1}/{d2}/{d3}/{d4}")

    horizons = {}
    for h in (1, 3, 5):
        idx = aligned(M, D[h])
        x, y = M[idx], D[h][idx]
        m = len(idx)
        b, t, se = simple_reg(x, y, h + 5) if m >= 3 else (None, None, None)
        K, pp, pm, p2 = rotation_p(x, y)
        horizons[str(h)] = {"n": m, "b": b, "nw_t": t, "p_plus": pp, "p_minus": pm, "p2": p2,
                            "mde": (2.80 * se if se is not None else None)}
        sd = float(np.std(x)) if m else NaN
        P(f"h={h}: n={m} K={K} b={b} (per sd {None if b is None else b*sd}) nw_t={t} p+={pp} p-={pm} p2={p2}")
        if h == 5:
            K5, idx5 = K, idx
    b5 = horizons["5"]["b"]
    s = sgn(b5) if b5 is not None else 0
    s = 0 if s is None else s

    # halves
    m5 = len(idx5)
    hm = m5 // 2
    x5, y5 = M[idx5], D[5][idx5]
    bf = simple_reg(x5[:hm], y5[:hm], 10)[0] if hm >= 3 else None
    br = simple_reg(x5[hm:], y5[hm:], 10)[0] if m5 - hm >= 3 else None
    halves = {"n_first": hm, "b_first": bf, "n_rest": m5 - hm, "b_rest": br}
    P(f"halves: {halves}")

    # incremental
    idxI = aligned(M, SpK, dSp1, dSp5, n1, n5, D[5])
    XI = np.column_stack([np.ones(len(idxI)), M[idxI], SpK[idxI], dSp1[idxI], dSp5[idxI], n1[idxI], n5[idxI]])
    g = gt = None
    if len(idxI) > XI.shape[1]:
        beta, se = ols_nw(XI, D[5][idxI], 10)
        if beta is not None:
            g = float(beta[1])
            gt = g / float(se[1]) if se[1] > 0 else NaN
    incremental = {"n": len(idxI), "g": g, "nw_t": gt}
    P(f"incremental: {incremental}")

    # out of sample (same aligned sample as the incremental regression)
    yO = D[5][idxI]
    Xa = XI
    Xb = np.delete(XI, 1, axis=1)
    eb, ea, cw = [], [], []
    for t in range(1000, len(idxI)):
        n_fit = t - 5 + 1  # positions 0..t-5 inclusive
        if n_fit < Xa.shape[1]:
            continue
        bb = np.linalg.lstsq(Xb[:n_fit], yO[:n_fit], rcond=None)[0]
        ba = np.linalg.lstsq(Xa[:n_fit], yO[:n_fit], rcond=None)[0]
        fb = float(Xb[t] @ bb)
        fa = float(Xa[t] @ ba)
        e_b = yO[t] - fb
        e_a = yO[t] - fa
        eb.append(e_b)
        ea.append(e_a)
        cw.append(e_b ** 2 - (e_a ** 2 - (fb - fa) ** 2))
    nf = len(cw)
    r2 = cwm = cwt = None
    if nf > 0:
        sseb = float(np.sum(np.square(eb)))
        ssea = float(np.sum(np.square(ea)))
        r2 = 1.0 - ssea / sseb if sseb > 0 else None
        cwa = np.array(cw)
        cwm = float(cwa.mean())
        if nf > 1:
            beta, se = ols_nw(np.ones((nf, 1)), cwa, 10)
            if beta is not None and se[0] > 0:
                cwt = float(beta[0] / se[0])
    oos = {"n_forecasts": nf, "r2_os": r2, "cw_mean": cwm, "cw_nw_t": cwt}
    P(f"oos: {oos}")

    # size
    if m5 > 0:
        sM = s * x5
        Q = float(np.percentile(sM, 80))
        top = sM >= Q
        n_top = int(top.sum())
        Dq = 0.0 if s == 0 else float(y5[top].mean() - y5.mean())
    else:
        Q, n_top, Dq = None, 0, None
    size = {"Q": Q, "n_top": n_top, "Dq": Dq}
    P(f"size: {size}")

    p2_5 = horizons["5"]["p2"]
    crit = {
        "a": bool(b5 is not None and b5 != 0 and p2_5 is not None and p2_5 <= 0.025),
        "b": bool(sgn(horizons["1"]["b"]) == s and sgn(horizons["3"]["b"]) == s),
        "c": bool(sgn(bf) == s and sgn(br) == s),
        "d": bool(g is not None and sgn(g) == s and gt is not None and abs(gt) >= 2.0),
        "e": bool(r2 is not None and r2 > 0),
        "f": bool(Dq is not None and Dq >= 0.157),
    }
    if K5 < 100:
        verdict = "UNSCORABLE"
    elif not crit["a"]:
        verdict = "FAIL"
    elif all(crit.values()):
        verdict = "PASS"
    else:
        verdict = "WEAK"
    P(f"criteria: {crit}; s={s}; verdict={verdict}")

    res = {"horizons": horizons, "s": s, "halves": halves, "incremental": incremental,
           "oos": oos, "size": size, "criteria": crit, "verdict": verdict}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify_b.json"), "w") as fh:
        json.dump(clean(res), fh, indent=2)
    for line in log:
        print(line)
    print("ambiguities resolved (literal reading):")
    for x in AMBIGUITIES:
        print("  " + x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
