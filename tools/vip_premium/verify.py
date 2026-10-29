"""Independent second implementation of tools/vip_premium/PREREG.md.

Written from vip_premium/PREREG.md (governs) and degross_proxy_b/PREREG.md
sections 3 and 4 (basket return rules) and the input formats alone.

Usage: python verify.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]
BENCH = ["SPY", "QQQ", "RSP"]
NW_LAGS = 3
MIN_MONTHS = 120
T_MIN = 2.0
ALPHA_MIN = 0.02


# ----------------------------------------------------------------- reading
def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s.strip())


def _f(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    v = float(s)
    if math.isnan(v):
        return None
    return v


def read_wide(path: str) -> tuple[list[str], dict[dt.date, dict[str, float | None]]]:
    with open(path, newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        cols = header[1:]
        out: dict[dt.date, dict[str, float | None]] = {}
        for row in r:
            if not row or not row[0].strip():
                continue
            row = row + [""] * (len(header) - len(row))
            d = _d(row[0])
            if d in out:
                raise SystemExit(f"duplicate date {d} in {path}")
            out[d] = {c: _f(v) for c, v in zip(cols, row[1:])}
    return cols, out


def read_baskets(path: str):
    """Return list of (effective, [symbols...]) sorted by effective, long leg only."""
    groups: dict[tuple[str, dt.date], list[tuple[int, str]]] = defaultdict(list)
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["leg"].strip() != "long":
                continue
            key = (row["period"].strip(), _d(row["effective"]))
            groups[key].append((int(row["rank"]), row["symbol"].strip()))
    by_eff: dict[dt.date, list[str]] = {}
    for (period, eff), rows in groups.items():
        if eff in by_eff:
            raise SystemExit(f"two long baskets share effective date {eff}; refusing")
        by_eff[eff] = [s for _, s in sorted(rows)]
    return sorted(by_eff.items())


# ----------------------------------------------------------- daily series
def basket_daily(baskets, prices, spy_days):
    """degross_proxy_b section 3/4: dict day -> long-leg return (only defined days)."""
    idx = {d: i for i, d in enumerate(spy_days)}
    out: dict[dt.date, float] = {}
    windows = []  # (first earning day, last earning day)
    for k, (eff, syms) in enumerate(baskets):
        end = baskets[k + 1][0] if k + 1 < len(baskets) else spy_days[-1]
        days = [d for d in spy_days if eff < d <= end]
        if days:
            windows.append((days[0], days[-1]))
        # entered: has an adjusted close on E_q (E_q must itself be looked up in prices)
        entered = []
        row_e = prices.get(eff, {})
        for s in syms:
            if row_e.get(s) is not None:
                entered.append(s)
        for d in days:
            i = idx[d]
            prev = spy_days[i - 1]
            pr, pp = prices[d], prices[prev]
            rets = []
            for s in entered:  # a symbol listed twice counts twice
                a, b = pr.get(s), pp.get(s)
                if a is not None and b is not None:
                    rets.append(a / b - 1.0)
            if rets:
                out[d] = float(np.mean(rets))
    first_earn = windows[0][0] if windows else None
    return out, first_earn


def close_returns(closes, spy_days, col):
    out = {}
    for i in range(1, len(spy_days)):
        d, p = spy_days[i], spy_days[i - 1]
        a = closes.get(d, {}).get(col)
        b = closes.get(p, {}).get(col)
        if a is not None and b is not None:
            out[d] = a / b - 1.0
    return out


# ------------------------------------------------------------------ months
def ym(d: dt.date) -> tuple[int, int]:
    return (d.year, d.month)


def next_ym(m):
    y, mo = m
    return (y + 1, 1) if mo == 12 else (y, mo + 1)


def last_full_factor_month(fac_days, spy_days):
    """Last calendar month M for which the factors exist for the whole month.

    M qualifies when the last complete factor date is on or after M's last
    SPY trading day and M's calendar is known complete (SPY data, or the
    factor data, run past M, or M's last SPY day is its last weekday);
    coverage of every day is then tested per month.
    """
    if not fac_days:
        return None
    fmax = max(fac_days)
    spy_by_m = defaultdict(list)
    for d in spy_days:
        spy_by_m[ym(d)].append(d)
    best = None
    for m, ds in spy_by_m.items():
        last_wd = dt.date(*next_ym(m), 1) - dt.timedelta(days=1)
        while last_wd.weekday() >= 5:
            last_wd -= dt.timedelta(days=1)
        known_complete = spy_days[-1] > ds[-1] or ym(fmax) > m or ds[-1] >= last_wd
        if fmax >= ds[-1] and known_complete:
            if best is None or m > best:
                best = m
    return best


# ---------------------------------------------------------- regressions
def ols_nw(y, X, L=NW_LAGS):
    """OLS with plain HAC Newey-West (Bartlett 1 - l/(L+1)), no small-sample correction."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    if n <= k:
        return None
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ (X.T @ y)
    e = y - X @ b
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for l in range(1, L + 1):
        if l >= n:
            break
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.diag(V))
    return b, se


def alpha_stats(y, cols):
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in cols])
    r = ols_nw(y, X)
    if r is None:
        return None
    b, se = r
    return {"alpha_monthly": float(b[0]), "alpha_annual": float(12 * b[0]),
            "se": float(se[0]), "t": float(b[0] / se[0]) if se[0] > 0 else None,
            "betas": [float(x) for x in b[1:]]}


