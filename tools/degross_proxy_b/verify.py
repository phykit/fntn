#!/usr/bin/env python3
"""Independent second implementation of the de-gross proxy, Version B.

Written from tools/degross_proxy_b/PREREG.md (Version B, governs) and
tools/degross_proxy/PREREG.md (Version A, sections 3 to 5 carried over) alone.

Usage: python verify.py --data DATA_DIR --out OUT_DIR [--force-gate]

--force-gate (hidden, default off) computes the outcome test even when the gate
does not PASS; it exists only for synthetic testing and is never used on a run
of record.
"""
import argparse
import bisect
import csv
import datetime as dt
import io
import json
import math
import os
import sys
import zipfile

import numpy as np

FUND_WORDS = ("ETF", "ETN", "FUND", "SPDR", "ISHARES", "PROSHARES", "POWERSHARES",
              "INVESCO QQQ", "SELECT SECTOR", "VANGUARD", "DIREXION", "VANECK",
              "WISDOMTREE", "GLOBAL X")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

REFERENCES = [dt.date(2021, 1, 29), dt.date(2026, 5, 1), dt.date(2026, 10, 16)]
BETA_WIN = 52
Z_WIN = 104
S_WIN = 13
PCT_WIN = 104
N_PERM = 10000
SEED = 20261029
MERGE = 63


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def parse_date(s):
    s = s.strip()
    if not s:
        return None
    try:
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return dt.date.fromisoformat(s)
        if len(s) == 11 and s[2] == "-" and s[6] == "-":
            return dt.date(int(s[7:11]), MONTHS[s[3:6].upper()], int(s[0:2]))
    except (ValueError, KeyError):
        return None
    return None


# ---------------------------------------------------------------- 13F reading

def find_member(zf, name):
    for m in zf.namelist():
        if os.path.basename(m).upper() == name.upper():
            return m
    return None


def iter_tsv(zf, member):
    """Yield (header_index, fields) per data line; columns located by header name."""
    with zf.open(member) as raw:
        txt = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
        header = None
        for line in txt:
            line = line.rstrip("\r\n")
            if header is None:
                header = {h.strip().upper(): i for i, h in enumerate(line.split("\t"))}
                yield header, None
                continue
            if not line:
                continue
            yield header, line.split("\t")


def read_submissions(zips):
    """Pool SUBMISSION rows across files, de-duplicated by accession (first file in
    sorted order wins). Returns dict acc -> (zip, filing_date, type, cik, period)."""
    subs = {}
    bad = 0
    for zp in zips:
        with zipfile.ZipFile(zp) as zf:
            m = find_member(zf, "SUBMISSION.tsv")
            if m is None:
                log("no SUBMISSION.tsv in", zp)
                continue
            h = None
            for header, f in iter_tsv(zf, m):
                if f is None:
                    h = header
                    ia, ifd, it, ic, ip = (h["ACCESSION_NUMBER"], h["FILING_DATE"],
                                           h["SUBMISSIONTYPE"], h["CIK"], h["PERIODOFREPORT"])
                    mx = max(ia, ifd, it, ic, ip)
                    continue
                if len(f) <= mx:
                    bad += 1
                    continue
                acc = f[ia].strip()
                if not acc or acc in subs:
                    continue
                subs[acc] = (zp, parse_date(f[ifd]), f[it].strip(), f[ic].strip(), parse_date(f[ip]))
    log(f"submissions pooled: {len(subs)} (malformed lines {bad})")
    return subs


def select_filings(subs):
    best = {}
    for acc, (zp, f, typ, cik, q) in subs.items():
        if typ != "13F-HR" or f is None or q is None:
            continue
        if (f - q).days > 45:
            continue
        key = (cik, q)
        cand = (f, acc)
        if key not in best or cand > best[key][0]:
            best[key] = (cand, zp)
    kept = {}
    for (cik, q), ((f, acc), zp) in best.items():
        kept[acc] = (zp, q)
    return kept


def is_fund(name, title):
    s1 = name.upper()
    s2 = title.upper()
    for w in FUND_WORDS:
        if w in s1 or w in s2:
            return True
    return False


