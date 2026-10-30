"""Independent second implementation of PREREG.md sections 3 to 5.

Written from PREREG.md alone, without reference to any other implementation in
this directory, so that compare.py can test whether the registered statistic,
the bootstrap and the verdict are reproducible from the document as written.
Python 3.12, numpy and the standard library only, float64 throughout.

Usage: python verify.py --data DIR --out DIR
Reads DIR/series.csv (columns date, BXM, SPY, VIX) and writes OUT/verify.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os

import numpy as np

SEED = 20261104
B = 2000
BLOCK = 12
N_MIN = 120
DISCARD_MAX = 20
LAST_MONTH = (2026, 9)
SPLIT_MONTH = (2011, 1)        # from2011 begins here; pre2011 ends at 2010-12
RECON_FIRST = (2011, 2)        # proxy reconciliation window, inclusive
RECON_LAST = (2026, 9)
NW_LAGS = 3


def _parse_float(cell: str) -> float | None:
    """A blank or non-numeric cell stays missing (PREREG section 2); it is
    never replaced by a neighbouring value, because a filled value would be a
    price the index never printed."""
    cell = (cell or "").strip()
    if cell == "":
        return None
    try:
        v = float(cell)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    return v


def load_month_values(path: str) -> dict[tuple[int, int], tuple[float, float]]:
    """For each calendar month, the BXM and SPY values on the last date in
    that month on which both are present. VIX is not consulted; it serves the
    proxy reconciliation in the primary implementation only, and the
    reconciliation registered in section 5 uses BXM and SPY alone."""
    best: dict[tuple[int, int], tuple[str, float, float]] = {}
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            date = (row.get("date") or "").strip()
            if len(date) < 10:
                continue
            bxm = _parse_float(row.get("BXM", ""))
            spy = _parse_float(row.get("SPY", ""))
            if bxm is None or spy is None:
                continue
            key = (int(date[0:4]), int(date[5:7]))
            prior = best.get(key)
            # String comparison of ISO dates orders them correctly, and taking
            # the maximum makes the result independent of row order.
            if prior is None or date > prior[0]:
                best[key] = (date, bxm, spy)
    return {k: (v[1], v[2]) for k, v in best.items()}


def _next_month(ym: tuple[int, int]) -> tuple[int, int]:
    y, m = ym
    return (y + 1, 1) if m == 12 else (y, m + 1)


def _prev_month(ym: tuple[int, int]) -> tuple[int, int]:
    y, m = ym
    return (y - 1, 12) if m == 1 else (y, m - 1)


def monthly_returns(values):
    """Monthly returns from the first calendar month after the first month
    with both series present, through LAST_MONTH. A month lacking its own
    value, or whose previous calendar month lacks one, has no return and is
    excluded; it is not bridged across the gap, since a two-month return
    counted as one month would misstate both the mean and the variance."""
    if not values:
        return [], np.empty(0), np.empty(0)
    first = min(values)
    ym = _next_month(first)
    months, rb, rs = [], [], []
    while ym <= LAST_MONTH:
        prev = _prev_month(ym)
        if ym in values and prev in values:
            b1, s1 = values[ym]
            b0, s0 = values[prev]
            months.append(ym)
            rb.append(b1 / b0 - 1.0)
            rs.append(s1 / s0 - 1.0)
        ym = _next_month(ym)
    return months, np.asarray(rb, dtype=np.float64), np.asarray(rs, dtype=np.float64)


def sharpe(x: np.ndarray) -> float:
    """Sh(x) = mean / sd (ddof 1), monthly, rate 0. Refuses (returns NaN)
    rather than returning zero where the ratio is undefined."""
    if x.size < 2:
        return float("nan")
    sd = float(np.std(x, ddof=1))
    if sd == 0.0:
        return float("nan")
    return float(np.mean(x)) / sd


def max_drawdown(x: np.ndarray) -> float:
    """Most negative drawdown of the compounded series starting from 1,
    measured against the running maximum including the starting value."""
    wealth = np.concatenate(([1.0], np.cumprod(1.0 + x)))
    peak = np.maximum.accumulate(wealth)
    return float(np.min(wealth / peak - 1.0))


def downside_ratio(x: np.ndarray) -> float:
    denom = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    if denom == 0.0:
        return float("nan")
    return float(np.mean(x)) / denom


def annualised(x: np.ndarray) -> dict:
    return {
        "mean": 12.0 * float(np.mean(x)),
        "vol": math.sqrt(12.0) * float(np.std(x, ddof=1)),
        "sharpe": math.sqrt(12.0) * sharpe(x),
        "maxdd": max_drawdown(x),
        "downside_ratio": downside_ratio(x),
    }


def newey_west_t(d: np.ndarray, lags: int = NW_LAGS) -> float:
    """Constant-only Newey-West t of the mean, Bartlett weights 1 - l/(L+1),
    no small-sample correction:
    var(mean) = (1/n^2)[sum e^2 + 2 sum_l w_l sum_{t>l} e_t e_{t-l}]."""
    n = d.size
    if n < 2:
        return float("nan")
    e = d - np.mean(d)
    s = float(np.sum(e * e))
    for lag in range(1, lags + 1):
        if lag >= n:
            break
        w = 1.0 - lag / (lags + 1.0)
        s += 2.0 * w * float(np.sum(e[lag:] * e[:-lag]))
    var_mean = s / (n * n)
    if var_mean <= 0.0:
        return float("nan")
    return float(np.mean(d)) / math.sqrt(var_mean)


def bootstrap(rb: np.ndarray, rs: np.ndarray):
    """Moving-block bootstrap of Delta, exactly as registered: one generator,
    for each replication ceil(n/12) starts drawn from [0, n-11), blocks
    concatenated in draw order and truncated to n. A replication with a zero
    standard deviation in either series is discarded and counted; it is not
    redrawn, because redrawing would change every later replication and so
    the registered sequence."""
    n = rb.size
    rng = np.random.default_rng(SEED)
    k = math.ceil(n / BLOCK)
    kept = []
    discarded = 0
    for _ in range(B):
        starts = rng.integers(0, n - (BLOCK - 1), size=k)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        xb, xs = rb[idx], rs[idx]
        if float(np.std(xb, ddof=1)) == 0.0 or float(np.std(xs, ddof=1)) == 0.0:
            discarded += 1
            continue
        kept.append(sharpe(xb) - sharpe(xs))
    return np.asarray(kept, dtype=np.float64), discarded


def _clean(v):
    """JSON has no NaN; an undefined figure is written as null, never as 0."""
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _ym(ym) -> str | None:
    return None if ym is None else f"{ym[0]:04d}-{ym[1]:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    values = load_month_values(os.path.join(args.data, "series.csv"))
    months, rb, rs = monthly_returns(values)
    n = len(months)

    out: dict = {"n": n,
                 "first_month": _ym(months[0]) if n else None,
                 "last_month": _ym(months[-1]) if n else None}

    delta = sharpe(rb) - sharpe(rs) if n >= 2 else float("nan")

    # The bootstrap needs at least one full block; below that it is not run
    # and its fields are null. The verdict is INSUFFICIENT in that case anyway.
    if n >= BLOCK:
        kept, discarded = bootstrap(rb, rs)
    else:
        kept, discarded = np.empty(0), 0
    if kept.size:
        lower = float(np.percentile(kept, 1))
        boot_mean = float(np.mean(kept))
        p05 = float(np.percentile(kept, 5))
        p95 = float(np.percentile(kept, 95))
    else:
        lower = boot_mean = p05 = p95 = float("nan")

    if n < N_MIN:
        verdict = "INSUFFICIENT"
    elif discarded > DISCARD_MAX:
        verdict = "REFUSED"
    elif delta > 0 and lower > 0:
        verdict = "SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"

    pre = np.array([m < SPLIT_MONTH for m in months], dtype=bool)
    post = ~pre
    recon = np.array([RECON_FIRST <= m <= RECON_LAST for m in months], dtype=bool)
    d = rb - rs

    def sub_delta(mask):
        return sharpe(rb[mask]) - sharpe(rs[mask]) if mask.sum() >= 2 else float("nan")

    def pct_mean(mask):
        return 100.0 * float(np.mean(d[mask])) if mask.any() else float("nan")

    out.update({
        "verdict": verdict,
        "Delta": delta,
        "lower": lower,
        "discarded": discarded,
        "boot_mean": boot_mean,
        "boot_p05": p05,
        "boot_p95": p95,
        "sh_bxm": sharpe(rb) if n else float("nan"),
        "sh_spy": sharpe(rs) if n else float("nan"),
        "ann": {"BXM": annualised(rb), "SPY": annualised(rs)} if n >= 2 else None,
        "delta_pre2011": sub_delta(pre),
        "delta_from2011": sub_delta(post),
        "diff_mean_pct": pct_mean(np.ones(n, dtype=bool)),
        "diff_t": newey_west_t(d),
        "diff_mean_pct_from2011": pct_mean(post),
        "diff_t_from2011": newey_west_t(d[post]),
        "recon_mean_pct": pct_mean(recon),
    })

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as fh:
        json.dump(_clean(out), fh, indent=2)
    print(f"verify.py: wrote {os.path.join(args.out, 'verify.json')} (n={n}, verdict={verdict})")


if __name__ == "__main__":
    main()
