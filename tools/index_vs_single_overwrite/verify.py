"""Independent second implementation of tools/index_vs_single_overwrite/PREREG.md.

Written from that document, tools/single_name_vrp/PREREG.md (data definitions) and
section 5 of tools/pair_risk_adjusted/PREREG.md (bootstrap scheme) alone, without reading
any other implementation. The reason a second implementation exists is that a defect in
one reading of the documents is only visible when a separate reading disagrees with it;
it therefore shares no code with the primary run.

Usage: python verify.py --data DIR --out DIR
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os

import numpy as np

NAMES = ["AAPL", "AMZN", "GOOG", "GS", "IBM"]
TAU = 21 / 252          # one-month option life in years, as both documents state
HOLD = 21               # trading days in the holding window
BETA_N = 252            # returns in the beta window, ending at and including t0
CUTOFF = "2026-09-01"   # last admissible formation day for U
SEED = 20261101         # registered seed for this test's bootstrap
B = 2000                # registered number of replications
BLOCK = 12              # registered block length, in months
NW_LAGS = 3             # registered Newey-West lag count


def read_csv(path: str) -> tuple[list[str], dict[str, list[float]]]:
    """Read a dated CSV; an empty or non-numeric cell becomes NaN.

    A missing value must stay missing (single_name_vrp section 2), so nothing is filled.
    """
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        dates: list[str] = []
        cols: dict[str, list[float]] = {h: [] for h in header[1:]}
        for row in reader:
            if not row:
                continue
            dates.append(row[0].strip())
            for j, h in enumerate(header[1:], start=1):
                cell = row[j].strip() if j < len(row) else ""
                try:
                    v = float(cell) if cell else math.nan
                except ValueError:
                    v = math.nan
                cols[h].append(v)
    return dates, cols


def ncdf(x: float) -> float:
    """Standard normal distribution function in the form the document prescribes."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def atm_call(s: float) -> float:
    """At-the-money call premium per unit of spot, rate 0, life 21/252.

    With strike equal to spot and zero rate, d1 = s*sqrt(tau)/2 and d2 = -d1, so the
    premium is N(d1) - N(-d1).
    """
    d1 = s * math.sqrt(TAU) / 2.0
    return ncdf(d1) - ncdf(-d1)


def sharpe(x: np.ndarray) -> float:
    """Monthly Sharpe ratio at rate 0: mean over sample standard deviation (ddof 1)."""
    return float(np.mean(x) / np.std(x, ddof=1))


def newey_west_t(x: np.ndarray) -> float:
    """t of the mean with a Bartlett-weighted Newey-West variance, 3 lags, no correction.

    var(mean) = (1/n^2)[sum e^2 + 2 sum_{l=1..L} (1 - l/(L+1)) sum_{t>l} e_t e_{t-l}].
    """
    n = len(x)
    m = float(np.mean(x))
    e = x - m
    s = float(np.sum(e * e))
    for lag in range(1, NW_LAGS + 1):
        w = 1.0 - lag / (NW_LAGS + 1)
        s += 2.0 * w * float(np.sum(e[lag:] * e[:-lag]))
    return m / math.sqrt(s / (n * n))