def read_holdings(zips, kept):
    """Stream INFOTABLE rows of kept filings, each filing read only from the file
    to which its accession was assigned. Returns per-period list of HF-like
    filing summaries and per-period kept-filing counts."""
    by_zip = {}
    for acc, (zp, q) in kept.items():
        by_zip.setdefault(zp, set()).add(acc)
    hf = {}  # period -> list of (top10 list, long set, put set)
    for zp in zips:
        accs = by_zip.get(zp)
        if not accs:
            continue
        state = {}  # acc -> [longs dict, overflow, has_opt, puts set]
        with zipfile.ZipFile(zp) as zf:
            m = find_member(zf, "INFOTABLE.tsv")
            if m is None:
                log("no INFOTABLE.tsv in", zp)
                continue
            nrows = 0
            for header, f in iter_tsv(zf, m):
                if f is None:
                    h = header
                    ia = h["ACCESSION_NUMBER"]; iname = h["NAMEOFISSUER"]; ititle = h["TITLEOFCLASS"]
                    icus = h["CUSIP"]; ival = h["VALUE"]; ityp = h["SSHPRNAMTTYPE"]; ipc = h["PUTCALL"]
                    mx = max(ia, iname, ititle, icus, ival, ityp, ipc)
                    continue
                if len(f) <= mx:
                    continue
                acc = f[ia].strip()
                if acc not in accs:
                    continue
                nrows += 1
                st = state.get(acc)
                if st is None:
                    st = state[acc] = [{}, False, False, set()]
                pc = f[ipc].strip().upper()
                cus = f[icus].strip().upper()
                if pc in ("PUT", "CALL"):
                    st[2] = True
                    if pc == "PUT" and cus and not is_fund(f[iname], f[ititle]):
                        st[3].add(cus)
                    continue
                if pc == "" and f[ityp].strip().upper() == "SH":
                    if st[1] or not cus or is_fund(f[iname], f[ititle]):
                        continue
                    try:
                        v = float(f[ival].strip().replace(",", ""))
                    except ValueError:
                        v = 0.0
                    d = st[0]
                    d[cus] = d.get(cus, 0.0) + v
                    if len(d) > 200:
                        st[1] = True
                        st[0] = {}
        log(f"{os.path.basename(zp)}: {nrows} rows for {len(state)} kept filings")
        for acc, (longs, over, has_opt, puts) in state.items():
            if over or not has_opt or not (10 <= len(longs) <= 200):
                continue
            q = kept[acc][1]
            top = sorted(longs.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
            hf.setdefault(q, []).append(([c for c, _ in top], frozenset(longs), frozenset(puts)))
    return hf


def build_baskets(hf):
    out = {}
    for q, fl in hf.items():
        top_cnt, hold_cnt, put_cnt = {}, {}, {}
        for top, longs, puts in fl:
            for c in top:
                top_cnt[c] = top_cnt.get(c, 0) + 1
            for c in longs:
                hold_cnt[c] = hold_cnt.get(c, 0) + 1
            for c in puts:
                put_cnt[c] = put_cnt.get(c, 0) + 1
        long_b = sorted(top_cnt, key=lambda c: (-top_cnt[c], -hold_cnt.get(c, 0), c))[:50]
        lset = set(long_b)
        short_b = sorted((c for c, n in put_cnt.items() if n >= 2 and c not in lset),
                         key=lambda c: (-put_cnt[c], c))[:50]
        out[q] = (long_b, short_b)
    return out


# ---------------------------------------------------------------- FTD mapping

def read_ftd(paths, needed):
    rec = {}
    for zp in paths:
        with zipfile.ZipFile(zp) as zf:
            for m in zf.namelist():
                if m.endswith("/"):
                    continue
                with zf.open(m) as raw:
                    for line in io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline=""):
                        f = line.rstrip("\r\n").split("|")
                        if len(f) < 4:
                            continue
                        d = f[0].strip()
                        if len(d) != 8 or not d.isdigit():
                            continue
                        cus = f[1].strip().upper()
                        if cus not in needed:
                            continue
                        sym = f[2].strip()
                        if not sym:
                            continue
                        try:
                            day = dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))
                        except ValueError:
                            continue
                        rec.setdefault(cus, []).append((day, sym))
    for c in rec:
        rec[c].sort()
    return rec