def max_dd(r):
    w = np.cumprod(1.0 + np.asarray(r, float))
    w = np.concatenate([[1.0], w])
    peak = np.maximum.accumulate(w)
    return float(np.min(w / peak - 1.0))


def compound(vals):
    return float(np.prod(1.0 + np.asarray(vals, float)) - 1.0)


# -------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    D = a.data

    _, prices = read_wide(os.path.join(D, "prices.csv"))
    spy_days = sorted(d for d, r in prices.items() if r.get("SPY") is not None)
    baskets = read_baskets(os.path.join(D, "baskets.csv"))
    if not baskets:
        raise SystemExit("no long baskets")
    bret, first_earn = basket_daily(baskets, prices, spy_days)
    if first_earn is None:
        raise SystemExit("basket never earns")

    _, bench = read_wide(os.path.join(D, "bench.csv"))
    bench_ret = {c: close_returns(bench, spy_days, c) for c in BENCH}

    _, ff5 = read_wide(os.path.join(D, "ff5_daily.csv"))
    _, mom = read_wide(os.path.join(D, "mom_daily.csv"))
    fac: dict[dt.date, dict[str, float]] = {}
    for d, r in ff5.items():
        m = mom.get(d)
        if m is None:
            continue
        vals = {c: r.get(c) for c in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]}
        vals["Mom"] = m.get("Mom")
        if all(v is not None for v in vals.values()):
            fac[d] = {c: v / 100.0 for c, v in vals.items()}

    first_m = next_ym(ym(first_earn))
    last_m = last_full_factor_month(list(fac), spy_days)
    if last_m is None:
        raise SystemExit("no full factor month")

    spy_by_m = defaultdict(list)
    for d in spy_days:
        spy_by_m[ym(d)].append(d)

    rows = []  # per used month
    m = first_m
    while m <= last_m:
        ds = spy_by_m.get(m, [])
        ok = bool(ds) and all(
            d in bret and d in fac and all(d in bench_ret[c] for c in BENCH) for d in ds)
        if ok:
            rows.append({
                "month": m,
                "basket": compound([bret[d] for d in ds]),
                "rf": compound([fac[d]["RF"] for d in ds]),
                **{f: compound([fac[d][f] for d in ds]) for f in FACTORS},
                **{"b_" + c: compound([bench_ret[c][d] for d in ds]) for c in BENCH},
            })
        m = next_ym(m)

    n = len(rows)
    res: dict = {"n_months": n,
                 "first_month": "%04d-%02d" % rows[0]["month"] if n else None,
                 "last_month": "%04d-%02d" % rows[-1]["month"] if n else None}

    def col(k, rs=None):
        return np.array([r[k] for r in (rows if rs is None else rs)], float)

    x = col("basket") - col("rf")
    prim = alpha_stats(x, [col(f) for f in FACTORS]) if n else None
    if prim is None:
        res.update({"alpha_monthly": None, "alpha_annual": None, "se": None, "t": None,
                    "loadings": None})
    else:
        res.update({k: prim[k] for k in ["alpha_monthly", "alpha_annual", "se", "t"]})
        res["loadings"] = dict(zip(FACTORS, prim["betas"]))
    if n < MIN_MONTHS:
        verdict = "INSUFFICIENT"
    elif prim["t"] is not None and prim["t"] >= T_MIN and prim["alpha_annual"] >= ALPHA_MIN:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    res["verdict"] = verdict

    capm = alpha_stats(x, [col("Mkt-RF")]) if n else None
    res["capm_alpha_annual"] = capm and capm["alpha_annual"]
    res["capm_t"] = capm and capm["t"]
    qqq = alpha_stats(x, [col("b_QQQ") - col("rf")]) if n else None
    res["qqq_alpha_annual"] = qqq and qqq["alpha_annual"]
    res["qqq_t"] = qqq and qqq["t"]

    ex = {}
    for c in BENCH:
        dlt = col("basket") - col("b_" + c) if n else np.array([])
        s = alpha_stats(dlt, []) if n else None
        ex[c] = {"annual": s and s["alpha_annual"], "t": s and s["t"]}
    res["excess_vs"] = ex
    res["share_months_beat_spy"] = float(np.mean(col("basket") > col("b_SPY"))) if n else None

    series = {"basket": "basket", "SPY": "b_SPY", "QQQ": "b_QQQ", "RSP": "b_RSP"}
    res["ann_mean"] = {k: float(12 * col(v).mean()) if n else None for k, v in series.items()}
    res["ann_vol"] = {k: float(math.sqrt(12) * col(v).std(ddof=1)) if n > 1 else None
                      for k, v in series.items()}
    res["max_drawdown"] = {k: max_dd(col(v)) if n else None for k, v in series.items()}

    h = n // 2
    halves = []
    for part in (rows[:h], rows[h:]):
        if not part:
            halves.append({"first_month": None, "last_month": None,
                           "alpha_annual": None, "t": None})
            continue
        xp = col("basket", part) - col("rf", part)
        s = alpha_stats(xp, [col(f, part) for f in FACTORS])
        halves.append({"first_month": "%04d-%02d" % part[0]["month"],
                       "last_month": "%04d-%02d" % part[-1]["month"],
                       "alpha_annual": s and s["alpha_annual"], "t": s and s["t"]})
    res["halves"] = halves

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps({k: res[k] for k in
                      ["n_months", "first_month", "last_month", "alpha_annual", "t", "verdict"]}))


if __name__ == "__main__":
    main()
