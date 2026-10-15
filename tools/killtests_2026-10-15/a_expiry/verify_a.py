#!/usr/bin/env python3
"""verify_a.py: independent second implementation of kill test A (PREREG.md).

Written from tools/killtests_2026-10-15/a_expiry/PREREG.md alone, without sight of run_a.py or
kt.py, so that every criterion figure can be compared on the runner. Standard library and numpy
only.

Usage: python verify_a.py --data data --out out

Implements sections 3, 4, 5 and 7 for the primary asset (ng) and the replication assets (ho, rb).
Section 8 is not implemented; contract 2 is therefore not read.

Reading rules taken where the text admits more than one reading are stated where they bind, in
the docstring or comment of the function that applies them, because a rule whose reason is not
written down gets relaxed by whoever meets it next.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

L_NW = 5
ALPHA2 = 0.025
MDE_MULT = 2.80
SIZE_THRESHOLD = 0.157
OOS_START = 400
OOS_GAP = 5
ROT_MIN = 21
UNSCORABLE_SHIFTS = 100

ASSETS = {
    # asset: (spot file, contract 1 file, expiry rule, role)
    "ng": ("ng_spot.csv", "ng_c1.csv", "ng", "primary"),
    "ho": ("ho_spot.csv", "ho_c1.csv", "last_bd", "replication, no weight"),
    "rb": ("rb_spot.csv", "rb_c1.csv", "last_bd", "replication, no weight"),
}


# ----------------------------------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------------------------------

def read_series(path: str, field: str) -> tuple[list[dt.date], list[float | None]]:
    """Read DATE,<field>. Empty or "." is missing; anything else non-numeric is an error.

    The file must be in strictly ascending date order (PREREG section 2 says oldest first); a
    file that is not is refused rather than sorted, because a silently re-sorted input is not the
    input the prereg describes.
    """
    dates: list[dt.date] = []
    vals: list[float | None] = []
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        header = [h.strip().upper() for h in next(rd)]
        if "DATE" not in header or field not in header:
            raise SystemExit(f"{path}: header {header} lacks DATE and {field}")
        di, vi = header.index("DATE"), header.index(field)
        for row in rd:
            if not row or all(not c.strip() for c in row):
                continue
            d = dt.date.fromisoformat(row[di].strip())
            raw = row[vi].strip() if vi < len(row) else ""
            if raw in ("", "."):
                v = None
            else:
                v = float(raw)
                if not math.isfinite(v):
                    raise SystemExit(f"{path}: non-finite value {raw!r} on {d}")
            if dates and d <= dates[-1]:
                raise SystemExit(f"{path}: dates not strictly ascending at {d}")
            dates.append(d)
            vals.append(v)
    return dates, vals


# ----------------------------------------------------------------------------------------------
# Calendar (section 3)
# ----------------------------------------------------------------------------------------------

def easter(y: int) -> dt.date:
    """Gregorian computus (anonymous Gregorian algorithm)."""
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)


def nth_weekday(y: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(y, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def last_weekday(y: int, month: int, weekday: int) -> dt.date:
    nxt = dt.date(y + (month == 12), month % 12 + 1, 1)
    d = nxt - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def observed(d: dt.date) -> dt.date:
    """Saturday observed on the preceding Friday, Sunday on the following Monday.

    Exception (PREREG section 3, amended before freezing): New Year's Day falling on a
    Saturday is not observed, because the exchanges trade on that 31 December; the holiday
    then simply falls on a non-business day.
    """
    if d.weekday() == 5:
        if d.month == 1 and d.day == 1:
            return d
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:
        return d + dt.timedelta(days=1)
    return d


def holidays_of_year(y: int) -> set[dt.date]:
    MON, THU = 0, 3
    h = {
        observed(dt.date(y, 1, 1)),
        nth_weekday(y, 2, MON, 3),
        easter(y) - dt.timedelta(days=2),
        last_weekday(y, 5, MON),
        observed(dt.date(y, 7, 4)),
        nth_weekday(y, 9, MON, 1),
        nth_weekday(y, 11, THU, 4),
        observed(dt.date(y, 12, 25)),
    }
    if y >= 1998:
        h.add(nth_weekday(y, 1, MON, 3))
    if y >= 2022:
        h.add(observed(dt.date(y, 6, 19)))
    return h


class BusinessCalendar:
    def __init__(self, y0: int, y1: int):
        self.hol: set[dt.date] = set()
        for y in range(y0 - 1, y1 + 2):
            self.hol |= holidays_of_year(y)

    def is_bd(self, d: dt.date) -> bool:
        return d.weekday() < 5 and d not in self.hol


def month_iter(y0: int, m0: int, y1: int, m1: int):
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def expiry_for_delivery(cal: BusinessCalendar, y: int, m: int, rule: str) -> dt.date:
    """Expiry X of the contract delivering in month (y, m).

    ng: the third business day counting back from the last day of the preceding month, that
    last day counting as the first if it is itself a business day. last_bd: the last business
    day of the preceding month.
    """
    need = 3 if rule == "ng" else 1
    d = dt.date(y, m, 1) - dt.timedelta(days=1)
    count = 0
    while True:
        if cal.is_bd(d):
            count += 1
            if count == need:
                return d
        d -= dt.timedelta(days=1)


# ----------------------------------------------------------------------------------------------
# Estimators (section 4)
# ----------------------------------------------------------------------------------------------

def ols_nw(X: np.ndarray, y: np.ndarray, L: int = L_NW):
    """OLS coefficients with Newey-West (Bartlett, no df correction) standard errors.

    Returns (beta, se) or None where the design cannot be estimated; None is a refusal, not a
    zero, and every consumer records it as null.
    """
    m, k = X.shape
    if m <= k:
        return None
    XtX = X.T @ X
    if np.linalg.matrix_rank(XtX) < k:
        return None
    Xi = np.linalg.inv(XtX)
    b = Xi @ (X.T @ y)
    u = y - X @ b
    Z = X * u[:, None]
    S = Z.T @ Z
    for l in range(1, L + 1):
        if l >= m:
            break
        w = 1.0 - l / (L + 1.0)
        G = Z[l:].T @ Z[:-l]
        S += w * (G + G.T)
    V = Xi @ S @ Xi
    se = np.sqrt(np.maximum(np.diag(V), 0.0))
    return b, se


def slope_nw(x: np.ndarray, y: np.ndarray):
    """Slope of y on x with intercept: (n, b, se, t) with nulls on refusal."""
    n = len(x)
    if n < 3:
        return n, None, None, None
    r = ols_nw(np.column_stack([np.ones(n), x]), y)
    if r is None:
        return n, None, None, None
    b, se = r
    t = float(b[1] / se[1]) if se[1] > 0 else None
    return n, float(b[1]), float(se[1]), t


def rotation(x: np.ndarray, y: np.ndarray):
    """Rotation p-values: circular shifts k = 21, ..., m-21 of x against y, K = m - 41.

    The observed slope is recomputed by the same centred cross-product formula as the rotated
    ones, so that a tie is a tie in one arithmetic and not an artefact of two. The shift set is
    symmetric under k -> m-k, so the direction of the shift does not matter.
    """
    m = len(x)
    K = m - 2 * ROT_MIN + 1
    if K <= 0:
        return {"K": max(K, 0), "p_plus": None, "p_minus": None, "p2": None}
    xc = x - x.mean()
    yc = y - y.mean()
    v = float(xc @ xc)
    if v <= 0:
        return {"K": K, "p_plus": None, "p_minus": None, "p2": None}
    obs = float(xc @ yc) / v
    rot = np.array([float(np.roll(xc, k) @ yc) / v for k in range(ROT_MIN, m - ROT_MIN + 1)])
    assert len(rot) == K
    pp = (1 + int(np.sum(rot >= obs))) / (1 + K)
    pm = (1 + int(np.sum(rot <= obs))) / (1 + K)
    return {"K": K, "p_plus": pp, "p_minus": pm, "p2": min(1.0, 2 * min(pp, pm))}


def sgn(v) -> int | None:
    if v is None:
        return None
    return 1 if v > 0 else (-1 if v < 0 else 0)


# ----------------------------------------------------------------------------------------------
# Per asset
# ----------------------------------------------------------------------------------------------

def build_days(spot, c1, tb, rule):
    """Joint calendar, expiries, windows and the per-signal-day quantities of section 3."""
    sd, sv = spot
    cd, cv = c1
    s_map = {d: v for d, v in zip(sd, sv) if v is not None}
    c_map = {d: v for d, v in zip(cd, cv) if v is not None}
    dates = sorted(set(s_map) & set(c_map))
    N = len(dates)
    if N == 0:
        raise ValueError("empty_joint_calendar")
    S = np.array([s_map[d] for d in dates])
    F = np.array([c_map[d] for d in dates])

    tbd = [d for d, v in zip(*tb) if v is not None]
    tbv = [v for v in tb[1] if v is not None]

    def rate(d):
        i = bisect.bisect_right(tbd, d) - 1
        return None if i < 0 else tbv[i] / 100.0

    cal = BusinessCalendar(dates[0].year, dates[-1].year + 1)
    ly, lm = dates[-1].year, dates[-1].month
    ly2, lm2 = (ly + 1, 1) if lm == 12 else (ly, lm + 1)
    all_expiries = [expiry_for_delivery(cal, y, m, rule)
                    for y, m in month_iter(dates[0].year, dates[0].month, ly2, lm2)]
    # PREREG section 3 (amended): only expiries on or before the last joint date are used; a
    # contract whose expiry lies beyond the data has no return to expiry, so no window.
    expiries = [X for X in all_expiries if X <= dates[-1]]
    beyond_data = len(all_expiries) - len(expiries)
    ks = []
    for X in expiries:
        i = bisect.bisect_right(dates, X) - 1
        ks.append(None if i < 0 else i)

    owner: dict[int, tuple[int, int]] = {}   # position -> (expiry index, e)
    collisions = 0
    for j, (X, k) in enumerate(zip(expiries, ks)):
        if k is None:
            continue
        for t in range(max(0, k - 4), k + 1):
            if t in owner:
                collisions += 1
                continue
            owner[t] = (j, k - t)

    days = []
    for t in sorted(owner):
        j, e = owner[t]
        if e == 0:
            continue
        X, k = expiries[j], ks[j]
        k_prev = ks[j - 1] if j > 0 else None
        lo = 0 if k_prev is None else k_prev + 1
        r = rate(dates[t])
        M = None
        if r is not None and S[t] > 0 and F[t] > 0:
            tau = (X - dates[t]).days / 365.0
            fstar = S[t] * math.exp(r * tau)
            M = 100.0 * (F[t] / fstar - 1.0)
        Y = 100.0 * math.log(F[k] / F[t]) if (F[k] > 0 and F[t] > 0) else None
        m1 = m5 = None
        if t - 1 >= lo and F[t] > 0 and F[t - 1] > 0:
            m1 = 100.0 * math.log(F[t] / F[t - 1])
        if t - 5 >= lo and F[t] > 0 and F[t - 5] > 0:
            m5 = 100.0 * math.log(F[t] / F[t - 5])
        days.append({"t": t, "date": dates[t], "e": e, "X": X, "M": M, "Y": Y,
                     "m1": m1, "m5": m5})
    diag = {"n_joint": N, "first": dates[0].isoformat(), "last": dates[-1].isoformat(),
            "n_expiries": len(expiries),
            "n_expiries_with_window": sum(k is not None for k in ks),
            "n_expiries_after_last_date_excluded": beyond_data,
            "window_position_collisions": collisions,
            "n_signal_days": len(days)}
    return days, diag


def aligned(days, keys, cond=None):
    rows = [d for d in days if all(d[k] is not None for k in keys) and (cond is None or cond(d))]
    return {k: np.array([d[k] for d in rows], dtype=float) for k in keys}, rows


def analyse(days):
    out: dict = {}

    # Primary, pooled
    A, _ = aligned(days, ["M", "Y"])
    x, y = A["M"], A["Y"]
    n, b, se, t = slope_nw(x, y)
    rot = rotation(x, y)
    out["pooled"] = {"n": n, "b": b, "nw_t": t, "p_plus": rot["p_plus"],
                     "p_minus": rot["p_minus"], "p2": rot["p2"],
                     "mde": MDE_MULT * se if se is not None else None,
                     "K": rot["K"]}
    s = sgn(b) if b is not None else None
    out["s"] = s

    # By days remaining
    out["by_e"] = {}
    for e in (1, 2, 3, 4):
        Ae, _ = aligned(days, ["M", "Y"], lambda d, e=e: d["e"] == e)
        ne, be, _, te = slope_nw(Ae["M"], Ae["Y"])
        out["by_e"][str(e)] = {"n": ne, "b": be, "nw_t": te,
                               "p2": rotation(Ae["M"], Ae["Y"])["p2"]}
    for name, es in (("e12", (1, 2)), ("e34", (3, 4))):
        Ae, _ = aligned(days, ["M", "Y"], lambda d, es=es: d["e"] in es)
        ne, be, _, _ = slope_nw(Ae["M"], Ae["Y"])
        out[name] = {"n": ne, "b": be}

    # Halves of the pooled aligned sample
    h = len(x) // 2
    n1_, b1_, _, _ = slope_nw(x[:h], y[:h])
    n2_, b2_, _, _ = slope_nw(x[h:], y[h:])
    out["halves"] = {"n_first": n1_, "b_first": b1_, "n_rest": n2_, "b_rest": b2_}

    # Incremental and out of sample, on the aligned sample of {M, m1, m5, Y}
    B, _ = aligned(days, ["M", "m1", "m5", "Y"])
    mB = len(B["Y"])
    g = gt = None
    if mB > 4:
        Xa = np.column_stack([np.ones(mB), B["M"], B["m1"], B["m5"]])
        r = ols_nw(Xa, B["Y"])
        if r is not None:
            g = float(r[0][1])
            gt = float(r[0][1] / r[1][1]) if r[1][1] > 0 else None
    out["incremental"] = {"n": mB, "g": g, "nw_t": gt}

    Xb_all = np.column_stack([np.ones(mB), B["m1"], B["m5"]]) if mB else np.zeros((0, 3))
    Xa_all = np.column_stack([np.ones(mB), B["m1"], B["m5"], B["M"]]) if mB else np.zeros((0, 4))
    yb = B["Y"]
    eb, ea, fb_minus_fa = [], [], []
    # Positions are counted within the aligned sample of {M, m1, m5, Y} (PREREG section 5).
    for tt in range(OOS_START, mB):
        hi = tt - OOS_GAP + 1          # rows 0..tt-5 inclusive
        bb, *_ = np.linalg.lstsq(Xb_all[:hi], yb[:hi], rcond=None)
        ba, *_ = np.linalg.lstsq(Xa_all[:hi], yb[:hi], rcond=None)
        fb = float(Xb_all[tt] @ bb)
        fa = float(Xa_all[tt] @ ba)
        eb.append(yb[tt] - fb)
        ea.append(yb[tt] - fa)
        fb_minus_fa.append(fb - fa)
    nf = len(eb)
    r2 = cwm = cwt = None
    if nf > 0:
        eb_, ea_, d_ = np.array(eb), np.array(ea), np.array(fb_minus_fa)
        sse_b, sse_a = float(eb_ @ eb_), float(ea_ @ ea_)
        r2 = 1.0 - sse_a / sse_b if sse_b > 0 else None
        f = eb_ ** 2 - (ea_ ** 2 - d_ ** 2)
        cwm = float(f.mean())
        r = ols_nw(np.ones((nf, 1)), f)
        if r is not None and r[1][0] > 0:
            cwt = float(r[0][0] / r[1][0])
    out["oos"] = {"n_forecasts": nf, "r2_os": r2, "cw_mean": cwm, "cw_nw_t": cwt}

    # Size, on the pooled aligned sample
    if s is None or len(x) == 0:
        out["size"] = {"Q": None, "n_top": None, "Dq": None}
    else:
        sM = s * x
        Q = float(np.percentile(sM, 80))
        top = sM >= Q
        Dq = 0.0 if s == 0 else float(y[top].mean() - y.mean())
        out["size"] = {"Q": Q, "n_top": int(top.sum()), "Dq": Dq}

    # Verdict (section 7)
    p2 = out["pooled"]["p2"]
    c = {
        "a": bool(b is not None and b != 0 and p2 is not None and p2 <= ALPHA2),
        "b": bool(s is not None and sgn(out["e12"]["b"]) == s and sgn(out["e34"]["b"]) == s),
        "c": bool(s is not None and sgn(b1_) == s and sgn(b2_) == s),
        "d": bool(s is not None and sgn(g) == s and gt is not None and abs(gt) >= 2.0),
        "e": bool(r2 is not None and r2 > 0),
        "f": bool(out["size"]["Dq"] is not None and out["size"]["Dq"] >= SIZE_THRESHOLD),
    }
    out["criteria"] = c
    if rot["K"] < UNSCORABLE_SHIFTS:
        v = "UNSCORABLE"
    elif not c["a"]:
        v = "FAIL"
    elif all(c.values()):
        v = "PASS"
    else:
        v = "WEAK"
    out["verdict"] = v
    return out


def fmt(v, p=4):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "T" if v else "F"
    if isinstance(v, int):
        return str(v)
    return f"{v:.{p}g}"


def log_asset(a, role, res):
    P = res["pooled"]
    print(f"[{a}] diag " + " ".join(f"{k}={v}" for k, v in res["diag"].items()))
    print(f"[{a}] pooled n={P['n']} b={fmt(P['b'])} t={fmt(P['nw_t'])} p+={fmt(P['p_plus'])} "
          f"p-={fmt(P['p_minus'])} p2={fmt(P['p2'])} mde={fmt(P['mde'])} K={P['K']} s={res['s']}")
    print(f"[{a}] by_e " + " | ".join(
        f"e{e}: n={r['n']} b={fmt(r['b'])} t={fmt(r['nw_t'])} p2={fmt(r['p2'])}"
        for e, r in res["by_e"].items())
        + f" | e12 n={res['e12']['n']} b={fmt(res['e12']['b'])}"
        f" | e34 n={res['e34']['n']} b={fmt(res['e34']['b'])}")
    H = res["halves"]
    print(f"[{a}] halves n1={H['n_first']} b1={fmt(H['b_first'])} n2={H['n_rest']} "
          f"b2={fmt(H['b_rest'])}")
    I, O, Z = res["incremental"], res["oos"], res["size"]
    print(f"[{a}] incremental n={I['n']} g={fmt(I['g'])} t={fmt(I['nw_t'])}")
    print(f"[{a}] oos n={O['n_forecasts']} r2_os={fmt(O['r2_os'])} cw={fmt(O['cw_mean'])} "
          f"cw_t={fmt(O['cw_nw_t'])}")
    print(f"[{a}] size Q={fmt(Z['Q'])} n_top={Z['n_top']} Dq={fmt(Z['Dq'])}")
    print(f"[{a}] criteria " + " ".join(f"{k}={fmt(v)}" for k, v in res["criteria"].items())
          + f" verdict={res['verdict']} ({role})")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    tb = read_series(os.path.join(args.data, "tbill.csv"), "RATE")
    result = {}
    for a, (sf, cf, rule, role) in ASSETS.items():
        sp, cp = os.path.join(args.data, sf), os.path.join(args.data, cf)
        missing = [p for p in (sp, cp) if not os.path.exists(p)]
        if missing:
            if a == "ng":
                raise SystemExit(f"primary input missing: {missing}")
            result[a] = {"role": role, "refused": "input_file_missing",
                         "missing": [os.path.basename(p) for p in missing]}
            print(f"[{a}] refused input_file_missing {missing}")
            continue
        days, diag = build_days(read_series(sp, "VALUE"), read_series(cp, "CLOSE"), tb, rule)
        res = analyse(days)
        res["role"] = role
        res["diag"] = diag
        log_asset(a, role, res)
        result[a] = res

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "verify_a.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(f"wrote {path}")


if __name__ == "__main__":
    sys.exit(main())
