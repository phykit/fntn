"""Frozen test: the futures residual over spot (financing only) as a predictor of the spot price,
US energy. Implements PREREG.md sections 2 to 8 and applies the verdict rule of section 7
mechanically. Usage: python run.py --data data --out out

Reads data/<asset>_spot.csv (DATE,VALUE), data/<asset>_fut.csv (DATE,CLOSE) for asset in ng, ho,
rb, and data/tbill.csv (DATE,RATE). Writes out/results.json and prints a log of derived statistics
only. No observation of any input is printed or stored.
"""
import argparse
import bisect
import csv
import datetime as dt
import json
import os

import numpy as np

HORIZONS = [1, 5, 20]
PRIMARY = 5
MIN_SHIFT = 21
ALPHA2 = 0.0125          # two-sided, per hypothesis (family-wise 2.5% over two hypotheses)
OOS_START = 1000
FLOOR = 0.157
EXCL_BEFORE, EXCL_AFTER = 4, 1
ROLL_JUMP = 5.0          # pp, section 8 item 5
ASSETS = ["ng", "ho", "rb"]
MOM = ["n1", "n5", "n20"]


def num(v):
    v = v.strip()
    return float("nan") if v in ("", ".") else float(v.replace(",", ""))


def read(path, ncols):
    out = {}
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        if len(hdr) < ncols:
            raise SystemExit(f"{path}: expected {ncols} columns, header {hdr}")
        for row in rd:
            if not row or not row[0].strip():
                continue
            d = row[0].strip()
            if d in out:
                raise SystemExit(f"{path}: duplicate date {d}")
            out[d] = [num(row[k]) if k < len(row) else float("nan") for k in range(1, ncols)]
    return out


# ---- estimators (section 4) --------------------------------------------------------------------

def ols(y, X):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    return beta, y - X @ beta, XtX_inv


def nw_se(X, resid, XtX_inv, L):
    m = len(resid)
    Xe = X * resid[:, None]
    S = Xe.T @ Xe
    for l in range(1, L + 1):
        if l >= m:
            break
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        S += w * (G + G.T)
    return np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))


def reg(y, cols, L):
    X = np.column_stack([np.ones(len(y))] + list(cols))
    beta, resid, XtX_inv = ols(y, X)
    se = nw_se(X, resid, XtX_inv, L)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / tss if tss > 0 else float("nan")
    return beta, se, r2


def slope_only(x, y):
    xc = x - x.mean()
    den = float(xc @ xc)
    return float((xc @ (y - y.mean())) / den) if den > 0 else float("nan")


def rot_slopes(x, y):
    m = len(x)
    xc, yc = x - x.mean(), y - y.mean()
    den = xc @ xc
    return np.array([(np.roll(xc, -k) @ yc) / den for k in range(MIN_SHIFT, m - MIN_SHIFT + 1)])


def pvals(obs, rot):
    rot = rot[np.isfinite(rot)]
    K = len(rot)
    pp = float((1 + np.sum(rot >= obs)) / (1 + K))
    pm = float((1 + np.sum(rot <= obs)) / (1 + K))
    return {"shifts": int(K), "p_plus": pp, "p_minus": pm, "p2": min(1.0, 2.0 * min(pp, pm))}


def sign(b):
    if not np.isfinite(b):
        return 0
    return 1 if b > 0 else (-1 if b < 0 else 0)


def slope_stats(x, y, L):
    if len(x) < 2 * MIN_SHIFT + 2 or x.std() == 0:
        return {"n": int(len(x)), "slope": float("nan"), "nw_t": float("nan"), "p_plus": float("nan"),
                "p_minus": float("nan"), "p2": float("nan"), "mde": float("nan")}
    beta, se, _ = reg(y, [x], L)
    b = float(beta[1])
    sd = float(x.std())
    out = {"n": int(len(x)), "slope": b, "slope_per_sd": b * sd, "sd_x": sd,
           "corr": float(np.corrcoef(x, y)[0, 1]), "nw_se": float(se[1]), "nw_t": b / float(se[1]),
           "nw_lag": int(L), "mde": 2.80 * float(se[1])}
    out.update(pvals(b, rot_slopes(x, y)))
    return out


