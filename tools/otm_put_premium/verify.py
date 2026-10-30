"""Independent second implementation of the OTM put premium test (PREREG sections 3 to 5).

Written from PREREG.md alone, without reference to any other implementation in this
directory, so that compare.py can test the primary figures against a separately derived
set. Python 3.12, numpy and the standard library only; all arithmetic in float64.

Usage: python verify.py --data DIR --out DIR
Reads DIR/series.csv (columns date, PPUT, SPY, PUT, BXM) and writes OUT/verify.json.
"""

import argparse
import csv
import json
import math
import os

import numpy as np

LAST_MONTH = (2026, 9)
SPLIT_MONTH = (2016, 5)  # pre-period runs up to and including this month
NW_LAGS = 3
SEED = 20261105
B = 2000
TCRIT_SEED = 20261106
TCRIT_B = 1999
BLOCK = 12
HURDLE_T = 2.326
MIN_N = 120


def parse_value(text):
    """Return a float, or None where the cell is blank or non-numeric.

    PREREG section 2 says a blank or non-numeric value stays missing; it is never
    replaced by a neighbouring value, since that would invent a price.
    """
    text = (text or "").strip()
    if text == "":
        return None
    try:
        v = float(text)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    return v


def read_series(path):
    rows = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            d = r["date"].strip()
            y, m, _ = d.split("-")
            rows.append({
                "date": d,
                "ym": (int(y), int(m)),
                "PPUT": parse_value(r.get("PPUT")),
                "SPY": parse_value(r.get("SPY")),
                "PUT": parse_value(r.get("PUT")),
                "BXM": parse_value(r.get("BXM")),
            })
    rows.sort(key=lambda r: r["date"])
    return rows


def month_values(rows):
    """Month-end values per PREREG section 3.

    A month's date is the last date in the calendar month on which PPUT and SPY are both
    present; PUT and BXM are read on that same date and are missing for the month where
    their own cell is missing on it (no search for another date). Months after 2026-09 are
    discarded.
    """
    months = {}
    for r in rows:
        if r["ym"] > LAST_MONTH:
            continue
        if r["PPUT"] is None or r["SPY"] is None:
            continue
        # Rows are sorted ascending, so the last assignment is the last qualifying date.
        months[r["ym"]] = r
    return months


def prev_month(ym):
    y, m = ym
    return (y - 1, 12) if m == 1 else (y, m - 1)


def monthly_returns(months):
    """Returns for each month whose previous calendar month also has a value.

    A gap month breaks the chain: the following month has no return, because PREREG
    defines the return over the previous calendar month's value only.
    """
    out = []
    for ym in sorted(months):
        pm = prev_month(ym)
        if pm not in months:
            continue
        cur, prv = months[ym], months[pm]
        rec = {"ym": ym}
        for s in ("PPUT", "SPY", "PUT", "BXM"):
            if cur[s] is not None and prv[s] is not None:
                rec[s] = cur[s] / prv[s] - 1.0
            else:
                rec[s] = None
        out.append(rec)
    return out


def newey_west_se(x):
    """Newey-West standard error of the mean, 3 lags, Bartlett 1 - l/4, no small-sample correction."""
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    mu = x.mean()
    e = x - mu
    s = float(np.sum(e * e))
    for lag in range(1, NW_LAGS + 1):
        if lag >= n:
            break
        w = 1.0 - lag / (NW_LAGS + 1)
        s += 2.0 * w * float(np.sum(e[lag:] * e[:-lag]))
    return math.sqrt(s / (n * n))


def newey_west_t(x):
    """Mean and t = mean / se_NW."""
    x = np.asarray(x, dtype=np.float64)
    mu = float(x.mean())
    se = newey_west_se(x)
    # A zero standard error leaves t undefined; it is reported as NaN, not floored.
    t = mu / se if se > 0 else float("nan")
    return mu, float(t)


def bootstrap_t_crit(y):
    """Block-bootstrap critical value per PREREG section 4 (amended 30 October 2026).

    All 1999 rows of starts are drawn in one call, so the draw order is fixed by the
    shape of the request rather than by a loop. Each replication's t is centred on the
    full-sample mean, so the bootstrap distribution approximates the null shape of t
    including the skew that inflates its upper tail on short-put data.
    """
    n = y.size
    rng = np.random.default_rng(TCRIT_SEED)
    starts = rng.integers(0, n - (BLOCK - 1), size=(TCRIT_B, math.ceil(n / BLOCK)))
    mu = y.mean()
    tstar = np.empty(TCRIT_B, dtype=np.float64)
    for b in range(TCRIT_B):
        idx = np.concatenate([np.arange(st, st + BLOCK) for st in starts[b]])[:n]
        yb = y[idx]
        tstar[b] = (yb.mean() - mu) / newey_west_se(yb)
    return float(np.percentile(tstar, 99))


def max_drawdown(r):
    """Maximum drawdown of the compounded path starting at 1, against a running maximum
    that includes the starting value; reported as a negative fraction."""
    wealth = np.concatenate(([1.0], np.cumprod(1.0 + np.asarray(r, dtype=np.float64))))
    peak = np.maximum.accumulate(wealth)
    return float(np.min(wealth / peak - 1.0))