def map_symbol(rec, cus, E):
    lst = rec.get(cus)
    if not lst:
        return None
    i = bisect.bisect_right(lst, (E, "￿")) - 1  # last record dated <= E (ties: greatest symbol)
    if i < 0:
        return None
    day, sym = lst[i]
    if (E - day).days > 365:
        return None
    return sym.replace(".", "-").replace("/", "-")


# ---------------------------------------------------------------- prices

def read_prices(path, wanted):
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        header = next(r)
        cols = {h.strip(): i for i, h in enumerate(header)}
        use = {s: cols[s] for s in wanted if s in cols}
        dates, data = [], {s: [] for s in use}
        for row in r:
            if not row:
                continue
            dates.append(dt.date.fromisoformat(row[0].strip()))
            for s, i in use.items():
                v = row[i].strip() if i < len(row) else ""
                data[s].append(float(v) if v else math.nan)
    order = np.argsort(np.array([d.toordinal() for d in dates]), kind="stable")
    dates = [dates[i] for i in order]
    return dates, {s: np.asarray(v, float)[order] for s, v in data.items()}


def read_ndx(path):
    dates, vals = [], []
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        next(r)
        for row in r:
            if len(row) < 2 or not row[1].strip() or row[1].strip() == ".":
                continue
            dates.append(dt.date.fromisoformat(row[0].strip()))
            vals.append(float(row[1]))
    o = sorted(range(len(dates)), key=lambda i: dates[i])
    return [dates[i] for i in o], np.array([vals[i] for i in o], float)


# ---------------------------------------------------------------- signals

def ols_slope(x, y):
    xm = x - x.mean()
    den = (xm * xm).sum()
    if den == 0:
        return math.nan
    return (xm * (y - y.mean())).sum() / den


def window_ok(arr, a, b):
    """True when arr[a:b] is fully defined and a >= 0."""
    return a >= 0 and not np.isnan(arr[a:b]).any()


def compute_signals(W, L, M):
    n = len(W)
    defined = ~(np.isnan(W) | np.isnan(L) | np.isnan(M))
    P = np.full(n, np.nan)
    for t in range(n):
        if not defined[t] or t < BETA_WIN or not defined[t - BETA_WIN:t].all():
            continue
        x = M[t - BETA_WIN:t]
        bW = ols_slope(x, W[t - BETA_WIN:t])
        bL = ols_slope(x, L[t - BETA_WIN:t])
        P[t] = (W[t] - bW * M[t]) - (L[t] - bL * M[t])
    z = np.full(n, np.nan)
    S = np.full(n, np.nan)
    for t in range(n):
        if not np.isnan(P[t]) and window_ok(P, t - Z_WIN, t):
            w = P[t - Z_WIN:t]
            sd = w.std(ddof=1)
            if sd > 0:
                z[t] = (P[t] - w.mean()) / sd
        if defined[t] and window_ok(P, t - S_WIN, t):
            S[t] = P[t - S_WIN:t].sum()
    C = np.full(n, np.nan)  # 1.0 / 0.0 / nan
    for t in range(n):
        if not np.isnan(S[t]) and window_ok(S, t - PCT_WIN, t):
            C[t] = 1.0 if S[t] >= np.percentile(S[t - PCT_WIN:t], 90) else 0.0
    ev = ~np.isnan(z) & ~np.isnan(C)
    D = ev & (z <= -2.0) & (W < 0) & (L > 0)
    D_nosign = ev & (z <= -2.0)
    Cb = ev & (C == 1.0)
    return dict(P=P, z=z, S=S, C=Cb, ev=ev, D=D, D_nosign=D_nosign)


# ---------------------------------------------------------------- outcome test