def build_months(data_dir: str) -> tuple[list[str], dict[str, np.ndarray]]:
    """Construct the month set U and the per-month quantities of PREREG section 2."""
    pdates, pcols = read_csv(os.path.join(data_dir, "prices.csv"))
    vdates, vcols = read_csv(os.path.join(data_dir, "vx.csv"))

    # Trading days are the rows on which SPY is present (single_name_vrp section 3);
    # a row without SPY is not a trading day and so cannot serve as d-1 for any return.
    keep = [k for k, v in enumerate(pcols["SPY"]) if not math.isnan(v)]
    tdays = [pdates[k] for k in keep]
    P = {c: np.array([pcols[c][k] for k in keep], dtype=np.float64) for c in NAMES + ["SPY"]}
    N = len(tdays)

    # Log returns indexed by the day they end on; index 0 has no predecessor. A return is
    # undefined (NaN) whenever either price is missing, which NaN arithmetic yields.
    R = {}
    for c, p in P.items():
        r = np.full(N, np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            r[1:] = np.log(p[1:] / p[:-1])
        R[c] = r

    # Implied volatility is read at t0 exactly, keyed by date; no carrying forward.
    vx_by_date = {}
    for k, d in enumerate(vdates):
        vx_by_date[d] = {c: vcols[c][k] for c in NAMES + ["MKT"]}

    rows = {k: [] for k in ["date", "hI", "kI", "hB", "kB", "yI", "yB", "yI_s", "yB_s"]}
    seen_months: set[str] = set()
    for idx, d in enumerate(tdays):
        month = d[:7]
        if month in seen_months:
            continue
        seen_months.add(month)
        # t0 is the first trading day of its calendar month; the month is used only if at
        # least 21 trading days follow it, so that T1 exists.
        if idx + HOLD > N - 1:
            continue
        if d > CUTOFF:
            continue
        # The beta window needs 252 returns ending at t0, i.e. 252 prior trading days.
        if idx - BETA_N + 1 < 1:
            continue
        vx = vx_by_date.get(d)
        if vx is None or math.isnan(vx["MKT"]):
            continue
        t1 = idx + HOLD
        bw = slice(idx - BETA_N + 1, idx + 1)
        hw = slice(idx + 1, t1 + 1)
        rm_b = R["SPY"][bw]
        rm_h = R["SPY"][hw]
        # All SPY returns in both windows must be present (index PREREG section 2 note).
        if np.isnan(rm_b).any() or np.isnan(rm_h).any():
            continue
        # A beta is defined only where SPY varies in the window; a zero variance would make
        # the slope a division by zero, so the name-month is unusable rather than defaulted.
        if float(np.var(rm_b)) == 0.0:
            continue
        all_used = True
        G = []
        vols = []
        for c in NAMES:
            v = vx[c]
            if math.isnan(v):
                all_used = False
                break
            ri_b = R[c][bw]
            ri_h = R[c][hw]
            if np.isnan(ri_b).any() or np.isnan(ri_h).any():
                all_used = False
                break
            # The slope itself is not used in this test, but its definedness is part of the
            # name-month rule, which is why the SPY-variance check above is applied.
            G.append(P[c][t1] / P[c][idx])
            vols.append(v / 100.0)
        if not all_used:
            continue
        G = np.array(G)
        vols = np.array(vols)
        GI = P["SPY"][t1] / P["SPY"][idx]
        vix = vx["MKT"] / 100.0

        y_i = np.array([atm_call(s) for s in vols]) - np.maximum(G - 1.0, 0.0)
        y_i_s = np.array([atm_call(0.95 * s) for s in vols]) - np.maximum(G - 1.0, 0.0)
        hB = float(np.mean(G) - 1.0)
        yB = float(np.mean(y_i))
        hI = GI - 1.0
        yI = atm_call(vix) - max(GI - 1.0, 0.0)

        rows["date"].append(d)
        rows["hI"].append(hI)
        rows["kI"].append(hI + yI)
        rows["hB"].append(hB)
        rows["kB"].append(hB + yB)
        rows["yI"].append(yI)
        rows["yB"].append(yB)
        # Skew sensitivity: index call at 0.9 VIX, each name's at 0.95 of its own index.
        rows["yI_s"].append(atm_call(0.9 * vix) - max(GI - 1.0, 0.0))
        rows["yB_s"].append(float(np.mean(y_i_s)))

    dates = rows.pop("date")
    return dates, {k: np.array(v, dtype=np.float64) for k, v in rows.items()}


def delta_of(hI, kI, hB, kB) -> float | None:
    """Delta = [Sh(kI) - Sh(hI)] - [Sh(kB) - Sh(hB)]; None if any sd is zero.

    A zero standard deviation leaves a Sharpe ratio undefined, and an undefined figure is
    refused rather than replaced by a default.
    """
    for x in (hI, kI, hB, kB):
        if float(np.std(x, ddof=1)) == 0.0:
            return None
    return (sharpe(kI) - sharpe(hI)) - (sharpe(kB) - sharpe(hB))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dates, m = build_months(a.data)
    n = len(dates)
    out: dict = {"n": n,
                 "first_month": dates[0] if n else None,
                 "last_month": dates[-1] if n else None}

    keys = ["verdict", "Delta", "lower", "discarded", "boot_mean", "boot_p95",
            "sh_hI", "sh_kI", "sh_hB", "sh_kB", "impr_I", "impr_B",
            "yI_mean_pct", "yI_sd_pct", "yI_ir", "yB_mean_pct", "yB_sd_pct", "yB_ir",
            "diff_mean_pct", "diff_t", "Delta_skew", "ann"]
    for k in keys:
        out[k] = None

    if n < 12:
        # Below one block the bootstrap cannot draw a start (n - 11 <= 0), and the document
        # requires figures only where n >= 12.
        out["verdict"] = "INSUFFICIENT"
    else:
        hI, kI, hB, kB = m["hI"], m["kI"], m["hB"], m["kB"]
        Delta = delta_of(hI, kI, hB, kB)

        rng = np.random.default_rng(SEED)
        nb = math.ceil(n / BLOCK)
        kept = []
        discarded = 0
        for _ in range(B):
            starts = rng.integers(0, n - 11, size=nb)
            ix = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
            d = delta_of(hI[ix], kI[ix], hB[ix], kB[ix])
            if d is None:
                discarded += 1
            else:
                kept.append(d)
        kept_a = np.array(kept, dtype=np.float64)
        lower = float(np.percentile(kept_a, 5)) if len(kept_a) else None

        # Verdict order as registered: sample floor first, then the discard ceiling, then
        # the one-sided test on Delta and its bootstrap lower bound.
        if n < 120:
            verdict = "INSUFFICIENT"
        elif discarded > 20:
            verdict = "REFUSED"
        elif Delta is not None and lower is not None and Delta > 0 and lower > 0:
            verdict = "SUPPORTED"
        else:
            verdict = "NOT SUPPORTED"

        sh = {k: sharpe(m[k]) for k in ("hI", "kI", "hB", "kB")}
        diff = m["yI"] - m["yB"]
        out.update({
            "verdict": verdict,
            "Delta": Delta,
            "lower": lower,
            "discarded": discarded,
            "boot_mean": float(np.mean(kept_a)) if len(kept_a) else None,
            "boot_p95": float(np.percentile(kept_a, 95)) if len(kept_a) else None,
            "sh_hI": sh["hI"], "sh_kI": sh["kI"], "sh_hB": sh["hB"], "sh_kB": sh["kB"],
            "impr_I": sh["kI"] - sh["hI"],
            "impr_B": sh["kB"] - sh["hB"],
            "yI_mean_pct": 100.0 * float(np.mean(m["yI"])),
            "yI_sd_pct": 100.0 * float(np.std(m["yI"], ddof=1)),
            "yI_ir": sharpe(m["yI"]),
            "yB_mean_pct": 100.0 * float(np.mean(m["yB"])),
            "yB_sd_pct": 100.0 * float(np.std(m["yB"], ddof=1)),
            "yB_ir": sharpe(m["yB"]),
            "diff_mean_pct": 100.0 * float(np.mean(diff)),
            "diff_t": newey_west_t(diff),
            "Delta_skew": delta_of(hI, hI + m["yI_s"], hB, hB + m["yB_s"]),
            "ann": {k: v * math.sqrt(12.0) for k, v in
                    (("sh_hI", sh["hI"]), ("sh_kI", sh["kI"]),
                     ("sh_hB", sh["hB"]), ("sh_kB", sh["kB"]))},
        })

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
