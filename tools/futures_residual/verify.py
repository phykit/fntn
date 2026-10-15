"""Independent second implementation of PREREG.md sections 3, 4, 5 and 7.

Written from PREREG.md alone, without sight of run.py, selftest.py or fetch.py,
so that agreement between the two on the runner is evidence about the
specification rather than about shared code. Standard library and numpy only.

Usage:  python verify.py --data data --out out

Where an input needed by a quantity is missing, non-numeric or non-finite, the
quantity is undefined and the day leaves that test's aligned sample; nothing is
substituted. A statistic that cannot be computed (too few days, a signal with
zero variance) is reported as null, never as zero.
"""

import argparse
import bisect
import calendar
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

HORIZONS = (1, 5, 20)
ALPHA_EACH = 0.0125
SIZE_FLOOR = 0.157
MDS_FACTOR = 2.80
OOS_START = 1000
ASSETS = (("ng", "primary"), ("ho", "replication, no weight"), ("rb", "replication, no weight"))


# ---------------------------------------------------------------- input

def read_series(path, field):
    """Return {date: float} for rows whose field is numeric; empty or '.' is missing."""
    out = {}
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "DATE" not in reader.fieldnames or field not in reader.fieldnames:
            raise ValueError(f"{path}: expected columns DATE,{field}, found {reader.fieldnames}")
        for row in reader:
            d = (row.get("DATE") or "").strip()
            v = (row.get(field) or "").strip()
            if not d or v == "" or v == ".":
                continue
            try:
                fv = float(v)
            except ValueError:
                continue
            if not math.isfinite(fv):
                continue
            out[dt.date.fromisoformat(d)] = fv
    return out


# ---------------------------------------------------------------- calendar

def weekdays_back(year, month, n):
    """The n-th weekday counting backwards from the last day of the month inclusive."""
    d = dt.date(year, month, calendar.monthrange(year, month)[1])
    count = 0
    while True:
        if d.weekday() < 5:
            count += 1
            if count == n:
                return d
        d -= dt.timedelta(days=1)


def expiries_for(asset, first, last):
    """Expiry of each contract month from first's month to the month after last's month."""
    nth = 3 if asset == "ng" else 1
    out = []
    y, m = first.year, first.month
    end_y, end_m = (last.year + 1, 1) if last.month == 12 else (last.year, last.month + 1)
    while (y, m) <= (end_y, end_m):
        py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
        out.append(weekdays_back(py, pm, nth))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return sorted(set(out))


def build_asset(asset, spot, fut, tb_dates, tb_vals):
    dates = sorted(set(spot) & set(fut))
    N = len(dates)
    S = np.array([spot[d] for d in dates], dtype=float)
    F = np.array([fut[d] for d in dates], dtype=float)

    expiries = expiries_for(asset, dates[0], dates[-1])
    kept = np.ones(N, dtype=bool)
    for X in expiries:
        k = bisect.bisect_right(dates, X) - 1
        if k < 0:
            continue
        kept[max(0, k - 4):min(N - 1, k + 1) + 1] = False

    last_date = dates[-1]
    Xt = [None] * N
    tau = np.full(N, np.nan)
    r = np.full(N, np.nan)
    for t, d in enumerate(dates):
        j = bisect.bisect_right(tb_dates, d) - 1
        if j >= 0:
            r[t] = tb_vals[j] / 100.0
        if not kept[t]:
            continue
        i = bisect.bisect_right(expiries, d)
        while i < len(expiries):
            X = expiries[i]
            kx_exists = bisect.bisect_right(dates, X) - 1 >= 0
            if kx_exists or X > last_date:
                Xt[t] = X
                tau[t] = (X - d).days / 365.0
                break
            i += 1

    with np.errstate(all="ignore"):
        Fstar = S * np.exp(r * tau)
        M = 100.0 * (F / Fstar - 1.0)
    M[~kept] = np.nan
    M[~np.isfinite(M)] = np.nan

    dM = np.full(N, np.nan)
    for t in range(1, N):
        if kept[t] and kept[t - 1] and Xt[t] is not None and Xt[t] == Xt[t - 1]:
            dM[t] = M[t] - M[t - 1]

    with np.errstate(all="ignore"):
        lnS = np.log(S)
    lnS[~np.isfinite(lnS)] = np.nan

    def back(k):
        a = np.full(N, np.nan)
        a[k:] = 100.0 * (lnS[k:] - lnS[:-k])
        return a

    def fwd(h):
        a = np.full(N, np.nan)
        a[:-h] = 100.0 * (lnS[h:] - lnS[:-h])
        return a

    return {
        "dates": dates, "N": N, "kept": kept, "M": M, "dM": dM,
        "n1": back(1), "n5": back(5), "n20": back(20),
        "R": {h: fwd(h) for h in HORIZONS},
        "n_expiries": len(expiries),
    }