def outcome_test(week_end, ev, trig, ndx_dates, ndx, window, thresh):
    nd_ord = [d.toordinal() for d in ndx_dates]
    rows = []  # (t, i, E, DD, R21, trig)
    for t in np.nonzero(ev)[0]:
        e = week_end[t]
        if not ndx_dates or e < ndx_dates[0]:
            continue
        i = bisect.bisect_right(nd_ord, e.toordinal()) - 1
        if i + window >= len(ndx) or i < 21:
            continue  # no N(i+window), or no R21: dropped
        seg = ndx[i:i + window + 1]
        runmax = np.maximum.accumulate(seg)
        dd = float((seg[1:] / runmax[1:]).min() - 1.0)
        r21 = ndx[i] / ndx[i - 21] - 1.0
        rows.append((int(t), i, dd <= thresh, dd, r21, bool(trig[t])))
    res = dict(n_episodes=0, E_T=None, E_O=None, delta=None, p=None, verdict="INSUFFICIENT",
               episodes=[], n_outcome_evaluable=len(rows))
    if not rows:
        return res
    r21 = np.array([r[4] for r in rows])
    c1, c2 = np.percentile(r21, 100 / 3), np.percentile(r21, 200 / 3)
    strat = np.where(r21 < c1, 0, np.where(r21 >= c2, 2, 1))
    eps = []
    start_i = None
    for k, r in enumerate(rows):
        if not r[5]:
            continue
        if start_i is not None and r[1] - start_i <= MERGE:
            continue
        start_i = r[1]
        eps.append(k)
    untrig = [k for k, r in enumerate(rows) if not r[5]]
    Evec = np.array([1.0 if r[2] else 0.0 for r in rows])
    res["n_episodes"] = len(eps)
    res["episodes"] = [dict(date=week_end[rows[k][0]].isoformat(), E=bool(rows[k][2]),
                            DD=rows[k][3]) for k in eps]
    if not untrig:
        return res
    E_O = float(Evec[untrig].mean())
    res["E_O"] = E_O
    if not eps:
        return res
    E_T = float(Evec[eps].mean())
    delta = E_T - E_O
    res["E_T"], res["delta"] = E_T, delta
    pools = {s: np.array([k for k in untrig if strat[k] == s]) for s in (0, 1, 2)}
    need = {s: sum(1 for k in eps if strat[k] == s) for s in (0, 1, 2)}
    for s in (0, 1, 2):
        if need[s] > len(pools[s]):
            raise RuntimeError(f"stratum {s} runs out: need {need[s]}, have {len(pools[s])}")
    rng = np.random.default_rng(SEED)
    cnt = 0
    for _ in range(N_PERM):
        avail = {s: list(pools[s]) for s in (0, 1, 2)}
        tot = 0.0
        for k in eps:
            pool = avail[strat[k]]
            j = int(rng.integers(len(pool)))
            tot += Evec[pool.pop(j)]
        if tot / len(eps) - E_O >= delta - 1e-12:
            cnt += 1
    p = (1 + cnt) / (1 + N_PERM)
    res["p"] = p
    n = len(eps)
    if n < 8:
        res["verdict"] = "INSUFFICIENT"
    elif p <= 0.05 and delta >= 0.10:
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
    return res


# ---------------------------------------------------------------- main

