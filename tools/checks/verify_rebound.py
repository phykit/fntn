"""Independent second implementation of study R (tools/crowd_degross/PREREG_rebound.md).

Written from the pre-registration alone, without reading the first implementation, so that the
headline figures can be compared item by item by compare_rebound.py. Every ambiguity the
pre-registration leaves open is resolved in CHOICES below and written into the output, because a
disagreement between two implementations is only diagnosable if each says what it assumed.

Usage:
    python verify_rebound.py --bench DIR --data-b DIR --episodes CSV --out DIR

Non-evidentiary side test outside the FNTN funnel; authorises nothing.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import math
import os
import sys

import numpy as np

SEED = 20261029
N_PERM = 10_000
PCT_WIN = 104
PCT = 10.0
EXCL_DAYS = 14
H_PRIMARY = 20
DECLUSTER = 4
MIN_SIGNALS = 20
ALPHA = 0.05
COST_RT = 0.004
BORROW = 0.005

CHOICES = [
    "Weeks are ISO (isoyear, isoweek) groups of bench rows; week t-k means the k-th preceding "
    "week present in the bench, not a calendar offset.",
    "Weekly return is the product of (1 + daily return) over the week's bench days, a daily "
    "return being close/previous bench row's close - 1; the week is undefined if any GVIP or QQQ "
    "daily return in it is undefined, including the first day's link to the prior week.",
    "Basket weekly return compounds W over the week's bench days; undefined if any W in the week "
    "is NaN (or QQQ's week is undefined).",
    "W is mapped onto bench days by date: W[k] on B's day k is taken as the return on that date; "
    "bench days absent from B's days get NaN. A B day missing from the bench is dropped.",
    "Signal: x_t <= numpy.percentile(x[t-104..t-1], 10) (linear), requiring all 104 window "
    "weeks defined and x_t defined.",
    "Week end for the episode rule is the date of week t's last bench row; excluded when "
    "|week_end - episode week_end| <= 14 calendar days for any episode row (D or N).",
    "Entry is the bench row after week t's last bench row; exit is entry + h rows. For GVIP and "
    "QQQ the forward window is defined when both closes at entry and exit are present "
    "(intermediate days not required).",
    "Basket R_t = prod(1 + W) over rows entry+1..exit - 1, minus (QQQ exit/entry - 1); defined "
    "only if every W in that span is present and QQQ endpoints are present.",
    "The basket test uses its own signal (basket weekly minus QQQ weekly, own 104-week window) "
    "and its own eligible set.",
    "For h5 and h10 the eligible set is recomputed with that horizon's forward window; the signal "
    "definition is unchanged. h5/h10/declustered are GVIP-QQQ only.",
    "De-clustered: an eligible signal week is kept if none of the 4 preceding bench weeks is a "
    "signal week, a signal week being any week meeting the signal definition whether eligible or "
    "not. The permutation pool is the full eligible set at 20 days.",
    "Permutation: pool = eligible R in date order; n = number of (relevant) signal weeks; "
    "observed = mean of the signal weeks' R; 10,000 draws rng.choice(pool, n, replace=False).mean() "
    "from a fresh default_rng(20261029) per test; p = (1 + #(draw >= observed)) / 10001. "
    "p is null when n is 0 or n exceeds the pool.",
    "Verdict: INSUFFICIENT if n_signal < 20; else SUPPORTED if p_upper <= 0.05; else NOT SUPPORTED. "
    "The same rule is applied to the basket.",
    "Trade: eligible signals in date order; a signal is skipped when its week's last bench row "
    "(the moment it is read) is before the open trade's exit row, i.e. entry_idx <= prev exit_idx.",
    "Trade net = R - 0.004 - 0.005 * 20 / 252, days_held being trading rows between entry and exit.",
    "t_mean = mean / (sample sd ddof=1 / sqrt(n)); null when fewer than 2 trades or sd is 0. "
    "share_profitable is the share with net > 0.",
    "Years spanned = (last eligible week end - first eligible week end) in days / 365.25, using "
    "that series' 20-day eligible set (GVIP for trade_gvip, basket for trade_basket).",
]


# ---------------------------------------------------------------------------- inputs

def load_bench(d):
    with open(os.path.join(d, "bench.csv"), newline="") as fh:
        rows = list(csv.reader(fh))
    head = [h.strip() for h in rows[0]]
    days, cols = [], {h: [] for h in head[1:]}
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        days.append(dt.date.fromisoformat(r[0].strip()))
        for j, h in enumerate(head[1:], start=1):
            v = r[j].strip() if j < len(r) else ""
            cols[h].append(float(v) if v else np.nan)
    return days, {h: np.array(v, dtype=float) for h, v in cols.items()}


def load_w(data_b, bench_days):
    n = len(bench_days)
    if data_b is None or data_b.lower() == "none":
        return np.full(n, np.nan)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "degross_proxy_b", "run.py")
    spec = importlib.util.spec_from_file_location("_verify_rebound_b_run", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    days, col, px = mod.load_prices(data_b)
    bk = mod.load_baskets(data_b)
    bk = {e: {"long": list(v.get("long", [])), "short": []} for e, v in bk.items()}
    W, _L, _M, _cov = mod.daily_legs(days, col, px, bk)
    by_date = {d: W[i] for i, d in enumerate(days)}
    return np.array([by_date.get(d, np.nan) for d in bench_days], dtype=float)


def load_episodes(path):
    with open(path, newline="") as fh:
        return [dt.date.fromisoformat(r["week_end"].strip()) for r in csv.DictReader(fh)
                if r.get("week_end", "").strip()]


# ---------------------------------------------------------------------------- weeks

def week_groups(days):
    """List of (first_row, last_row) for each ISO week present, in date order."""
    groups, cur, start = [], None, 0
    for i, d in enumerate(days):
        key = d.isocalendar()[:2]
        if key != cur:
            if cur is not None:
                groups.append((start, i - 1))
            cur, start = key, i
    if cur is not None:
        groups.append((start, len(days) - 1))
    return groups


def daily_ret(px):
    r = np.full(len(px), np.nan)
    r[1:] = px[1:] / px[:-1] - 1.0
    return r


def weekly_compound(dr, groups):
    out = np.full(len(groups), np.nan)
    for k, (a, b) in enumerate(groups):
        seg = dr[a:b + 1]
        if not np.any(np.isnan(seg)):
            out[k] = np.prod(1.0 + seg) - 1.0
    return out


# ---------------------------------------------------------------------------- study

def signals(x):
    """sig[k] True/False where defined, None where the window or x_k is undefined."""
    sig = [None] * len(x)
    for k in range(PCT_WIN, len(x)):
        win = x[k - PCT_WIN:k]
        if np.isnan(x[k]) or np.any(np.isnan(win)):
            continue
        sig[k] = bool(x[k] <= np.percentile(win, PCT))
    return sig


def forward_etf(gv, qq, entry, exit_):
    if exit_ >= len(gv):
        return np.nan
    vals = (gv[entry], gv[exit_], qq[entry], qq[exit_])
    if any(np.isnan(v) for v in vals):
        return np.nan
    return gv[exit_] / gv[entry] - qq[exit_] / qq[entry]


def forward_basket(W, qq, entry, exit_):
    if exit_ >= len(W):
        return np.nan
    seg = W[entry + 1:exit_ + 1]
    if np.any(np.isnan(seg)) or np.isnan(qq[entry]) or np.isnan(qq[exit_]):
        return np.nan
    return (np.prod(1.0 + seg) - 1.0) - (qq[exit_] / qq[entry] - 1.0)


def build(days, groups, sig, fwd, h, episodes):
    """Eligible rows: list of dicts in date order."""
    rows = []
    for k, (a, b) in enumerate(groups):
        if sig[k] is None:
            continue
        we = days[b]
        if any(abs((we - e).days) <= EXCL_DAYS for e in episodes):
            continue
        entry = b + 1
        if entry >= len(days):
            continue
        R = fwd(entry, entry + h)
        if np.isnan(R):
            continue
        rows.append({"k": k, "week_end": we, "entry": entry, "exit": entry + h,
                     "R": float(R), "signal": sig[k]})
    return rows


def perm_test(pool, sig_vals):
    rng = np.random.default_rng(SEED)
    pool = np.asarray(pool, dtype=float)
    n = len(sig_vals)
    if n == 0 or n > len(pool):
        return None, None
    obs = float(np.mean(sig_vals))
    draws = np.array([rng.choice(pool, size=n, replace=False).mean() for _ in range(N_PERM)])
    return obs, (1 + int(np.sum(draws >= obs))) / (1 + N_PERM)


def verdict(n_sig, p):
    if n_sig < MIN_SIGNALS:
        return "INSUFFICIENT"
    return "SUPPORTED" if (p is not None and p <= ALPHA) else "NOT SUPPORTED"


def test_block(rows, subset=None, full=True):
    pool = [r["R"] for r in rows]
    chosen = subset if subset is not None else [r for r in rows if r["signal"]]
    sv = [r["R"] for r in chosen]
    obs, p = perm_test(pool, sv)
    out = {}
    if full:
        out["n_eligible"] = len(rows)
    out["n_signal"] = len(sv)
    out["mean_signal"] = obs
    out["mean_eligible"] = float(np.mean(pool)) if pool else None
    out["p_upper"] = p
    if full:
        out["verdict"] = verdict(len(sv), p)
    return out


def trade_block(rows, h):
    nets, prev_exit = [], -1
    for r in rows:
        if not r["signal"]:
            continue
        if r["entry"] <= prev_exit:
            continue
        nets.append(r["R"] - COST_RT - BORROW * h / 252.0)
        prev_exit = r["exit"]
    n = len(nets)
    a = np.array(nets, dtype=float)
    years = None
    if rows:
        span = (rows[-1]["week_end"] - rows[0]["week_end"]).days / 365.25
        years = span if span > 0 else None
    t = None
    if n >= 2:
        sd = float(np.std(a, ddof=1))
        if sd > 0:
            t = float(a.mean() / (sd / math.sqrt(n)))
    return {
        "trades": n,
        "share_profitable": float(np.mean(a > 0)) if n else None,
        "mean_net": float(a.mean()) if n else None,
        "median_net": float(np.median(a)) if n else None,
        "t_mean": t,
        "worst": float(a.min()) if n else None,
        "sum_net_per_year": float(a.sum() / years) if (n and years) else None,
    }


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, np.floating):
        return clean(float(o))
    if isinstance(o, np.integer):
        return int(o)
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--episodes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    days, px = load_bench(a.bench)
    gv, qq = px["GVIP"], px["QQQ"]
    W = load_w(a.data_b, days)
    episodes = load_episodes(a.episodes)
    groups = week_groups(days)

    gw = weekly_compound(daily_ret(gv), groups)
    qw = weekly_compound(daily_ret(qq), groups)
    ww = weekly_compound(W, groups)
    x = gw - qw
    xb = ww - qw

    sig = signals(x)
    sig_b = signals(xb)

    def fe(e, x_):
        return forward_etf(gv, qq, e, x_)

    def fb(e, x_):
        return forward_basket(W, qq, e, x_)

    rows = build(days, groups, sig, fe, H_PRIMARY, episodes)
    rows_b = build(days, groups, sig_b, fb, H_PRIMARY, episodes)
    rows5 = build(days, groups, sig, fe, 5, episodes)
    rows10 = build(days, groups, sig, fe, 10, episodes)

    res = test_block(rows)                                  # primary
    basket = test_block(rows_b)                             # basket
    h5 = test_block(rows5, full=False)
    h10 = test_block(rows10, full=False)
    dec_sub = [r for r in rows if r["signal"]
               and not any(sig[j] for j in range(max(0, r["k"] - DECLUSTER), r["k"]))]
    declustered = test_block(rows, subset=dec_sub, full=False)

    out = dict(res)
    out["basket"] = basket
    out["h5"] = h5
    out["h10"] = h10
    out["declustered"] = declustered
    out["trade_gvip"] = trade_block(rows, H_PRIMARY)
    out["trade_basket"] = trade_block(rows_b, H_PRIMARY)
    out["choices"] = CHOICES

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify_rebound.json"), "w") as fh:
        json.dump(clean(out), fh, indent=2)
    print(json.dumps({k: out[k] for k in ("n_eligible", "n_signal", "mean_signal",
                                          "mean_eligible", "p_upper", "verdict")}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