# ---------------------------------------------------------------- estimators

def sgn(b):
    if b is None:
        return None
    return 1 if b > 0 else (-1 if b < 0 else 0)


def ols_nw(X, y, L):
    """OLS coefficients and Newey-West standard errors, Bartlett weights, no dof correction."""
    m = len(y)
    if m <= X.shape[1]:
        return None
    XtX = X.T @ X
    try:
        inv = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        return None
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ beta
    Xe = X * e[:, None]
    Smat = Xe.T @ Xe
    for l in range(1, L + 1):
        if l >= m:
            break
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        Smat += w * (G + G.T)
    V = inv @ Smat @ inv
    se = np.sqrt(np.diag(V))
    with np.errstate(all="ignore"):
        tstat = beta / se
    ss_res = float(e @ e)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None
    return {"beta": beta, "se": se, "t": tstat, "r2": r2}


def simple_slope(x, y):
    xc = x - x.mean()
    sxx = float(xc @ xc)
    if sxx == 0:
        return None
    return float(xc @ (y - y.mean())) / sxx


def rotation(x, y):
    m = len(x)
    K = m - 41
    if K < 1:
        return None
    xc = x - x.mean()
    yc = y - y.mean()
    sxx = float(xc @ xc)
    if sxx == 0:
        return None
    obs = float(xc @ yc) / sxx
    rot = np.empty(K)
    for idx, k in enumerate(range(21, m - 20)):
        rot[idx] = float(np.roll(xc, -k) @ yc) / sxx  # x_k[i] = x[(i + k) mod m]
    p_plus = (1 + int((rot >= obs).sum())) / (1 + K)
    p_minus = (1 + int((rot <= obs).sum())) / (1 + K)
    return {"K": K, "p_plus": p_plus, "p_minus": p_minus, "p2": min(1.0, 2.0 * min(p_plus, p_minus))}


def fnum(v):
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------- section 5

def bivariate(x, y, L):
    m = len(x)
    out = {"n": m, "b": None, "b_per_sd": None, "corr": None, "nw_se": None, "nw_t": None,
           "p_plus": None, "p_minus": None, "p2": None, "K": None, "mds": None}
    if m < 3 or float(np.std(x)) == 0:
        return out
    X = np.column_stack([np.ones(m), x])
    fit = ols_nw(X, y, L)
    if fit is None:
        return out
    b = float(fit["beta"][1])
    sd = float(np.std(x))
    out.update(b=b, b_per_sd=b * sd, nw_se=fnum(fit["se"][1]), nw_t=fnum(fit["t"][1]))
    if float(np.std(y)) > 0:
        out["corr"] = float(np.corrcoef(x, y)[0, 1])
    if out["nw_se"] is not None:
        out["mds"] = MDS_FACTOR * out["nw_se"]
    rot = rotation(x, y)
    if rot is not None:
        out.update(rot)
    return out