def stage_baskets(data):
    zips13 = sorted(os.path.join(data, "13f", f) for f in os.listdir(os.path.join(data, "13f"))
                    if f.lower().endswith(".zip"))
    subs = read_submissions(zips13)
    kept = select_filings(subs)
    del subs
    n_kept = {}
    for acc, (zp, q) in kept.items():
        n_kept[q] = n_kept.get(q, 0) + 1
    log(f"kept filings: {len(kept)} over {len(n_kept)} periods")
    hf = read_holdings(zips13, kept)
    baskets = build_baskets(hf)

    with open(os.path.join(data, "prices.csv"), newline="", encoding="utf-8") as fh:
        price_cols = set(h.strip() for h in next(csv.reader(fh)))
    pdates, spy_only = read_prices(os.path.join(data, "prices.csv"), ["SPY"])
    spy_mask = ~np.isnan(spy_only["SPY"])
    spy_days = [d for d, m in zip(pdates, spy_mask) if m]
    spy_ord = [d.toordinal() for d in spy_days]

    periods = []
    for q in sorted(baskets):
        target = (q + dt.timedelta(days=45)).toordinal()
        j = bisect.bisect_right(spy_ord, target)
        if j >= len(spy_days):
            log(f"period {q}: no SPY day after q+45; no basket")
            continue
        periods.append((spy_days[j], q))
    periods.sort()
    effs = [E for E, q in periods]
    if len(set(effs)) != len(effs):
        log("WARNING: two periods share one effective date; the later period wins the holding span")

    needed = set()
    for E, q in periods:
        needed.update(baskets[q][0]); needed.update(baskets[q][1])
    ftd_dir = os.path.join(data, "ftd")
    ftd = read_ftd(sorted(os.path.join(ftd_dir, f) for f in os.listdir(ftd_dir)
                          if f.lower().endswith(".zip")), needed)

    basket_rows, mapped, summary = [], [], []
    for E, q in periods:
        legs = {}
        for leg, lst in (("long", baskets[q][0]), ("short", baskets[q][1])):
            out = []
            for r, c in enumerate(lst, 1):
                s = map_symbol(ftd, c, E)
                if s is None:
                    continue
                out.append((r, c, s))
                basket_rows.append((q.isoformat(), E.isoformat(), leg, r, c, s))
            legs[leg] = out
        mapped.append((E, q, legs["long"], legs["short"]))
        qe = (q + dt.timedelta(days=1)).day == 1 and q.month in (3, 6, 9, 12)
        summary.append(dict(period=q.isoformat(), effective=E.isoformat(),
                            n_kept_filings=n_kept.get(q, 0), n_hf_like=len(hf.get(q, [])),
                            long_n=len(legs["long"]), short_n=len(legs["short"]),
                            long_pre_map=len(baskets[q][0]), short_pre_map=len(baskets[q][1]),
                            quarter_end=qe))
    return dict(basket_rows=basket_rows, mapped=mapped, summary=summary,
                price_cols=price_cols, spy_mask=spy_mask, spy_days=spy_days)


def stage_returns(data, st):
    basket_rows, mapped, spy_days, spy_mask = st["basket_rows"], st["mapped"], st["spy_days"], st["spy_mask"]
    syms = sorted({r[5] for r in basket_rows} & st["price_cols"])
    _, pr = read_prices(os.path.join(data, "prices.csv"), syms + ["SPY"])
    pr = {s: v[spy_mask] for s, v in pr.items()}
    nd = len(spy_days)
    spy = pr["SPY"]
    M = np.full(nd, np.nan)
    M[1:] = spy[1:] / spy[:-1] - 1.0
    idx_of = {d: i for i, d in enumerate(spy_days)}
    Wd = np.full(nd, np.nan)
    Ld = np.full(nd, np.nan)
    priced = []
    for k, (E, q, lg, sh) in enumerate(mapped):
        iE = idx_of[E]
        iN = idx_of[mapped[k + 1][0]] if k + 1 < len(mapped) else nd - 1
        if iN <= iE:
            continue
        pinfo = {"period": q.isoformat()}
        for leg, cons, tgt in (("long", lg, Wd), ("short", sh, Ld)):
            series = []
            for r, c, s in cons:
                v = pr.get(s)
                if v is None or np.isnan(v[iE]):
                    continue
                series.append(v)
            pinfo[leg + "_priced_share"] = (len(series) / len(cons)) if cons else None
            if not series:
                continue  # days stay undefined
            X = np.vstack(series)[:, iE:iN + 1]
            R = X[:, 1:] / X[:, :-1] - 1.0
            cntv = (~np.isnan(R)).sum(0)
            with np.errstate(invalid="ignore", divide="ignore"):
                mean = np.where(cntv > 0, np.nansum(R, 0) / np.maximum(cntv, 1), np.nan)
            tgt[iE + 1:iN + 1] = mean
        priced.append(pinfo)
    return spy_days, Wd, Ld, M, priced


