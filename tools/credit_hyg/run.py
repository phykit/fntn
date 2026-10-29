"""Frozen test (PREREG.md governs): 20-day HYG-minus-IEF credit excess return against the next 20
days of QQQ, with the warning-rule description of section 4.

Usage: python run.py --data DATA_DIR --out OUT_DIR   (DATA_DIR/prices.csv: DATE,HYG,IEF,QQQ)

Choices where the PREREG is silent, fixed here before any data was retrieved:
- aligned sample: every t with S_t and F_t defined; halves are the first floor(n/2) and the rest;
- shift slopes are computed on the aligned arrays with S rolled by k (np.roll);
- rule timing: the signal at the close of t acts at the close of t+1, so day t+1's return is still
  earned and the new position applies from t+2; the 10 bp cost is charged on the day t+1 return;
- percentiles: numpy default (linear) over all S_0..S_t defined, signals only once 504 S values exist;
- false alarm: an exit (at the close of t+1) with QQQ higher 20 trading days after that close;
- missed decline: a QQQ peak-to-trough fall of 10% or more (troughs between successive new highs, in
  the evaluation window) where the rule held QQQ over the trough day's return;
- return given up while out: QQQ's summed log return over the days the rule was out.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

import numpy as np

W, H, LAG, NW_L, MINSHIFT, BURN = 20, 20, 1, 20, 250, 504
COST = 0.001


def load(path):
    rows = [r for r in csv.DictReader(open(path, newline=""))
            if r["HYG"].strip() and r["IEF"].strip() and r["QQQ"].strip()]
    d = [r["DATE"] for r in rows]
    px = {k: np.array([float(r[k]) for r in rows]) for k in ("HYG", "IEF", "QQQ")}
    return d, px


def nw(y, X, L):
    X = np.column_stack([np.ones(len(y)), X])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    XtX = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += w * (G + G.T)
    se = np.sqrt(np.diag(XtX @ S @ XtX))
    return b, se


def slope(y, x):
    xc = x - x.mean()
    return float((xc * (y - y.mean())).sum() / (xc * xc).sum())


def roll_sum(x, w):
    c = np.concatenate([[0.0], np.cumsum(x)])
    out = np.full(len(x), np.nan)
    out[w - 1:] = c[w:] - c[:-w]
    return out


def fwd(q, start, h):
    """F_t = q_(t+start) + ... + q_(t+start+h-1)."""
    n = len(q)
    c = np.concatenate([[0.0], np.cumsum(q)])
    out = np.full(n, np.nan)
    for t in range(n):
        a, b = t + start, t + start + h - 1
        if b < n:
            out[t] = c[b + 1] - c[a]
    return out


def shift_p(y, x):
    b = slope(y, x)
    n = len(x)
    ks = range(MINSHIFT, n - MINSHIFT + 1)
    sl = np.array([slope(y, np.roll(x, k)) for k in ks])
    return b, float((1 + np.sum(sl >= b)) / (1 + len(sl))), len(sl)


def rule(sig, q, start_idx):
    """Section 4.4: out at <= expanding 10th pct, back above expanding 50th pct; acts one close later."""
    n = len(q)
    pos = np.ones(n, bool)  # position held over day t's return
    hist = []
    inv, pending = True, None
    exits, false_al = 0, 0
    r = np.zeros(n)
    for t in range(n):
        pos[t] = inv
        r[t] = (np.exp(q[t]) - 1) if inv else 0.0
        if pending is not None and pending[0] == t:  # switch at this close
            inv = pending[1]
            r[t] -= COST
            if not inv:
                exits += 1
                if t + 20 < n and q[t + 1:t + 21].sum() > 0:
                    false_al += 1
            pending = None
        if not np.isnan(sig[t]):
            hist.append(sig[t])
        if t + 1 < n and pending is None and len(hist) >= BURN and not np.isnan(sig[t]):
            p10, p50 = np.percentile(hist, 10), np.percentile(hist, 50)
            if inv and sig[t] <= p10:
                pending = (t + 1, False)
            elif not inv and sig[t] > p50:
                pending = (t + 1, True)
    ev = slice(start_idx, n)
    return pos, r, exits, false_al, ev


def stats(simple):
    w = np.cumprod(1 + simple)
    ann = float(w[-1] ** (252 / len(simple)) - 1)
    path = np.concatenate([[1.0], w])
    mdd = float(np.min(path / np.maximum.accumulate(path)) - 1)
    vol = float(np.sqrt(252) * simple.std(ddof=1))
    return ann, vol, mdd


def declines(q):
    """Peak-to-trough falls of 10% or more; returns trough indices."""
    lvl = np.exp(np.cumsum(q))
    out, peak, trough_i, trough_v = [], lvl[0], None, None
    for i, v in enumerate(lvl):
        if v >= peak:
            if trough_v is not None and trough_v / peak_at - 1 <= -0.10:
                out.append(trough_i)
            peak, trough_i, trough_v, peak_at = v, None, None, v
        else:
            if trough_v is None or v < trough_v:
                trough_i, trough_v = i, v
                peak_at = peak
    if trough_v is not None and trough_v / peak_at - 1 <= -0.10:
        out.append(trough_i)
    return out


def rule_report(sig, q, burn_start):
    pos, r, exits, fa, ev = rule(sig, q, burn_start)
    qe, re_, pe = q[ev], r[ev], pos[ev]
    ann, vol, mdd = stats(re_)
    tr = declines(qe)
    missed = sum(bool(pe[i]) for i in tr)
    return {"ann_return": ann, "volatility": vol, "max_drawdown": mdd, "invested_share": float(pe.mean()),
            "exits": exits, "false_alarms": fa, "declines_10pct": len(tr), "missed_declines": missed,
            "qqq_logret_while_out": float(qe[~pe].sum())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    d, px = load(os.path.join(a.data, "prices.csv"))
    lr = {k: np.diff(np.log(v)) for k, v in px.items()}  # return t is day t+1's; dates shift with it
    d = d[1:]
    c, q = lr["HYG"] - lr["IEF"], lr["QQQ"]
    S, M = roll_sum(c, W), roll_sum(q, W)
    F = fwd(q, 1 + LAG, H)
    ok = ~np.isnan(S) & ~np.isnan(F) & ~np.isnan(M)
    y, x, m = F[ok], S[ok], M[ok]
    n = len(y)
    res = {"n": int(n), "first": d[int(np.argmax(ok))], "last_signal": d[int(np.where(ok)[0][-1])], "last_price": d[-1]}
    b, p, ns = shift_p(y, x)
    res.update({"b": b, "p_shift": p, "n_shifts": ns})
    bi, si = nw(y, np.column_stack([x, m]), NW_L)
    res["b_incremental"], res["t_incremental"] = float(bi[1]), float(bi[1] / si[1])
    h = n // 2
    res["b_half1"], res["b_half2"] = slope(y[:h], x[:h]), slope(y[h:], x[h:])
    for hz in (5, 10):
        Fh = fwd(q, 1 + LAG, hz)
        okh = ~np.isnan(S) & ~np.isnan(Fh)
        res[f"b_h{hz}"] = slope(Fh[okh], S[okh])
    crit = {"a": b > 0 and p <= 0.025, "b": res["b_incremental"] > 0 and res["t_incremental"] >= 2.0,
            "c": res["b_half1"] > 0 and res["b_half2"] > 0, "d": res["b_h5"] > 0 and res["b_h10"] > 0}
    res["criteria"] = crit
    res["verdict"] = "PASS" if all(crit.values()) else ("WEAK" if crit["a"] else "FAIL")
    # section 4, no weight
    okc = ~np.isnan(c) & ~np.isnan(q)
    res["corr_contemporaneous"] = float(np.corrcoef(c[okc], q[okc])[0, 1])
    Sn = np.full(len(S), np.nan)
    Sn[:-(1 + LAG + W - 1) or None] = S[1 + LAG + W - 1:]
    okr = ~np.isnan(Sn) & ~np.isnan(M)
    br, sr = nw(Sn[okr], M[okr], NW_L)
    res["reverse_b"], res["reverse_t"] = float(br[1]), float(br[1] / sr[1])
    Fi = fwd(q, 1, H)
    oki = ~np.isnan(S) & ~np.isnan(Fi)
    res["b_info"], res["p_info"], _ = shift_p(Fi[oki], S[oki])
    first_s = int(np.argmax(~np.isnan(S)))
    burn_start = first_s + BURN
    qq = np.nan_to_num(q)
    res["rule"] = rule_report(S, qq, burn_start)
    res["mom_rule"] = rule_report(M, qq, burn_start)
    ann, vol, mdd = stats(np.exp(qq[burn_start:]) - 1)
    res["bh"] = {"ann_return": ann, "volatility": vol, "max_drawdown": mdd}
    res["evaluation_start"] = d[burn_start]
    print(json.dumps(res, indent=1, default=str))
    print("VERDICT:", res["verdict"])
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
