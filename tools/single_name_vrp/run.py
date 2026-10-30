"""Single-stock option premium, split into systematic and idiosyncratic parts
(tools/single_name_vrp/PREREG.md). Frozen implementation; every rule is the pre-registration's.

The question it answers for the covered-call thesis: if the idiosyncratic part is not positive,
a low-correlation pair cannot earn more from selling calls than a high-correlation one."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

NAMES = ["AAPL", "AMZN", "GOOG", "GS", "IBM"]
WIN = 21
BETA_N = 252
ANN = 252.0 / WIN
MIN_NAMES = 3
MIN_MONTHS = 120
T_BAR = 2.0
NW_LAGS = 3


def ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def atm_call(sigma: float, tau: float = WIN / 252.0) -> float:
    """Black-Scholes at-the-money call per unit of spot, rate 0 (PREREG section 4.3)."""
    d1 = sigma * math.sqrt(tau) / 2.0
    return ncdf(d1) - ncdf(-d1)


def nw_t(x) -> tuple[float, float, float]:
    """Mean, Newey-West standard error (3 lags, Bartlett, no small-sample correction), t."""
    x = np.asarray(x, dtype=float)
    n = x.size
    m = float(x.mean())
    e = x - m
    s = float((e * e).sum())
    for l in range(1, NW_LAGS + 1):
        if l < n:
            s += 2.0 * (1.0 - l / (NW_LAGS + 1.0)) * float((e[l:] * e[:-l]).sum())
    se = math.sqrt(s) / n
    return m, se, (m / se if se > 0 else float("nan"))


def read_csv(path: str) -> tuple[list[str], dict[str, list[float]]]:
    with open(path) as f:
        rows = list(csv.reader(f))
    head = rows[0]
    dates = [r[0] for r in rows[1:]]
    cols = {}
    for j, c in enumerate(head[1:], start=1):
        cols[c] = [float(r[j]) if j < len(r) and r[j].strip() != "" else float("nan") for r in rows[1:]]
    return dates, cols


def load(data_dir: str):
    pd_, pc = read_csv(os.path.join(data_dir, "prices.csv"))
    vd, vc = read_csv(os.path.join(data_dir, "vx.csv"))
    # Trading days are SPY's dates (PREREG section 3).
    keep = [i for i, v in enumerate(pc["SPY"]) if v == v]
    dates = [pd_[i] for i in keep]
    px = {k: np.array([pc[k][i] for i in keep]) for k in NAMES + ["SPY"]}
    vmap = {k: dict(zip(vd, vc[k])) for k in NAMES + ["MKT"]}
    vx = {k: np.array([vmap[k].get(d, float("nan")) for d in dates]) for k in NAMES + ["MKT"]}
    return dates, px, vx


def analyse(dates: list[str], px: dict, vx: dict) -> dict:
    n = len(dates)
    r = {}
    for k, p in px.items():
        rr = np.full(n, np.nan)
        rr[1:] = np.log(p[1:] / p[:-1])
        r[k] = rr
    # Formation days: first trading day of each calendar month with 21 trading days after it.
    t0s = []
    seen = set()
    for j, d in enumerate(dates):
        ym = d[:7]
        if ym in seen:
            continue
        seen.add(ym)
        if j + WIN <= n - 1:
            t0s.append(j)
    rm = r["SPY"]
    rows = []  # one per used name-month
    for j in t0s:
        if j - BETA_N + 1 < 1:
            continue
        ivm = vx["MKT"][j]
        bw = slice(j - BETA_N + 1, j + 1)
        hw = slice(j + 1, j + WIN + 1)
        xm_b, xm_h = rm[bw], rm[hw]
        if np.isnan(xm_b).any() or np.isnan(xm_h).any() or not (ivm == ivm):
            continue
        rvm2 = ANN * float((xm_h ** 2).sum())
        ivm2 = (ivm / 100.0) ** 2
        for i in NAMES:
            v = vx[i][j]
            xi_b, xi_h = r[i][bw], r[i][hw]
            if not (v == v) or np.isnan(xi_b).any() or np.isnan(xi_h).any():
                continue
            b = float(np.polyfit(xm_b, xi_b, 1)[0])
            b_post = float(np.polyfit(xm_h, xi_h, 1)[0])
            iv2 = (v / 100.0) ** 2
            rv2 = ANN * float((xi_h ** 2).sum())
            vrp = iv2 - rv2
            svrp = b * b * (ivm2 - rvm2)
            g = px[i][j + WIN] / px[i][j]
            rows.append({
                "j": j, "name": i, "vrp": vrp, "svrp": svrp, "ivrp": vrp - svrp,
                "implied_idio": iv2 - b * b * ivm2,
                "ivrp_post": vrp - b_post * b_post * (ivm2 - rvm2),
                "y": atm_call(v / 100.0) - max(g - 1.0, 0.0),
                "bw": (j - BETA_N + 1, j + 1),
            })
    by_j: dict[int, list[dict]] = {}
    for row in rows:
        by_j.setdefault(row["j"], []).append(row)
    months = [j for j in sorted(by_j) if len(by_j[j]) >= MIN_NAMES]

    def series(key):
        return np.array([np.mean([row[key] for row in by_j[j]]) for j in months])

    out = {"n_months": len(months),
           "first_month": dates[months[0]] if months else None,
           "last_month": dates[months[-1]] if months else None}
    if not months:
        out["verdict"] = "INSUFFICIENT"
        return out
    m, se, t = nw_t(series("ivrp"))
    out.update({"ivrp_mean": m, "ivrp_t": t})
    if len(months) < MIN_MONTHS:
        out["verdict"] = "INSUFFICIENT"
    elif m > 0 and t >= T_BAR:
        out["verdict"] = "SUPPORTED"
    else:
        out["verdict"] = "NOT SUPPORTED"
    for k in ("vrp", "svrp"):
        mm, _, tt = nw_t(series(k))
        out[f"{k}_mean"], out[f"{k}_t"] = mm, tt
    out["share_ivrp_of_vrp"] = out["ivrp_mean"] / out["vrp_mean"]
    per = {}
    for i in NAMES:
        js = sorted({row["j"] for row in rows if row["name"] == i})
        d = {"n": len(js)}
        for k in ("vrp", "svrp", "ivrp"):
            xs = [row[k] for row in rows if row["name"] == i]
            if xs:
                d[f"{k}_mean"], _, d[f"{k}_t"] = nw_t(xs)
        per[i] = d
    out["per_name"] = per
    h = len(months) // 2
    halves = []
    ivs = series("ivrp")
    for sl in (slice(0, h), slice(h, len(months))):
        mm, _, tt = nw_t(ivs[sl])
        ms = months[sl]
        halves.append({"first": dates[ms[0]], "last": dates[ms[-1]], "mean": mm, "t": tt, "n": len(ms)})
    out["halves"] = halves
    out["implied_idio_mean"] = float(series("implied_idio").mean())
    out["ivrp_over_implied_idio"] = out["ivrp_mean"] / out["implied_idio_mean"]
    mm, _, tt = nw_t(series("ivrp_post"))
    out["expost_ivrp_mean"], out["expost_ivrp_t"] = mm, tt
    mm, _, tt = nw_t(100.0 * series("y"))
    out["cc_mean_pct"], out["cc_t"], out["cc_n"] = mm, tt, len(months)
    # Pair proxy: every formation day on which both names are used (no 3-name rule; section 4.3).
    pairs = []
    for j, lst in by_j.items():
        d = {row["name"]: row for row in lst}
        for a_i in range(len(NAMES)):
            for b_i in range(a_i + 1, len(NAMES)):
                a, b = NAMES[a_i], NAMES[b_i]
                if a in d and b in d:
                    s0, s1 = d[a]["bw"]
                    rho = float(np.corrcoef(r[a][s0:s1], r[b][s0:s1])[0, 1])
                    pairs.append((rho, 0.5 * (d[a]["y"] + d[b]["y"])))
    rhos = np.array([p[0] for p in pairs])
    ys = 100.0 * np.array([p[1] for p in pairs])
    med = float(np.median(rhos))
    lo, hi = ys[rhos < med], ys[rhos >= med]
    out.update({"pair_low_mean_pct": float(lo.mean()), "pair_high_mean_pct": float(hi.mean()),
                "pair_diff_pct": float(hi.mean() - lo.mean()), "pair_n": int(len(pairs)),
                "pair_median_rho": med})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = analyse(*load(a.data))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    print("VERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
