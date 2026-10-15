"""Frozen test C: the VIX term-structure basis as a predictor of a tradable long-VIX instrument.
Implements PREREG.md (test C) sections 2 to 8 and applies the verdict rule mechanically.
Usage: python run_c.py --data data --out out
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kt  # noqa: E402

ALPHA2 = 0.025
OOS_START = 750


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    vix = kt.read(os.path.join(a.data, "vix.csv"), 2)
    v3 = kt.read(os.path.join(a.data, "vix3m.csv"), 2)
    etp = kt.read(os.path.join(a.data, "etp.csv"), 4)
    dates = sorted(d for d in set(vix) & set(v3) & set(etp)
                   if np.isfinite(vix[d][0]) and np.isfinite(v3[d][0]) and all(np.isfinite(etp[d])))
    N = len(dates)
    darr = np.array(dates)
    V = np.array([vix[d][0] for d in dates])
    V3 = np.array([v3[d][0] for d in dates])
    O = np.array([etp[d][0] for d in dates])
    C = np.array([etp[d][1] for d in dates])
    A = np.array([etp[d][2] for d in dates])
    adj = A / C
    B = 100.0 * (V3 / V - 1.0)
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
    H = kt.hypothesis(B, R, base, sample, darr, OOS_START, ALPHA2, extra_regime=regimes)
    res = {"calendar": {"joint_days": int(N), "first": dates[0], "last": dates[-1]}, "hypothesis": H}

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
    split = {}
    for h in kt.HORIZONS:
        mk = al(B, R[h])
        xs, ys = B[mk], R[h][mk]
        split[str(h)] = {"contango": {"n": int((xs > 0).sum()), "mean": float(ys[xs > 0].mean()) if (xs > 0).any() else float("nan")},
                         "backwardation_or_flat": {"n": int((xs <= 0).sum()), "mean": float(ys[xs <= 0].mean()) if (xs <= 0).any() else float("nan")}}
    res["contango_vs_backwardation"] = split
    res["level_of_B"] = {"n": int(N), "mean": float(B.mean()), "median": float(np.median(B)), "sd": float(B.std()),
                         "p5": float(np.percentile(B, 5)), "p95": float(np.percentile(B, 95)), "share_positive": float(np.mean(B > 0))}
    s = H["sign"]
    m5 = al(B, R[5])
    x5, y5 = B[m5], R[5][m5]
    if s != 0 and len(x5) > 5:
        sx = s * x5
        top = sx >= np.percentile(sx, 80)
        res["path_in_size_group"] = {"n": int(top.sum()), "p5_R5": float(np.percentile(y5[top], 5)), "min_R5": float(y5[top].min()),
                                     "mean_R5": float(y5[top].mean())}
    with open(os.path.join(a.out, "results_c.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, allow_nan=True)
    c = res["calendar"]
    L = res["level_of_B"]
    print(f"=== C VIX: joint {c['joint_days']} {c['first']}..{c['last']}")
    print(f"  B mean {L['mean']:+.3f} median {L['median']:+.3f} sd {L['sd']:.3f} p5 {L['p5']:+.3f} p95 {L['p95']:+.3f} share>0 {L['share_positive']:.3f}")
    kt.print_h("H (B on VIXY next-open-to-close return)", H)
    sp = split["5"]
    print(f"  contango vs backwardation h=5: {sp['contango']['n']} days mean {sp['contango']['mean']:+.3f}; "
          f"{sp['backwardation_or_flat']['n']} days mean {sp['backwardation_or_flat']['mean']:+.3f}")
    if "path_in_size_group" in res:
        p = res["path_in_size_group"]
        print(f"  path in size group: n {p['n']} mean {p['mean_R5']:+.3f} p5 {p['p5_R5']:+.3f} min {p['min_R5']:+.3f}")


if __name__ == "__main__":
    main()