def ann_block(r, with_downside):
    r = np.asarray(r, dtype=np.float64)
    mu = r.mean()
    sd = r.std(ddof=1)
    out = {
        "mean": float(12.0 * mu),
        "vol": float(math.sqrt(12.0) * sd),
        "sharpe": float(math.sqrt(12.0) * mu / sd),
        "maxdd": max_drawdown(r),
    }
    if with_downside:
        # Monthly, not annualised, as the instruction specifies.
        out["downside_ratio"] = float(mu / math.sqrt(np.mean(np.minimum(r, 0.0) ** 2)))
    return out


def monthly_sharpe(r):
    return r.mean() / r.std(ddof=1)


def bootstrap_delta(k, spy):
    """Moving-block bootstrap of Sh(k) - Sh(spy), monthly Sharpe, both series resampled on
    the same indices so the pairing within each month is kept."""
    n = k.size
    rng = np.random.default_rng(SEED)
    nblocks = math.ceil(n / BLOCK)
    deltas = np.empty(B, dtype=np.float64)
    for b in range(B):
        starts = rng.integers(0, n - (BLOCK - 1), size=nblocks)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        deltas[b] = monthly_sharpe(k[idx]) - monthly_sharpe(spy[idx])
    return float(np.percentile(deltas, 5)), float(np.percentile(deltas, 95))


def fmt(ym):
    return f"{ym[0]:04d}-{ym[1]:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = read_series(os.path.join(args.data, "series.csv"))
    rets = monthly_returns(month_values(rows))
    main_rets = [r for r in rets if r["PPUT"] is not None and r["SPY"] is not None]
    n = len(main_rets)

    result = {"n": n}
    if n == 0:
        # Refuse to score rather than emit figures over an empty sample.
        result.update({"first_month": None, "last_month": None, "verdict": "INSUFFICIENT"})
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "verify.json"), "w") as fh:
            json.dump(result, fh, indent=2)
        return

    yms = [r["ym"] for r in main_rets]
    r_spy = np.array([r["SPY"] for r in main_rets], dtype=np.float64)
    r_pput = np.array([r["PPUT"] for r in main_rets], dtype=np.float64)
    y = r_spy - r_pput

    mean_y, t = newey_west_t(y)
    t_crit = bootstrap_t_crit(y) if n >= BLOCK else None

    def decide(crit):
        if n < MIN_N:
            return "INSUFFICIENT"
        return "SUPPORTED" if (mean_y > 0 and t >= crit) else "NOT SUPPORTED"

    verdict = decide(t_crit)
    verdict_normal = decide(HURDLE_T)

    pre = np.array([ym <= SPLIT_MONTH for ym in yms])
    mean_pre, t_pre = newey_west_t(y[pre]) if pre.any() else (None, None)
    mean_post, t_post = newey_west_t(y[~pre]) if (~pre).any() else (None, None)

    mu = y.mean()
    sd = y.std(ddof=1)
    e = y - mu
    sd_pop = y.std(ddof=0)
    pos_sum = float(np.sum(y[y > 0]))
    worst5 = float(np.sum(np.sort(y)[:5]))
    y_stats = {
        "ann_mean": float(12.0 * mu),
        "sd": float(sd),
        "ratio": float(mu / sd),
        "skew": float(np.mean(e ** 3) / sd_pop ** 3),
        "worst": float(y.min()),
        "share_neg": float(np.mean(y < 0)),
        "worst5_over_pos": worst5 / pos_sum if pos_sum > 0 else None,
    }

    k = r_spy + y
    lo, hi = bootstrap_delta(k, r_spy)
    overlay = {
        "k": ann_block(k, True),
        "spy": ann_block(r_spy, True),
        "delta_k": float(monthly_sharpe(k) - monthly_sharpe(r_spy)),
        "boot_p05": lo,
        "boot_p95": hi,
    }

    atm_rows = [r for r in rets if r["PUT"] is not None and r["BXM"] is not None and r["SPY"] is not None]
    atm = {"n": len(atm_rows)}
    if len(atm_rows) >= 2:
        for s in ("PUT", "BXM", "SPY"):
            atm[s] = ann_block([r[s] for r in atm_rows], False)

    result.update({
        "first_month": fmt(yms[0]),
        "last_month": fmt(yms[-1]),
        "verdict": verdict,
        "t_crit": t_crit,
        "verdict_normal": verdict_normal,
        "mean_y": mean_y,
        "t": t,
        "mean_y_pre": mean_pre,
        "t_pre": t_pre,
        "n_pre": int(pre.sum()),
        "mean_y_post": mean_post,
        "t_post": t_post,
        "n_post": int((~pre).sum()),
        "y_stats": y_stats,
        "overlay": overlay,
        "atm": atm,
    })
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as fh:
        json.dump(result, fh, indent=2)


if __name__ == "__main__":
    main()
