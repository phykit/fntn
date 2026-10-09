#!/usr/bin/env python
"""verify.py: an independent implementation of the credit drift pilot, hypothesis H1.

Written from PREREG.md alone, as revised (sections 2 to 7, and S5 to S8, S11 and S12 of section 8).
The only things taken
from `cdlib` are the retrieval and hashing helpers named in IO_INTERFACE.md; every analytical step
below (month index, parsing, reconstruction, validation, issuer-month collapse, ranks, fifths,
statistics) is this file's own.

Publication constraint: nothing in this file prints or writes a row of either input, a per-security
value or a reconstructed stock return. Only aggregates leave the process.

usage: python verify.py --out <dir> [--pins <json file>]
exit code 0 on PASS, WEAK or FAIL; 2 on UNSCORABLE.

UNSCORABLE is returned only for what section 7.4 names (a hash that differs, a column used that is
absent, a duplicated key, a unit that is not decimal, a failed validation, fewer than 120 valid
months in the primary) and for the two further refusals section 2.2 writes down for a signal file
(any other column set; no rows). An input that cannot be keyed at all (a null date, a null cusip,
a month outside 1 to 12) is in neither list: it raises InputUnreadable and the process stops with
a traceback and exit code 1, which is none of the four states and cannot be mistaken for one.
"""
import argparse
import io
import json
import math
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import cdlib

# --------------------------------------------------------------------------------------------
# Constants of the specification
# --------------------------------------------------------------------------------------------

SIGNAL_NAMES = ("MomSeasonShort", "Mom6m", "Mom12m")

# Section 2: the pins. Used when --pins is not given.
DEFAULT_PINS = {
    "panel_zip_sha256": "bfcd509a923d34950318732171f571dbd202b05778048ce67121e5cf53c1e96f",
    "panel_member": "main_panel_2026.parquet",
    "panel_member_sha256": "64bf67fc6eeb5b89323576e024da436a7f80d07ce9cdb6ba9f9808576cfd035a",
    "MomSeasonShort": "09e494a3da4041e53c9efcb3f9c7b269fef0967cd8010804b5a6f04c44e39d6d",
    "Mom6m": "7b1ee9dc26a477719423780e9e016dceb6880b5eabcb23ab625447178a105911",
    "Mom12m": "a5fef64b62bf64ae1babc66aa1d9483f6142dadac132f86ff0e53d081564d7ec",
}
# Section 2.1, "Columns used". The published shape (rows, columns, date range, byte counts) is not
# tested: section 7.4 as revised names the hash, an absent column and a duplicated key, and a file
# with the pinned hash has the published shape already.
PANEL_COLUMNS = ["cusip", "date", "permno", "country", "spc_rat", "ret_vw", "tret", "mcap_s", "cs"]
PANEL_READ_NOT_USED = "ret_type"   # "is read and not used": read where present, never required

KM = 100000                 # key = id * KM + mi; mi is about 24,300 so there is ample headroom
MI_START = 12 * 2002 + 7    # 2002-08 (section 3.3)

TOL = 0.001                 # section 3.3
SHARE_MIN = 0.99
ROWS_MIN = 1000
COMPARABLE_MIN = 0.90
GUARD = 0.01                # section 3.2, both guards

N_MIN = 100                 # section 5.3
FIFTH_OUT_MIN = 10
VALID_MONTHS_MIN = 120
NW_LAG = 3                  # section 6.2
FM_N_MIN = 50               # section 6.3
COST_RATE = 0.0025          # section 6.4
IMPUTE = -0.30              # section 6.6


