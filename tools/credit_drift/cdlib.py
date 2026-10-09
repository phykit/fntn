"""Shared plumbing for the credit-drift pilot: download, hashing, reconstruction, universe, linkage.

NON-EVIDENTIARY side test, outside the FNTN funnel. See docs/CREDIT_DRIFT_2026-10-09.md.

Why one module: the probe and the frozen test must read the inputs, rebuild the stock returns and
join bonds to stocks in exactly the same way, or the probe's coverage figures describe a different
population from the one the test scores. Everything here is deterministic arithmetic over the two
published inputs. Nothing here relates a signal to an outcome.

Two rules this module keeps, and why:

1. It refuses rather than defaults. A missing column, an empty download, a duplicated key or a
   unit it cannot classify raises `Refusal`; no caller may substitute a working value, because a
   test scored on a silently repaired input reports a number about some other input.
2. Reconstructed stock returns never leave memory. The open release withholds raw returns, and the
   series rebuilt here is equivalent to them, so no function writes them to disk, to a log or to a
   result file. Callers publish derived statistics only.
"""
import hashlib
import io
import os
import time
import zipfile

import numpy as np
import pandas as pd

UA = {"User-Agent": "phykit-fntn credit-drift pilot (research; github.com/phykit/fntn)"}

OSAP_RELEASE = 202510
SIGNALS = ("MomSeasonShort", "Mom6m", "Mom12m")
OSBAP_REPO = "Alexander-M-Dickerson/osbap-site"
OSBAP_TAG = "data-2026"
OSBAP_ASSET = "osbap_main_data_2026.zip"
PANEL_REQUIRED = ["cusip", "date", "permno", "country", "ret_type", "spc_rat", "ret_vw", "tret", "mcap_s", "cs"]
US_COUNTRY = "USA"
HY_CODE = 11
IG_CODE = 1
KEY_BASE = 100000          # key = permno * KEY_BASE + month index; month index < 100000 by construction
GUARD = 0.01               # a roll-forward step is refused where 1 + Mom6m(t) or 1 + r(t-5) is below this
MAX_PASSES = 12


