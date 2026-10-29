"""Independent second implementation of tools/credit_hyg/PREREG.md, sections 2 to 4.

Written from PREREG.md alone, without reading run.py or any results, so that a
disagreement between the two implementations is evidence of a defect or of an
ambiguity in the pre-registration rather than a shared mistake. Every point at
which the pre-registration admits more than one reading is resolved here and
recorded in the ``choices`` list of verify.json, because an unrecorded choice
is indistinguishable from an error when the two outputs are compared.

Usage: python verify.py --data DIR --out DIR
Input: DIR/prices.csv with columns DATE,HYG,IEF,QQQ (adjusted closes, blank where missing).
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

WINDOW = 20
DELAY = 1          # one day between the signal close and the start of the forward window
NW_LAG = 20
SHIFT_MIN = 250
BURN_IN = 504
COST = 0.001       # 10 bp per switch
LO_PCT = 10.0
HI_PCT = 50.0
DECLINE = 0.10

CHOICES = [
    "Alignment: rows with a blank or non-positive close in any of HYG, IEF, QQQ are dropped before "
    "returns are taken, so a log return spans consecutive aligned days, not consecutive calendar days.",
    "Index: t = 0 is the first aligned day; log returns exist from t = 1; S_t and M_t exist from t = 20.",
    "Primary sample: every t at which S_t and F_t (q_(t+2)..q_(t+21)) both exist; M_t exists on the same "
    "set, so (a), (b) and (c) share one aligned sample of n days.",
    "Circular shift: the rotated series is S shifted forward by k positions with wrap-around "
    "(numpy.roll(S, k)) against unrotated F, k = 250..n-250 inclusive; the count uses slope >= b with no "
    "tolerance; the rotated slope is OLS with intercept on the full n.",
    "Halves: first half is the first floor(n/2) aligned observations, second half the remainder; OLS of F on "
    "S with intercept in each.",
    "Horizons (d): F5_t = q_(t+2)..q_(t+6) and F10_t = q_(t+2)..q_(t+11), each regressed on S_t over its own "
    "maximal sample (every t where S_t and that forward sum exist), not restricted to the 20-day sample.",
    "Newey-West: HAC covariance (X'X)^-1 Omega (X'X)^-1 with Omega = G0 + sum_{l=1..20} (1 - l/21)(G_l + G_l'), "
    "G_l = sum_t u_t u_(t-l) x_t x_(t-l)', no degrees-of-freedom or small-sample correction.",
    "Reverse direction: Y_t = c_(t+2)..c_(t+21) (equal to S_(t+21)) regressed on M_t with intercept over every "
    "t where both exist; reported as b_reverse with Newey-West t (L = 20).",
    "Information convention: F1_t = q_(t+1)..q_(t+20) on S_t over its own maximal sample (n + 1 days); shift p "
    "computed as in (a) with k = 250..n_info-250.",
    "Contemporaneous correlation: Pearson correlation of c_t with q_t over every t >= 1.",
    "Warning rule burn-in: the first 504 observations of the signal (S or M, which both start at t = 20) are "
    "burn-in; the first signal is taken at the 505th observation (t0 = 524). The percentiles at t use all "
    "signal values from the first observation up to and including t (burn-in included), numpy linear "
    "interpolation.",
    "Warning rule states: start invested; if invested and signal_t <= 10th percentile_t, switch out; if out "
    "and signal_t > 50th percentile_t, switch in; otherwise hold. Signals are evaluated for t = t0..N-2.",
    "Warning rule timing: a switch decided at the close of t executes at the close of t+1, so the new "
    "position first earns q_(t+2). The 10 bp cost is charged at the close of t+1 by multiplying that day's "
    "gross wealth by (1 - 0.001).",
    "Evaluation window: return days d = t0+1..N-1 (wealth 1 at the close of t0); buy-and-hold uses QQQ simple "
    "returns over the same days, with no entry cost.",
    "Annual return: prod(1 + r)^(252 / number of return days) - 1 on simple daily returns. Volatility "
    "(ann_vol): sample standard deviation (ddof = 1) of simple daily returns times sqrt(252).",
    "Maximum drawdown: min over the path of W / running max(W) - 1, with W starting at 1 before the first "
    "return day; reported as a NEGATIVE fraction (e.g. -0.35).",
    "Invested share: fraction of evaluation return days on which the position was QQQ.",
    "Exits: number of in-to-out switches decided at t0..N-2 (all of which execute inside the window).",
    "False alarms: an exit decided at t executes at the close of t+1; it is a false alarm if the QQQ close at "
    "t+21 exceeds the close at t+1. Exits whose t+21 lies beyond the sample are not evaluated and not counted "
    "(reported separately as exits_unevaluated).",
    "Missed declines: QQQ drawdown episodes on the close path from t0 to N-1; an episode runs from a running "
    "peak until the close first regains that peak (or the sample ends); its trough is the minimum close in "
    "it; it qualifies if trough / peak - 1 <= -0.10. Missed if the rule held QQQ over the trough day's return "
    "(close of trough-1 to close of trough). n_declines reports the number of qualifying episodes.",
    "Return given up while out: out_qqq_logret is the sum of QQQ log returns over return days on which the "
    "rule was out; rally_given_up is the sum of only the positive ones.",
    "Verdict: PASS if (a)-(d) all hold; WEAK if (a) holds and any other fails; FAIL if (a) fails. Criterion "
    "(a) requires b > 0 and p_shift <= 0.025.",
]


def load(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "prices.csv"))
    df.columns = [c.strip().upper() for c in df.columns]
    for col in ("HYG", "IEF", "QQQ"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.sort_values("DATE")
    ok = df[["HYG", "IEF", "QQQ"]].notna().all(axis=1) & (df[["HYG", "IEF", "QQQ"]] > 0).all(axis=1)
    df = df[ok].reset_index(drop=True)
    return df


def ols(y, X):
    """OLS with intercept; X is (n,) or (n,k) without the constant. Returns coefficients, residuals, design."""
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    Z = np.column_stack([np.ones(len(y)), X])
    coef, *_ = np.linalg.lstsq(Z, y, rcond=None)
    return coef, y - Z @ coef, Z


def nw_t(y, X, lag=NW_LAG):
    coef, u, Z = ols(y, X)
    XtX_inv = np.linalg.inv(Z.T @ Z)
    Zu = Z * u[:, None]
    omega = Zu.T @ Zu
    for l in range(1, lag + 1):
        w = 1.0 - l / (lag + 1.0)
        G = Zu[l:].T @ Zu[:-l]
        omega += w * (G + G.T)
    V = XtX_inv @ omega @ XtX_inv
    se = np.sqrt(np.diag(V))
    return coef, coef / se


def slope(y, x):
    return ols(y, x)[0][1]


def shift_p(F, S, b):
    n = len(S)
    Sc = S - S.mean()
    Fc = F - F.mean()
    denom = Sc @ Sc
    ks = range(SHIFT_MIN, n - SHIFT_MIN + 1)
    count = 0
    total = 0
    for k in ks:
        bk = (np.roll(Sc, k) @ Fc) / denom
        total += 1
        if bk >= b:
            count += 1
    return (1 + count) / (1 + total)


def rolling_sum(x, w):
    """out[t] = x[t-w+1] + ... + x[t]; NaN where any term is missing."""
    out = np.full(len(x), np.nan)
    cs = np.concatenate([[0.0], np.nancumsum(np.where(np.isnan(x), 0.0, x))])
    for t in range(w - 1, len(x)):
        seg = x[t - w + 1:t + 1]
        if not np.isnan(seg).any():
            out[t] = cs[t + 1] - cs[t - w + 1]
    return out


def forward_sum(x, start, length):
    """out[t] = x[t+start] + ... + x[t+start+length-1]."""
    N = len(x)
    out = np.full(N, np.nan)
    for t in range(N):
        a, e = t + start, t + start + length - 1
        if a >= 1 and e <= N - 1:
            out[t] = x[a:e + 1].sum()
    return out


def max_dd(r):
    W = np.concatenate([[1.0], np.cumprod(1.0 + r)])
    return float((W / np.maximum.accumulate(W) - 1.0).min())


def ann(r):
    return float(np.prod(1.0 + r) ** (252.0 / len(r)) - 1.0)


def warning_rule(sig, qlog, price):
    N = len(sig)
    valid = np.where(~np.isnan(sig))[0]
    first = valid[0]
    t0 = first + BURN_IN
    qs = np.expm1(qlog)
    # pos[d] = position held over return day d (close d-1 to close d)
    pos = np.ones(N, dtype=int)
    cost_day = np.zeros(N, dtype=bool)
    state = 1
    exits = []
    for t in range(t0, N - 1):
        hist = sig[first:t + 1]
        p_lo = np.percentile(hist, LO_PCT)
        p_hi = np.percentile(hist, HI_PCT)
        new = state
        if state == 1 and sig[t] <= p_lo:
            new = 0
            exits.append(t)
        elif state == 0 and sig[t] > p_hi:
            new = 1
        if new != state:
            cost_day[t + 1] = True
        state = new
        if t + 2 <= N - 1:
            pos[t + 2] = state
    days = np.arange(t0 + 1, N)
    r = np.where(pos[days] == 1, qs[days], 0.0)
    r = np.where(cost_day[days], (1.0 + r) * (1.0 - COST) - 1.0, r)

    fa = 0
    unevaluated = 0
    for t in exits:
        if t + 21 <= N - 1:
            if price[t + 21] > price[t + 1]:
                fa += 1
        else:
            unevaluated += 1

    # drawdown episodes on QQQ closes t0..N-1
    missed = 0
    n_dec = 0
    peak_i = t0
    i = t0 + 1
    while i <= N - 1:
        if price[i] >= price[peak_i]:
            peak_i = i
            i += 1
            continue
        j = i
        while j <= N - 1 and price[j] < price[peak_i]:
            j += 1
        seg = np.arange(i, j)
        trough = seg[np.argmin(price[seg])]
        if price[trough] / price[peak_i] - 1.0 <= -DECLINE:
            n_dec += 1
            if pos[trough] == 1:
                missed += 1
        if j <= N - 1:
            peak_i = j
        i = j + 1

    out_days = days[pos[days] == 0]
    out_q = qlog[out_days]
    return {
        "ann_return": ann(r),
        "ann_vol": float(np.std(r, ddof=1) * np.sqrt(252.0)),
        "max_drawdown": max_dd(r),
        "invested_share": float((pos[days] == 1).mean()),
        "exits": len(exits),
        "false_alarms": fa,
        "exits_unevaluated": unevaluated,
        "missed_declines": missed,
        "n_declines": n_dec,
        "out_qqq_logret": float(out_q.sum()),
        "rally_given_up": float(out_q[out_q > 0].sum()),
        "first_signal_date_index": int(t0),
        "n_days": int(len(days)),
    }, days, qs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    df = load(a.data)
    N = len(df)
    P = df[["HYG", "IEF", "QQQ"]].to_numpy(float)
    lr = np.full((N, 3), np.nan)
    lr[1:] = np.log(P[1:] / P[:-1])
    h, i, q = lr[:, 0], lr[:, 1], lr[:, 2]
    c = h - i

    S = rolling_sum(c, WINDOW)
    M = rolling_sum(q, WINDOW)
    F = forward_sum(q, 1 + DELAY, WINDOW)
    F5 = forward_sum(q, 1 + DELAY, 5)
    F10 = forward_sum(q, 1 + DELAY, 10)
    F1 = forward_sum(q, 1, WINDOW)
    Yrev = forward_sum(c, 1 + DELAY, WINDOW)

    m = ~np.isnan(S) & ~np.isnan(F) & ~np.isnan(M)
    Sa, Fa, Ma = S[m], F[m], M[m]
    n = int(m.sum())

    b = float(slope(Fa, Sa))
    p_shift = float(shift_p(Fa, Sa, b))
    coef_inc, t_inc = nw_t(Fa, np.column_stack([Sa, Ma]))
    half = n // 2
    b1 = float(slope(Fa[:half], Sa[:half]))
    b2 = float(slope(Fa[half:], Sa[half:]))
    m5 = ~np.isnan(S) & ~np.isnan(F5)
    m10 = ~np.isnan(S) & ~np.isnan(F10)
    b5 = float(slope(F5[m5], S[m5]))
    b10 = float(slope(F10[m10], S[m10]))

    crit = {
        "a_primary": bool(b > 0 and p_shift <= 0.025),
        "b_incremental": bool(coef_inc[1] > 0 and t_inc[1] >= 2.0),
        "c_stability": bool(b1 > 0 and b2 > 0),
        "d_horizons": bool(b5 > 0 and b10 > 0),
    }
    if not crit["a_primary"]:
        verdict = "FAIL"
    elif all(crit.values()):
        verdict = "PASS"
    else:
        verdict = "WEAK"

    mc = ~np.isnan(c) & ~np.isnan(q)
    corr = float(np.corrcoef(c[mc], q[mc])[0, 1])

    mr = ~np.isnan(Yrev) & ~np.isnan(M)
    coef_rev, t_rev = nw_t(Yrev[mr], M[mr])

    mi = ~np.isnan(S) & ~np.isnan(F1)
    b_info = float(slope(F1[mi], S[mi]))
    p_info = float(shift_p(F1[mi], S[mi], b_info))

    price = P[:, 2]
    rule, days, qs = warning_rule(S, q, price)
    mom, _, _ = warning_rule(M, q, price)
    bh_r = qs[days]
    bh = {"ann_return": ann(bh_r), "ann_vol": float(np.std(bh_r, ddof=1) * np.sqrt(252.0)),
          "max_drawdown": max_dd(bh_r)}

    res = {
        "n": n,
        "N_aligned_days": N,
        "start": str(df["DATE"].iloc[0].date()),
        "end": str(df["DATE"].iloc[-1].date()),
        "b": b,
        "p_shift": p_shift,
        "verdict": verdict,
        "criteria": crit,
        "b_incremental": float(coef_inc[1]),
        "t_incremental": float(t_inc[1]),
        "g_momentum": float(coef_inc[2]),
        "t_momentum": float(t_inc[2]),
        "b_half1": b1,
        "b_half2": b2,
        "b_h5": b5,
        "b_h10": b10,
        "corr_contemporaneous": corr,
        "b_reverse": float(coef_rev[1]),
        "t_reverse": float(t_rev[1]),
        "b_info": b_info,
        "p_info": p_info,
        "rule": rule,
        "mom_rule": mom,
        "bh": bh,
        "choices": CHOICES,
    }
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps({k: res[k] for k in ("n", "b", "p_shift", "t_incremental", "b_half1", "b_half2",
                                          "b_h5", "b_h10", "verdict")}, indent=2))


if __name__ == "__main__":
    main()
