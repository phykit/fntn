"""Independent second implementation of the single-name variance risk premium test.

Written from PREREG.md alone, without sight of run.py, selftest.py, compare.py or
fetch.py. The point of a second implementation is that a defect shared by both can
only arise from the pre-registration itself, not from code copied between them; that
is why this file deliberately reuses nothing from its sibling.

Usage: python verify.py --data DIR --out DIR

Inputs are DIR/vx.csv (date, AAPL, AMZN, GOOG, GS, IBM, MKT) and DIR/prices.csv
(date, AAPL, AMZN, GOOG, GS, IBM, SPY). Output is OUT/verify.json. Numpy and the
standard library only, so that the arithmetic is not delegated to a library whose
conventions (for example a default small-sample correction) have not been read.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

NAMES = ["AAPL", "AMZN", "GOOG", "GS", "IBM"]
BETA_WINDOW = 252   # section 3: 252 trading days ending at and including t0
HOLD = 21           # section 3: 21 trading days after t0
ANNUAL = 252.0
NW_LAGS = 3         # section 4.1
MIN_NAMES = 3       # section 3: a formation day needs at least 3 used names
MIN_MONTHS = 120    # section 4.2: fewer monthly observations is INSUFFICIENT
T_CRIT = 2.0        # section 4.2: one-sided, positive sign registered


def read_csv(path: str) -> tuple[list[str], dict[str, list[float]]]:
    """Read a dated CSV, keeping an empty cell as NaN.

    A missing value must stay missing (section 2); converting it to zero or
    carrying the previous value forward would manufacture an observation the
    source never recorded.
    """
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        cols = {h: [] for h in header[1:]}
        dates: list[str] = []
        for row in reader:
            if not row:
                continue
            dates.append(row[0].strip())
            for j, h in enumerate(header[1:], start=1):
                cell = row[j].strip() if j < len(row) else ""
                cols[h].append(float(cell) if cell != "" else math.nan)
    return dates, cols


def nw_mean_t(x: np.ndarray) -> tuple[float | None, float | None]:
    """Mean and Newey-West t of a series on a constant-only regression.

    Three lags with Bartlett weights 1 - l / (L + 1) and no small-sample
    correction, exactly as section 4.1 registers; a correction would be a
    different statistic and would not reproduce the registered threshold.
    Returns None for a quantity that cannot be computed, rather than a
    default, because a fabricated zero would read as a measurement.
    """
    n = len(x)
    if n == 0:
        return None, None
    m = float(np.mean(x))
    if n < 2:
        return m, None
    e = x - m
    s = float(np.sum(e * e))
    for lag in range(1, NW_LAGS + 1):
        if lag >= n:
            break
        w = 1.0 - lag / (NW_LAGS + 1.0)
        s += 2.0 * w * float(np.sum(e[lag:] * e[:-lag]))
    var = s / (n * n)
    if not (var > 0.0):
        return m, None
    return m, m / math.sqrt(var)


def ols_slope(y: np.ndarray, x: np.ndarray) -> float | None:
    """OLS slope with intercept. Undefined (None) when x has no variance."""
    xd = x - x.mean()
    sxx = float(np.sum(xd * xd))
    if not (sxx > 0.0):
        return None
    return float(np.sum(xd * (y - y.mean()))) / sxx


def norm_cdf(z: float) -> float:
    """N(x) = 0.5 * erfc(-x / sqrt(2)), the form section 4.3 specifies."""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def bs_atm_call(sigma: float, tau: float) -> float:
    """At-the-money Black-Scholes call per unit of spot at rate zero.

    With strike equal to spot and no rate, d1 = sigma sqrt(tau) / 2 and d2 = -d1,
    so the premium depends on total volatility alone.
    """
    d1 = sigma * math.sqrt(tau) / 2.0
    return norm_cdf(d1) - norm_cdf(-d1)


def none_if_nan(v):
    if v is None:
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pdates, pcols = read_csv(os.path.join(args.data, "prices.csv"))
    vdates, vcols = read_csv(os.path.join(args.data, "vx.csv"))

    # Trading days are SPY's dates (section 3). A row without SPY is not a
    # trading day at all, so it is removed before returns are formed; the
    # previous trading day of d is then the previous retained row.
    spy_all = np.array(pcols["SPY"])
    keep = np.isfinite(spy_all)
    tdays = [d for d, k in zip(pdates, keep) if k]
    P = {k: np.array(pcols[k])[keep] for k in NAMES + ["SPY"]}
    n_days = len(tdays)

    # r(d) is defined only where both prices are present; NaN propagates
    # through the logarithm, so an undefined return stays undefined.
    R = {}
    for k, p in P.items():
        r = np.full(n_days, math.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            r[1:] = np.log(p[1:] / p[:-1])
        R[k] = r

    # Implied volatilities are read at t0 exactly (section 3): no carrying
    # forward, so a date absent from vx.csv is treated as missing.
    vx_index = {d: i for i, d in enumerate(vdates)}

    def vx_at(col: str, d: str) -> float:
        i = vx_index.get(d)
        if i is None:
            return math.nan
        return vcols[col][i]

    # Formation days: the first trading day of each calendar month, used only
    # if at least 21 trading days follow it in the file.
    formation: list[int] = []
    seen_months = set()
    for idx, d in enumerate(tdays):
        ym = d[:7]
        if ym in seen_months:
            continue
        seen_months.add(ym)
        if idx + HOLD <= n_days - 1:
            formation.append(idx)

    tau = HOLD / ANNUAL
    # rec[t0_idx][name] holds the per-name-month quantities.
    rec: dict[int, dict[str, dict]] = {}
    for t0 in formation:
        # The beta window needs the return dated t0 and the 251 before it,
        # each of which needs the prior price, so t0 must be at index >= 252.
        if t0 < BETA_WINDOW:
            continue
        vix = vx_at("MKT", tdays[t0])
        if not math.isfinite(vix):
            continue
        ivm2 = (vix / 100.0) ** 2
        bw = slice(t0 - BETA_WINDOW + 1, t0 + 1)
        hw = slice(t0 + 1, t0 + HOLD + 1)
        rspy_b = R["SPY"][bw]
        rspy_h = R["SPY"][hw]
        if not (np.all(np.isfinite(rspy_b)) and np.all(np.isfinite(rspy_h))):
            continue
        rv2_spy = ANNUAL / HOLD * float(np.sum(rspy_h * rspy_h))
        out = {}
        for nm in NAMES:
            vx = vx_at(nm, tdays[t0])
            if not math.isfinite(vx):
                continue
            ri_b = R[nm][bw]
            ri_h = R[nm][hw]
            # All 252 beta pairs and all 21 window returns must be present;
            # a partial window would silently change the estimator's span.
            if not (np.all(np.isfinite(ri_b)) and np.all(np.isfinite(ri_h))):
                continue
            b = ols_slope(ri_b, rspy_b)
            if b is None:
                continue
            iv2 = (vx / 100.0) ** 2
            rv2 = ANNUAL / HOLD * float(np.sum(ri_h * ri_h))
            vrp = iv2 - rv2
            svrp = b * b * (ivm2 - rv2_spy)
            ivrp = vrp - svrp
            b_post = ols_slope(ri_h, rspy_h)
            ivrp_post = None if b_post is None else vrp - b_post * b_post * (ivm2 - rv2_spy)
            g = P[nm][t0 + HOLD] / P[nm][t0]
            y = bs_atm_call(vx / 100.0, tau) - max(g - 1.0, 0.0)
            out[nm] = {
                "vrp": vrp, "svrp": svrp, "ivrp": ivrp,
                "impl_idio": iv2 - b * b * ivm2,
                "ivrp_post": ivrp_post, "y": y, "rb": ri_b,
            }
        if out:
            rec[t0] = out

    # Monthly series: equal mean across used names, on formation days with at
    # least three used names; fewer would let one name dominate a month.
    months = sorted(t for t, o in rec.items() if len(o) >= MIN_NAMES)

    def series(key: str) -> np.ndarray:
        return np.array([np.mean([rec[t][nm][key] for nm in rec[t]]) for t in months])

    ivrp_x = series("ivrp")
    vrp_x = series("vrp")
    svrp_x = series("svrp")
    n = len(months)
    ivrp_mean, ivrp_t = nw_mean_t(ivrp_x)
    vrp_mean, vrp_t = nw_mean_t(vrp_x)
    svrp_mean, svrp_t = nw_mean_t(svrp_x)

    if n < MIN_MONTHS:
        verdict = "INSUFFICIENT"
    elif ivrp_mean is not None and ivrp_t is not None and ivrp_mean > 0 and ivrp_t >= T_CRIT:
        verdict = "SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"

    share = None
    if ivrp_mean is not None and vrp_mean not in (None, 0.0):
        share = ivrp_mean / vrp_mean

    # Per-name series: every used name-month of that name, with no minimum-name
    # rule, as section 4.3 states.
    per_name = {}
    for nm in NAMES:
        ts = sorted(t for t in rec if nm in rec[t])
        entry = {"n": len(ts)}
        for key in ("vrp", "svrp", "ivrp"):
            m, tt = nw_mean_t(np.array([rec[t][nm][key] for t in ts]))
            entry[key + "_mean"] = none_if_nan(m)
            entry[key + "_t"] = none_if_nan(tt)
        per_name[nm] = entry

    # Halves split at floor(n / 2), the first half taking the first floor(n / 2).
    h = n // 2
    halves = []
    for sl in (slice(0, h), slice(h, n)):
        idxs = months[sl]
        m, tt = nw_mean_t(ivrp_x[sl])
        halves.append({
            "first": tdays[idxs[0]] if idxs else None,
            "last": tdays[idxs[-1]] if idxs else None,
            "mean": none_if_nan(m), "t": none_if_nan(tt), "n": len(idxs),
        })

    impl_x = series("impl_idio")
    impl_mean = float(np.mean(impl_x)) if n else None
    ratio = (ivrp_mean / impl_mean) if (ivrp_mean is not None and impl_mean) else None

    # Ex-post robustness: same name-months and month set as the primary, so
    # the only thing that differs is the beta. A name-month whose in-window
    # beta is undefined cannot be scored and is dropped from that month's mean.
    post_vals = []
    for t in months:
        vals = [rec[t][nm]["ivrp_post"] for nm in rec[t] if rec[t][nm]["ivrp_post"] is not None]
        post_vals.append(np.mean(vals) if vals else math.nan)
    post_x = np.array(post_vals)
    post_x = post_x[np.isfinite(post_x)]
    expost_mean, expost_t = nw_mean_t(post_x)

    # Covered-call proxy, per cent of spot per month, same 3-name rule.
    cc_x = 100.0 * series("y")
    cc_mean, cc_t = nw_mean_t(cc_x)

    # Pair proxy: every formation day on which both names are used. Section
    # 4.3 applies the 3-name rule to the covered-call proxy explicitly and
    # does not repeat it here, so no minimum-name rule is applied.
    pair_y, pair_c = [], []
    for t in sorted(rec):
        o = rec[t]
        for a in range(len(NAMES)):
            for b in range(a + 1, len(NAMES)):
                na, nb = NAMES[a], NAMES[b]
                if na in o and nb in o:
                    ra, rb = o[na]["rb"], o[nb]["rb"]
                    if np.std(ra) == 0.0 or np.std(rb) == 0.0:
                        continue
                    c = float(np.corrcoef(ra, rb)[0, 1])
                    pair_y.append(0.5 * (o[na]["y"] + o[nb]["y"]))
                    pair_c.append(c)
    pair_y_a = 100.0 * np.array(pair_y)
    pair_c_a = np.array(pair_c)
    if len(pair_c_a):
        med = float(np.median(pair_c_a))
        lo = pair_y_a[pair_c_a < med]
        hi = pair_y_a[pair_c_a >= med]
        pl = float(np.mean(lo)) if len(lo) else None
        ph = float(np.mean(hi)) if len(hi) else None
        pd_ = (ph - pl) if (pl is not None and ph is not None) else None
    else:
        pl = ph = pd_ = None

    result = {
        "n_months": n,
        "first_month": tdays[months[0]] if n else None,
        "last_month": tdays[months[-1]] if n else None,
        "verdict": verdict,
        "ivrp_mean": none_if_nan(ivrp_mean), "ivrp_t": none_if_nan(ivrp_t),
        "vrp_mean": none_if_nan(vrp_mean), "vrp_t": none_if_nan(vrp_t),
        "svrp_mean": none_if_nan(svrp_mean), "svrp_t": none_if_nan(svrp_t),
        "share_ivrp_of_vrp": none_if_nan(share),
        "per_name": per_name,
        "halves": halves,
        "implied_idio_mean": none_if_nan(impl_mean),
        "ivrp_over_implied_idio": none_if_nan(ratio),
        "expost_ivrp_mean": none_if_nan(expost_mean), "expost_ivrp_t": none_if_nan(expost_t),
        "cc_mean_pct": none_if_nan(cc_mean), "cc_t": none_if_nan(cc_t), "cc_n": int(len(cc_x)),
        "pair_low_mean_pct": none_if_nan(pl), "pair_high_mean_pct": none_if_nan(ph),
        "pair_diff_pct": none_if_nan(pd_), "pair_n": int(len(pair_y_a)),
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as fh:
        json.dump(result, fh, indent=2)

    print(f"months used: {n}  verdict: {verdict}")
    print(f"{'name':6s} {'n':>4s} {'vrp_t':>8s} {'svrp_t':>8s} {'ivrp_t':>8s}")
    for nm in NAMES:
        e = per_name[nm]
        f = lambda v: f"{v:8.2f}" if v is not None else f"{'n/a':>8s}"
        print(f"{nm:6s} {e['n']:4d} {f(e['vrp_t'])} {f(e['svrp_t'])} {f(e['ivrp_t'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
