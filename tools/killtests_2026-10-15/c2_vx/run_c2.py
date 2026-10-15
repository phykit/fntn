"""Frozen test C2: the constant-30-day VIX futures basis as a predictor of VIXY.
Implements PREREG.md (test C2) sections 2 to 8. Usage: python run_c2.py --data data --out out
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kt  # noqa: E402

ALPHA2 = 0.025
OOS_START = 750


def read_vx(path):
    by_date = {}
    expiries = set()
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        for r in rd:
            d, x, s = r["DATE"].strip(), r["EXPIRY"].strip(), r["SETTLE"].strip()
            expiries.add(x)
            try:
                v = float(s)
            except ValueError:
                continue
            if not np.isfinite(v) or v == 0.0:
                continue
            if x > d:
                by_date.setdefault(d, {})[x] = v
    return by_date, expiries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    vx, expiries = read_vx(os.path.join(a.data, "vx.csv"))
    vix = kt.read(os.path.join(a.data, "vix.csv"), 2)
    etp = kt.read(os.path.join(a.data, "etp.csv"), 4)
    front = {}
    for d, cs in vx.items():
        xs = sorted(cs)
        if len(xs) >= 2:
            dd = dt.date.fromisoformat(d)
            front[d] = (cs[xs[0]], cs[xs[1]], (dt.date.fromisoformat(xs[0]) - dd).days, (dt.date.fromisoformat(xs[1]) - dd).days)
    dates = sorted(d for d in set(vix) & set(etp) & set(front) if np.isfinite(vix[d][0]) and all(np.isfinite(etp[d])))
    N = len(dates)
    darr = np.array(dates)
    V = np.array([vix[d][0] for d in dates])
    O = np.array([etp[d][0] for d in dates])
    C = np.array([etp[d][1] for d in dates])
    A = np.array([etp[d][2] for d in dates])
    F1 = np.array([front[d][0] for d in dates])
    F2 = np.array([front[d][1] for d in dates])
    tau1 = np.array([front[d][2] for d in dates], dtype=float)
    tau2 = np.array([front[d][3] for d in dates], dtype=float)
    w = np.clip((tau2 - 30.0) / (tau2 - tau1), 0.0, 1.0)
    F30 = w * F1 + (1.0 - w) * F2
    B30 = 100.0 * (F30 / V - 1.0)
    Bf = 100.0 * (F1 / V - 1.0)
    RY = Bf / tau1
    adj = A / C
    lv = np.log(V)
    base = {"lv": lv, "n1": 100 * kt.lagd(lv, 1), "n5": 100 * kt.lagd(lv, 5), "n20": 100 * kt.lagd(lv, 20)}
    lC, lO = np.log(C * adj), np.log(O * adj)
    R = {}
    for h in kt.HORIZONS:
        o = np.full(N, np.nan)
        o[: N - h] = 100.0 * (lC[h:] - lO[1: N - h + 1])
        R[h] = o
    vol = np.full(N, np.nan)
    for t in range(20, N):
        vol[t] = np.std(base["n1"][t - 19: t + 1])
    sample = np.ones(N, dtype=bool)
    med = float(np.nanmedian(vol))
    regimes = {"vix_above_20": V > 20.0, "high_vol": vol > med}
    H = kt.hypothesis(B30, R, base, sample, darr, OOS_START, ALPHA2, extra_regime=regimes)
    etp_days = sorted(d for d in etp if all(np.isfinite(etp[d])) and d >= dates[0])
    res = {"calendar": {"joint_days": int(N), "first": dates[0], "last": dates[-1], "monthly_contracts": len(expiries),
                        "first_expiry": min(expiries), "last_expiry": max(expiries),
                        "vixy_days_without_futures_pair": int(sum(1 for d in etp_days if d not in front))},
           "hypothesis": H}

    def al(*arrs):
        m_ = sample.copy()
        for v in arrs:
            m_ &= np.isfinite(v)
        return m_

    alone = {}
    for b_ in base:
        alone[b_] = {str(h): kt.slope_stats(base[b_][al(base[b_], R[h])], R[h][al(base[b_], R[h])], h + 5) for h in kt.HORIZONS}
    mk = al(*base.values(), R[5])
    if mk.sum() > OOS_START + 5:
        Mm = np.column_stack([base[b_][mk] for b_ in base])
        fmom, fmean, yy2 = kt.oos(R[5][mk], None, Mm, OOS_START, 5, with_x=False)
        alone["baseline_vs_mean_r2_os"] = 1.0 - float(((yy2 - fmom) ** 2).sum()) / float(((yy2 - fmean) ** 2).sum())
    res["baseline_alone"] = alone
    res["front_basis_and_roll"] = {nm: {str(h): kt.slope_stats(x[al(x, R[h])], R[h][al(x, R[h])], h + 5) for h in kt.HORIZONS}
                                   for nm, x in (("Bf", Bf), ("RY", RY))}
    split = {}
    for h in kt.HORIZONS:
        mk = al(B30, R[h])
        xs, ys = B30[mk], R[h][mk]
        split[str(h)] = {"contango": {"n": int((xs > 0).sum()), "mean": float(ys[xs > 0].mean()) if (xs > 0).any() else float("nan")},
                         "backwardation_or_flat": {"n": int((xs <= 0).sum()), "mean": float(ys[xs <= 0].mean()) if (xs <= 0).any() else float("nan")}}
    res["contango_vs_backwardation"] = split
    for nm, x in (("B30", B30), ("Bf", Bf)):
        res[f"level_of_{nm}"] = {"mean": float(x.mean()), "median": float(np.median(x)), "sd": float(x.std()), "p5": float(np.percentile(x, 5)),
                                 "p95": float(np.percentile(x, 95)), "share_positive": float(np.mean(x > 0))}
    res["tau1_mean_days"] = float(tau1.mean())
    s = H["sign"]
    m5 = al(B30, R[5])
    x5, y5 = B30[m5], R[5][m5]
    if s != 0 and len(x5) > 5:
        sx = s * x5
        top = sx >= np.percentile(sx, 80)
        res["path_in_size_group"] = {"n": int(top.sum()), "p5_R5": float(np.percentile(y5[top], 5)), "min_R5": float(y5[top].min()), "mean_R5": float(y5[top].mean())}
    with open(os.path.join(a.out, "results_c2.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, allow_nan=True)
    c = res["calendar"]
    print(f"=== C2 VX basis: joint {c['joint_days']} {c['first']}..{c['last']}; {c['monthly_contracts']} monthly contracts {c['first_expiry']}..{c['last_expiry']}; "
          f"VIXY days without a futures pair {c['vixy_days_without_futures_pair']}")
    L = res["level_of_B30"]
    Lf = res["level_of_Bf"]
    print(f"  B30 mean {L['mean']:+.3f} median {L['median']:+.3f} sd {L['sd']:.3f} p5 {L['p5']:+.3f} p95 {L['p95']:+.3f} share>0 {L['share_positive']:.3f}; "
          f"Bf mean {Lf['mean']:+.3f} share>0 {Lf['share_positive']:.3f}; tau1 mean {res['tau1_mean_days']:.1f} d")
    kt.print_h("H (B30 on VIXY next-open-to-close return)", H)
    for nm in ("Bf", "RY"):
        print(f"  {nm}:", " ".join(f"h={h} b={kt.fmt(res['front_basis_and_roll'][nm][str(h)]['slope'])} t={kt.fmt(res['front_basis_and_roll'][nm][str(h)]['nw_t'])} "
                                 f"p2={res['front_basis_and_roll'][nm][str(h)]['p2']:.4f};" for h in kt.HORIZONS))
    sp = split["5"]
    print(f"  contango vs backwardation h=5: {sp['contango']['n']} days mean {sp['contango']['mean']:+.3f}; {sp['backwardation_or_flat']['n']} days mean {sp['backwardation_or_flat']['mean']:+.3f}")
    if "path_in_size_group" in res:
        p = res["path_in_size_group"]
        print(f"  path in size group: n {p['n']} mean {p['mean_R5']:+.3f} p5 {p['p5_R5']:+.3f} min {p['min_R5']:+.3f}")


if __name__ == "__main__":
    main()
