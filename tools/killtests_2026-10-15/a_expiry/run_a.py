"""Frozen test A: the spot residual in the last days of a futures contract as a predictor of that
contract's return to expiry. Implements PREREG.md (test A) sections 2 to 8.
Usage: python run_a.py --data data --out out
"""
import argparse
import bisect
import datetime as dt
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cal  # noqa: E402
import kt  # noqa: E402

ALPHA2 = 0.025
OOS_START = 400
L = 5
ES = [1, 2, 3, 4]


def rate_series(tb, dates):
    tbd = sorted(d for d, v in tb.items() if np.isfinite(v[0]))
    RATE = np.full(len(dates), np.nan)
    for t, d in enumerate(dates):
        k = bisect.bisect_right(tbd, d) - 1
        if k >= 0:
            RATE[t] = tb[tbd[k]][0]
    return RATE


def build(asset, data_dir, tb):
    spot = kt.read(os.path.join(data_dir, f"{asset}_spot.csv"), 2)
    c1 = kt.read(os.path.join(data_dir, f"{asset}_c1.csv"), 2)
    c2p = os.path.join(data_dir, f"{asset}_c2.csv")
    c2 = kt.read(c2p, 2) if os.path.exists(c2p) else None
    dates = sorted(d for d in set(spot) & set(c1) if np.isfinite(spot[d][0]) and np.isfinite(c1[d][0]))
    N = len(dates)
    S = np.array([spot[d][0] for d in dates])
    F = np.array([c1[d][0] for d in dates])
    F2 = np.array([c2[d][0] if (c2 is not None and d in c2) else np.nan for d in dates])
    r = rate_series(tb, dates) / 100.0
    d0, d1 = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    last_month = (d1 + dt.timedelta(days=32)).replace(day=1)
    allx = sorted(set(cal.expiry_for_delivery(asset, y, m) for (y, m) in cal.months_between(d0, last_month)))
    xs = []
    for X in allx:
        if X > d1:
            continue
        k = bisect.bisect_right(dates, X.isoformat()) - 1
        if k < 0:
            continue
        xs.append((X, k))
    # window days and quantities
    e_of = np.full(N, -1)
    xid = np.full(N, -1)
    tau = np.full(N, np.nan)
    prev_last = -1
    prev_k = {}
    for i, (X, k) in enumerate(xs):
        for t in range(max(0, k - 4), k + 1):
            if e_of[t] == -1:           # the earlier expiry keeps the day if windows overlapped
                e_of[t] = k - t
                xid[t] = i
                tau[t] = (X - dt.date.fromisoformat(dates[t])).days / 365.0
        prev_k[i] = xs[i - 1][1] if i > 0 else -1
    Fstar = S * np.exp(r * tau)
    M = np.where((e_of >= 0) & np.isfinite(tau) & np.isfinite(r), 100.0 * (F / Fstar - 1.0), np.nan)
    lF, lS = np.log(F), np.log(S)
    Y = np.full(N, np.nan)
    m1 = np.full(N, np.nan)
    m5 = np.full(N, np.nan)
    for t in range(N):
        i = xid[t]
        if i < 0 or e_of[t] == 0:
            continue
        k = xs[i][1]
        Y[t] = 100.0 * (lF[k] - lF[t])
        pk = prev_k[i]
        if t - 1 > pk and t - 1 >= 0:
            m1[t] = 100.0 * (lF[t] - lF[t - 1])
        if t - 5 > pk and t - 5 >= 0:
            m5[t] = 100.0 * (lF[t] - lF[t - 5])
    n1 = 100 * kt.lagd(lS, 1)
    n5 = 100 * kt.lagd(lS, 5)
    signal = (e_of >= 1)
    return {"dates": np.array(dates), "N": N, "S": S, "F": F, "F2": F2, "M": M, "Y": Y, "m1": m1, "m5": m5,
            "n1": n1, "n5": n5, "e": e_of, "xid": xid, "xs": xs, "allx": allx, "r": r, "signal": signal, "tau": tau}


