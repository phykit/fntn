"""Independent second implementation of PREREG.md sections 3 to 5.

Written from PREREG.md alone, without reading any other module under tools/,
so that agreement with the primary implementation is evidence that both
implement the document rather than evidence that one copied the other.

Usage: python verify.py --data DIR --out DIR
Reads DIR/vx.csv (date,MKT,M3) and DIR/prices.csv (date,SPY); writes
OUT/verify.json. Python 3.12, numpy and the standard library, float64.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os

import numpy as np

CUTOFF = "2026-09-01"
HORIZON = 21
SEED = 20261102
SEED_RAND = 20261103
B = 2000
R = 2000
BLOCK = 12
N_MIN = 120
N_REPORT = 12
MAX_DISCARD = 20
NW_LAGS = 3


def read_series(path: str, columns: list[str]) -> dict[str, dict[str, float]]:
    """Read a date-keyed CSV; an empty or non-numeric cell stays missing.

    A missing value is omitted from the mapping rather than replaced, because
    the registration reads levels at t0 exactly and forbids carrying a prior
    value forward.
    """
    out: dict[str, dict[str, float]] = {c: {} for c in columns}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            date = (row.get("date") or "").strip()
            if not date:
                continue
            for c in columns:
                raw = (row.get(c) or "").strip()
                if raw == "":
                    continue
                try:
                    v = float(raw)
                except ValueError:
                    continue
                if math.isfinite(v):
                    out[c][date] = v
    return out


def ncdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF written as 0.5 * erfc(-x / sqrt 2), as registered."""
    v = np.vectorize(lambda z: 0.5 * math.erfc(-z / math.sqrt(2.0)), otypes=[np.float64])
    return v(np.asarray(x, dtype=np.float64))


def atm_call(s: np.ndarray) -> np.ndarray:
    """At-the-money call per unit of spot at rate zero over 21 of 252 days."""
    d1 = s * math.sqrt(HORIZON / 252.0) / 2.0
    return ncdf(d1) - ncdf(-d1)


def sharpe(x: np.ndarray) -> float | None:
    """Monthly Sharpe ratio, mean over sample sd (ddof 1), rate zero.

    Returns None where the sd is zero or undefined, since a ratio over a zero
    denominator is a refusal to score and not a number.
    """
    if x.size < 2:
        return None
    sd = float(np.std(x, ddof=1))
    if not sd > 0.0:
        return None
    return float(np.mean(x)) / sd


def mean_sd_pct(x: np.ndarray) -> tuple[float | None, float | None]:
    """Mean and sd (ddof 1) in per cent; None where the sample cannot carry one."""
    m = float(np.mean(x)) * 100.0 if x.size >= 1 else None
    s = float(np.std(x, ddof=1)) * 100.0 if x.size >= 2 else None
    return m, s


def newey_west_t(d: np.ndarray) -> float | None:
    """Constant-only Newey-West t with three lags and Bartlett weights 1 - l/4.

    No small-sample correction is applied because the registration names
    none; the residuals are deviations from the sample mean.
    """
    n = d.size
    if n < 2:
        return None
    m = float(np.mean(d))
    e = d - m
    s = float(np.sum(e * e))
    for lag in range(1, NW_LAGS + 1):
        if lag >= n:
            break
        s += 2.0 * (1.0 - lag / (NW_LAGS + 1.0)) * float(np.sum(e[lag:] * e[:-lag]))
    var = s / (n * n)
    if not var > 0.0:
        return None
    return m / math.sqrt(var)