def oos(y, x, M, start, h, with_x=True):
    m = len(y)
    Xb = np.column_stack([np.ones(m), M])
    Xa = np.column_stack([Xb, x]) if with_x else np.ones((m, 1))
    cb_xx = np.cumsum(np.einsum("ti,tj->tij", Xb, Xb), axis=0)
    cb_xy = np.cumsum(Xb * y[:, None], axis=0)
    ca_xx = np.cumsum(np.einsum("ti,tj->tij", Xa, Xa), axis=0)
    ca_xy = np.cumsum(Xa * y[:, None], axis=0)
    fb, fa, yy = [], [], []
    for t in range(start, m):
        last = t - h
        fb.append(float(Xb[t] @ np.linalg.solve(cb_xx[last], cb_xy[last])))
        fa.append(float(Xa[t] @ np.linalg.solve(ca_xx[last], ca_xy[last])))
        yy.append(float(y[t]))
    return tuple(map(np.array, (fb, fa, yy)))


def oos_stats(fb, fa, yy):
    r2 = 1.0 - float(((yy - fa) ** 2).sum()) / float(((yy - fb) ** 2).sum())
    f = (yy - fb) ** 2 - ((yy - fa) ** 2 - (fb - fa) ** 2)
    beta, se, _ = reg(f, [], 10)
    return {"n_forecasts": int(len(yy)), "r2_os": r2, "cw_mean": float(beta[0]),
            "cw_nw_t": float(beta[0] / se[0]) if se[0] > 0 else float("nan")}


# ---- calendar (section 3) ----------------------------------------------------------------------

def expiry_for_delivery(asset, year, month):
    """Expiry of the contract for delivery in (year, month): NG on the third weekday counting back
    from the last day of the preceding month inclusive; HO and RB on the last weekday of it."""
    first = dt.date(year, month, 1)
    d = first - dt.timedelta(days=1)
    need = 3 if asset == "ng" else 1
    n = 0
    while True:
        if d.weekday() < 5:
            n += 1
            if n == need:
                return d
        d -= dt.timedelta(days=1)


