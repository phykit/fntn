"""Independent second implementation of tools/pair_risk_adjusted/PREREG.md.

Written from that document and tools/single_name_vrp/PREREG.md alone, without
reading any other implementation, so that agreement between the two is
evidence that both read the documents the same way and not that one copied
the other's mistakes.

Usage: python verify.py --data DIR --out DIR

Python 3.12, numpy and the standard library only; every quantity is float64.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

NAMES = ["AAPL", "AMZN", "GOOG", "GS", "IBM"]

# The pair order is fixed by section 4 of the pair PREREG; the JSON keeps it so
# that a comparison script can walk both outputs in the same sequence.
PAIRS = [
    ("AAPL", "AMZN"), ("AAPL", "GOOG"), ("AAPL", "GS"), ("AAPL", "IBM"),
    ("AMZN", "GOOG"), ("AMZN", "GS"), ("AMZN", "IBM"),
    ("GOOG", "GS"), ("GOOG", "IBM"), ("GS", "IBM"),
]

BETA_WINDOW = 252   # single_name_vrp section 3: 252 trading days ending at t0
HOLD = 21           # single_name_vrp section 3: the 21 trading days after t0
TAU = 21.0 / 252.0  # single_name_vrp section 4.3: option time to expiry
CUTOFF = "2026-09-01"  # pair PREREG section 3: the last month of run 3
MIN_N = 120         # pair PREREG section 3: the sample floor
BLOCK = 12          # pair PREREG section 5: block length in months
B = 2000            # pair PREREG section 5: bootstrap replications
SEED = 20261031     # pair PREREG section 5: the registered seed
MAX_DISCARD = 20    # pair PREREG section 5: more discards than this refuses


class ZeroSD(Exception):
    """Raised where an IR would divide by a zero (or undefined) standard deviation.

    The bootstrap rule counts and discards such a replication rather than
    substituting a value, because a substituted IR would be a fabricated
    observation feeding the percentile.
    """


def read_csv(path):
    """Read a section 2 CSV into (dates, {column: list of float or None}).

    Empty or non-numeric cells are kept as missing, because section 2 says a
    missing value stays missing and nothing is to be filled.
    """
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    header = [h.strip() for h in rows[0]]
    if header[0] != "date":
        raise SystemExit(f"{path}: first column must be 'date'")
    dates = []
    cols = {h: [] for h in header[1:]}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        dates.append(row[0].strip())
        for j, h in enumerate(header[1:], start=1):
            cell = row[j].strip() if j < len(row) else ""
            try:
                v = float(cell) if cell else None
            except ValueError:
                v = None
            if v is not None and not math.isfinite(v):
                v = None
            cols[h].append(v)
    return dates, cols


def norm_cdf(x):
    """N(x) = 0.5 * erfc(-x / sqrt(2)), exactly as single_name_vrp section 4.3 writes it."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bs_atm_call(vol_points):
    """At-the-money Black-Scholes call per unit of spot, rate 0, time 21/252.

    With strike equal to spot and zero rate, d1 = sigma * sqrt(tau) / 2 and
    d2 = -d1, so the premium is N(d1) - N(d2); this is the closed form the
    single-name PREREG states, used here so that the two implementations
    evaluate the same expression.
    """
    sigma = vol_points / 100.0
    d1 = sigma * math.sqrt(TAU) / 2.0
    return norm_cdf(d1) - norm_cdf(-d1)


def sd1(x):
    """Sample standard deviation with ddof 1, as section 4 of the pair PREREG requires."""
    return float(np.std(x, ddof=1))