def build_months(vx: dict, px: dict):
    """Select the used months per section 3 and return aligned arrays.

    Trading days are the dates with a SPY price, sorted. t0 is the first such
    day in each calendar month, kept only where at least 21 trading days
    follow it, so that T1 exists within the data.
    """
    spy = px["SPY"]
    days = sorted(spy)
    last = len(days) - 1
    seen: set[str] = set()
    t0_idx: list[int] = []
    for i, d in enumerate(days):
        ym = d[:7]
        if ym in seen:
            continue
        seen.add(ym)
        if i + HORIZON <= last:
            t0_idx.append(i)
    dates, vix, v3m, g = [], [], [], []
    for i in t0_idx:
        d = days[i]
        if d > CUTOFF:
            continue
        a = vx["MKT"].get(d)
        b = vx["M3"].get(d)
        if a is None or b is None:
            continue
        dates.append(d)
        vix.append(a)
        v3m.append(b)
        g.append(spy[days[i + HORIZON]] / spy[d])
    return (dates, np.array(vix, dtype=np.float64), np.array(v3m, dtype=np.float64),
            np.array(g, dtype=np.float64))


def delta_of(h: np.ndarray, y: np.ndarray, w: np.ndarray) -> float | None:
    """Sh(k_F) - Sh(k_A); None where either Sharpe ratio is undefined."""
    a = sharpe(h + y)
    f = sharpe(h + w * y)
    if a is None or f is None:
        return None
    return f - a


def bootstrap(h: np.ndarray, y: np.ndarray, w: np.ndarray):
    """Moving-block bootstrap of Delta, exactly as section 4 draws it.

    The draw sequence is fixed by the seed and by drawing all starts for a
    replication in one call, so a second implementation reproduces it.
    A replication with zero sd in k_F or k_A is discarded and counted rather
    than scored, because Delta is undefined there.
    """
    n = h.size
    rng = np.random.default_rng(SEED)
    nblocks = math.ceil(n / BLOCK)
    kept: list[float] = []
    discarded = 0
    for _ in range(B):
        starts = rng.integers(0, n - BLOCK + 1, size=nblocks)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        hh, yy, ww = h[idx], y[idx], w[idx]
        ka = hh + yy
        kf = hh + ww * yy
        if not (np.std(ka, ddof=1) > 0.0 and np.std(kf, ddof=1) > 0.0):
            discarded += 1
            continue
        kept.append(float(np.mean(kf) / np.std(kf, ddof=1) - np.mean(ka) / np.std(ka, ddof=1)))
    return np.array(kept, dtype=np.float64), discarded