class Unscorable(Exception):
    """Section 7.4: a state with a reason, never a pass and never a fail."""

    def __init__(self, reason, detail=""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class InputUnreadable(Exception):
    """An input that cannot be keyed. Section 7.4 does not name it, so it is not dressed as
    UNSCORABLE: it stops the process. It cannot arise on a file with a pinned hash."""


# --------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------

def mi_to_yyyymm(mi):
    mi = int(mi)
    return (mi // 12) * 100 + (mi % 12) + 1


def lookup(sorted_keys, query):
    """Positions of `query` in `sorted_keys` (unique, ascending). Returns (found, position)."""
    query = np.asarray(query)
    if len(sorted_keys) == 0:
        return np.zeros(len(query), dtype=bool), np.zeros(len(query), dtype=np.int64)
    pos = np.searchsorted(sorted_keys, query)
    pos = np.minimum(pos, len(sorted_keys) - 1)
    return sorted_keys[pos] == query, pos


def median_abs(values):
    v = np.asarray(values, dtype=np.float64)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return float("nan")
    return float(np.median(np.abs(v)))


def classify_unit(m, kind):
    """Section 2.3. Returns 'decimal', 'percent' or 'refuse'."""
    lo, hi = (0.05, 0.2) if kind == "bond" else (0.3, 1.0)
    if m < lo:
        return "decimal"
    if m > hi:
        return "percent"
    return "refuse"


def newey_west(x, lag=NW_LAG):
    """Section 6.2: mean, Bartlett-weighted variance at the given lag, t. No small-sample
    correction and no pre-whitening. Observations are treated as consecutive. Where T < L + 2 or
    V is not positive, t is undefined (NaN here, null in the output) and no criterion that needs
    it can be met."""
    x = np.asarray(x, dtype=np.float64)
    T = len(x)
    if T == 0:
        return float("nan"), float("nan")
    m = float(x.sum() / T)
    if T < lag + 2:
        return m, float("nan")
    d = x - m
    V = float(np.dot(d, d) / T)
    for j in range(1, lag + 1):
        gamma_j = float(np.dot(d[j:], d[:-j]) / T)
        V += 2.0 * (1.0 - j / (lag + 1.0)) * gamma_j
    if not (V > 0.0):
        return m, float("nan")
    se = math.sqrt(V / T)
    return m, m / se


def assign_fifths(mi, permno, signal):
    """Section 5.2. Within each month: ascending by signal, ties by permno ascending, k = 1..N,
    fifth = floor(5 (k - 1) / N) + 1. Integer arithmetic throughout, so there is no rounding."""
    n = len(mi)
    order = np.lexsort((permno, signal, mi))
    mi_s = mi[order]
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    starts = np.concatenate(([0], np.flatnonzero(mi_s[1:] != mi_s[:-1]) + 1))
    counts = np.diff(np.concatenate((starts, [n])))
    k0 = np.arange(n, dtype=np.int64) - np.repeat(starts, counts)
    N = np.repeat(counts, counts).astype(np.int64)
    fifth_s = (5 * k0) // N + 1
    fifth = np.empty(n, dtype=np.int64)
    fifth[order] = fifth_s
    return fifth


def scaled_rank(values, permno):
    """Section 6.3: rank ascending, ties by permno, k = 1..n, scaled (k - 1) / (n - 1) - 0.5."""
    n = len(values)
    order = np.lexsort((permno, values))
    k0 = np.empty(n, dtype=np.float64)
    k0[order] = np.arange(n, dtype=np.float64)
    return k0 / (n - 1.0) - 0.5


# --------------------------------------------------------------------------------------------
# Section 2: retrieval, pins, units
# --------------------------------------------------------------------------------------------

def load_inputs(pins, tmp_root):
    """Returns (panel DataFrame, {signal name: {"key", "value"}}, a few aggregate facts). Finding
    no bytes under a pinned name is treated as finding other bytes (section 2's first sentence)."""
    rel = cdlib.release_assets(os.environ.get("GH_TOKEN"))
    asset = None
    for a in rel["assets"]:
        if a["name"] == cdlib.OSBAP_ASSET:
            asset = a
            break
    if asset is None:
        raise Unscorable("panel_asset_absent", "release has no asset named %s" % cdlib.OSBAP_ASSET)

    dest = os.path.join(tmp_root, "panel.zip")
    cdlib.download_to(asset["url"], dest)
    zip_sha = cdlib.sha256_file(dest)
    if zip_sha != pins["panel_zip_sha256"]:
        raise Unscorable("panel_archive_hash_mismatch",
                         "got %s, pinned %s" % (zip_sha, pins["panel_zip_sha256"]))

    ex_dir = os.path.join(tmp_root, "extracted")
    os.makedirs(ex_dir, exist_ok=True)
    members = cdlib.extract_parquet_members(dest, ex_dir)
    hits = [m for m in members if m[0] == pins["panel_member"]]
    if len(hits) != 1:
        hits = [m for m in members
                if m[0].replace("\\", "/").split("/")[-1] == pins["panel_member"]]
    if len(hits) != 1:
        raise Unscorable("panel_member_absent",
                         "archive has %d members matching %s" % (len(hits), pins["panel_member"]))
    member_path = hits[0][1]
    member_sha = cdlib.sha256_file(member_path)
    if member_sha != pins["panel_member_sha256"]:
        raise Unscorable("panel_member_hash_mismatch",
                         "got %s, pinned %s" % (member_sha, pins["panel_member_sha256"]))

    pf = pq.ParquetFile(member_path)
    names = list(pf.schema_arrow.names)
    missing = [c for c in PANEL_COLUMNS if c not in names]
    if missing:
        raise Unscorable("panel_column_absent", "columns absent: %s" % ", ".join(missing))
    facts = {"panel_rows": int(pf.metadata.num_rows), "panel_columns": len(names)}
    extra = [PANEL_READ_NOT_USED] if PANEL_READ_NOT_USED in names else []
    panel = pf.read(columns=PANEL_COLUMNS + extra).to_pandas()
    if extra:
        panel = panel.drop(columns=extra)  # read and not used
    del pf

    signals = {}
    client = cdlib.new_osap_client()
    for name in SIGNAL_NAMES:
        body, _file_id = cdlib.fetch_signal_bytes(name, client)
        sha = cdlib.sha256_bytes(body)
        if sha != pins[name]:
            raise Unscorable("signal_hash_mismatch", "%s: got %s, pinned %s" % (name, sha, pins[name]))
        df = pd.read_csv(io.BytesIO(body))
        del body
        signals[name] = parse_signal(df, name)
    return panel, signals, facts


def _as_int_array(series, what):
    a = series.to_numpy()
    if a.dtype.kind in "iu":
        return a.astype(np.int64)
    try:
        f = a.astype(np.float64)
    except (TypeError, ValueError):
        raise InputUnreadable("%s is not numeric" % what)
    if np.isnan(f).any() or not np.array_equal(f, np.round(f)):
        raise InputUnreadable("%s is null or not an integer" % what)
    return f.astype(np.int64)


def parse_signal(df, name):
    """Section 2.2 as revised. Rows whose signal is null are dropped FIRST; the emptiness and
    duplicate tests are then made on what is left, and from here on a signal row means a row whose
    signal is not null. The column set has to be tested before the drop, because there is nothing
    to drop from a file that lacks the column."""
    if len(df.columns) != 3 or set(df.columns) != {"permno", "yyyymm", name}:
        raise Unscorable("signal_column_set", "%s: column set is not permno, yyyymm, %s" % (name, name))
    try:
        value = pd.to_numeric(df[name], errors="raise").to_numpy(dtype=np.float64, na_value=np.nan)
    except (TypeError, ValueError):
        raise InputUnreadable("%s: signal is not numeric" % name)
    keep = ~np.isnan(value)
    df = df.loc[keep]
    value = value[keep]
    if len(value) == 0:
        raise Unscorable("signal_no_rows", "%s: no rows with a signal" % name)
    permno = _as_int_array(df["permno"], "%s.permno" % name)
    yyyymm = _as_int_array(df["yyyymm"], "%s.yyyymm" % name)
    year = yyyymm // 100
    month = yyyymm % 100
    if (month < 1).any() or (month > 12).any() or (permno < 0).any():
        raise InputUnreadable("%s: yyyymm or permno out of range" % name)
    mi = 12 * year + (month - 1)
    if mi.max() + 2 >= KM or mi.min() - 12 < 0:
        raise InputUnreadable("%s: month out of range" % name)
    key = permno * KM + mi
    order = np.argsort(key, kind="stable")
    key = key[order]
    value = value[order]
    if len(key) > 1 and (key[1:] == key[:-1]).any():
        raise Unscorable("signal_key_duplicated", "%s: duplicated (permno, yyyymm)" % name)
    return {"key": key, "value": value}


# --------------------------------------------------------------------------------------------
# Section 3.2: reconstruction
# --------------------------------------------------------------------------------------------

def reconstruct(sig):
    """Returns a dict with the recovered returns as three aligned arrays sorted by key:
    key (permno * KM + mi), r, src (0 for a seed, 1 for a rolled value); and the step-2 candidate
    arrays, which the validation reuses."""
    ks, vs = sig["MomSeasonShort"]["key"], sig["MomSeasonShort"]["value"]
    k6, v6 = sig["Mom6m"]["key"], sig["Mom6m"]["value"]

    # Step 1. For every month t with a MomSeasonShort row, r(t - 11) = MomSeasonShort(t).
    # Subtracting 11 from a sorted unique key keeps it sorted and unique.
    known_k = ks - 11
    known_v = vs.copy()
    known_s = np.zeros(len(known_k), dtype=np.int8)

    # Step 2 candidates: months t at which Mom6m has rows at both t and t + 1.
    has_next, pos_next = lookup(k6, k6 + 1)
    cand_k = k6[has_next]
    cand_mt = v6[has_next]
    cand_mt1 = v6[pos_next[has_next]]
    cand_guard1 = (1.0 + cand_mt) >= GUARD

    passes = 0
    added_total = 0
    while True:
        already, _ = lookup(known_k, cand_k)
        f5, p5 = lookup(known_k, cand_k - 5)
        r5 = np.where(f5, known_v[p5] if len(known_v) else 0.0, np.nan)
        ok = (~already) & cand_guard1 & f5 & ((1.0 + r5) >= GUARD)
        n_new = int(ok.sum())
        if n_new == 0:
            break
        passes += 1
        added_total += n_new
        new_k = cand_k[ok]
        new_v = (1.0 + r5[ok]) * (1.0 + cand_mt1[ok]) / (1.0 + cand_mt[ok]) - 1.0
        known_k = np.concatenate((known_k, new_k))
        known_v = np.concatenate((known_v, new_v))
        known_s = np.concatenate((known_s, np.ones(n_new, dtype=np.int8)))
        order = np.argsort(known_k, kind="stable")
        known_k, known_v, known_s = known_k[order], known_v[order], known_s[order]

    return {"key": known_k, "r": known_v, "src": known_s, "passes": passes, "rolled": added_total,
            "cand_k": cand_k, "cand_mt": cand_mt, "cand_mt1": cand_mt1, "cand_guard1": cand_guard1}


def listing_terms(sig):
    """Section 3.2's three terms: the listed set, L(p) and E. Listed at t means a row in any of
    the three signals at t and nothing else. A recovered return at t is NOT evidence of listing:
    in a stock's first five listed months it is known only from MomSeasonShort eleven months
    later, so admitting it would make eligibility depend on survival to t + 11 (section 5.1)."""
    sig_keys = np.unique(np.concatenate([sig[n]["key"] for n in SIGNAL_NAMES]))
    listed_keys = sig_keys
    permno = sig_keys // KM
    mi = sig_keys % KM
    # sig_keys is sorted, so the last row of each permno block is its last month
    last = np.concatenate((np.flatnonzero(permno[1:] != permno[:-1]), [len(permno) - 1]))
    L_permno = permno[last]
    L_mi = mi[last]
    E = int(L_mi.max())
    return listed_keys, L_permno, L_mi, E


# --------------------------------------------------------------------------------------------
# Section 3.3: validation
# --------------------------------------------------------------------------------------------

def validate(sig, rec, H):
    """H is the sorted array of permnos with hy_share >= 0.5 in at least one issuer-month of the
    panel, in any month, listed or not. The 2002-08 restriction is on the row's own month t; the
    eleven returns behind a V1 row may be earlier."""
    known_k, known_v, known_s = rec["key"], rec["r"], rec["src"]
    out = {}

    # V1
    k12, v12 = sig["Mom12m"]["key"], sig["Mom12m"]["value"]
    p12 = k12 // KM
    m12 = k12 % KM
    inH, _ = lookup(H, p12)
    sel = inH & (m12 >= MI_START)
    kq = k12[sel]
    published = v12[sel]
    n_pub = int(len(kq))
    comparable = np.ones(n_pub, dtype=bool)
    any_rolled = np.zeros(n_pub, dtype=bool)
    prod = np.ones(n_pub, dtype=np.float64)
    for lag in range(1, 12):
        f, p = lookup(known_k, kq - lag)
        comparable &= f
        any_rolled |= f & (known_s[p] == 1)
        prod *= np.where(f, 1.0 + known_v[p], 1.0)
    err = np.abs((prod - 1.0) - published)
    n_all = int(comparable.sum())
    rolled = comparable & any_rolled
    n_rolled = int(rolled.sum())
    out["v1_all_n"] = n_all
    out["v1_all_share"] = float((err[comparable] <= TOL).sum() / n_all) if n_all else float("nan")
    out["v1_rolled_n"] = n_rolled
    out["v1_rolled_share"] = float((err[rolled] <= TOL).sum() / n_rolled) if n_rolled else float("nan")
    out["v1_comparable_share"] = float(n_all / n_pub) if n_pub else float("nan")
    out["_v1_published_n"] = n_pub
    out["_v1_max_err"] = float(err[comparable].max()) if n_all else float("nan")

    # V2: (p, t) whose return is a seed, step 2's inputs exist, both guards hold, r(t-5) a seed.
    ck = rec["cand_k"]
    f0, p0 = lookup(known_k, ck)
    f5, p5 = lookup(known_k, ck - 5)
    r5 = np.where(f5, known_v[p5], np.nan)
    inH2, _ = lookup(H, ck // KM)
    sel2 = (f0 & (known_s[p0] == 0) & f5 & (known_s[p5] == 0) & rec["cand_guard1"]
            & ((1.0 + r5) >= GUARD) & inH2 & ((ck % KM) >= MI_START))
    step2 = (1.0 + r5[sel2]) * (1.0 + rec["cand_mt1"][sel2]) / (1.0 + rec["cand_mt"][sel2]) - 1.0
    err2 = np.abs(known_v[p0[sel2]] - step2)
    n2 = int(sel2.sum())
    out["v2_n"] = n2
    out["v2_share"] = float((err2 <= TOL).sum() / n2) if n2 else float("nan")
    out["_v2_max_err"] = float(err2.max()) if n2 else float("nan")
    return out


def validation_failure(v):
    """Returns None when every threshold of section 3.3 holds, else a description."""
    fails = []
    for label, share, n in (("V1 all", v["v1_all_share"], v["v1_all_n"]),
                            ("V1 rolled", v["v1_rolled_share"], v["v1_rolled_n"]),
                            ("V2", v["v2_share"], v["v2_n"])):
        if n < ROWS_MIN:
            fails.append("%s: %d rows, below %d" % (label, n, ROWS_MIN))
        elif not (share >= SHARE_MIN):
            fails.append("%s: share %.6f below %.2f" % (label, share, SHARE_MIN))
    if not (v["v1_comparable_share"] >= COMPARABLE_MIN):
        fails.append("V1 comparable share %r below %.2f" % (v["v1_comparable_share"], COMPARABLE_MIN))
    return "; ".join(fails) if fails else None


# --------------------------------------------------------------------------------------------
# Section 4: bond side
# --------------------------------------------------------------------------------------------

def build_issuer_months(panel):
    """Returns the issuer-month table as a dict of aligned arrays sorted by key, the two
    bond-return unit medians and a few aggregate counts. Section 2.5: every 32-bit column is
    widened to 64 bits before any subtraction, product or sum."""
    n = len(panel)
    if n == 0:
        raise InputUnreadable("panel has no rows")
    date = pd.to_datetime(panel["date"])
    if date.isna().any():
        raise InputUnreadable("panel has a null date")
    year = date.dt.year.to_numpy().astype(np.int64)
    month = date.dt.month.to_numpy().astype(np.int64)
    mi = 12 * year + (month - 1)

    codes, _uniq = pd.factorize(panel["cusip"])
    codes = np.asarray(codes, dtype=np.int64)
    if (codes < 0).any():
        raise InputUnreadable("panel has a null cusip")
    ckey = codes * KM + mi
    if len(np.unique(ckey)) != n:
        raise Unscorable("panel_key_duplicated", "duplicated (cusip, month)")

    ret_vw = panel["ret_vw"].to_numpy(dtype=np.float64, na_value=np.nan)
    tret = panel["tret"].to_numpy(dtype=np.float64, na_value=np.nan)
    mcap = panel["mcap_s"].to_numpy(dtype=np.float64, na_value=np.nan)
    cs = panel["cs"].to_numpy(dtype=np.float64, na_value=np.nan)
    spc = panel["spc_rat"].to_numpy(dtype=np.float64, na_value=np.nan)
    permno_f = panel["permno"].to_numpy(dtype=np.float64, na_value=np.nan)

    # Section 2.3, on every non-null value of the column as published.
    units = {"ret_vw": median_abs(ret_vw), "tret": median_abs(tret)}
    for col, m in units.items():
        u = classify_unit(m, "bond")
        if u != "decimal":
            raise Unscorable("unit_not_decimal", "%s: median absolute value %r classifies as %s" % (col, m, u))

    # Section 4.1.
    is_usa = (panel["country"] == "USA").fillna(False).to_numpy(dtype=bool)
    keep = (is_usa & ~np.isnan(permno_f) & ~np.isnan(ret_vw) & ~np.isnan(tret)
            & ~np.isnan(mcap) & (mcap > 0) & ((spc == 1.0) | (spc == 11.0)))
    pf = permno_f[keep]
    if not np.array_equal(pf, np.round(pf)) or (pf < 0).any():
        raise InputUnreadable("panel permno is not a non-negative integer")
    permno = pf.astype(np.int64)
    f_mi = mi[keep]
    w = mcap[keep]
    excess = ret_vw[keep] - tret[keep]
    is_hy = (spc[keep] == 11.0)
    f_cs = cs[keep]
    f_codes = codes[keep]

    # DCS, section 4.2 as revised: numerator and denominator over the SAME bonds, the filtered
    # bonds at t with cs present at t and cs present in the previous calendar month for the same
    # cusip; that earlier row need not pass the filter.
    has_cs = ~np.isnan(cs)
    cs_keys = ckey[has_cs]
    cs_vals = cs[has_cs]
    o = np.argsort(cs_keys, kind="stable")
    cs_keys, cs_vals = cs_keys[o], cs_vals[o]
    fprev, pprev = lookup(cs_keys, f_codes * KM + (f_mi - 1))
    qual = (~np.isnan(f_cs)) & fprev
    dcs_num = np.where(qual, w * (f_cs - np.where(fprev, cs_vals[pprev], 0.0)), 0.0)
    dcs_den = np.where(qual, w, 0.0)

    ikey = permno * KM + f_mi
    g = pd.DataFrame({
        "key": ikey,
        "w": w,
        "wx": w * excess,
        "whi": np.where(is_hy, w, 0.0),
        "dnum": dcs_num,
        "dden": dcs_den,
        "dq": qual.astype(np.int64),
    }).groupby("key", sort=True).sum()
    key = g.index.to_numpy().astype(np.int64)
    bond_value = g["w"].to_numpy()
    cr = g["wx"].to_numpy() / bond_value
    hy_share = g["whi"].to_numpy() / bond_value
    dq = g["dq"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        dcs = np.where(dq > 0, g["dnum"].to_numpy() / g["dden"].to_numpy(), np.nan)

    im = {"key": key, "permno": key // KM, "mi": key % KM, "CR": cr, "hy_share": hy_share,
          "bond_value": bond_value, "DCS": dcs}
    counts = {"panel_rows": n, "filtered_rows": int(keep.sum()), "issuer_months": int(len(key)),
              "first_month": mi_to_yyyymm(mi.min()), "last_month": mi_to_yyyymm(mi.max())}
    return im, units, counts


# --------------------------------------------------------------------------------------------
# Sections 5 and 6: one long-short analysis
# --------------------------------------------------------------------------------------------

class Analysis:
    """A set of eligible issuer-months with a signal: fifths are assigned once, before any outcome
    is consulted, and every outcome vector is then scored against those same fifths."""

    def __init__(self, mi, permno, signal):
        self.mi = mi
        self.permno = permno
        self.signal = signal
        self.fifth = assign_fifths(mi, permno, signal)
        self.months = np.unique(mi)
        self.idx = np.searchsorted(self.months, mi)
        self.N = np.bincount(self.idx, minlength=len(self.months))

    def series(self, y):
        """Per month: valid flag, LS, top mean, bottom mean, universe mean."""
        nm = len(self.months)
        has = ~np.isnan(y)
        yz = np.where(has, y, 0.0)

        def part(mask):
            m = mask & has
            cnt = np.bincount(self.idx[m], minlength=nm)
            tot = np.bincount(self.idx[m], weights=yz[m], minlength=nm)
            with np.errstate(invalid="ignore", divide="ignore"):
                mean = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
            return cnt, mean

        n_top, top = part(self.fifth == 5)
        n_bot, bot = part(self.fifth == 1)
        n_all, univ = part(np.ones(len(y), dtype=bool))
        valid = (self.N >= N_MIN) & (n_top >= FIFTH_OUT_MIN) & (n_bot >= FIFTH_OUT_MIN)
        return {"valid": valid, "LS": top - bot, "top": top, "bot": bot, "univ": univ,
                "n_top": n_top, "n_bot": n_bot, "n_all": n_all}

    def costs(self):
        """Section 6.4: cost(t) for every month with eligible issuers. w(t-1, .) is the weight
        vector of the previous CALENDAR month (its top fifth, whether or not that month is valid),
        zero where that month has no eligible issuers, so the first month bears a full purchase.
        Members without an outcome carry weight here and none in the return."""
        tops = {}
        order = np.argsort(self.idx, kind="stable")
        bounds = np.concatenate(([0], np.cumsum(self.N)))
        for j, t in enumerate(self.months):
            rows = order[bounds[j]:bounds[j + 1]]
            tops[int(t)] = np.sort(self.permno[rows][self.fifth[rows] == 5])
        cost = np.zeros(len(self.months), dtype=np.float64)
        empty = np.zeros(0, dtype=np.int64)
        for j, t in enumerate(self.months):
            cur = tops[int(t)]
            prev = tops.get(int(t) - 1, empty)
            union = np.union1d(cur, prev)
            w_cur = np.where(np.isin(union, cur), 1.0 / len(cur), 0.0) if len(cur) else np.zeros(len(union))
            w_prev = np.where(np.isin(union, prev), 1.0 / len(prev), 0.0) if len(prev) else np.zeros(len(union))
            cost[j] = COST_RATE * float(np.abs(w_cur - w_prev).sum())
        return cost


def ls_stats(analysis, y):
    s = analysis.series(y)
    v = s["valid"]
    x = s["LS"][v]
    mean, t = newey_west(x)
    return {"mean": mean, "t": t, "months_valid": int(v.sum()), "x": x,
            "months": analysis.months[v], "series": s}


def fama_macbeth(mi, permno, cr, own, mom6, y):
    """Section 6.3. Inputs are the eligible issuer-months of the universe; `own`, `mom6` and `y`
    are NaN where absent. One regression per formation month with at least 50 complete rows."""
    ok = ~np.isnan(y) & ~np.isnan(own) & ~np.isnan(mom6)
    mi, permno, cr, own, mom6, y = mi[ok], permno[ok], cr[ok], own[ok], mom6[ok], y[ok]
    order = np.argsort(mi, kind="stable")
    mi, permno, cr, own, mom6, y = mi[order], permno[order], cr[order], own[order], mom6[order], y[order]
    if len(mi) == 0:
        return np.zeros(0), np.zeros(0, dtype=np.int64)
    starts = np.concatenate(([0], np.flatnonzero(mi[1:] != mi[:-1]) + 1, [len(mi)]))
    slopes, months = [], []
    for a, b in zip(starts[:-1], starts[1:]):
        n = b - a
        if n < FM_N_MIN:
            continue
        p = permno[a:b]
        X = np.column_stack((np.ones(n), scaled_rank(cr[a:b], p), scaled_rank(own[a:b], p),
                             scaled_rank(mom6[a:b], p)))
        beta = np.linalg.lstsq(X, y[a:b], rcond=None)[0]
        slopes.append(float(beta[1]))
        months.append(int(mi[a]))
    return np.array(slopes, dtype=np.float64), np.array(months, dtype=np.int64)


# --------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------

def clean(o):
    """JSON-safe: numpy scalars to Python, NaN and infinities to null, floats left unrounded."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return f if math.isfinite(f) else None
    return o


SECONDARY_KEYS = ("S5", "S6", "S7", "S8", "S11", "S12")


def empty_result():
    stat3 = {"mean": None, "t": None, "months_valid": None}
    return {
        "verdict": None,
        "refusal": None,
        "months_valid": None,
        "sample": {"eligible_issuer_months": None, "with_outcome": None, "lost_final_months": None,
                   "first_outcome_month": None, "last_outcome_month": None},
        "validation": {"v1_all_share": None, "v1_all_n": None, "v1_rolled_share": None,
                       "v1_rolled_n": None, "v2_share": None, "v2_n": None,
                       "v1_comparable_share": None},
        "a": {"met": None, "mean": None, "t": None},
        "b": {"met": None, "slope": None, "t": None, "months": None},
        "c": {"met": None, "first_half_mean": None, "second_half_mean": None},
        "d": {"met": None, "mean": None, "t": None, "gross_mean": None, "mean_cost": None},
        "e1": {"met": None, "mean": None, "months_valid": None},
        "e2": {"met": None, "mean": None, "months_valid": None},
        "secondary": {k: dict(stat3) for k in SECONDARY_KEYS},
        "monthly_long_short": [],
    }


def met(mean, t=None, t_min=None):
    if mean is None or not math.isfinite(mean) or not (mean > 0):
        return False
    if t_min is None:
        return True
    return t is not None and math.isfinite(t) and t >= t_min


# --------------------------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------------------------

def run(pins, tmp_root, result, log):
    panel, sig, facts = load_inputs(pins, tmp_root)
    log("inputs retrieved and hashes matched: panel %d rows, %d columns; signal rows %s" % (
        facts["panel_rows"], facts["panel_columns"],
        ", ".join("%s %d" % (n, len(sig[n]["key"])) for n in SIGNAL_NAMES)))

    # Section 2.3 for the stock side.
    m_stock = median_abs(sig["MomSeasonShort"]["value"])
    u = classify_unit(m_stock, "stock")
    if u != "decimal":
        raise Unscorable("unit_not_decimal", "MomSeasonShort: median absolute value %r classifies as %s" % (m_stock, u))

    im, units, counts = build_issuer_months(panel)
    del panel
    log("unit medians: ret_vw %.6f, tret %.6f, MomSeasonShort %.6f (all decimal)" % (
        units["ret_vw"], units["tret"], m_stock))
    log("bond side: months %d to %d; %d filtered bond-months of %d; %d issuer-months" % (
        counts["first_month"], counts["last_month"], counts["filtered_rows"], counts["panel_rows"],
        counts["issuer_months"]))

    rec = reconstruct(sig)
    listed_keys, L_permno, L_mi, E = listing_terms(sig)
    log("reconstruction: %d seeds, %d rolled in %d passes; stock file end %d" % (
        int((rec["src"] == 0).sum()), rec["rolled"], rec["passes"], mi_to_yyyymm(E)))

    hy = im["hy_share"] >= 0.5
    H = np.unique(im["permno"][hy])

    v = validate(sig, rec, H)
    for k in result["validation"]:
        result["validation"][k] = v[k]
    log("validation: V1 all %.6f on %d; V1 rolled %.6f on %d; V2 %.6f on %d; comparable %.6f of %d; "
        "largest errors V1 %.3g, V2 %.3g" % (
            v["v1_all_share"], v["v1_all_n"], v["v1_rolled_share"], v["v1_rolled_n"],
            v["v2_share"], v["v2_n"], v["v1_comparable_share"], v["_v1_published_n"],
            v["_v1_max_err"], v["_v2_max_err"]))
    why = validation_failure(v)
    if why is not None:
        raise Unscorable("validation_failed", why)

    # Section 5.1 on every issuer-month.
    key = im["key"]
    listed, _ = lookup(listed_keys, key)
    fy, py = lookup(rec["key"], key + 1)
    y = np.where(fy, rec["r"][py], np.nan)
    fo, po = lookup(rec["key"], key)
    own = np.where(fo, rec["r"][po], np.nan)
    f6, p6 = lookup(sig["Mom6m"]["key"], key)
    mom6 = np.where(f6, sig["Mom6m"]["value"][p6], np.nan)
    fL, pL = lookup(L_permno, im["permno"])
    L_of = np.where(fL, L_mi[pL], -1)
    lost = listed & np.isnan(y) & fL & (im["mi"] + 1 == L_of) & (L_of < E)

    def make(mask, signal):
        return Analysis(im["mi"][mask], im["permno"][mask], signal[mask])

    # ------------------------------------------------------------------ primary
    elig = hy & listed
    result["sample"]["eligible_issuer_months"] = int(elig.sum())
    result["sample"]["with_outcome"] = int((elig & ~np.isnan(y)).sum())
    result["sample"]["lost_final_months"] = int((elig & lost).sum())
    wo = elig & ~np.isnan(y)
    if wo.any():
        result["sample"]["first_outcome_month"] = mi_to_yyyymm(im["mi"][wo].min() + 1)
        result["sample"]["last_outcome_month"] = mi_to_yyyymm(im["mi"][wo].max() + 1)

    prim = make(elig, im["CR"])
    y_p = y[elig]
    lost_p = lost[elig]
    a = ls_stats(prim, y_p)
    T = a["months_valid"]
    result["months_valid"] = T
    log("sample: %d eligible high-yield issuer-months, %d with an outcome, %d lost final months; "
        "%d valid months" % (result["sample"]["eligible_issuer_months"],
                             result["sample"]["with_outcome"],
                             result["sample"]["lost_final_months"], T))
    if T < VALID_MONTHS_MIN:
        raise Unscorable("too_few_valid_months", "%d valid months, the floor is %d" % (T, VALID_MONTHS_MIN))

    # (a)
    result["a"] = {"met": met(a["mean"], a["t"], 3.0), "mean": a["mean"], "t": a["t"]}
    result["monthly_long_short"] = [[mi_to_yyyymm(m + 1), float(x)] for m, x in zip(a["months"], a["x"])]

    # (b)
    slopes, fm_months = fama_macbeth(prim.mi, prim.permno, prim.signal, own[elig], mom6[elig], y_p)
    b_mean, b_t = newey_west(slopes)
    result["b"] = {"met": met(b_mean, b_t, 2.0), "slope": b_mean, "t": b_t, "months": int(len(slopes))}

    # (c)
    n1 = int(math.ceil(T / 2.0))
    h1 = float(a["x"][:n1].mean()) if n1 > 0 else float("nan")
    h2 = float(a["x"][n1:].mean()) if T - n1 > 0 else float("nan")
    result["c"] = {"met": met(h1) and met(h2), "first_half_mean": h1, "second_half_mean": h2}

    # (d)
    s = a["series"]
    valid = s["valid"]
    cost = prim.costs()
    gross = (s["top"] - s["univ"])[valid]
    net = (s["top"] - cost - s["univ"])[valid]
    d_mean, d_t = newey_west(net)
    result["d"] = {"met": met(d_mean, d_t, 2.0), "mean": d_mean, "t": d_t,
                   "gross_mean": float(gross.mean()), "mean_cost": float(cost[valid].mean())}

    # (e1), (e2)
    y_e1 = np.where(lost_p & np.isnan(y_p), IMPUTE, y_p)
    y_e2 = np.where(lost_p & np.isnan(y_p) & (prim.fifth == 5), IMPUTE, y_p)
    e1 = ls_stats(prim, y_e1)
    e2 = ls_stats(prim, y_e2)
    result["e1"] = {"met": met(e1["mean"]), "mean": e1["mean"], "months_valid": e1["months_valid"]}
    result["e2"] = {"met": met(e2["mean"]), "mean": e2["mean"], "months_valid": e2["months_valid"]}

    # ------------------------------------------------------------------ secondary
    # No floor on the number of valid months applies to anything below (section 8 as revised).
    def secondary(mask, signal):
        an = make(mask, signal)
        st = ls_stats(an, y[mask])
        return {"mean": st["mean"], "t": st["t"], "months_valid": st["months_valid"]}

    result["secondary"]["S5"] = secondary((~hy) & listed, im["CR"])
    result["secondary"]["S6"] = secondary(listed, im["CR"])
    result["secondary"]["S7"] = secondary(elig & ~np.isnan(im["DCS"]), -im["DCS"])
    f1, p1 = lookup(key, key - 1)
    f2, p2 = lookup(key, key - 2)
    cr3 = np.where(f1 & f2, im["CR"] + np.where(f1, im["CR"][p1], 0.0) + np.where(f2, im["CR"][p2], 0.0), np.nan)
    result["secondary"]["S8"] = secondary(elig & f1 & f2, cr3)

    # S11, the widest adversarial bound: -0.30 for EVERY top-fifth member whose outcome is missing,
    # whatever the reason, with LS taken over the primary's valid months (not recomputed).
    y_s11 = np.where(np.isnan(y_p) & (prim.fifth == 5), IMPUTE, y_p)
    x11 = prim.series(y_s11)["LS"][valid]
    m11, t11 = newey_west(x11)
    result["secondary"]["S11"] = {"mean": m11, "t": t11, "months_valid": int(len(x11))}

    # S12, the long-only form under e2: section 6.4 with the e2 outcome vector in both of its
    # means (top fifth and universe), over e2's own valid months. Costs depend on the fifths
    # alone and are those of (d).
    s2 = e2["series"]
    v2 = s2["valid"]
    x12 = (s2["top"] - cost - s2["univ"])[v2]
    m12, t12 = newey_west(x12)
    result["secondary"]["S12"] = {"mean": m12, "t": t12, "months_valid": int(len(x12))}

    # ------------------------------------------------------------------ verdict
    all_met = all(result[k]["met"] for k in ("a", "b", "c", "d", "e1", "e2"))
    if all_met:
        result["verdict"] = "PASS"
    elif met(a["mean"], a["t"], 2.0):
        result["verdict"] = "WEAK"
    else:
        result["verdict"] = "FAIL"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pins", default=None)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)

    result = empty_result()
    lines = []

    def log(msg):
        lines.append(msg)
        print(msg, flush=True)

    tmp_root = None
    try:
        if args.pins:
            with open(args.pins) as fh:
                pins = json.load(fh)
            need = set(DEFAULT_PINS)
            if not isinstance(pins, dict) or not need.issubset(pins):
                raise ValueError("pins file lacks one of: %s" % ", ".join(sorted(need)))
        else:
            pins = dict(DEFAULT_PINS)
        base = os.environ.get("RUNNER_TEMP") or None
        tmp_root = tempfile.mkdtemp(prefix="verify_", dir=base)
        run(pins, tmp_root, result, log)
    except Unscorable as e:
        result["verdict"] = "UNSCORABLE"
        result["refusal"] = {"reason": e.reason, "detail": e.detail}
    except cdlib.Refusal as e:
        reason = getattr(e, "reason", None) or (str(e.args[0]) if e.args else "refusal")
        detail = getattr(e, "detail", None)
        if detail is None:
            detail = str(e.args[1]) if len(e.args) > 1 else ""
        result["verdict"] = "UNSCORABLE"
        result["refusal"] = {"reason": str(reason), "detail": str(detail)}
    finally:
        if tmp_root is not None:
            shutil.rmtree(tmp_root, ignore_errors=True)

    if result["verdict"] == "UNSCORABLE":
        # Section 7.4: a reason and no test statistics. The counts and the validation shares
        # that explain the refusal are kept; every test statistic is null.
        blank = empty_result()
        for k in ("a", "b", "c", "d", "e1", "e2", "secondary", "monthly_long_short"):
            result[k] = blank[k]

    out_path = os.path.join(args.out, "verify.json")
    with open(out_path, "w") as fh:
        json.dump(clean(result), fh, indent=1, allow_nan=False)
        fh.write("\n")

    print("")
    print("verdict: %s" % result["verdict"])
    if result["refusal"]:
        print("refusal: %s (%s)" % (result["refusal"]["reason"], result["refusal"]["detail"]))
    else:
        r = clean(result)

        def f(x, spec="%+.6f"):
            return "n/a" if x is None else spec % x

        print("valid months: %s" % r["months_valid"])
        print("(a)  long-short     mean %s  t %s  met %s" % (f(r["a"]["mean"]), f(r["a"]["t"], "%+.3f"), r["a"]["met"]))
        print("(b)  Fama-MacBeth   slope %s  t %s  months %s  met %s" % (
            f(r["b"]["slope"]), f(r["b"]["t"], "%+.3f"), r["b"]["months"], r["b"]["met"]))
        print("(c)  halves         first %s  second %s  met %s" % (
            f(r["c"]["first_half_mean"]), f(r["c"]["second_half_mean"]), r["c"]["met"]))
        print("(d)  long-only net  mean %s  t %s  gross %s  cost %s  met %s" % (
            f(r["d"]["mean"]), f(r["d"]["t"], "%+.3f"), f(r["d"]["gross_mean"]),
            f(r["d"]["mean_cost"], "%.6f"), r["d"]["met"]))
        print("(e1) symmetric      mean %s  months %s  met %s" % (
            f(r["e1"]["mean"]), r["e1"]["months_valid"], r["e1"]["met"]))
        print("(e2) adversarial    mean %s  months %s  met %s" % (
            f(r["e2"]["mean"]), r["e2"]["months_valid"], r["e2"]["met"]))
        for k in SECONDARY_KEYS:
            sv = r["secondary"][k]
            print("%-4s (secondary)   mean %s  t %s  months %s" % (
                k, f(sv["mean"]), f(sv["t"], "%+.3f"), sv["months_valid"]))
    print("written: %s" % out_path)
    return 2 if result["verdict"] == "UNSCORABLE" else 0


if __name__ == "__main__":
    sys.exit(main())
