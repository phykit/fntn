"""Frozen test B: the spot residual as a predictor of the front-to-second calendar spread, gas.
Implements PREREG.md (test B) sections 2 to 8. Usage: python run_b.py --data data --out out
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
OOS_START = 1000
HOR = [1, 3, 5]
EXCL_BEFORE, EXCL_AFTER = 4, 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    spot = kt.read(os.path.join(a.data, "ng_spot.csv"), 2)
    c1 = kt.read(os.path.join(a.data, "ng_c1.csv"), 2)
    c2 = kt.read(os.path.join(a.data, "ng_c2.csv"), 2)
    tb = kt.read(os.path.join(a.data, "tbill.csv"), 2)
    dates = sorted(d for d in set(spot) & set(c1) & set(c2)
                   if np.isfinite(spot[d][0]) and np.isfinite(c1[d][0]) and np.isfinite(c2[d][0]))
    N = len(dates)
    darr = np.array(dates)
    S = np.array([spot[d][0] for d in dates])
    F1 = np.array([c1[d][0] for d in dates])
    F2 = np.array([c2[d][0] for d in dates])
    tbd = sorted(d for d, v in tb.items() if np.isfinite(v[0]))
    RATE = np.full(N, np.nan)
    for t, d in enumerate(dates):
        k = bisect.bisect_right(tbd, d) - 1
        if k >= 0:
            RATE[t] = tb[tbd[k]][0]
    r = RATE / 100.0
    d0, d1 = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    last_month = (d1 + dt.timedelta(days=32)).replace(day=1)
    allx = sorted(set(cal.expiry_for_delivery("ng", y, m) for (y, m) in cal.months_between(d0, last_month)))
    excluded = np.zeros(N, dtype=bool)
    xdates = []
    for X in allx:
        k = bisect.bisect_right(dates, X.isoformat()) - 1
        if k < 0:
            continue
        xdates.append(X)
        excluded[max(0, k - EXCL_BEFORE): min(N, k + EXCL_AFTER + 1)] = True
    kept = ~excluded
    xiso = [X.isoformat() for X in xdates]
    Xid = np.full(N, -1)
    tau = np.full(N, np.nan)
    for t, d in enumerate(dates):
        if not kept[t]:
            continue
        k = bisect.bisect_right(xiso, d)
        if k < len(xiso):
            Xid[t] = k
            tau[t] = (xdates[k] - dt.date.fromisoformat(d)).days / 365.0
    Fstar = S * np.exp(r * tau)
    M = np.where(kept & np.isfinite(tau) & np.isfinite(r), 100.0 * (F1 / Fstar - 1.0), np.nan)
    Sp = 100.0 * np.log(F2 / F1)
    lS, lF1 = np.log(S), np.log(F1)

    def same(t, u):
        return 0 <= t < N and 0 <= u < N and kept[t] and kept[u] and Xid[t] >= 0 and Xid[t] == Xid[u]

    D = {}
    for h in HOR:
        o = np.full(N, np.nan)
        for t in range(N - h):
            if same(t, t + h):
                o[t] = Sp[t + h] - Sp[t]
        D[h] = o
    dSp1 = np.full(N, np.nan)
    dSp5 = np.full(N, np.nan)
    for t in range(N):
        if same(t, t - 1):
            dSp1[t] = Sp[t] - Sp[t - 1]
        if same(t, t - 5):
            dSp5[t] = Sp[t] - Sp[t - 5]
    Spk = np.where(kept, Sp, np.nan)
    base = {"Sp": Spk, "dSp1": dSp1, "dSp5": dSp5, "n1": 100 * kt.lagd(lS, 1), "n5": 100 * kt.lagd(lS, 5)}
    sample = kept.copy()
    years = np.array([d[:4] for d in dates])
    months = np.array([int(d[5:7]) for d in dates])

    def al(*arrs):
        m_ = sample.copy()
        for v in arrs:
            m_ &= np.isfinite(v)
        return m_

    # sections 5 and 7, with horizons {1, 3, 5}: use the harness on a horizon dict keyed 1, 5, 20 is wrong,
    # so compute directly here.
    H = {"by_h": {}}
    for h in HOR:
        mk = al(M, D[h])
        H["by_h"][str(h)] = kt.slope_stats(M[mk], D[h][mk], h + 5)
    b = {h: H["by_h"][str(h)]["slope"] for h in HOR}
    s = kt.sign(b[5])
    H["sign"] = s
    m5 = al(M, D[5])
    x5, y5, yr5, mo5 = M[m5], D[5][m5], years[m5], months[m5]
    half = len(x5) // 2
    H["halves"] = {"first": {"n": half, "slope": kt.slope_only(x5[:half], y5[:half])},
                   "second": {"n": len(x5) - half, "slope": kt.slope_only(x5[half:], y5[half:])}}
    names = list(base.keys())
    mi = al(M, *[base[k] for k in names], D[5])
    beta, se, r2a = kt.reg(D[5][mi], [M[mi]] + [base[k][mi] for k in names], 10)
    _, _, r2b = kt.reg(D[5][mi], [base[k][mi] for k in names], 10)
    H["incremental"] = {"n": int(mi.sum()), "coef": dict(zip(["const", "signal"] + names, map(float, beta))),
                        "nw_t": dict(zip(["const", "signal"] + names, map(float, beta / se))), "r2_augmented": r2a, "r2_baseline": r2b}
    Mb = np.column_stack([base[k][mi] for k in names])
    if mi.sum() > OOS_START + 5:
        fb, fa, yy = kt.oos(D[5][mi], M[mi], Mb, OOS_START, 5)
        H["oos"] = kt.oos_stats(fb, fa, yy)
        H["oos"]["first_date"] = str(darr[mi][OOS_START])
    else:
        H["oos"] = {"n_forecasts": 0, "r2_os": float("nan"), "cw_mean": float("nan"), "cw_nw_t": float("nan")}
    if s == 0:
        H["size"] = {"threshold": float("nan"), "n_top": 0, "Dq": 0.0}
    else:
        sx = s * x5
        Qthr = float(np.percentile(sx, 80))
        top = sx >= Qthr
        H["size"] = {"threshold": Qthr, "n_top": int(top.sum()), "Dq": float(y5[top].mean() - y5.mean())}
    crit = {
        "a_primary": bool(s != 0 and np.isfinite(H["by_h"]["5"]["p2"]) and H["by_h"]["5"]["p2"] <= ALPHA2),
        "b_horizons": bool(s != 0 and kt.sign(b[1]) == s and kt.sign(b[3]) == s),
        "c_halves": bool(s != 0 and kt.sign(H["halves"]["first"]["slope"]) == s and kt.sign(H["halves"]["second"]["slope"]) == s),
        "d_incremental": bool(s != 0 and kt.sign(H["incremental"]["coef"]["signal"]) == s and abs(H["incremental"]["nw_t"]["signal"]) >= 2.0),
        "e_oos": bool(np.isfinite(H["oos"]["r2_os"]) and H["oos"]["r2_os"] > 0),
        "f_size": bool(s != 0 and H["size"]["Dq"] >= kt.FLOOR),
    }
    if H["by_h"]["5"]["shifts"] < 100:
        crit = {k: False for k in crit}
        v = "UNSCORABLE"
    elif all(crit.values()):
        v = "PASS"
    elif crit["a_primary"]:
        v = "WEAK"
    else:
        v = "FAIL"
    H["criteria"], H["verdict"] = crit, f"{v} (sign {'+' if s > 0 else '-' if s < 0 else '0'})"

    # section 8
    sec8 = {"baseline_alone": {}}
    for k in names:
        sec8["baseline_alone"][k] = {str(h): kt.slope_stats(base[k][al(base[k], D[h])], D[h][al(base[k], D[h])], h + 5) for h in HOR}
    mk = al(*base.values(), D[5])
    if mk.sum() > OOS_START + 5:
        Mm = np.column_stack([base[k][mk] for k in names])
        fmom, fmean, yy2 = kt.oos(D[5][mk], None, Mm, OOS_START, 5, with_x=False)
        sec8["baseline_vs_mean_r2_os"] = 1.0 - float(((yy2 - fmom) ** 2).sum()) / float(((yy2 - fmean) ** 2).sum())
    R5 = np.full(N, np.nan)
    R5[: N - 5] = 100.0 * (lS[5:] - lS[: N - 5])
    mk = al(M, R5)
    par = {"spot_R5_on_M": kt.slope_stats(M[mk], R5[mk], 10)}
    xq, yq = M[mk], R5[mk]
    qb = np.percentile(xq, [20, 40, 60, 80])
    qq = np.searchsorted(qb, xq, side="left") + 1
    par["spot_R5_quintiles_by_M"] = [float(yq[qq == k].mean()) for k in range(1, 6)]
    Q5 = np.full(N, np.nan)
    for t in range(N - 5):
        if same(t, t + 5):
            Q5[t] = 100.0 * (lF1[t + 5] - lF1[t])
    mk = al(M, Q5)
    par["front_Q5_on_M"] = kt.slope_stats(M[mk], Q5[mk], 10)
    sec8["parent_replication_settlement"] = par
    for nm, v in (("Sp", Spk[kept]), ("M", M[np.isfinite(M)])):
        sec8[f"level_of_{nm}"] = {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)), "sd": float(v.std()),
                                  "p5": float(np.percentile(v, 5)), "p95": float(np.percentile(v, 95)), "share_positive": float(np.mean(v > 0))}
    reg_ = {"per_year": {}}
    for y in sorted(set(yr5)):
        s_ = yr5 == y
        if s_.sum() >= 20:
            reg_["per_year"][y] = {"n": int(s_.sum()), "slope": kt.slope_only(x5[s_], y5[s_])}
    heat = (mo5 >= 11) | (mo5 <= 3)
    reg_["heating_nov_mar"] = {"in": {"n": int(heat.sum()), "slope": kt.slope_only(x5[heat], y5[heat])}, "out": {"n": int((~heat).sum()), "slope": kt.slope_only(x5[~heat], y5[~heat])}}
    vol = np.full(N, np.nan)
    for t in range(20, N):
        vol[t] = np.std(base["n1"][t - 19: t + 1])
    med = float(np.nanmedian(vol[sample]))
    hv = vol[m5] > med
    reg_["vol"] = {"high": {"n": int(hv.sum()), "slope": kt.slope_only(x5[hv], y5[hv])}, "low": {"n": int((~hv).sum()), "slope": kt.slope_only(x5[~hv], y5[~hv])}}
    cont = Sp[m5] > 0
    reg_["Sp_positive"] = {"in": {"n": int(cont.sum()), "slope": kt.slope_only(x5[cont], y5[cont])}, "out": {"n": int((~cont).sum()), "slope": kt.slope_only(x5[~cont], y5[~cont])}}
    sec8["regimes"] = reg_
    cut = int(np.floor(0.7 * len(x5)))
    sec8["holdout_last30"] = {"n": len(x5) - cut, "slope": kt.slope_only(x5[cut:], y5[cut:])}
    dev = np.abs(x5 - np.median(x5))
    c99 = float(np.percentile(dev, 99))
    loo = {y: kt.slope_only(x5[yr5 != y], y5[yr5 != y]) for y in sorted(set(yr5))}
    fin = {k: v for k, v in loo.items() if np.isfinite(v)}
    sec8["influence"] = {"trim_slope": kt.slope_only(x5[dev < c99], y5[dev < c99]), "trim_dropped": int((dev >= c99).sum()),
                         "loo_min": {"year": min(fin, key=fin.get), "slope": min(fin.values())}, "loo_max": {"year": max(fin, key=fin.get), "slope": max(fin.values())}}
    qb = np.percentile(x5, [20, 40, 60, 80])
    qq = np.searchsorted(qb, x5, side="left") + 1
    sec8["quintiles"] = {"breakpoints": list(map(float, qb)), "D5": {str(k): {"n": int((qq == k).sum()), "mean": float(y5[qq == k].mean())} for k in range(1, 6)}}
    res = {"calendar": {"joint_days": int(N), "first": dates[0], "last": dates[-1], "excluded_days": int(excluded.sum()), "kept_days": int(kept.sum()),
                        "M_defined": int(np.isfinite(M).sum())}, "hypothesis": H, "section8": sec8}
    with open(os.path.join(a.out, "results_b.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, allow_nan=True)
    c = res["calendar"]
    print(f"=== B gas spread: joint {c['joint_days']} {c['first']}..{c['last']}; excluded {c['excluded_days']}; kept {c['kept_days']}; M defined {c['M_defined']}")
    L1, L2 = sec8["level_of_Sp"], sec8["level_of_M"]
    print(f"  Sp mean {L1['mean']:+.3f} sd {L1['sd']:.3f} share>0 {L1['share_positive']:.3f}; M mean {L2['mean']:+.3f} sd {L2['sd']:.3f}")
    print(f"  H (M on spread change) sign {s:+d}")
    for h in HOR:
        t = H["by_h"][str(h)]
        print(f"    h={h} n={t['n']} slope={kt.fmt(t['slope'])} per_sd={kt.fmt(t.get('slope_per_sd'))} NW t={kt.fmt(t['nw_t'])} p2={t['p2']:.4f} MDE={kt.fmt(t['mde'])}")
    i, o, sz = H["incremental"], H["oos"], H["size"]
    print(f"    incremental g={kt.fmt(i['coef']['signal'])} t={kt.fmt(i['nw_t']['signal'])}; OOS n={o['n_forecasts']} R2_OS={kt.fmt(o['r2_os'])} CW t={kt.fmt(o['cw_nw_t'])}; "
          f"size Dq={kt.fmt(sz['Dq'])} (n_top {sz['n_top']}); halves {kt.fmt(H['halves']['first']['slope'])} / {kt.fmt(H['halves']['second']['slope'])}")
    print("    quintile means D5:", [round(sec8["quintiles"]["D5"][str(k)]["mean"], 3) for k in range(1, 6)])
    print("    criteria", json.dumps(crit), "VERDICT:", H["verdict"])
    pr = sec8["parent_replication_settlement"]
    print(f"  parent replication (settlement): spot R5 on M slope={kt.fmt(pr['spot_R5_on_M']['slope'])} t={kt.fmt(pr['spot_R5_on_M']['nw_t'])}; "
          f"quintiles {[round(x, 2) for x in pr['spot_R5_quintiles_by_M']]}; front Q5 on M slope={kt.fmt(pr['front_Q5_on_M']['slope'])} t={kt.fmt(pr['front_Q5_on_M']['nw_t'])}")


if __name__ == "__main__":
    main()