def ir(x):
    """IR = mean / sd (ddof 1), monthly and not annualised.

    Fewer than two observations leave the standard deviation undefined, and
    a zero standard deviation leaves the ratio undefined; both raise ZeroSD
    so that the caller refuses rather than reporting a number.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size < 2:
        raise ZeroSD("fewer than two observations")
    s = sd1(x)
    if s == 0.0 or not math.isfinite(s):
        raise ZeroSD("zero standard deviation")
    return float(np.mean(x)) / s


def split_halves(c):
    """Low half is c < median, high half is c >= median (pair PREREG section 4).

    A value equal to the median goes to the high half, which the self-test of
    section 7 also checks; numpy.median is used because the document names it.
    """
    med = np.median(c)
    low = c < med
    return low, ~low


def d_stat(Y, C):
    """D(S) for the month list S already applied: Y and C are (months, 10) arrays.

    Returns D and the per-pair deltas. Every IR on the path raises ZeroSD if
    undefined, so a bootstrap replication with any such IR is discarded whole.
    """
    deltas = np.empty(Y.shape[1], dtype=np.float64)
    for p in range(Y.shape[1]):
        low, high = split_halves(C[:, p])
        deltas[p] = ir(Y[low, p]) - ir(Y[high, p])
    return float(np.mean(deltas)), deltas


def rankdata_avg(x):
    """Ranks 1..n with ties given their average rank (pair PREREG section 6)."""
    x = np.asarray(x, dtype=np.float64)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=np.float64)
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and x[order[j + 1]] == x[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(a, b):
    """Spearman correlation as Pearson correlation of average ranks."""
    ra, rb = rankdata_avg(a), rankdata_avg(b)
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float(np.sum(ra * ra)) * float(np.sum(rb * rb)))
    if den == 0.0:
        return None
    return float(np.sum(ra * rb)) / den


def fnum(v):
    """Render a float for JSON, refusing to emit NaN or infinity as a number."""
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


def safe_ir(x):
    """IR for no-weight reporting: null where undefined rather than a substitute."""
    try:
        return ir(x)
    except ZeroSD:
        return None


def build_sample(data_dir):
    """Construct U and the per-month arrays from the two input files.

    Returns a dict with the month dates of U and float64 arrays y (n, 5),
    G (n, 5) and c (n, 10).
    """
    pdates, pcols = read_csv(os.path.join(data_dir, "prices.csv"))
    vdates, vcols = read_csv(os.path.join(data_dir, "vx.csv"))

    # Trading days are SPY's dates. A row whose SPY cell is empty is read as
    # not a SPY date, because a day on which SPY has no close is not one on
    # which SPY traded in this file.
    keep = [k for k, v in enumerate(pcols["SPY"]) if v is not None]
    tdays = [pdates[k] for k in keep]
    if tdays != sorted(tdays):
        order = sorted(range(len(keep)), key=lambda m: tdays[m])
        keep = [keep[m] for m in order]
        tdays = [pdates[k] for k in keep]
    nT = len(tdays)

    def series(col):
        return np.array([np.nan if pcols[col][k] is None else pcols[col][k] for k in keep],
                        dtype=np.float64)

    P = {s: series(s) for s in NAMES + ["SPY"]}

    # Log return on trading day d uses the previous SPY trading day, and is
    # missing if either price is missing; NaN propagates that through ln.
    R = {}
    for s, px in P.items():
        r = np.full(nT, np.nan, dtype=np.float64)
        r[1:] = np.log(px[1:] / px[:-1])
        R[s] = r

    # Implied volatilities are read at t0 exactly, matched by date, with no
    # carrying forward from an earlier day.
    vx_index = {d: k for k, d in enumerate(vdates)}

    def vx_at(col, d):
        k = vx_index.get(d)
        return None if k is None else vcols[col][k]

    # Formation day: the first trading day of each calendar month present in
    # the trading-day list, used only if at least 21 trading days follow it.
    formation = []
    seen = set()
    for k, d in enumerate(tdays):
        ym = d[:7]
        if ym in seen:
            continue
        seen.add(ym)
        if k + HOLD <= nT - 1:
            formation.append(k)

    months, Y, Gm, Cm = [], [], [], []
    counts = {"formation_days": len(formation), "after_cutoff": 0, "not_all_five": 0}
    for k in formation:
        d = tdays[k]
        if d > CUTOFF:
            counts["after_cutoff"] += 1
            continue
        # The beta window is the 252 returns dated t0 and the 251 trading days
        # before it; the return dated the first trading day is undefined, so
        # t0 must sit at index 252 or later.
        if k - BETA_WINDOW + 1 < 1:
            counts["not_all_five"] += 1
            continue
        wb = slice(k - BETA_WINDOW + 1, k + 1)
        wh = slice(k + 1, k + HOLD + 1)
        vix = vx_at("MKT", d)
        spy_ok = (np.all(np.isfinite(R["SPY"][wb])) and np.all(np.isfinite(R["SPY"][wh])))
        ok = vix is not None and spy_ok
        yrow, grow = [], []
        if ok:
            xspy = R["SPY"][wb]
            for s in NAMES:
                v = vx_at(s, d)
                ri = R[s][wb]
                if v is None or not np.all(np.isfinite(ri)) or not np.all(np.isfinite(R[s][wh])):
                    ok = False
                    break
                # Beta must be defined (single_name_vrp section 3); it is not used
                # by this test, but an undefined slope would make the name-month
                # unused, so the condition is checked rather than assumed.
                if np.var(xspy) == 0.0:
                    ok = False
                    break
                G = P[s][k + HOLD] / P[s][k]
                c = bs_atm_call(v)
                yrow.append(c - max(G - 1.0, 0.0))
                grow.append(G)
        if not ok:
            counts["not_all_five"] += 1
            continue
        crow = []
        for a, b in PAIRS:
            crow.append(float(np.corrcoef(R[a][wb], R[b][wb])[0, 1]))
        months.append(d)
        Y.append(yrow)
        Gm.append(grow)
        Cm.append(crow)

    return {
        "months": months,
        "y": np.array(Y, dtype=np.float64).reshape(-1, len(NAMES)),
        "G": np.array(Gm, dtype=np.float64).reshape(-1, len(NAMES)),
        "c": np.array(Cm, dtype=np.float64).reshape(-1, len(PAIRS)),
        "counts": counts,
        "n_trading_days": nT,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    S = build_sample(args.data)
    months, y, G, C = S["months"], S["y"], S["G"], S["c"]
    n = len(months)
    idx = {s: j for j, s in enumerate(NAMES)}

    # Pair series: y_p, h_p and k_p of section 4, one column per pair.
    Yp = np.empty((n, len(PAIRS)), dtype=np.float64)
    Hp = np.empty((n, len(PAIRS)), dtype=np.float64)
    for p, (a, b) in enumerate(PAIRS):
        Yp[:, p] = (y[:, idx[a]] + y[:, idx[b]]) / 2.0
        Hp[:, p] = (G[:, idx[a]] + G[:, idx[b]]) / 2.0 - 1.0
    Kp = Hp + Yp

    out = {
        "n": n,
        "first_month": months[0] if n else None,
        "last_month": months[-1] if n else None,
    }

    # Full-sample statistic. If an IR on U is undefined, D cannot be computed
    # and no number is substituted; the run is recorded as REFUSED.
    D = None
    deltas = None
    full_refusal = None
    if n >= 2:
        try:
            D, deltas = d_stat(Yp, C)
        except ZeroSD as e:
            full_refusal = str(e)
    else:
        full_refusal = "fewer than two months"

    # Bootstrap, in the exact draw order section 5 fixes, so that a second
    # implementation reproduces the same D* list from the same seed.
    Dstar = []
    discarded = 0
    if n >= BLOCK:
        rng = np.random.default_rng(SEED)
        nb = math.ceil(n / BLOCK)
        for _ in range(B):
            starts = rng.integers(0, n - (BLOCK - 1), size=nb)
            pos = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
            try:
                d, _ = d_stat(Yp[pos], C[pos])
            except ZeroSD:
                discarded += 1
                continue
            Dstar.append(d)
    Dstar = np.array(Dstar, dtype=np.float64)

    lower = float(np.percentile(Dstar, 5)) if Dstar.size else None
    p95 = float(np.percentile(Dstar, 95)) if Dstar.size else None
    bmean = float(np.mean(Dstar)) if Dstar.size else None

    # Verdict order follows section 5: the sample floor first, then the
    # discard ceiling, then the one-sided test on D and its lower bound.
    if n < MIN_N:
        verdict = "INSUFFICIENT"
    elif discarded > MAX_DISCARD or D is None or lower is None:
        verdict = "REFUSED"
    elif D > 0 and lower > 0:
        verdict = "SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"

    out.update({
        "verdict": verdict,
        "D": fnum(D),
        "lower": fnum(lower),
        "discarded": discarded,
        "boot_mean": fnum(bmean),
        "boot_p05": fnum(lower),
        "boot_p95": fnum(p95),
    })

    # Per-name figures over U (section 6), needed also for the
    # diversification ratio's denominator.
    names = {}
    name_sd = {}
    for s in NAMES:
        col = y[:, idx[s]]
        name_sd[s] = sd1(col) if n >= 2 else None
        names[s] = {"mean_y": fnum(np.mean(col)) if n else None,
                    "sd_y": fnum(name_sd[s]), "ir": fnum(safe_ir(col))}

    pairs = {}
    mean_c, ir_u, divr = [], [], []
    dm, ds, sh_h, sh_k, sh_d = [], [], [], [], []
    for p, (a, b) in enumerate(PAIRS):
        yp, cp = Yp[:, p], C[:, p]
        low, high = split_halves(cp) if n else (np.zeros(0, bool), np.zeros(0, bool))
        yl, yh = yp[low], yp[high]
        sd_u = sd1(yp) if n >= 2 else None
        sd_l = sd1(yl) if yl.size >= 2 else None
        sd_h = sd1(yh) if yh.size >= 2 else None
        den = None
        if name_sd[a] is not None and name_sd[b] is not None:
            den = (name_sd[a] + name_sd[b]) / 2.0
        dr = sd_u / den if (sd_u is not None and den) else None
        shh = safe_ir(Hp[:, p])
        shk = safe_ir(Kp[:, p])
        # "Covered minus held" is read as the difference of the two Sharpe
        # ratios, since section 6 lists it among the Sharpe ratios of the
        # two positions and not as a third series.
        shd = (shk - shh) if (shh is not None and shk is not None) else None
        mc = float(np.mean(cp)) if n else None
        pairs[f"{a}-{b}"] = {
            "mean_c": fnum(mc),
            "mean_y": fnum(np.mean(yp)) if n else None,
            "sd_y": fnum(sd_u),
            "ir": fnum(safe_ir(yp)),
            "mean_y_low": fnum(np.mean(yl)) if yl.size else None,
            "sd_y_low": fnum(sd_l),
            "ir_low": fnum(safe_ir(yl)),
            "mean_y_high": fnum(np.mean(yh)) if yh.size else None,
            "sd_y_high": fnum(sd_h),
            "ir_high": fnum(safe_ir(yh)),
            "delta": fnum(deltas[p]) if deltas is not None else None,
            "div_ratio": fnum(dr),
            "sharpe_held": fnum(shh),
            "sharpe_covered": fnum(shk),
            "sharpe_diff": fnum(shd),
        }
        mean_c.append(mc)
        ir_u.append(safe_ir(yp))
        divr.append(dr)
        if yl.size and yh.size:
            dm.append(float(np.mean(yl)) - float(np.mean(yh)))
        if sd_l is not None and sd_h is not None:
            ds.append(sd_l - sd_h)
        sh_h.append(shh)
        sh_k.append(shk)
        sh_d.append(shd)
    out["pairs"] = pairs
    out["names"] = names

    def mean_or_none(v):
        # A mean over pairs is reported only if every pair supplied a value,
        # because a mean over a subset would silently change its population.
        return fnum(np.mean(v)) if len(v) == len(PAIRS) and all(x is not None for x in v) else None

    def spear_or_none(a, b):
        if any(x is None for x in a) or any(x is None for x in b):
            return None
        return fnum(spearman(a, b))

    out["spearman_c_ir"] = spear_or_none(mean_c, ir_u)
    out["spearman_c_divratio"] = spear_or_none(mean_c, divr)
    out["decomp_mean_diff"] = mean_or_none(dm)
    out["decomp_sd_diff"] = mean_or_none(ds)
    out["sharpe_held_mean"] = mean_or_none(sh_h)
    out["sharpe_covered_mean"] = mean_or_none(sh_k)
    out["sharpe_diff_mean"] = mean_or_none(sh_d)

    # Reconciliation with run 3: pooled over all pairs and months of U, split
    # at the pooled median of c_p with ties to the upper half, matching the
    # single-name document's "below" and "at or above" wording.
    if n:
        yall, call = Yp.ravel(), C.ravel()
        lo, hi = split_halves(call)
        out["recon_low_pct"] = fnum(100.0 * np.mean(yall[lo])) if lo.any() else None
        out["recon_high_pct"] = fnum(100.0 * np.mean(yall[hi])) if hi.any() else None
    else:
        out["recon_low_pct"] = None
        out["recon_high_pct"] = None

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    c = S["counts"]
    print(f"trading days: {S['n_trading_days']}")
    print(f"formation days with 21 following: {c['formation_days']}; "
          f"after cutoff: {c['after_cutoff']}; not all five used: {c['not_all_five']}")
    print(f"n = {n} ({out['first_month']} to {out['last_month']})")
    print(f"bootstrap kept {Dstar.size}, discarded {discarded}")
    if full_refusal:
        print(f"full-sample D undefined: {full_refusal}")
    print(f"verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