def weekly(spy_days, Wd, Ld, M):
    keys = [d.isocalendar()[:2] for d in spy_days]
    groups = []
    for i, k in enumerate(keys):
        if i == 0 or k != keys[i - 1]:
            groups.append([])
        groups[-1].append(i)
    nw = len(groups)
    Ww, Lw, Mw = np.full(nw, np.nan), np.full(nw, np.nan), np.full(nw, np.nan)
    week_end = []
    for t, g in enumerate(groups):
        week_end.append(spy_days[g[-1]])
        for dsrc, dst in ((Wd, Ww), (Ld, Lw), (M, Mw)):
            x = dsrc[g]
            if not np.isnan(x).any():
                dst[t] = np.prod(1.0 + x) - 1.0
    return week_end, Ww, Lw, Mw


def gate_and_test(week_end, Ww, Lw, Mw, ndx_path, force=False):
    nw = len(week_end)
    sig = compute_signals(Ww, Lw, Mw)
    ev, D = sig["ev"], sig["D"]
    last = week_end[-1]
    avail = [r for r in REFERENCES if r <= last]
    matched = []
    for r in avail:
        for t in np.nonzero(D)[0]:
            if abs((week_end[t] - r).days) <= 7:
                matched.append(r.isoformat())
                break
    nev = int(ev.sum())
    b = float(D.sum() / nev) if nev else None
    if len(avail) < 2:
        status = "UNTESTABLE"
    elif len(matched) >= 2 and b is not None and b <= 0.05:
        status = "PASS"
    else:
        status = "FAIL"
    chance = None
    if b is not None and avail:
        # A section 4, information only: each reference window taken as 3 weeks
        pr1 = 1.0 - (1.0 - b) ** 3
        na, nm = len(avail), len(matched)
        chance = float(sum(math.comb(na, k) * pr1 ** k * (1 - pr1) ** (na - k) for k in range(nm, na + 1)))
    f = lambda x: None if np.isnan(x) else float(x)
    diag = []
    for r in REFERENCES:
        for t in range(nw):
            if abs((week_end[t] - r).days) <= 10:
                diag.append(dict(reference=r.isoformat(), week_end=week_end[t].isoformat(),
                                 z=f(sig["z"][t]), W=f(Ww[t]), L=f(Lw[t]), D=bool(D[t])))
    out = dict(gate=dict(status=status, available=[r.isoformat() for r in avail], matched=matched,
                         n_available=len(avail), n_matched=len(matched),
                         base_rate=b, n_signal_evaluable=nev, last_week_end=last.isoformat(),
                         chance_of_match_info_only=chance),
               gate_diagnostics=diag, n_weeks=nw, n_D=int(D.sum()), n_T=int((D & sig["C"]).sum()),
               D_weeks=[week_end[t].isoformat() for t in np.nonzero(D)[0]],
               T_weeks=[week_end[t].isoformat() for t in np.nonzero(D & sig["C"])[0]])
    if status == "PASS" or (force and nev):
        if status != "PASS":
            out["forced"] = True
        nd_dates, ndx = read_ndx(ndx_path)
        T = D & sig["C"]
        T2 = sig["D_nosign"] & sig["C"]
        out["primary"] = outcome_test(week_end, ev, T, nd_dates, ndx, 63, -0.10)
        out["secondary_21d_5pct"] = outcome_test(week_end, ev, T, nd_dates, ndx, 21, -0.05)
        out["secondary_no_sign_filter"] = outcome_test(week_end, ev, T2, nd_dates, ndx, 63, -0.10)
    else:
        out["primary"] = out["secondary_21d_5pct"] = out["secondary_no_sign_filter"] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--force-gate", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    st = stage_baskets(a.data)
    with open(os.path.join(a.out, "verify_baskets.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["period", "effective", "leg", "rank", "cusip", "symbol"])
        w.writerows(st["basket_rows"])
    spy_days, Wd, Ld, M, priced = stage_returns(a.data, st)
    week_end, Ww, Lw, Mw = weekly(spy_days, Wd, Ld, M)
    out = gate_and_test(week_end, Ww, Lw, Mw, os.path.join(a.data, "ndx.csv"), a.force_gate)
    out["baskets_summary"] = st["summary"]
    out["priced_share"] = priced
    with open(os.path.join(a.out, "verify.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    log("gate:", json.dumps(out["gate"]))
    if out["primary"]:
        log("primary:", {k: v for k, v in out["primary"].items() if k != "episodes"})


if __name__ == "__main__":
    main()