def test_asset(asset, B):
    darr, N = B["dates"], B["N"]
    M, Y, e = B["M"], B["Y"], B["e"]
    signal = B["signal"]
    years = np.array([d[:4] for d in darr])

    def al(mask, *arrs):
        m_ = mask.copy()
        for v in arrs:
            m_ &= np.isfinite(v)
        return m_

    res = {"calendar": {"joint_days": int(N), "first": str(darr[0]), "last": str(darr[-1]), "expiries_used": len(B["xs"]),
                        "signal_days": int(signal.sum()), "M_defined_on_signal_days": int(np.sum(signal & np.isfinite(M)))}}
    mk = al(signal, M, Y)
    pooled = kt.slope_stats(M[mk], Y[mk], L)
    s = kt.sign(pooled["slope"])
    H = {"pooled": pooled, "sign": s, "by_e": {}}
    for ee in ES:
        mm = al(signal & (e == ee), M, Y)
        H["by_e"][str(ee)] = kt.slope_stats(M[mm], Y[mm], L)
    for lab, es_ in (("e12", (1, 2)), ("e34", (3, 4))):
        mm = al(signal & np.isin(e, es_), M, Y)
        H[lab] = {"n": int(mm.sum()), "slope": kt.slope_only(M[mm], Y[mm])}
    x5, y5, yr5, d5 = M[mk], Y[mk], years[mk], darr[mk]
    half = len(x5) // 2
    H["halves"] = {"first": {"n": half, "slope": kt.slope_only(x5[:half], y5[:half])},
                   "second": {"n": len(x5) - half, "slope": kt.slope_only(x5[half:], y5[half:])}}
    mi = al(signal, M, B["m1"], B["m5"], Y)
    if mi.sum() > 10:
        beta, se, r2a = kt.reg(Y[mi], [M[mi], B["m1"][mi], B["m5"][mi]], L)
        _, _, r2b = kt.reg(Y[mi], [B["m1"][mi], B["m5"][mi]], L)
        H["incremental"] = {"n": int(mi.sum()), "coef": dict(zip(["const", "signal", "m1", "m5"], map(float, beta))),
                            "nw_t": dict(zip(["const", "signal", "m1", "m5"], map(float, beta / se))),
                            "r2_augmented": r2a, "r2_baseline": r2b}
        Mb = np.column_stack([B["m1"][mi], B["m5"][mi]])
        if mi.sum() > OOS_START + 5:
            fb, fa, yy = kt.oos(Y[mi], M[mi], Mb, OOS_START, 5)
            r2 = 1.0 - float(((yy - fa) ** 2).sum()) / float(((yy - fb) ** 2).sum())
            f = (yy - fb) ** 2 - ((yy - fa) ** 2 - (fb - fa) ** 2)
            bcw, secw, _ = kt.reg(f, [], L)
            H["oos"] = {"n_forecasts": int(len(yy)), "r2_os": r2, "cw_mean": float(bcw[0]),
                        "cw_nw_t": float(bcw[0] / secw[0]) if secw[0] > 0 else float("nan"), "first_date": str(darr[mi][OOS_START])}
        else:
            H["oos"] = {"n_forecasts": 0, "r2_os": float("nan"), "cw_mean": float("nan"), "cw_nw_t": float("nan")}
    else:
        H["incremental"] = {"n": int(mi.sum()), "coef": {"signal": float("nan")}, "nw_t": {"signal": float("nan")}}
        H["oos"] = {"n_forecasts": 0, "r2_os": float("nan"), "cw_mean": float("nan"), "cw_nw_t": float("nan")}
    if s == 0 or len(x5) == 0:
        H["size"] = {"threshold": float("nan"), "n_top": 0, "Dq": 0.0}
    else:
        sx = s * x5
        Qthr = float(np.percentile(sx, 80))
        top = sx >= Qthr
        H["size"] = {"threshold": Qthr, "n_top": int(top.sum()), "Dq": float(y5[top].mean() - y5.mean())}
    # section 8
    sec8 = {}
    sec8["baseline_alone"] = {b_: kt.slope_stats(B[b_][al(signal, B[b_], Y)], Y[al(signal, B[b_], Y)], L) for b_ in ("m1", "m5")}
    mi2 = al(signal, M, B["m1"], B["m5"], B["n1"], B["n5"], Y)
    if mi2.sum() > 12:
        beta, se, _ = kt.reg(Y[mi2], [M[mi2], B["m1"][mi2], B["m5"][mi2], B["n1"][mi2], B["n5"][mi2]], L)
        sec8["with_spot_momentum"] = {"n": int(mi2.sum()), "g": float(beta[1]), "nw_t": float(beta[1] / se[1])}
    # item 3: away from the window, the parent's null on settlement data
    kept = np.ones(N, dtype=bool)
    for X, k in B["xs"]:
        kept[max(0, k - 4): min(N, k + 2)] = False
    allx_iso = sorted(X.isoformat() for X in B["allx"])
    r = B["r"]
    lF = np.log(B["F"])
    Mk = np.full(N, np.nan)
    Xk = np.full(N, -1)
    Q4 = np.full(N, np.nan)
    for t in range(N):
        if not kept[t]:
            continue
        kx = bisect.bisect_right(allx_iso, darr[t])
        if kx < len(allx_iso):
            Xk[t] = kx
            tt = (dt.date.fromisoformat(allx_iso[kx]) - dt.date.fromisoformat(darr[t])).days / 365.0
            if np.isfinite(r[t]):
                Mk[t] = 100.0 * (B["F"][t] / (B["S"][t] * np.exp(r[t] * tt)) - 1.0)
    for t in range(N - 4):
        if kept[t] and kept[t + 4] and Xk[t] >= 0 and Xk[t + 4] == Xk[t]:
            Q4[t] = 100.0 * (lF[t + 4] - lF[t])
    mq = np.isfinite(Mk) & np.isfinite(Q4)
    sec8["control_away_from_window_Q4_on_M"] = kt.slope_stats(Mk[mq], Q4[mq], 9)
    lvl = {}
    for ee in ES + [0]:
        mm = (e == ee) & np.isfinite(M)
        v = M[mm]
        lvl[str(ee)] = {"n": int(mm.sum()), "mean": float(v.mean()) if len(v) else float("nan"), "median": float(np.median(v)) if len(v) else float("nan"),
                        "sd": float(v.std()) if len(v) else float("nan"), "p5": float(np.percentile(v, 5)) if len(v) else float("nan"),
                        "p95": float(np.percentile(v, 95)) if len(v) else float("nan"), "share_positive": float(np.mean(v > 0)) if len(v) else float("nan")}
    sec8["level_of_M_by_e"] = lvl
    reg_ = {"per_year": {}}
    for y in sorted(set(yr5)):
        s_ = yr5 == y
        if s_.sum() >= 20:
            reg_["per_year"][y] = {"n": int(s_.sum()), "slope": kt.slope_only(x5[s_], y5[s_])}
    xm = np.array([B["xs"][i][0].month for i in B["xid"][mk]])
    heat = np.isin(xm, [10, 11, 12, 1, 2])
    reg_["heating_delivery_nov_mar"] = {"in": {"n": int(heat.sum()), "slope": kt.slope_only(x5[heat], y5[heat])},
                                        "out": {"n": int((~heat).sum()), "slope": kt.slope_only(x5[~heat], y5[~heat])}}
    vol = np.full(N, np.nan)
    for t in range(20, N):
        vol[t] = np.std(B["n1"][t - 19: t + 1])
    med = float(np.nanmedian(vol))
    hv = vol[mk] > med
    reg_["vol"] = {"high": {"n": int(hv.sum()), "slope": kt.slope_only(x5[hv], y5[hv])}, "low": {"n": int((~hv).sum()), "slope": kt.slope_only(x5[~hv], y5[~hv])}}
    sec8["regimes"] = reg_
    cut = int(np.floor(0.7 * len(x5)))
    sec8["holdout_last30"] = {"n": len(x5) - cut, "slope": kt.slope_only(x5[cut:], y5[cut:])}
    if len(x5) > 10:
        dev = np.abs(x5 - np.median(x5))
        c99 = float(np.percentile(dev, 99))
        loo = {y: kt.slope_only(x5[yr5 != y], y5[yr5 != y]) for y in sorted(set(yr5))}
        fin = {k: v for k, v in loo.items() if np.isfinite(v)}
        sec8["influence"] = {"trim_slope": kt.slope_only(x5[dev < c99], y5[dev < c99]), "trim_dropped": int((dev >= c99).sum()),
                             "loo_min": {"year": min(fin, key=fin.get), "slope": min(fin.values())} if fin else {},
                             "loo_max": {"year": max(fin, key=fin.get), "slope": max(fin.values())} if fin else {}}
        qb = np.percentile(x5, [20, 40, 60, 80])
        qq = np.searchsorted(qb, x5, side="left") + 1
        sec8["quintiles"] = {"breakpoints": list(map(float, qb)),
                             "Y": {str(k): {"n": int((qq == k).sum()), "mean": float(y5[qq == k].mean()) if (qq == k).any() else float("nan")} for k in range(1, 6)}}
    # item 9: switch check
    if np.isfinite(B["F2"]).any():
        lF2 = np.log(B["F2"])
        hits = {0: 0, 1: 0, 2: 0}
        tot = 0
        for X, k in B["xs"]:
            if k + 2 >= N or k - 1 < 0:
                continue
            if not all(np.isfinite([lF[k - 1], lF[k], lF[k + 1], lF[k + 2], lF2[k - 1], lF2[k], lF2[k + 1]])):
                continue
            tot += 1
            for off in (0, 1, 2):
                t = k + off
                if abs(lF[t] - lF2[t - 1]) < abs(lF[t] - lF[t - 1]):
                    hits[off] += 1
        sec8["switch_check"] = {"expiries": tot, "share_switch_at_kX": hits[0] / tot if tot else float("nan"),
                                "share_switch_at_kX_plus_1": hits[1] / tot if tot else float("nan"),
                                "share_switch_at_kX_plus_2": hits[2] / tot if tot else float("nan")}
    # verdict
    crit = {
        "a_primary": bool(s != 0 and np.isfinite(pooled["p2"]) and pooled["p2"] <= ALPHA2),
        "b_horizons": bool(s != 0 and kt.sign(H["e12"]["slope"]) == s and kt.sign(H["e34"]["slope"]) == s),
        "c_halves": bool(s != 0 and kt.sign(H["halves"]["first"]["slope"]) == s and kt.sign(H["halves"]["second"]["slope"]) == s),
        "d_incremental": bool(s != 0 and kt.sign(H["incremental"]["coef"]["signal"]) == s
                              and np.isfinite(H["incremental"]["nw_t"]["signal"]) and abs(H["incremental"]["nw_t"]["signal"]) >= 2.0),
        "e_oos": bool(np.isfinite(H["oos"]["r2_os"]) and H["oos"]["r2_os"] > 0),
        "f_size": bool(s != 0 and H["size"]["Dq"] >= kt.FLOOR),
    }
    if pooled["shifts"] < 100:
        crit = {k: False for k in crit}
        v = "UNSCORABLE"
    elif all(crit.values()):
        v = "PASS"
    elif crit["a_primary"]:
        v = "WEAK"
    else:
        v = "FAIL"
    H["criteria"], H["verdict"] = crit, f"{v} (sign {'+' if s > 0 else '-' if s < 0 else '0'})"
    res["hypothesis"], res["section8"] = H, sec8
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", default="ng,ho,rb")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tb = kt.read(os.path.join(a.data, "tbill.csv"), 2)
    out = {"primary_asset": "ng", "replication_assets_no_weight": ["ho", "rb"], "assets": {}}
    for asset in a.assets.split(","):
        B = build(asset, a.data, tb)
        out["assets"][asset] = test_asset(asset, B)
    with open(os.path.join(a.out, "results_a.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, allow_nan=True)
    for asset, res in out["assets"].items():
        c = res["calendar"]
        H = res["hypothesis"]
        tag = "PRIMARY" if asset == "ng" else "replication, no weight"
        print(f"=== A {asset} ({tag}): joint {c['joint_days']} {c['first']}..{c['last']}; expiries {c['expiries_used']}; signal days {c['signal_days']}; M defined {c['M_defined_on_signal_days']}")
        p = H["pooled"]
        print(f"  pooled: n={p['n']} slope={kt.fmt(p['slope'])} per_sd={kt.fmt(p.get('slope_per_sd'))} NW t={kt.fmt(p['nw_t'])} p2={p['p2']:.4f} MDE={kt.fmt(p['mde'])} sign {H['sign']:+d}")
        print("  by e:", " ".join(f"e={ee} n={H['by_e'][str(ee)]['n']} b={kt.fmt(H['by_e'][str(ee)]['slope'])} t={kt.fmt(H['by_e'][str(ee)]['nw_t'])};" for ee in ES),
              f"e12 {kt.fmt(H['e12']['slope'])} e34 {kt.fmt(H['e34']['slope'])}")
        i, o, sz = H["incremental"], H["oos"], H["size"]
        print(f"  incremental g={kt.fmt(i['coef']['signal'])} t={kt.fmt(i['nw_t']['signal'])}; OOS n={o['n_forecasts']} R2_OS={kt.fmt(o['r2_os'])} CW t={kt.fmt(o['cw_nw_t'])}; "
              f"size Dq={kt.fmt(sz['Dq'])} (n_top {sz['n_top']}); halves {kt.fmt(H['halves']['first']['slope'])} / {kt.fmt(H['halves']['second']['slope'])}")
        s8 = res["section8"]
        ctl = s8["control_away_from_window_Q4_on_M"]
        print(f"  control away from window (Q4 on M): n={ctl['n']} slope={kt.fmt(ctl['slope'])} t={kt.fmt(ctl['nw_t'])} p2={ctl['p2'] if np.isfinite(ctl['p2']) else float('nan'):.4f}")
        if "switch_check" in s8:
            sc = s8["switch_check"]
            print(f"  switch check: {sc['expiries']} expiries; share at k_X {sc['share_switch_at_kX']:.3f}, k_X+1 {sc['share_switch_at_kX_plus_1']:.3f}, k_X+2 {sc['share_switch_at_kX_plus_2']:.3f}")
        if "quintiles" in s8:
            print("  quintile means Y:", [round(s8["quintiles"]["Y"][str(k)]["mean"], 3) for k in range(1, 6)])
        print("  criteria", json.dumps(H["criteria"]), "VERDICT:", H["verdict"])


if __name__ == "__main__":
    main()