def months_between(d0, d1):
    y, m = d0.year, d0.month
    out = []
    while (y, m) <= (d1.year, d1.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def build(asset, data_dir, tb):
    spot = read(os.path.join(data_dir, f"{asset}_spot.csv"), 2)
    fut = read(os.path.join(data_dir, f"{asset}_fut.csv"), 2)
    dates = sorted(d for d in set(spot) & set(fut) if np.isfinite(spot[d][0]) and np.isfinite(fut[d][0]))
    N = len(dates)
    if N < 100:
        raise SystemExit(f"{asset}: joint calendar has only {N} days")
    S = np.array([spot[d][0] for d in dates])
    F = np.array([fut[d][0] for d in dates])
    tbd = sorted(d for d, v in tb.items() if np.isfinite(v[0]))
    RATE = np.full(N, np.nan)
    for t, d in enumerate(dates):
        k = bisect.bisect_right(tbd, d) - 1
        if k >= 0:
            RATE[t] = tb[tbd[k]][0]
    r = RATE / 100.0

    d0, d1 = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    last_month = (d1 + dt.timedelta(days=32)).replace(day=1)   # the month after d1's month
    expiries = [expiry_for_delivery(asset, y, m) for (y, m) in months_between(d0, last_month)]
    expiries = sorted(set(expiries))
    excluded = np.zeros(N, dtype=bool)
    xdates = []
    for X in expiries:
        k = bisect.bisect_right(dates, X.isoformat()) - 1
        if k < 0:
            continue                       # no joint date on or before X: k_X undefined
        xdates.append(X)
        excluded[max(0, k - EXCL_BEFORE): min(N, k + EXCL_AFTER + 1)] = True
    kept = ~excluded
    Xid = np.full(N, -1)
    tau = np.full(N, np.nan)
    xiso = [X.isoformat() for X in xdates]
    for t, d in enumerate(dates):
        if not kept[t]:
            continue
        k = bisect.bisect_right(xiso, d)   # first expiry strictly after d
        if k < len(xiso):
            Xid[t] = k
            tau[t] = (xdates[k] - dt.date.fromisoformat(d)).days / 365.0

    nan = np.full(N, np.nan)
    Fstar = S * np.exp(r * tau)
    M = np.where(kept & np.isfinite(tau) & np.isfinite(r), 100.0 * (F / Fstar - 1.0), np.nan)
    P = np.where(kept, 100.0 * (F / S - 1.0), np.nan)
    dM = nan.copy()
    for t in range(1, N):
        if kept[t] and kept[t - 1] and Xid[t] >= 0 and Xid[t] == Xid[t - 1]:
            dM[t] = M[t] - M[t - 1]
    # the roll step across each exclusion window: first kept day after it minus last kept day before
    steps = []
    t = 0
    while t < N:
        if excluded[t]:
            u = t
            while u < N and excluded[u]:
                u += 1
            if t - 1 >= 0 and u < N and np.isfinite(M[t - 1]) and np.isfinite(M[u]):
                steps.append(M[u] - M[t - 1])
            t = u
        else:
            t += 1
    steps = np.array(steps)

    def lagd(v, k):
        o = nan.copy()
        o[k:] = v[k:] - v[:-k]
        return o

    lS, lF = np.log(S), np.log(F)
    V = {"M": M, "dM": dM, "P": P,
         "n1": 100 * lagd(lS, 1), "n5": 100 * lagd(lS, 5), "n20": 100 * lagd(lS, 20)}
    R, Q = {}, {}
    for h in HORIZONS:
        o = nan.copy()
        o[: N - h] = 100.0 * (lS[h:] - lS[: N - h])
        R[h] = o
        q = nan.copy()
        for t in range(N - h):
            if kept[t] and kept[t + h] and Xid[t] >= 0 and Xid[t] == Xid[t + h]:
                q[t] = 100.0 * (lF[t + h] - lF[t])
        Q[h] = q
    vol = nan.copy()
    for t in range(20, N):
        vol[t] = np.std(V["n1"][t - 19: t + 1])
    return {"dates": np.array(dates), "N": N, "kept": kept, "excluded": excluded, "S": S, "F": F,
            "Fstar": Fstar, "tau": tau, "RATE": RATE, "V": V, "R": R, "Q": Q, "vol": vol,
            "roll_steps": steps, "n_expiries": len(xdates)}


# ---- the test (sections 5, 7, 8) ---------------------------------------------------------------

def al(sample, *arrs):
    m_ = sample.copy()
    for v in arrs:
        m_ &= np.isfinite(v)
    return m_


def test_asset(asset, B):
    V, R, Q, kept, darr = B["V"], B["R"], B["Q"], B["kept"], B["dates"]
    years = np.array([d[:4] for d in darr])
    months = np.array([int(d[5:7]) for d in darr])
    sample = kept.copy()
    res = {"calendar": {"joint_days": int(B["N"]), "first": str(darr[0]), "last": str(darr[-1]),
                        "excluded_days": int(B["excluded"].sum()), "kept_days": int(kept.sum()),
                        "expiries": int(B["n_expiries"]),
                        "rate_missing_on_kept": int(np.sum(kept & ~np.isfinite(B["RATE"]))),
                        "M_defined": int(np.sum(np.isfinite(V["M"])))}}
    hyps = {}
    for hid, sig in (("HL", "M"), ("HC", "dM")):
        x_all = V[sig]
        H = {"signal": sig, "by_h": {}}
        for h in HORIZONS:
            mk = al(sample, x_all, R[h])
            H["by_h"][str(h)] = slope_stats(x_all[mk], R[h][mk], h + 5)
        b = {h: H["by_h"][str(h)]["slope"] for h in HORIZONS}
        s = sign(b[PRIMARY])
        H["sign"] = s
        m5 = al(sample, x_all, R[PRIMARY])
        x5, y5, yr5, mo5 = x_all[m5], R[PRIMARY][m5], years[m5], months[m5]
        half = len(x5) // 2
        H["halves"] = {"first": {"n": half, "from": str(darr[m5][0]), "to": str(darr[m5][half - 1]),
                                 "slope": slope_only(x5[:half], y5[:half])},
                       "second": {"n": len(x5) - half, "from": str(darr[m5][half]), "to": str(darr[m5][-1]),
                                  "slope": slope_only(x5[half:], y5[half:])}}
        mi = al(sample, x_all, *[V[b_] for b_ in MOM], R[PRIMARY])
        beta, se, r2a = reg(R[PRIMARY][mi], [x_all[mi]] + [V[b_][mi] for b_ in MOM], 10)
        _, _, r2b = reg(R[PRIMARY][mi], [V[b_][mi] for b_ in MOM], 10)
        names = ["const", "signal"] + MOM
        H["incremental"] = {"n": int(mi.sum()), "coef": dict(zip(names, map(float, beta))),
                            "nw_t": dict(zip(names, map(float, beta / se))),
                            "r2_augmented": r2a, "r2_baseline": r2b}
        Mb = np.column_stack([V[b_][mi] for b_ in MOM])
        if mi.sum() > OOS_START + 5:
            fb, fa, yy = oos(R[PRIMARY][mi], x_all[mi], Mb, OOS_START, PRIMARY)
            H["oos"] = oos_stats(fb, fa, yy)
            H["oos"]["first_date"] = str(darr[mi][OOS_START])
        else:
            H["oos"] = {"n_forecasts": 0, "r2_os": float("nan"), "cw_mean": float("nan"), "cw_nw_t": float("nan")}
        sx = s * x5
        if s == 0:
            H["size"] = {"threshold": float("nan"), "n_top": 0, "Dq": 0.0}
        else:
            Qthr = float(np.percentile(sx, 80))
            top = sx >= Qthr
            H["size"] = {"threshold": Qthr, "n_top": int(top.sum()), "Dq": float(y5[top].mean() - y5.mean())}
        # section 8 items 2, 6, 7, 8, 9
        trad = {}
        for h in HORIZONS:
            mk = al(sample, x_all, Q[h])
            trad[str(h)] = slope_stats(x_all[mk], Q[h][mk], h + 5)
        mq = al(sample, x_all, Q[PRIMARY])
        xq, yq = s * x_all[mq], Q[PRIMARY][mq]
        if s != 0 and len(xq) > 0:
            Qt = float(np.percentile(xq, 80))
            topq = xq >= Qt
            trad["Dq_Q5"] = float(yq[topq].mean() - yq.mean())
        else:
            trad["Dq_Q5"] = float("nan")
        H["tradable_expression"] = trad
        reg_ = {"per_year": {}, "vol": {}}
        for y in sorted(set(yr5)):
            s_ = yr5 == y
            if s_.sum() >= 20:
                reg_["per_year"][y] = {"n": int(s_.sum()), "slope": slope_only(x5[s_], y5[s_])}
        v5 = B["vol"][m5]
        med = float(np.nanmedian(B["vol"][sample]))
        for lab, s_ in (("high_vol", v5 > med), ("low_vol", v5 <= med)):
            reg_["vol"][lab] = {"n": int(s_.sum()), "slope": slope_only(x5[s_], y5[s_]) if s_.sum() > 2 else float("nan")}
        if asset == "ng":
            heat = (mo5 >= 11) | (mo5 <= 3)
            reg_["season"] = {"heating_nov_mar": {"n": int(heat.sum()), "slope": slope_only(x5[heat], y5[heat])},
                              "other": {"n": int((~heat).sum()), "slope": slope_only(x5[~heat], y5[~heat])}}
        H["regimes"] = reg_
        cut = int(np.floor(0.7 * len(x5)))
        H["holdout_last30"] = {"n": len(x5) - cut, "from": str(darr[m5][cut]), "slope": slope_only(x5[cut:], y5[cut:])}
        dev = np.abs(x5 - np.median(x5))
        c99 = float(np.percentile(dev, 99))
        loo = {y: slope_only(x5[yr5 != y], y5[yr5 != y]) for y in sorted(set(yr5))}
        H["influence"] = {"trim_cut": c99, "trim_dropped": int((dev >= c99).sum()),
                          "trim_slope": slope_only(x5[dev < c99], y5[dev < c99]),
                          "leave_one_year_out": loo,
                          "min": {"year": min(loo, key=loo.get), "slope": min(loo.values())},
                          "max": {"year": max(loo, key=loo.get), "slope": max(loo.values())}}
        qb = np.percentile(x5, [20, 40, 60, 80])
        qq = np.searchsorted(qb, x5, side="left") + 1
        H["quintiles"] = {"breakpoints": list(map(float, qb)),
                          "R5": {str(k): {"n": int((qq == k).sum()), "mean": float(y5[qq == k].mean()) if (qq == k).any() else float("nan")}
                                 for k in range(1, 6)}}
        # verdict (section 7)
        crit = {
            "a_primary": bool(s != 0 and np.isfinite(H["by_h"][str(PRIMARY)]["p2"]) and H["by_h"][str(PRIMARY)]["p2"] <= ALPHA2),
            "b_horizons": bool(s != 0 and sign(b[1]) == s and sign(b[20]) == s),
            "c_halves": bool(s != 0 and sign(H["halves"]["first"]["slope"]) == s and sign(H["halves"]["second"]["slope"]) == s),
            "d_incremental": bool(s != 0 and sign(H["incremental"]["coef"]["signal"]) == s
                                  and abs(H["incremental"]["nw_t"]["signal"]) >= 2.0),
            "e_oos": bool(np.isfinite(H["oos"]["r2_os"]) and H["oos"]["r2_os"] > 0),
            "f_size": bool(s != 0 and H["size"]["Dq"] >= FLOOR),
        }
        if all(crit.values()):
            v = "PASS"
        elif crit["a_primary"]:
            v = "WEAK"
        else:
            v = "FAIL"
        H["criteria"], H["verdict"] = crit, f"{v} (sign {'+' if s > 0 else '-' if s < 0 else '0'})"
        hyps[hid] = H
    res["hypotheses"] = hyps

    # section 8 items 1, 3, 4, 5
    alone = {}
    for b_ in MOM:
        alone[b_] = {}
        for h in HORIZONS:
            mk = al(sample, V[b_], R[h])
            alone[b_][str(h)] = slope_stats(V[b_][mk], R[h][mk], h + 5)
    mk = al(sample, *[V[b_] for b_ in MOM], R[PRIMARY])
    if mk.sum() > OOS_START + 5:
        Mm = np.column_stack([V[b_][mk] for b_ in MOM])
        fmom, fmean, yy2 = oos(R[PRIMARY][mk], None, Mm, OOS_START, PRIMARY, with_x=False)
        alone["momentum_only_vs_mean_r2_os"] = 1.0 - float(((yy2 - fmom) ** 2).sum()) / float(((yy2 - fmean) ** 2).sum())
    res["momentum_alone"] = alone
    raw = {}
    for h in HORIZONS:
        mk = al(sample, V["P"], R[h])
        raw[str(h)] = slope_stats(V["P"][mk], R[h][mk], h + 5)
    res["raw_premium_P"] = raw
    mk = al(sample, V["M"])
    Ms = V["M"][mk]
    carry = 1e4 * np.log(B["F"][mk] / B["Fstar"][mk]) / B["tau"][mk]
    res["level_of_M"] = {"n": int(mk.sum()), "M_mean": float(Ms.mean()), "M_median": float(np.median(Ms)),
                         "M_p5": float(np.percentile(Ms, 5)), "M_p95": float(np.percentile(Ms, 95)),
                         "M_sd": float(Ms.std()), "share_M_positive": float(np.mean(Ms > 0)),
                         "tau_mean_days": float(np.mean(B["tau"][mk]) * 365),
                         "carry_bp_pa_mean": float(carry.mean()), "carry_bp_pa_median": float(np.median(carry))}
    mk = al(sample, V["dM"])
    a = np.abs(V["dM"][mk])
    st = np.abs(B["roll_steps"])
    res["roll_check"] = {"n_dM": int(mk.sum()), "max_abs_dM": float(a.max()) if len(a) else float("nan"),
                         "p99_abs_dM": float(np.percentile(a, 99)) if len(a) else float("nan"),
                         "count_abs_dM_over_5pp": int((a > ROLL_JUMP).sum()),
                         "n_roll_steps": int(len(st)),
                         "median_abs_roll_step": float(np.median(st)) if len(st) else float("nan"),
                         "roll_steps_over_5pp": int((st > ROLL_JUMP).sum())}
    return res


def fmt(v):
    return "nan" if v is None or not np.isfinite(v) else f"{v:+.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", default=",".join(ASSETS))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tb = read(os.path.join(a.data, "tbill.csv"), 2)
    out = {"primary_asset": "ng", "replication_assets_no_weight": ["ho", "rb"], "assets": {}}
    for asset in a.assets.split(","):
        B = build(asset, a.data, tb)
        out["assets"][asset] = test_asset(asset, B)
    with open(os.path.join(a.out, "results.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, allow_nan=True)
    for asset, res in out["assets"].items():
        c = res["calendar"]
        tag = "PRIMARY" if asset == "ng" else "replication, no weight"
        print(f"=== {asset} ({tag}): joint {c['joint_days']} {c['first']}..{c['last']}; excluded {c['excluded_days']}; "
              f"kept {c['kept_days']}; M defined {c['M_defined']}; rate missing on kept {c['rate_missing_on_kept']}")
        L = res["level_of_M"]
        rc = res["roll_check"]
        print(f"  M mean {L['M_mean']:+.3f} median {L['M_median']:+.3f} sd {L['M_sd']:.3f} p5 {L['M_p5']:+.3f} p95 {L['M_p95']:+.3f} "
              f"share>0 {L['share_M_positive']:.3f}; tau mean {L['tau_mean_days']:.1f} d; carry {L['carry_bp_pa_median']:+.0f} bp/yr median")
        print(f"  roll check: n {rc['n_dM']} max|dM| {fmt(rc['max_abs_dM'])} p99 {fmt(rc['p99_abs_dM'])} "
              f">5pp {rc['count_abs_dM_over_5pp']}; roll steps {rc['n_roll_steps']} median|step| {fmt(rc['median_abs_roll_step'])} "
              f">5pp {rc['roll_steps_over_5pp']}")
        for hid, H in res["hypotheses"].items():
            print(f"  {hid} ({H['signal']}) sign {H['sign']:+d}")
            for h in HORIZONS:
                t = H["by_h"][str(h)]
                print(f"    h={h} n={t['n']} slope/pp={fmt(t['slope'])} per_sd={fmt(t.get('slope_per_sd'))} "
                      f"NW t={fmt(t['nw_t'])} p+={t['p_plus']:.4f} p-={t['p_minus']:.4f} p2={t['p2']:.4f} MDE={fmt(t['mde'])}")
            i, o, sz = H["incremental"], H["oos"], H["size"]
            print(f"    incremental g={fmt(i['coef']['signal'])} t={fmt(i['nw_t']['signal'])}; OOS n={o['n_forecasts']} "
                  f"R2_OS={fmt(o['r2_os'])} CW t={fmt(o['cw_nw_t'])}; size Dq={fmt(sz['Dq'])} (n_top {sz['n_top']}); "
                  f"halves {fmt(H['halves']['first']['slope'])} / {fmt(H['halves']['second']['slope'])}")
            tr = H["tradable_expression"]
            print(f"    futures Q: " + " ".join(f"h={h} b={fmt(tr[str(h)]['slope'])} t={fmt(tr[str(h)]['nw_t'])} p2={tr[str(h)]['p2']:.4f};"
                                               for h in HORIZONS) + f" Dq_Q5={fmt(tr['Dq_Q5'])}")
            print("    criteria", json.dumps(H["criteria"]), "VERDICT:", H["verdict"])


if __name__ == "__main__":
    main()
