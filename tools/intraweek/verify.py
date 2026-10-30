#!/usr/bin/env python3
"""Independent second implementation of tools/intraweek/PREREG.md.

Written from PREREG.md and tools/degross_episodes/episodes.csv alone, so that
it can be compared key by key against the first implementation's results.json.
It is deliberately not a refactoring of anything else in the repository: the
value of a second implementation is that its mistakes are its own.

Usage:
    python verify.py --data DIR --episodes FILE --out DIR

Reads DIR/bench.csv (DATE,GVIP,QQQ,MTUM,SPY; blank where a ticker has no close)
and the frozen episode file, and writes OUT/verify.json with exactly the keys
PREREG section 5 lists, plus a `choices` dict recording every point where the
pre-registration left a reading to the implementer and which reading was taken.

Refusals. A missing input, a column that is not there, a cell that is neither
blank nor a positive number, a date that does not parse, a date out of order or
repeated, or an episode file that is not the frozen 21-row file stops the run
with a message and a non-zero exit. Nothing is defaulted: a quantity that
cannot be computed is written as null and the reason is in `choices`.

Only numpy and pandas are used.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys

import numpy as np
import pandas as pd

PAIRS = {"P1": ("GVIP", "QQQ"), "P2": ("MTUM", "SPY")}
TICKERS = ["GVIP", "QQQ", "MTUM", "SPY"]
REFERENCE_WINDOW = 104
REFERENCE_FLOOR = 52
SIGNAL_PCT = 10.0
TOP_PCT = 90.0
SHIFT_MARGIN = 5
NW_LAGS = 5
MIN_SIGNAL_WEEKS = 40
COST = {"P1": 0.0040, "P2": 0.0010}
BORROW_RATE = 0.005
DAYS_PER_YEAR = 252
WEEKS_PER_YEAR = 52
EPISODE_ROWS = 21

CHOICES = {
    "spread_definition": (
        "s_t = (first_t/first_{t-1} - 1) - (second_t/second_{t-1} - 1) where t-1 is the "
        "preceding ROW of bench.csv whatever the calendar gap; the first row has no s; s is "
        "undefined when any of the four closes on rows t or t-1 is blank"
    ),
    "week_grouping": (
        "rows grouped by date.isocalendar() (ISO year, ISO week); days numbered 1..n in date "
        "order within the group; week label = the date string of the last row in the group"
    ),
    "admissible": "n >= 4 trading rows in the ISO week and s defined on every one of them (per pair)",
    "reference_set": (
        "the admissible weeks of the same pair strictly preceding w in date order, the most "
        "recent 104 of them; not filtered for episodes; counted over admissible weeks, not "
        "eligible ones"
    ),
    "eligible": (
        "admissible, reference set of at least 52 weeks, and the week's (ISO year, ISO week) "
        "is not the (ISO year, ISO week) of any of the 21 episode week_end dates (D and N alike)"
    ),
    "signal_rule": (
        "S_w <= numpy.percentile(reference S values, 10) with the default linear method; "
        "'at or below' is <=; top decile is S_w >= numpy.percentile(reference S, 90)"
    ),
    "one_day_reference": (
        "the one-day signal uses S' = s_1 of the same reference set (preceding 104 admissible "
        "weeks) and the same eligibility; the 10th percentile is taken over the reference S' values"
    ),
    "mean_R_other": "mean of R over ELIGIBLE weeks that are not signal weeks (all of them)",
    "d_undefined": "d is null when either group is empty; the shift p is then null too",
    "shift_p": (
        "k = 5 .. n_eligible - 5 inclusive, I_k = numpy.roll(I, k) over the eligible weeks in "
        "date order, d_k = mean R[I_k] - mean R[~I_k]; lower p counts d_k <= d, upper counts "
        "d_k >= d; p = (1 + count) / (1 + n_shifts); n_shifts = max(0, n_eligible - 9); "
        "p is null when n_shifts == 0"
    ),
    "share_R_negative_signal": "share of signal weeks with R_w < 0 (strict)",
    "daily_regressions": (
        "OLS with an intercept; observation pairs are consecutive ROWS of bench.csv with every "
        "term defined (s_t and s_{t+1} for the first; s_{t-1}, s_t, s_{t+1}, s_{t+2}, s_{t+3} "
        "for the second); no week boundaries; overlapping observations kept"
    ),
    "newey_west_t": (
        "t = slope / sqrt(V[1,1]) with V = (X'X)^-1 S (X'X)^-1, S = sum_{l=-5}^{5} "
        "(1 - |l|/6) Gamma_l, Gamma_l = sum_t x_t e_t e_{t-l} x_{t-l}'; no n/(n-k) factor "
        "(statsmodels HAC maxlags=5 use_correction=False)"
    ),
    "episode_weeks": (
        "a pair's admissible weeks whose (ISO year, ISO week) matches that of an episode "
        "week_end; counted as weeks, so two episodes in one ISO week would count once; "
        "mean_by_day position k is the mean of s_k over those weeks that have a day k "
        "(positions beyond 5 are ignored); mean_S and mean_R are over all those weeks; "
        "hit_rate = hits / n_with_reference where n_with_reference counts those weeks whose "
        "reference set holds at least 52 weeks and a hit is S_w <= the 10th percentile of "
        "that reference set; hit_rate is null when n_with_reference == 0"
    ),
    "trade": (
        "one trade per eligible signal week: net = -R_w - cost - borrow, cost 0.0040 (P1) or "
        "0.0010 (P2), borrow = 0.005 * (n - 2) / 252 with n the week's trading-day count; "
        "share_profitable counts net > 0 strictly; t = mean / (std(ddof=1) / sqrt(n)), null "
        "when n < 2 or std == 0; worst = min(net); net_per_year = sum(net) / (n_eligible / 52); "
        "trade_passes = mean > 0 and t >= 2 and n >= 40"
    ),
    "criteria": (
        "criteria.p1 = (d < 0 and p <= 0.025) for P1 with no count condition, because the "
        "40-signal floor on P1 is the INSUFFICIENT clause; criteria.p2 = (d < 0 and p <= 0.05 "
        "and n_signal >= 40) for P2; a null d or p fails the criterion"
    ),
    "verdict": (
        "INSUFFICIENT if P1 n_signal < 40; else SUPPORTED if criteria.p1 and criteria.p2; "
        "else NOT SUPPORTED; p1_alone = (verdict == 'NOT SUPPORTED' and criteria.p1)"
    ),
    "legs": "a two-element list [first leg, second leg]",
    "labels": "week labels are ISO date strings YYYY-MM-DD of the week's last trading row",
    "nan": "any quantity that cannot be computed is written as JSON null",
    "ddof": "trade t uses ddof=1; the Newey-West variance uses no degrees-of-freedom factor",
}


class Refusal(Exception):
    """A reason the run cannot proceed. Raised, never caught into a default."""


def die(msg: str) -> None:
    sys.stderr.write(f"verify.py: {msg}\n")
    sys.exit(2)


# --------------------------------------------------------------------------- #
# Input
# --------------------------------------------------------------------------- #

def parse_date(text: str, where: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(text).strip())
    except ValueError as exc:
        raise Refusal(f"{where}: date {text!r} does not parse as YYYY-MM-DD") from exc


def read_bench(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise Refusal(f"bench file not found: {path}")
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    needed = ["DATE"] + TICKERS
    missing = [c for c in needed if c not in raw.columns]
    if missing:
        raise Refusal(f"bench.csv lacks columns {missing}; has {list(raw.columns)}")
    if len(raw) == 0:
        raise Refusal("bench.csv has no rows")
    dates = []
    for i, text in enumerate(raw["DATE"].tolist()):
        if text.strip() == "":
            raise Refusal(f"bench.csv row {i + 2}: blank DATE")
        dates.append(parse_date(text, f"bench.csv row {i + 2}"))
    for i in range(1, len(dates)):
        if dates[i] <= dates[i - 1]:
            raise Refusal(
                f"bench.csv row {i + 2}: date {dates[i]} is not after {dates[i - 1]} "
                "(rows must be in strictly increasing date order)"
            )
    out = pd.DataFrame({"DATE": dates})
    for tk in TICKERS:
        vals = np.full(len(raw), np.nan)
        for i, text in enumerate(raw[tk].tolist()):
            t = text.strip()
            if t == "":
                continue
            try:
                v = float(t)
            except ValueError as exc:
                raise Refusal(f"bench.csv row {i + 2} column {tk}: {text!r} is not a number") from exc
            if not math.isfinite(v) or v <= 0:
                raise Refusal(f"bench.csv row {i + 2} column {tk}: {text!r} is not a positive close")
            vals[i] = v
        out[tk] = vals
    return out


def read_episodes(path: str) -> list[tuple[int, int]]:
    if not os.path.isfile(path):
        raise Refusal(f"episodes file not found: {path}")
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    for c in ("episode_id", "class", "week_end"):
        if c not in raw.columns:
            raise Refusal(f"episodes file lacks column {c!r}")
    if len(raw) != EPISODE_ROWS:
        raise Refusal(f"episodes file has {len(raw)} rows; the frozen file has {EPISODE_ROWS}")
    keys: list[tuple[int, int]] = []
    for i, row in raw.iterrows():
        cls = row["class"].strip()
        if cls not in ("D", "N"):
            raise Refusal(f"episodes row {i + 2}: class {cls!r} is not D or N")
        d = parse_date(row["week_end"], f"episodes row {i + 2}")
        iso = d.isocalendar()
        keys.append((iso[0], iso[1]))
    return keys


# --------------------------------------------------------------------------- #
# Series and weeks
# --------------------------------------------------------------------------- #

def spread_series(bench: pd.DataFrame, first: str, second: str) -> np.ndarray:
    """s_t against the preceding row; NaN on the first row and wherever a close is blank."""
    a = bench[first].to_numpy(dtype=float)
    b = bench[second].to_numpy(dtype=float)
    s = np.full(len(bench), np.nan)
    ra = a[1:] / a[:-1] - 1.0
    rb = b[1:] / b[:-1] - 1.0
    s[1:] = ra - rb
    return s


def build_weeks(bench: pd.DataFrame, s: np.ndarray) -> list[dict]:
    """Every ISO week in the file, admissible or not, in date order."""
    dates = bench["DATE"].tolist()
    groups: dict[tuple[int, int], list[int]] = {}
    order: list[tuple[int, int]] = []
    for i, d in enumerate(dates):
        iso = d.isocalendar()
        key = (iso[0], iso[1])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(i)
    weeks = []
    for key in order:
        idx = groups[key]
        svals = s[idx]
        n = len(idx)
        admissible = bool(n >= 4 and np.all(np.isfinite(svals)))
        weeks.append(
            {
                "iso": key,
                "label": dates[idx[-1]].isoformat(),
                "n": n,
                "s": svals,
                "admissible": admissible,
            }
        )
    return weeks


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q))


def shift_p(R: np.ndarray, I: np.ndarray, d: float, side: str) -> tuple[float, int]:
    n = len(I)
    ks = list(range(SHIFT_MARGIN, n - SHIFT_MARGIN + 1))
    n_shifts = len(ks)
    if n_shifts == 0 or not math.isfinite(d):
        return float("nan"), n_shifts
    count = 0
    for k in ks:
        Ik = np.roll(I, k)
        dk = float(R[Ik].mean() - R[~Ik].mean())
        if side == "lower":
            if dk <= d:
                count += 1
        else:
            if dk >= d:
                count += 1
    return (1.0 + count) / (1.0 + n_shifts), n_shifts


def group_difference(R: np.ndarray, I: np.ndarray) -> tuple[float, float, float]:
    if I.sum() == 0 or (~I).sum() == 0:
        return float("nan"), float("nan"), float("nan")
    m_sig = float(R[I].mean())
    m_oth = float(R[~I].mean())
    return m_sig, m_oth, m_sig - m_oth


def newey_west_slope_t(x: np.ndarray, y: np.ndarray, lags: int) -> tuple[float, float]:
    n = len(x)
    X = np.column_stack([np.ones(n), x])
    XtX = X.T @ X
    beta = np.linalg.solve(XtX, X.T @ y)
    e = y - X @ beta
    u = X * e[:, None]
    S = u.T @ u
    for lag in range(1, lags + 1):
        if lag >= n:
            break
        w = 1.0 - lag / (lags + 1.0)
        G = u[lag:].T @ u[:-lag]
        S = S + w * (G + G.T)
    XtX_inv = np.linalg.inv(XtX)
    V = XtX_inv @ S @ XtX_inv
    var = float(V[1, 1])
    t = float(beta[1] / math.sqrt(var)) if var > 0 else float("nan")
    return float(beta[1]), t


def daily_block(s: np.ndarray) -> dict:
    # Regression 1: s_{t+1} on s_t, consecutive rows.
    x1 = s[:-1]
    y1 = s[1:]
    ok1 = np.isfinite(x1) & np.isfinite(y1)
    n1 = int(ok1.sum())
    if n1 >= 3:
        slope1, t1 = newey_west_slope_t(x1[ok1], y1[ok1], NW_LAGS)
    else:
        slope1, t1 = float("nan"), float("nan")
    # Regression 2: (s_{t+1}+s_{t+2}+s_{t+3}) on (s_{t-1}+s_t), rows t-1..t+3 all defined.
    T = len(s)
    if T >= 5:
        sm1 = s[0 : T - 4]
        s0 = s[1 : T - 3]
        sp1 = s[2 : T - 2]
        sp2 = s[3 : T - 1]
        sp3 = s[4 : T]
        ok2 = (
            np.isfinite(sm1)
            & np.isfinite(s0)
            & np.isfinite(sp1)
            & np.isfinite(sp2)
            & np.isfinite(sp3)
        )
        n23 = int(ok2.sum())
        x2 = (sm1 + s0)[ok2]
        y2 = (sp1 + sp2 + sp3)[ok2]
    else:
        n23 = 0
        x2 = y2 = np.array([])
    if n23 >= 3:
        slope23, t23 = newey_west_slope_t(x2, y2, NW_LAGS)
    else:
        slope23, t23 = float("nan"), float("nan")
    return {"slope1": slope1, "t1": t1, "n1": n1, "slope23": slope23, "t23": t23, "n23": n23}


def analyse_pair(bench: pd.DataFrame, pair: str, episode_keys: set[tuple[int, int]]) -> dict:
    first, second = PAIRS[pair]
    s = spread_series(bench, first, second)
    weeks = build_weeks(bench, s)
    adm = [w for w in weeks if w["admissible"]]
    n_admissible = len(adm)

    # Per admissible week: S, R, S' (one-day), R', the reference window.
    S = np.array([float(w["s"][0] + w["s"][1]) for w in adm])
    R = np.array([float(w["s"][2:].sum()) for w in adm])
    S1 = np.array([float(w["s"][0]) for w in adm])
    R1 = np.array([float(w["s"][1:].sum()) for w in adm])
    nday = np.array([w["n"] for w in adm], dtype=int)
    labels = [w["label"] for w in adm]
    is_episode = np.array([w["iso"] in episode_keys for w in adm], dtype=bool)

    ref_lo = np.full(n_admissible, np.nan)   # 10th percentile of S over the reference set
    ref_hi = np.full(n_admissible, np.nan)   # 90th percentile of S
    ref1_lo = np.full(n_admissible, np.nan)  # 10th percentile of S' over the reference set
    ref_n = np.zeros(n_admissible, dtype=int)
    for i in range(n_admissible):
        lo = max(0, i - REFERENCE_WINDOW)
        ref_n[i] = i - lo
        if ref_n[i] >= 1:
            ref_lo[i] = percentile(S[lo:i], SIGNAL_PCT)
            ref_hi[i] = percentile(S[lo:i], TOP_PCT)
            ref1_lo[i] = percentile(S1[lo:i], SIGNAL_PCT)

    eligible = (ref_n >= REFERENCE_FLOOR) & ~is_episode
    el = np.flatnonzero(eligible)
    n_eligible = int(len(el))

    out: dict = {
        "legs": [first, second],
        "n_admissible": n_admissible,
        "n_eligible": n_eligible,
        "first_eligible": labels[el[0]] if n_eligible else None,
        "last_eligible": labels[el[-1]] if n_eligible else None,
    }

    R_el = R[el]
    S_el = S[el]
    I = S_el <= ref_lo[el]
    n_signal = int(I.sum())
    m_sig, m_oth, d = group_difference(R_el, I)
    p, n_shifts = shift_p(R_el, I, d, "lower")
    out.update(
        {
            "n_signal": n_signal,
            "mean_R_signal": m_sig,
            "mean_R_other": m_oth,
            "d": d,
            "p_shift": p,
            "n_shifts": n_shifts,
            "share_R_negative_signal": float((R_el[I] < 0).mean()) if n_signal else float("nan"),
        }
    )

    # Top decile, upper p.
    It = S_el >= ref_hi[el]
    _, _, dt_ = group_difference(R_el, It)
    pt, _ = shift_p(R_el, It, dt_, "upper")
    out["top"] = {"n_signal": int(It.sum()), "d": dt_, "p_shift": pt}

    # One-day signal, lower p.
    I1 = S1[el] <= ref1_lo[el]
    _, _, d1 = group_difference(R1[el], I1)
    p1, _ = shift_p(R1[el], I1, d1, "lower")
    out["one_day"] = {"n_signal": int(I1.sum()), "d": d1, "p_shift": p1}

    # Daily autocorrelation, no week boundaries.
    out["daily"] = daily_block(s)

    # Episode weeks.
    ep = np.flatnonzero(is_episode)
    mean_by_day = []
    for pos in range(5):
        vals = [float(adm[i]["s"][pos]) for i in ep if adm[i]["n"] > pos]
        mean_by_day.append(float(np.mean(vals)) if vals else float("nan"))
    ep_ref = [i for i in ep if ref_n[i] >= REFERENCE_FLOOR]
    hits = sum(1 for i in ep_ref if S[i] <= ref_lo[i])
    out["episodes"] = {
        "n": int(len(ep)),
        "mean_by_day": mean_by_day,
        "mean_S": float(S[ep].mean()) if len(ep) else float("nan"),
        "mean_R": float(R[ep].mean()) if len(ep) else float("nan"),
        "hit_rate": (hits / len(ep_ref)) if len(ep_ref) else float("nan"),
        "n_with_reference": int(len(ep_ref)),
    }

    # The trade.
    sig_idx = el[I]
    net = np.array(
        [-R[i] - COST[pair] - BORROW_RATE * (nday[i] - 2) / DAYS_PER_YEAR for i in sig_idx],
        dtype=float,
    )
    n_tr = int(len(net))
    if n_tr >= 2:
        sd = float(net.std(ddof=1))
        t_tr = float(net.mean() / (sd / math.sqrt(n_tr))) if sd > 0 else float("nan")
    else:
        t_tr = float("nan")
    mean_tr = float(net.mean()) if n_tr else float("nan")
    out["trade"] = {
        "n": n_tr,
        "share_profitable": float((net > 0).mean()) if n_tr else float("nan"),
        "mean": mean_tr,
        "median": float(np.median(net)) if n_tr else float("nan"),
        "t": t_tr,
        "worst": float(net.min()) if n_tr else float("nan"),
        "net_per_year": (float(net.sum()) / (n_eligible / WEEKS_PER_YEAR)) if n_eligible else float("nan"),
        "trade_passes": bool(
            n_tr >= MIN_SIGNAL_WEEKS
            and math.isfinite(mean_tr)
            and mean_tr > 0
            and math.isfinite(t_tr)
            and t_tr >= 2.0
        ),
    }
    return out


def meets(dv: float, pv: float, bar: float) -> bool:
    return bool(math.isfinite(dv) and math.isfinite(pv) and dv < 0 and pv <= bar)


def nan_to_null(obj):
    if isinstance(obj, dict):
        return {k: nan_to_null(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [nan_to_null(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if not math.isfinite(f) else f
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, help="directory holding bench.csv")
    ap.add_argument("--episodes", required=True, help="the frozen episodes.csv")
    ap.add_argument("--out", required=True, help="directory to write verify.json into")
    args = ap.parse_args(argv)

    try:
        bench = read_bench(os.path.join(args.data, "bench.csv"))
        episode_keys = read_episodes(args.episodes)
        ep_set = set(episode_keys)
        pairs = {pair: analyse_pair(bench, pair, ep_set) for pair in ("P1", "P2")}
    except Refusal as exc:
        die(str(exc))
        return 2  # unreachable; keeps type checkers quiet

    p1 = pairs["P1"]
    p2 = pairs["P2"]
    crit_p1 = meets(p1["d"], p1["p_shift"], 0.025)
    crit_p2 = meets(p2["d"], p2["p_shift"], 0.05) and p2["n_signal"] >= MIN_SIGNAL_WEEKS
    if p1["n_signal"] < MIN_SIGNAL_WEEKS:
        verdict = "INSUFFICIENT"
    elif crit_p1 and crit_p2:
        verdict = "SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"
    p1_alone = bool(verdict == "NOT SUPPORTED" and crit_p1)

    result = {
        "pairs": pairs,
        "criteria": {"p1": crit_p1, "p2": crit_p2},
        "p1_alone": p1_alone,
        "verdict": verdict,
        "choices": dict(CHOICES, n_episode_iso_weeks=len(ep_set)),
    }
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "verify.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(nan_to_null(result), fh, indent=2, allow_nan=False)
        fh.write("\n")
    print(f"wrote {path}: verdict {verdict}; P1 n_signal={p1['n_signal']} d={p1['d']} "
          f"p={p1['p_shift']}; P2 n_signal={p2['n_signal']} d={p2['d']} p={p2['p_shift']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