def random_skip(h: np.ndarray, y: np.ndarray, n_back: int) -> np.ndarray:
    """Random-skip benchmark of section 4, drawn from its own seeded stream.

    Skipping any n_back months moves the Sharpe ratio by itself, so the
    filter must beat skipping the same number of months chosen at random;
    otherwise the verdict would not be about the term structure at all.
    The draws are taken in order from a generator separate from the
    bootstrap's, so neither stream perturbs the other. A draw whose Delta is
    undefined (zero sd) is left out of the distribution rather than scored.
    """
    n = h.size
    rng2 = np.random.default_rng(SEED_RAND)
    sh_a = sharpe(h + y)
    out: list[float] = []
    for _ in range(R):
        skip = rng2.choice(n, size=n_back, replace=False)
        wr = np.ones(n, dtype=np.float64)
        wr[skip] = 0.0
        sh_r = sharpe(h + wr * y)
        if sh_r is None or sh_a is None:
            continue
        out.append(sh_r - sh_a)
    return np.array(out, dtype=np.float64)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    vx = read_series(os.path.join(args.data, "vx.csv"), ["MKT", "M3"])
    px = read_series(os.path.join(args.data, "prices.csv"), ["SPY"])
    dates, vix, v3m, g = build_months(vx, px)
    n = len(dates)

    res: dict = {k: None for k in [
        "n", "n_back", "back_dates", "first_month", "last_month", "verdict", "Delta", "lower",
        "discarded", "boot_mean", "boot_p05", "boot_p95", "y_con_mean_pct", "y_con_sd_pct",
        "y_back_mean_pct", "y_back_sd_pct", "sh_h", "sh_kA", "sh_kF", "sh_kF_minus_h", "ann",
        "diff_mean_pct", "diff_t", "annret", "Delta_steep", "Delta_skew",
        "rand_mean", "rand_p99", "rand_share_ge"]}
    res["n"] = n

    if n < N_REPORT:
        # Below twelve months the block length exceeds the sample, so nothing
        # is computed; the verdict is INSUFFICIENT because n < 120 a fortiori.
        res["verdict"] = "INSUFFICIENT"
        res["n_back"] = None
        res["back_dates"] = []
        if n:
            res["first_month"], res["last_month"] = dates[0][:7], dates[-1][:7]
        write(args.out, res)
        return

    h = g - 1.0
    y = atm_call(vix / 100.0) - np.maximum(g - 1.0, 0.0)
    w = (vix < v3m).astype(np.float64)
    ka = h + y
    kf = h + w * y

    back = w == 0.0
    res["n_back"] = int(n - int(np.sum(w)))
    res["back_dates"] = [d for d, b in zip(dates, back) if b]
    res["first_month"], res["last_month"] = dates[0][:7], dates[-1][:7]

    res["y_con_mean_pct"], res["y_con_sd_pct"] = mean_sd_pct(y[~back])
    res["y_back_mean_pct"], res["y_back_sd_pct"] = mean_sd_pct(y[back])

    sh_h, sh_a, sh_f = sharpe(h), sharpe(ka), sharpe(kf)
    res["sh_h"], res["sh_kA"], res["sh_kF"] = sh_h, sh_a, sh_f
    res["sh_kF_minus_h"] = (sh_f - sh_h) if (sh_f is not None and sh_h is not None) else None
    r12 = math.sqrt(12.0)
    res["ann"] = {k: (v * r12 if v is not None else None)
                  for k, v in (("sh_h", sh_h), ("sh_kA", sh_a), ("sh_kF", sh_f))}

    d = kf - ka
    res["diff_mean_pct"] = float(np.mean(d)) * 100.0
    res["diff_t"] = newey_west_t(d)
    res["annret"] = {"h": 12.0 * float(np.mean(h)), "kA": 12.0 * float(np.mean(ka)),
                     "kF": 12.0 * float(np.mean(kf))}

    delta = delta_of(h, y, w)
    res["Delta"] = delta

    kept, discarded = bootstrap(h, y, w)
    res["discarded"] = discarded
    if kept.size:
        res["lower"] = float(np.percentile(kept, 1))
        res["boot_mean"] = float(np.mean(kept))
        res["boot_p05"] = float(np.percentile(kept, 5))
        res["boot_p95"] = float(np.percentile(kept, 95))

    # The benchmark uses the original indicator's n_back, so that it skips
    # exactly as many months as the filter under test does.
    rand = random_skip(h, y, res["n_back"])
    if rand.size:
        res["rand_mean"] = float(np.mean(rand))
        res["rand_p99"] = float(np.percentile(rand, 99))
        if delta is not None:
            res["rand_share_ge"] = float(np.mean(rand >= delta))

    # Sensitivity rows: each moves one input and leaves the other registered.
    w_steep = ((vix / v3m) < 0.95).astype(np.float64)
    res["Delta_steep"] = delta_of(h, y, w_steep)
    y_skew = atm_call(0.9 * vix / 100.0) - np.maximum(g - 1.0, 0.0)
    res["Delta_skew"] = delta_of(h, y_skew, w)

    # Verdict in the registered order. A Delta or lower that cannot be scored
    # is never read as a pass, so it falls through to NOT SUPPORTED.
    if n < N_MIN:
        res["verdict"] = "INSUFFICIENT"
    elif discarded > MAX_DISCARD:
        res["verdict"] = "REFUSED"
    elif (delta is not None and res["lower"] is not None and res["rand_p99"] is not None
          and delta > 0 and res["lower"] > 0 and delta > res["rand_p99"]):
        res["verdict"] = "SUPPORTED"
    else:
        res["verdict"] = "NOT SUPPORTED"

    write(args.out, res)


def write(out_dir: str, res: dict) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "verify.json"), "w") as fh:
        json.dump(res, fh, indent=2)


if __name__ == "__main__":
    main()