class Refusal(Exception):
    """A refusal to proceed, with a plain-language reason. Never caught to substitute a default."""

    def __init__(self, reason, detail=""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


# ---------------------------------------------------------------------------------------------
# hashing and months
# ---------------------------------------------------------------------------------------------

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def mi_from_yyyymm(yyyymm):
    """Month index: year * 12 + (month - 1). Consecutive calendar months differ by exactly 1."""
    y = np.asarray(yyyymm, dtype="int64")
    return (y // 100) * 12 + (y % 100) - 1


def yyyymm_from_mi(mi):
    m = np.asarray(mi, dtype="int64")
    return (m // 12) * 100 + (m % 12) + 1


def mi_from_dates(dates):
    d = pd.to_datetime(pd.Series(dates).reset_index(drop=True))
    if d.isna().any():
        raise Refusal("date_unparseable", f"{int(d.isna().sum())} rows")
    return (d.dt.year.to_numpy(dtype="int64") * 12 + d.dt.month.to_numpy(dtype="int64") - 1)


# ---------------------------------------------------------------------------------------------
# downloads (network; exercised on the runner only)
# ---------------------------------------------------------------------------------------------

def release_assets(token=None):
    """The asset list of the bond-data release, from the GitHub API. Read-only."""
    import requests
    h = dict(UA)
    h["Accept"] = "application/vnd.github+json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.get(f"https://api.github.com/repos/{OSBAP_REPO}/releases/tags/{OSBAP_TAG}", headers=h, timeout=60)
    if r.status_code != 200:
        raise Refusal("release_listing_unavailable", f"HTTP {r.status_code}")
    j = r.json()
    assets = [{"name": a.get("name"), "size": a.get("size"), "digest": a.get("digest"),
               "updated_at": a.get("updated_at"), "url": a.get("browser_download_url")} for a in j.get("assets", [])]
    if not assets:
        raise Refusal("release_has_no_assets", OSBAP_TAG)
    return {"tag": j.get("tag_name"), "published_at": j.get("published_at"), "target": j.get("target_commitish"), "assets": assets}


def download_to(url, dest, token=None, timeout=1800):
    """Stream a URL to a file. Returns (size in bytes, SHA-256). Refuses on any HTTP error."""
    import requests
    h = dict(UA)
    t0 = time.time()
    with requests.get(url, headers=h, timeout=timeout, stream=True, allow_redirects=True) as r:
        if r.status_code != 200:
            raise Refusal("download_failed", f"HTTP {r.status_code} for {url}")
        hh = hashlib.sha256()
        n = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                hh.update(chunk)
                n += len(chunk)
    if n == 0:
        raise Refusal("download_empty", url)
    return n, hh.hexdigest(), time.time() - t0


def fetch_signal_bytes(name, client):
    """The raw bytes of one individual-signal CSV from the pinned Open Source Asset Pricing release.

    Why not `client.dl_signal`: that method wraps its work in a bare `except` which prints a message
    and can hand back an empty or partial frame, and it gives the caller no bytes to hash. Fetching
    the same address directly lets the file be pinned by SHA-256 and lets every failure raise.
    """
    import requests
    from openassetpricing.gdrive_parse import _get_readable_link
    url = client._get_individual_signal_url(name)
    if not isinstance(url, str) or "drive.google.com" not in url:
        raise Refusal("signal_address_unavailable", name)
    file_id = url.split("id=")[-1]
    sess = requests.Session()
    sess.headers.update(UA)
    last = None
    for attempt in range(4):
        r = sess.get(url, timeout=900)
        last = r.status_code
        body = r.content
        head = body[:200].lstrip().lower()
        if r.status_code == 200 and not (head.startswith(b"<!doctype") or head.startswith(b"<html")):
            return body, file_id
        if r.status_code == 200:
            # Google Drive served its confirmation page; resolve the direct link once and retry.
            try:
                url = _get_readable_link(url)
                continue
            except Exception as e:  # the page was an error page (quota, permissions): refuse below
                last = f"confirmation page unresolved: {e!r}"
        time.sleep(20 * (attempt + 1))
    raise Refusal("signal_download_failed", f"{name}: {last}")


def parse_signal(name, body):
    """One signal as a frame of exactly permno, yyyymm, <name>, nulls dropped, keys unique."""
    df = pd.read_csv(io.BytesIO(body))
    if set(df.columns) != {"permno", "yyyymm", name}:
        raise Refusal("signal_columns_unexpected", f"{name}: {list(df.columns)}")
    if len(df) == 0:
        raise Refusal("signal_empty", name)
    df = df[["permno", "yyyymm", name]]
    n_null = int(df[name].isna().sum())
    df = df[df[name].notna()].copy()
    df["permno"] = df["permno"].astype("int64")
    df["yyyymm"] = df["yyyymm"].astype("int64")
    df[name] = df[name].astype("float64")
    if df.duplicated(["permno", "yyyymm"]).any():
        raise Refusal("signal_keys_duplicated", name)
    if not ((df["yyyymm"] % 100).between(1, 12).all() and (df["yyyymm"] // 100).between(1900, 2100).all()):
        raise Refusal("signal_yyyymm_out_of_range", name)
    return df, n_null


def new_osap_client():
    import openassetpricing as oap
    return oap.OpenAP(OSAP_RELEASE)


def extract_parquet_members(zip_path, dest_dir):
    """Extract every .parquet member of the archive. Returns [(member name, path, uncompressed size)]."""
    out = []
    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()
        for i in infos:
            if i.filename.lower().endswith(".parquet") and not i.is_dir():
                p = z.extract(i, dest_dir)
                out.append((i.filename, p, i.file_size))
    return out


def zip_listing(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return [{"name": i.filename, "size": i.file_size, "compressed": i.compress_size} for i in z.infolist()]


def read_panel(path, columns):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    names = pf.schema_arrow.names
    missing = [c for c in columns if c not in names]
    if missing:
        raise Refusal("panel_columns_missing", f"{missing}")
    return pf.read(columns=list(columns)).to_pandas()


# ---------------------------------------------------------------------------------------------
# units
# ---------------------------------------------------------------------------------------------

def unit_of(values, what):
    """Classify a return series as 'decimal' or 'percent' from the median absolute value.

    Monthly bond returns have a median absolute value near 0.5 per cent and monthly stock returns
    near 7 per cent, so the two readings are two orders of magnitude apart; the band between them
    is a refusal, not a guess. `what` is 'bond' or 'stock' and sets the band.
    """
    v = np.asarray(values, dtype="float64")
    v = v[np.isfinite(v)]
    if v.size < 1000:
        raise Refusal("unit_sample_too_small", what)
    med = float(np.median(np.abs(v)))
    lo, hi = {"bond": (0.05, 0.2), "stock": (0.3, 1.0)}[what]
    if med < lo:
        return "decimal", med
    if med > hi:
        return "percent", med
    raise Refusal("unit_unclassifiable", f"{what}: median absolute value {med:.6g}")


# ---------------------------------------------------------------------------------------------
# reconstruction of monthly stock returns (in memory only)
# ---------------------------------------------------------------------------------------------

def lookup(keys_sorted, vals, q):
    """Values at the query keys `q` from a sorted unique key array; NaN where the key is absent."""
    out = np.full(len(q), np.nan)
    if len(keys_sorted) == 0:
        return out
    pos = np.minimum(np.searchsorted(keys_sorted, q), len(keys_sorted) - 1)
    hit = keys_sorted[pos] == q
    out[hit] = np.asarray(vals, dtype="float64")[pos[hit]]
    return out


def _keyed(df, name):
    key = df["permno"].to_numpy(dtype="int64") * KEY_BASE + mi_from_yyyymm(df["yyyymm"].to_numpy())
    s = pd.Series(df[name].to_numpy(dtype="float64"), index=pd.Index(key, dtype="int64"))
    if not s.index.is_unique:
        raise Refusal("signal_keys_duplicated", name)
    return s.sort_index()


def reconstruct(sig):
    """Rebuild monthly stock returns from the three published signals.

    Definitions, as read in the publisher's source (missing returns set to zero first; a lag is null
    where the lagged row is absent; null rows are dropped):
        MomSeasonShort(t) = r(t-11)
        Mom6m(t)  = prod_{k=1..5}  (1 + r(t-k)) - 1
        Mom12m(t) = prod_{k=1..11} (1 + r(t-k)) - 1
    Seeds: r(s) = MomSeasonShort(s+11). Roll forward, repeated until a pass adds nothing:
        r(t) = (1 + r(t-5)) * (1 + Mom6m(t+1)) / (1 + Mom6m(t)) - 1
    because (1 + Mom6m(t+1)) / (1 + Mom6m(t)) = (1 + r(t)) / (1 + r(t-5)).
    A step is refused where 1 + Mom6m(t) or 1 + r(t-5) is below GUARD: both are then near zero and
    their ratio is noise. A firm's final month needs Mom6m one month later, which does not exist, so
    it is never recovered; that month carries the delisting return. Mom12m is NOT used here, which
    is what lets `validate_mom12m` test the result against something independent.

    Returns a dict of aligned arrays over K, the sorted union of every key seen:
        key, r (NaN where unrecovered), origin (0 seed, n = recovered in pass n, -1 unrecovered),
        has_row and listed (the same thing: any of the three signals at that key), m6 (Mom6m there)
    plus the first and last signal row per permno, and the stock file's final month.
    """
    for n in SIGNALS:
        if n not in sig:
            raise Refusal("signal_missing", n)
    S, M6, M12 = (_keyed(sig[n], n) for n in SIGNALS)
    sk, m6k = S.index.to_numpy(), M6.index.to_numpy()
    rows = np.union1d(np.union1d(sk, m6k), M12.index.to_numpy())
    K = np.union1d(rows, sk - 11)
    r = lookup(sk - 11, S.to_numpy(), K)          # seeds: r(s) = MomSeasonShort(s + 11)
    origin = np.where(np.isfinite(r), 0, -1).astype("int16")
    m6_now = lookup(m6k, M6.to_numpy(), K)
    m6_next = lookup(m6k, M6.to_numpy(), K + 1)
    passes = []
    for p in range(1, MAX_PASSES + 1):
        r_lag5 = lookup(K, r, K - 5)
        ok = (~np.isfinite(r)) & np.isfinite(r_lag5) & np.isfinite(m6_now) & np.isfinite(m6_next)
        ok &= (1.0 + np.where(np.isfinite(m6_now), m6_now, 0.0) >= GUARD)
        ok &= (1.0 + np.where(np.isfinite(r_lag5), r_lag5, 0.0) >= GUARD)
        n_new = int(ok.sum())
        passes.append(n_new)
        if n_new == 0:
            break
        r[ok] = (1.0 + r_lag5[ok]) * (1.0 + m6_next[ok]) / (1.0 + m6_now[ok]) - 1.0
        origin[ok] = p
    else:
        raise Refusal("reconstruction_did_not_converge", f"{MAX_PASSES} passes")
    has_row = np.isin(K, rows)
    permno = K // KEY_BASE
    mi = K % KEY_BASE
    # Listed at t means a signal row at t, and nothing else. A recovered return at t is NOT enough:
    # in a stock's first five months it is known only from MomSeasonShort eleven months later, so
    # admitting it would make eligibility at t depend on the stock surviving to t+11.
    listed = has_row.copy()
    g = pd.DataFrame({"permno": permno, "mi": mi, "has_row": has_row})
    last_row = g[g.has_row].groupby("permno")["mi"].max()
    first_listed = g[g.has_row].groupby("permno")["mi"].min()
    panel_end = int(mi[has_row].max())
    return {"key": K, "permno": permno, "mi": mi, "r": r, "origin": origin, "has_row": has_row, "listed": listed,
            "m6": m6_now, "last_row": last_row, "first_listed": first_listed, "panel_end": panel_end,
            "passes": passes, "_M12": M12}


def validate_mom12m(stk):
    """Rebuild Mom12m from the recovered returns and compare with the published Mom12m.

    For every key with a published Mom12m: rebuilt = prod_{k=1..11} (1 + r(key-k)) - 1 where all
    eleven lags are recovered. `rolled` marks comparisons in which at least one lag came from the
    roll-forward rather than from a seed; those are the ones that test the roll-forward.
    Returns arrays aligned on the published Mom12m keys.
    """
    M12 = stk["_M12"]
    k12 = M12.index.to_numpy()
    K, r, origin = stk["key"], stk["r"], stk["origin"]
    prod = np.ones(len(k12))
    complete = np.ones(len(k12), dtype=bool)
    rolled = np.zeros(len(k12), dtype=bool)
    for k in range(1, 12):
        rk = lookup(K, r, k12 - k)
        ok = np.isfinite(rk)
        complete &= ok
        prod *= np.where(ok, 1.0 + rk, 1.0)
        rolled |= (lookup(K, origin, k12 - k) > 0)
    err = np.where(complete, np.abs(prod - 1.0 - M12.to_numpy()), np.nan)
    return {"key": k12, "err": err, "complete": complete, "rolled": rolled & complete}


def validate_roll_on_seeds(stk):
    """Apply the roll-forward formula where the answer is already known from a seed, and compare.

    This tests the mechanism itself on every month that has both a seed and the three inputs.
    """
    K, r, origin = stk["key"], stk["r"], stk["origin"]
    r_lag5 = lookup(K, np.where(origin == 0, r, np.nan), K - 5)
    m6_now = stk["m6"]
    m6_next = lookup(K, m6_now, K + 1)
    ok = (origin == 0) & np.isfinite(r_lag5) & np.isfinite(m6_now) & np.isfinite(m6_next)
    ok &= (1.0 + np.where(np.isfinite(m6_now), m6_now, 0.0) >= GUARD)
    ok &= (1.0 + np.where(np.isfinite(r_lag5), r_lag5, 0.0) >= GUARD)
    est = (1.0 + r_lag5[ok]) * (1.0 + m6_next[ok]) / (1.0 + m6_now[ok]) - 1.0
    return {"key": K[ok], "err": np.abs(est - r[ok])}


def error_summary(err, tol):
    e = np.asarray(err, dtype="float64")
    e = e[np.isfinite(e)]
    if e.size == 0:
        return {"n": 0}
    q = np.quantile(e, [0.5, 0.9, 0.99, 0.999])
    return {"n": int(e.size), "share_within_tol": float((e <= tol).mean()), "tol": tol, "median": float(q[0]),
            "p90": float(q[1]), "p99": float(q[2]), "p999": float(q[3]), "max": float(e.max())}


# ---------------------------------------------------------------------------------------------
# the bond side: issuer-month frame
# ---------------------------------------------------------------------------------------------

def issuer_months(panel):
    """Collapse the bond-month panel to one row per issuer (permno) and month.

    Row filter F, applied to bond-months before anything else: country equal to US_COUNTRY; permno
    present; ret_vw and tret present; mcap_s present and positive; spc_rat equal to 1 or 11.
    For issuer i in month t over its bonds b in F, with weights w_b = mcap_s (bond value at t-1):
        CR       = sum(w_b * (ret_vw_b - tret_b)) / sum(w_b)        the issuer's credit return
        hy_share = sum(w_b where spc_rat = 11) / sum(w_b)
        bond_value = sum(w_b), n_bonds = count
        DCS      = sum(w_b * (cs_b(t) - cs_b(t-1))) / sum(w_b) over bonds in F at t whose cs is
                   present at t and at t-1 (the same cusip, the previous calendar month, any row)
    Returns permno, mi, CR, hy_share, bond_value, n_bonds, DCS (NaN where no bond qualifies).
    """
    for c in PANEL_REQUIRED:
        if c not in panel.columns:
            raise Refusal("panel_columns_missing", c)
    df = panel[PANEL_REQUIRED].copy()
    df["mi"] = mi_from_dates(df["date"])
    if df.duplicated(["cusip", "mi"]).any():
        raise Refusal("panel_keys_duplicated", "cusip, month")
    prev = df[["cusip", "mi", "cs"]].rename(columns={"cs": "cs_prev"})
    prev["mi"] = prev["mi"] + 1
    df = df.merge(prev, on=["cusip", "mi"], how="left")
    rat = pd.to_numeric(df["spc_rat"], errors="coerce")
    F = ((df["country"] == US_COUNTRY) & df["permno"].notna() & df["ret_vw"].notna() & df["tret"].notna()
         & df["mcap_s"].notna() & (df["mcap_s"] > 0) & rat.isin([IG_CODE, HY_CODE]))
    d = df[F].copy()
    if len(d) == 0:
        raise Refusal("panel_filter_empty", "no bond-month passes the row filter")
    d["permno"] = d["permno"].astype("int64")
    w = d["mcap_s"].astype("float64")
    d["w"] = w
    d["wx"] = w * (d["ret_vw"].astype("float64") - d["tret"].astype("float64"))
    d["whY"] = np.where(pd.to_numeric(d["spc_rat"], errors="coerce") == HY_CODE, w, 0.0)
    dcs = d["cs"].astype("float64") - d["cs_prev"].astype("float64")
    has = dcs.notna()
    d["w_dcs"] = np.where(has, w, 0.0)
    d["wdcs"] = np.where(has, w * dcs.fillna(0.0), 0.0)
    g = d.groupby(["permno", "mi"], sort=True).agg(bond_value=("w", "sum"), wx=("wx", "sum"), hy=("whY", "sum"),
                                                     n_bonds=("w", "size"), w_dcs=("w_dcs", "sum"), wdcs=("wdcs", "sum")).reset_index()
    g["CR"] = g["wx"] / g["bond_value"]
    g["hy_share"] = g["hy"] / g["bond_value"]
    g["DCS"] = np.where(g["w_dcs"] > 0, g["wdcs"] / g["w_dcs"].where(g["w_dcs"] > 0, 1.0), np.nan)
    return g[["permno", "mi", "CR", "hy_share", "bond_value", "n_bonds", "DCS"]]


# ---------------------------------------------------------------------------------------------
# linkage: issuer-month at t to the stock at t and t+1
# ---------------------------------------------------------------------------------------------

MISS_REASONS = ["ok", "permno_not_in_stock_file", "after_stock_file_end", "not_listed_yet_at_t", "delisted_before_t", "gap_at_t",
                "t_is_final_month", "t_is_panel_end", "t1_is_final_month_lost", "t1_is_panel_end",
                "t1_unrecovered_other"]


def link(im, stk):
    """Attach to each issuer-month (permno, mi = t) the stock's state at t and its return at t+1.

    listed_t: the stock has a row in any of the three signals at t. Required for two reasons. A first
    listing month, whose missing return the publisher set to zero, must not be scored as the outcome
    of a position that could not have been opened. And the test must be knowable at t: a signal row
    at t depends only on months up to t, whereas a recovered return at t can depend on the stock
    still being listed eleven months later.
    Reasons are mutually exclusive. The five 'not listed at t' reasons are assigned first, then
    'ok' (listed at t and a recovered return at t+1), then the rest in the order below:
      permno_not_in_stock_file   the permno never appears in the signals
      after_stock_file_end       t is after the stock file's final month, so no stock is listed at t.
                                 (Probe run 2 counted these under delisted_before_t; the bond panel
                                 runs eleven months beyond the stock file.)
      not_listed_yet_at_t        t is before the stock's first signal row (its first five listed
                                 months have none)
      delisted_before_t          t is after the stock's last signal row
      gap_at_t                   t is inside the stock's span but the stock is not listed at t
      t_is_final_month           listed at t, and t is the stock's last row before the panel's end
      t_is_panel_end             listed at t, and t is the panel's final month
      t1_is_final_month_lost     t+1 is the stock's last row before the panel's end: the return
                                 existed, carries any delisting return, and cannot be recovered
      t1_is_panel_end            t+1 is the panel's final month, unrecoverable for every stock
      t1_unrecovered_other       anything else (a gap at t+1, a guarded step, a short history)
    Adds: listed_t, r_t, m6_t, r_t1, reason.
    """
    out = im.copy()
    key_t = out["permno"].to_numpy(dtype="int64") * KEY_BASE + out["mi"].to_numpy(dtype="int64")
    K = stk["key"]
    listed_t = lookup(K, stk["listed"], key_t) > 0
    r_t = lookup(K, stk["r"], key_t)
    r_t1 = lookup(K, stk["r"], key_t + 1)
    last = stk["last_row"].reindex(out["permno"].to_numpy()).to_numpy()
    first = stk["first_listed"].reindex(out["permno"].to_numpy()).to_numpy()
    t = out["mi"].to_numpy(dtype="int64")
    end = stk["panel_end"]
    known = np.isfinite(first) | np.isfinite(last)
    reason = np.full(len(out), "t1_unrecovered_other", dtype=object)
    done = np.zeros(len(out), dtype=bool)

    def put(mask, name):
        m = mask & ~done
        reason[m] = name
        done[m] = True

    put(~known, "permno_not_in_stock_file")
    put(~listed_t & (t > end), "after_stock_file_end")
    put(~listed_t & (t < np.where(np.isfinite(first), first, np.inf)), "not_listed_yet_at_t")
    put(~listed_t & (t > np.where(np.isfinite(last), last, -np.inf)), "delisted_before_t")
    put(~listed_t, "gap_at_t")
    put(listed_t & np.isfinite(r_t1), "ok")
    put((t == last) & (last < end), "t_is_final_month")
    put((t == last) & (last == end), "t_is_panel_end")
    put((t + 1 == last) & (last < end), "t1_is_final_month_lost")
    put((t + 1 == last) & (last == end), "t1_is_panel_end")
    out["listed_t"] = listed_t
    out["r_t"] = r_t
    out["m6_t"] = lookup(K, stk["m6"], key_t)
    out["r_t1"] = np.where(reason == "ok", r_t1, np.nan)
    out["reason"] = reason
    return out