def hypothesis(A, sig):
    x_all = A[sig]
    res = {"signal": sig, "horizons": {}}

    samples = {}
    for h in HORIZONS:
        y_all = A["R"][h]
        ok = np.isfinite(x_all) & np.isfinite(y_all)
        x, y = x_all[ok], y_all[ok]
        samples[h] = (x, y)
        res["horizons"][str(h)] = bivariate(x, y, h + 5)

    b = {h: res["horizons"][str(h)]["b"] for h in HORIZONS}
    s = sgn(b[5])
    res["s"] = s

    # halves of the h = 5 aligned sample
    x5, y5 = samples[5]
    m5 = len(x5)
    half = m5 // 2
    b_first = simple_slope(x5[:half], y5[:half]) if half >= 2 else None
    b_rest = simple_slope(x5[half:], y5[half:]) if m5 - half >= 2 else None
    res["halves"] = {"n_first": half, "n_rest": m5 - half, "b_first": b_first, "b_rest": b_rest}

    # incremental regression and out of sample, same aligned sample
    R5 = A["R"][5]
    cols = [x_all, A["n1"], A["n5"], A["n20"], R5]
    ok = np.all(np.column_stack([np.isfinite(c) for c in cols]), axis=1)
    x, n1, n5, n20, y = (c[ok] for c in cols)
    m = len(y)
    inc = {"n": m, "g": None, "nw_se": None, "nw_t": None, "r2_baseline": None, "r2_augmented": None}
    Xa = np.column_stack([np.ones(m), x, n1, n5, n20])
    Xb = np.column_stack([np.ones(m), n1, n5, n20])
    if m > 5:
        fa = ols_nw(Xa, y, 10)
        fb = ols_nw(Xb, y, 10)
        if fa is not None:
            inc.update(g=fnum(fa["beta"][1]), nw_se=fnum(fa["se"][1]), nw_t=fnum(fa["t"][1]),
                       r2_augmented=fnum(fa["r2"]))
        if fb is not None:
            inc["r2_baseline"] = fnum(fb["r2"])
    res["incremental"] = inc

    oos = {"n_forecasts": 0, "r2_os": None, "cw_mean": None, "cw_nw_t": None}
    if m > OOS_START:
        fbv, fav, yv = [], [], []
        for t in range(OOS_START, m):
            rows = slice(0, t - 5 + 1)
            bb = np.linalg.lstsq(Xb[rows], y[rows], rcond=None)[0]
            ba = np.linalg.lstsq(Xa[rows], y[rows], rcond=None)[0]
            fbv.append(float(Xb[t] @ bb))
            fav.append(float(Xa[t] @ ba))
            yv.append(float(y[t]))
        fbv, fav, yv = np.array(fbv), np.array(fav), np.array(yv)
        sse_b = float(((yv - fbv) ** 2).sum())
        sse_a = float(((yv - fav) ** 2).sum())
        f = (yv - fbv) ** 2 - ((yv - fav) ** 2 - (fbv - fav) ** 2)
        cw = ols_nw(np.ones((len(f), 1)), f, 10)
        oos.update(n_forecasts=len(yv), r2_os=(1.0 - sse_a / sse_b) if sse_b > 0 else None,
                   cw_mean=float(f.mean()), cw_nw_t=fnum(cw["t"][0]) if cw else None)
    res["oos"] = oos

    # size, on the h = 5 aligned sample
    size = {"Q": None, "n_top": None, "Dq": None}
    if m5 > 0 and s is not None:
        z = s * x5
        Q = float(np.percentile(z, 80))
        top = z >= Q
        Dq = float(y5[top].mean() - y5.mean()) if s != 0 else 0.0
        size.update(Q=Q, n_top=int(top.sum()), Dq=Dq)
    res["size"] = size

    # section 7
    p2 = res["horizons"]["5"]["p2"]
    crit = {
        "a": bool(b[5] is not None and b[5] != 0 and p2 is not None and p2 <= ALPHA_EACH),
        "b": bool(s is not None and sgn(b[1]) == s and sgn(b[20]) == s),
        "c": bool(s is not None and sgn(b_first) == s and sgn(b_rest) == s),
        "d": bool(s is not None and inc["g"] is not None and sgn(inc["g"]) == s
                  and inc["nw_t"] is not None and abs(inc["nw_t"]) >= 2.0),
        "e": bool(oos["r2_os"] is not None and oos["r2_os"] > 0),
        # Dq is already taken in the direction s (section 5); not multiplied by s again.
        "f": bool(size["Dq"] is not None and size["Dq"] >= SIZE_FLOOR),
    }
    res["criteria"] = crit
    if not crit["a"]:
        verdict = "FAIL"
    elif all(crit.values()):
        verdict = "PASS"
    else:
        verdict = "WEAK"
    res["verdict"] = verdict
    return res


