"""Frozen test D: the CME bitcoin futures basis as a predictor of spot bitcoin.
Implements PREREG.md (test D) sections 2 to 8 and applies the verdict rule mechanically.
Usage: python run_d.py --data data --out out
"""
import argparse
import bisect
import datetime as dt
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kt  # noqa: E402

ALPHA2 = 0.025
OOS_START = 750
EXCL_BEFORE, EXCL_AFTER = 4, 1


def last_friday(y, m):
    d = (dt.date(y, m, 1) + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
    while d.weekday() != 4:
        d -= dt.timedelta(days=1)
    return d


def months_between(d0, d1):
    y, m = d0.year, d0.month
    out = []
    while (y, m) <= (d1.year, d1.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    spot = kt.read(os.path.join(a.data, "btc_spot.csv"), 2)
    fut = kt.read(os.path.join(a.data, "btc_fut.csv"), 2)
    tb = kt.read(os.path.join(a.data, "tbill.csv"), 2)
    dates = sorted(d for d in set(spot) & set(fut) if np.isfinite(spot[d][0]) and np.isfinite(fut[d][0]))
    N = len(dates)
    darr = np.array(dates)
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
    last_month = (d1 + dt.timedelta(days=32)).replace(day=1)
    expiries = sorted(set(last_friday(y, m) for (y, m) in months_between(d0, last_month)))
    excluded = np.zeros(N, dtype=bool)
    xdates = []
    for X in expiries:
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
    M = np.where(kept & np.isfinite(tau) & np.isfinite(r), 100.0 * (F / Fstar - 1.0), np.nan)
    lS, lF = np.log(S), np.log(F)
    base = {"n1": 100 * kt.lagd(lS, 1), "n5": 100 * kt.lagd(lS, 5), "n20": 100 * kt.lagd(lS, 20)}
    R, Q = {}, {}
    for h in kt.HORIZONS:
        o = np.full(N, np.nan)
        o[: N - h] = 100.0 * (lS[h:] - lS[: N - h])
        R[h] = o
        q = np.full(N, np.nan)
        for t in range(N - h):
            if kept[t] and kept[t + h] and Xid[t] >= 0 and Xid[t] == Xid[t + h]:
                q[t] = 100.0 * (lF[t + h] - lF[t])
        Q[h] = q
    vol = np.full(N, np.nan)
    for t in range(20, N):
        vol[t] = np.std(base["n1"][t - 19: t + 1])
    sample = kept.copy()
    med = float(np.nanmedian(vol[sample]))
    regimes = {"high_vol": vol > med, "M_positive": M > 0}
    H = kt.hypothesis(M, R, base, sample, darr, OOS_START, ALPHA2, extra_regime=regimes)
    res = {"calendar": {"joint_days": int(N), "first": dates[0], "last": dates[-1], "excluded_days": int(excluded.sum()),
                        "kept_days": int(kept.sum()), "expiries": len(xdates), "M_defined": int(np.isfinite(M).sum()),
                        "rate_missing_on_kept": int(np.sum(kept & ~np.isfinite(RATE)))},
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
        alone["momentum_only_vs_mean_r2_os"] = 1.0 - float(((yy2 - fmom) ** 2).sum()) / float(((yy2 - fmean) ** 2).sum())
    res["momentum_alone"] = alone
    s = H["sign"]
    trad = {str(h): kt.slope_stats(M[al(M, Q[h])], Q[h][al(M, Q[h])], h + 5) for h in kt.HORIZONS}
    mq = al(M, Q[5])
    if s != 0 and mq.sum() > 5:
        xq, yq = s * M[mq], Q[5][mq]
        Qt = float(np.percentile(xq, 80))
        trad["Dq_Q5"] = float(yq[xq >= Qt].mean() - yq.mean())
    else:
        trad["Dq_Q5"] = float("nan")
    res["futures_expression"] = trad
    mk = al(M, base["n1"])
    res["same_day_n1_on_M"] = kt.slope_stats(M[mk], base["n1"][mk], 5)
    mk = al(M)
    Ms = M[mk]
    carry = 1e4 * np.log(F[mk] / Fstar[mk]) / tau[mk]
    res["level_of_M"] = {"n": int(mk.sum()), "M_mean": float(Ms.mean()), "M_median": float(np.median(Ms)), "M_sd": float(Ms.std()),
                         "M_p5": float(np.percentile(Ms, 5)), "M_p95": float(np.percentile(Ms, 95)), "share_M_positive": float(np.mean(Ms > 0)),
                         "tau_mean_days": float(np.mean(tau[mk]) * 365), "carry_bp_pa_mean": float(carry.mean()),
                         "carry_bp_pa_median": float(np.median(carry))}
    dM = []
    for t in range(1, N):
        if kept[t] and kept[t - 1] and Xid[t] >= 0 and Xid[t] == Xid[t - 1] and np.isfinite(M[t]) and np.isfinite(M[t - 1]):
            dM.append(abs(M[t] - M[t - 1]))
    dM = np.array(dM)
    steps = []
    t = 0
    while t < N:
        if excluded[t]:
            u = t
            while u < N and excluded[u]:
                u += 1
            if t - 1 >= 0 and u < N and np.isfinite(M[t - 1]) and np.isfinite(M[u]):
                steps.append(abs(M[u] - M[t - 1]))
            t = u
        else:
            t += 1
    steps = np.array(steps)
    res["roll_check"] = {"n_dM": int(len(dM)), "max_abs_dM": float(dM.max()) if len(dM) else float("nan"),
                         "p99_abs_dM": float(np.percentile(dM, 99)) if len(dM) else float("nan"),
                         "n_roll_steps": int(len(steps)), "median_abs_roll_step": float(np.median(steps)) if len(steps) else float("nan"),
                         "roll_steps_over_5pp": int((steps > 5).sum())}
    with open(os.path.join(a.out, "results_d.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, allow_nan=True)
    c = res["calendar"]
    print(f"=== D bitcoin: joint {c['joint_days']} {c['first']}..{c['last']}; excluded {c['excluded_days']}; kept {c['kept_days']}; "
          f"expiries {c['expiries']}; M defined {c['M_defined']}")
    L = res["level_of_M"]
    print(f"  M mean {L['M_mean']:+.3f} median {L['M_median']:+.3f} sd {L['M_sd']:.3f} p5 {L['M_p5']:+.3f} p95 {L['M_p95']:+.3f} share>0 "
          f"{L['share_M_positive']:.3f}; tau mean {L['tau_mean_days']:.1f} d; carry {L['carry_bp_pa_median']:+.0f} bp/yr median")
    rc = res["roll_check"]
    print(f"  roll check: n {rc['n_dM']} max|dM| {kt.fmt(rc['max_abs_dM'])} p99 {kt.fmt(rc['p99_abs_dM'])}; roll steps {rc['n_roll_steps']} "
          f"median|step| {kt.fmt(rc['median_abs_roll_step'])} >5pp {rc['roll_steps_over_5pp']}")
    sd = res["same_day_n1_on_M"]
    print(f"  same-day n1 on M: slope {kt.fmt(sd['slope'])} t {kt.fmt(sd['nw_t'])}")
    kt.print_h("H (M on spot return)", H)
    print("  futures Q:", " ".join(f"h={h} b={kt.fmt(trad[str(h)]['slope'])} t={kt.fmt(trad[str(h)]['nw_t'])};" for h in kt.HORIZONS),
          f"Dq_Q5={kt.fmt(trad['Dq_Q5'])}")


if __name__ == "__main__":
    main()