# ---------------------------------------------------------------- main

def fmt(v, p=4):
    if v is None:
        return "na"
    if isinstance(v, (int, np.integer)) and not isinstance(v, bool):
        return str(v)
    return f"{v:.{p}g}"


def log_asset(name, label, out):
    print(f"== {name} ({label}) N={out['N']} kept={out['n_kept']} expiries={out['n_expiries']}")
    for hyp in ("HL", "HC"):
        H = out[hyp]
        for h in HORIZONS:
            r = H["horizons"][str(h)]
            print(f"  {hyp} h={h:<2} n={r['n']} b={fmt(r['b'])} b/sd={fmt(r['b_per_sd'])} "
                  f"nwt={fmt(r['nw_t'])} p+={fmt(r['p_plus'])} p-={fmt(r['p_minus'])} "
                  f"p2={fmt(r['p2'])} mds={fmt(r['mds'])}")
        hv, inc, oos, sz = H["halves"], H["incremental"], H["oos"], H["size"]
        print(f"  {hyp} halves b1={fmt(hv['b_first'])} b2={fmt(hv['b_rest'])} | "
              f"inc n={inc['n']} g={fmt(inc['g'])} t={fmt(inc['nw_t'])} | "
              f"oos n={oos['n_forecasts']} r2os={fmt(oos['r2_os'])} cw={fmt(oos['cw_mean'])} "
              f"cwt={fmt(oos['cw_nw_t'])} | size Q={fmt(sz['Q'])} ntop={fmt(sz['n_top'])} "
              f"Dq={fmt(sz['Dq'])}")
        c = H["criteria"]
        flags = " ".join(f"{k}={'Y' if c[k] else 'N'}" for k in "abcdef")
        print(f"  {hyp} criteria {flags} -> {H['verdict']} s={H['s']}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    tb = read_series(os.path.join(args.data, "tbill.csv"), "RATE")
    tb_dates = sorted(tb)
    tb_vals = [tb[d] for d in tb_dates]

    result = {"assets": {}}
    for name, label in ASSETS:
        try:
            spot = read_series(os.path.join(args.data, f"{name}_spot.csv"), "VALUE")
            fut = read_series(os.path.join(args.data, f"{name}_fut.csv"), "CLOSE")
        except (OSError, ValueError) as exc:
            result["assets"][name] = {"label": label, "error": f"input_unreadable: {exc}"}
            print(f"== {name}: input_unreadable: {exc}")
            continue
        if not (set(spot) & set(fut)):
            result["assets"][name] = {"label": label, "error": "joint_calendar_empty"}
            print(f"== {name}: joint_calendar_empty")
            continue
        A = build_asset(name, spot, fut, tb_dates, tb_vals)
        out = {"label": label, "N": A["N"], "n_kept": int(A["kept"].sum()),
               "n_expiries": A["n_expiries"],
               "first_date": A["dates"][0].isoformat(), "last_date": A["dates"][-1].isoformat(),
               "HL": hypothesis(A, "M"), "HC": hypothesis(A, "dM")}
        result["assets"][name] = out
        log_asset(name, label, out)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify.json"), "w") as fh:
        json.dump(result, fh, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
