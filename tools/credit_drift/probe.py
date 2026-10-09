"""Structure probe for the credit-drift pilot. NO OUTCOMES.

NON-EVIDENTIARY side test, outside the FNTN funnel. See docs/CREDIT_DRIFT_2026-10-09.md.

Why this exists: the test's two inputs had never been opened by this project when the test was
drafted, and the session that writes the specification cannot reach either host. This reports, in
one run, what the frozen specification has to name: the files with their sizes and SHA-256, the
panel's columns, dates and units, the rating, return-type and country counts, the number of
high-yield issuers each month, whether the reconstructed stock returns validate against the
published Mom12m, and how many high-yield issuer-months find a stock row at t and a recovered
return at t+1, with the reason for each miss.

What keeps it on the right side of the freeze: **it computes no relation between any signal and any
outcome.** The credit signal is never placed beside a stock return. Coverage is counted by reason
and by year only, never by the level of the signal.

What it publishes: counts, shares, quantiles of whole columns, file names and hashes. It never
prints or writes a row of either input, and it never writes a reconstructed return.

Why it does not swallow errors: its predecessor caught every exception and exited 0 behind a pipe
with no pipefail, so its one run reported success having proved nothing. Here each section records
its own failure and the sections that do not depend on it still run, so one run returns as much as
it can; but any failure makes the process exit non-zero.
"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdlib  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
TMP = tempfile.mkdtemp(prefix="cd_", dir=os.environ.get("RUNNER_TEMP") or None)
RES = {"what": "credit-drift probe: structure only, no outcomes; non-evidentiary", "errors": [], "sections": {}}
QS = [0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999]
EXTRA = ["mdc_rat", "rfret", "md_dur", "tmat", "144a", "issuer_cusip", "mcap_e", "ytm", "fce_val", "ret_vwx"]
TOL = 1e-3


def say(*a):
    print(*a, flush=True)


def section(name, needs=()):
    def deco(fn):
        say("\n" + "=" * 10 + " " + name)
        missing = [n for n in needs if n not in RES["sections"] or RES["sections"][n].get("failed")]
        if missing:
            RES["sections"][name] = {"skipped": f"depends on {missing}"}
            RES["errors"].append({"section": name, "error": f"skipped: depends on {missing}"})
            say("SKIPPED: depends on", missing)
            return fn
        t0 = time.time()
        try:
            out = fn() or {}
            out["seconds"] = round(time.time() - t0, 1)
            RES["sections"][name] = out
        except Exception as e:  # recorded, reported, and the process exits non-zero at the end
            tb = traceback.format_exc()
            RES["sections"][name] = {"failed": True, "error": repr(e)}
            RES["errors"].append({"section": name, "error": repr(e), "traceback": tb[-3000:]})
            say("SECTION FAILED:", repr(e))
            say(tb[-3000:])
        return fn
    return deco


def quantiles(x):
    v = np.asarray(pd.to_numeric(pd.Series(x), errors="coerce"), dtype="float64")
    n = int(v.size)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return {"n": n, "non_null": 0}
    q = np.quantile(v, QS)
    return {"n": n, "non_null": int(v.size), "mean": float(v.mean()), "median_abs": float(np.median(np.abs(v))),
            "q": {str(k): float(val) for k, val in zip(QS, q)}, "min": float(v.min()), "max": float(v.max())}


def counts(s, top=12):
    vc = pd.Series(s).value_counts(dropna=False).head(top)
    return {("null" if pd.isna(k) else str(k)): int(v) for k, v in vc.items()}


def year_of(mi):
    return (np.asarray(mi, dtype="int64") // 12)


STATE = {}


@section("environment")
def _():
    here = os.path.dirname(os.path.abspath(__file__))
    files = {f: cdlib.sha256_file(os.path.join(here, f)) for f in sorted(os.listdir(here)) if f.endswith((".py", ".md")) or f == "DISPATCH"}
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.splitlines()
    out = {"python": platform.python_version(), "platform": platform.platform(), "commit": os.environ.get("GITHUB_SHA"),
           "run_number": os.environ.get("GITHUB_RUN_NUMBER"), "code_sha256": files, "pip_freeze": freeze}
    say("python", out["python"], "| commit", out["commit"])
    for f, h in files.items():
        say(f"  {h}  {f}")
    return out


@section("site_links")
def _():
    import requests
    found = {}
    for page in ("https://openbondassetpricing.com/data/",):
        r = requests.get(page, headers=cdlib.UA, timeout=60)
        say(page, "HTTP", r.status_code, len(r.text), "characters")
        for h in re.findall(r'href=["\']([^"\']+)["\']', r.text):
            if re.search(r"\.(zip|parquet|csv|gz)(\?|$)", h, re.I) or "releases/download" in h:
                found[h] = None
    for h in sorted(found):
        try:
            hd = requests.head(h, headers=cdlib.UA, timeout=60, allow_redirects=True)
            found[h] = {"status": hd.status_code, "bytes": int(hd.headers.get("content-length", -1))}
        except Exception as e:  # a dead link is a finding, not a failure of the probe
            found[h] = {"error": repr(e)}
        say(" ", found[h], h)
    return {"links": found}


@section("release_assets")
def _():
    rel = cdlib.release_assets(os.environ.get("GH_TOKEN"))
    say("release", rel["tag"], "published", rel["published_at"], "| assets:", len(rel["assets"]))
    for a in rel["assets"]:
        say(f"  {a['size']:>14,}  {a['digest'] or 'no digest'}  {a['name']}")
    STATE["release"] = rel
    return rel


@section("panel_file", needs=("release_assets",))
def _():
    asset = [a for a in STATE["release"]["assets"] if a["name"] == cdlib.OSBAP_ASSET]
    if len(asset) != 1:
        raise cdlib.Refusal("panel_asset_not_found", cdlib.OSBAP_ASSET)
    asset = asset[0]
    dest = os.path.join(TMP, cdlib.OSBAP_ASSET)
    n, sha, secs = cdlib.download_to(asset["url"], dest)
    say(f"downloaded {cdlib.OSBAP_ASSET}: {n:,} bytes in {secs:.0f}s, sha256 {sha}")
    api = (asset.get("digest") or "").replace("sha256:", "")
    out = {"name": cdlib.OSBAP_ASSET, "url": asset["url"], "bytes": n, "sha256": sha, "api_size": asset["size"],
           "api_digest": asset.get("digest"), "digest_agrees": (api == sha) if api else None, "size_agrees": n == asset["size"]}
    out["zip_members"] = cdlib.zip_listing(dest)
    for m in out["zip_members"]:
        say(f"  member {m['size']:>14,}  {m['name']}")
    members = cdlib.extract_parquet_members(dest, os.path.join(TMP, "x"))
    import pyarrow.parquet as pq
    out["parquet_members"] = []
    cands = []
    for name, path, size in members:
        pf = pq.ParquetFile(path)
        cols = pf.schema_arrow.names
        has = all(c in cols for c in cdlib.PANEL_REQUIRED)
        out["parquet_members"].append({"name": name, "bytes": size, "sha256": cdlib.sha256_file(path), "rows": pf.metadata.num_rows,
                                       "n_columns": len(cols), "columns": cols,
                                       "dtypes": {f.name: str(f.type) for f in pf.schema_arrow}, "has_required": has})
        say(f"-- {name}: {pf.metadata.num_rows:,} rows, {len(cols)} columns, has the required columns: {has}")
        say("   columns:", ", ".join(cols))
        if has:
            cands.append((name, path))
    if len(cands) != 1:
        named = [c for c in cands if "main_panel" in c[0]]
        if len(named) != 1:
            raise cdlib.Refusal("panel_member_ambiguous", f"{[c[0] for c in cands]}")
        cands = named
    STATE["panel_member"], STATE["panel_path"] = cands[0]
    out["panel_member"] = cands[0][0]
    return out


@section("panel_description", needs=("panel_file",))
def _():
    import pyarrow.parquet as pq
    names = pq.ParquetFile(STATE["panel_path"]).schema_arrow.names
    cols = cdlib.PANEL_REQUIRED + [c for c in EXTRA if c in names]
    df = cdlib.read_panel(STATE["panel_path"], cols)
    STATE["panel"] = df
    out = {"rows": int(len(df)), "columns_read": cols}
    d = pd.to_datetime(df["date"])
    mi = cdlib.mi_from_dates(df["date"])
    out["date_min"], out["date_max"] = str(d.min().date()), str(d.max().date())
    out["distinct_months"] = int(pd.Series(mi).nunique())
    out["share_calendar_month_end"] = float((d == d + pd.offsets.MonthEnd(0)).mean())
    out["duplicate_cusip_month_rows"] = int(pd.DataFrame({"c": df["cusip"], "m": mi}).duplicated().sum())
    out["distinct_cusips"] = int(df["cusip"].nunique())
    say("rows", f"{len(df):,}", "| dates", out["date_min"], "to", out["date_max"], "| months", out["distinct_months"],
        "| calendar month-end share", round(out["share_calendar_month_end"], 4), "| duplicate cusip-months", out["duplicate_cusip_month_rows"])
    out["counts"] = {c: counts(df[c]) for c in ("spc_rat", "mdc_rat", "ret_type", "country", "144a") if c in df}
    for c, v in out["counts"].items():
        say(f"   {c}: {v}")
    out["non_null_share"] = {c: float(df[c].notna().mean()) for c in cols}
    say("   non-null shares:", {k: round(v, 4) for k, v in out["non_null_share"].items()})
    out["quantiles"] = {c: quantiles(df[c]) for c in ("ret_vw", "tret", "rfret", "cs", "md_dur", "tmat", "mcap_s", "ytm", "ret_vwx") if c in df}
    for c, v in out["quantiles"].items():
        say(f"   {c}: median abs {v.get('median_abs')}, q {v.get('q')}")
    units = {}
    for c in ("ret_vw", "tret"):
        try:
            u, med = cdlib.unit_of(pd.to_numeric(df[c], errors="coerce").dropna().to_numpy(), "bond")
            units[c] = {"unit": u, "median_abs": med}
        except cdlib.Refusal as e:
            units[c] = {"unit": "unclassifiable", "detail": str(e)}
    tr = pd.to_numeric(df["tret"], errors="coerce").dropna().to_numpy()
    units["tret_share_equal_to_2dp"] = float(np.isclose(tr, np.round(tr, 2), atol=1e-12).mean())
    units["tret_share_equal_to_4dp"] = float(np.isclose(tr, np.round(tr, 4), atol=1e-12).mean())
    out["units"] = units
    say("   units:", units)
    yr = pd.Series(year_of(mi))
    rat = pd.to_numeric(df["spc_rat"], errors="coerce")
    out["permno_non_null_share"] = {"all": float(df["permno"].notna().mean()),
                                    "investment_grade": float(df["permno"][rat == cdlib.IG_CODE].notna().mean()),
                                    "non_investment_grade": float(df["permno"][rat == cdlib.HY_CODE].notna().mean()),
                                    "unrated": float(df["permno"][rat.isna()].notna().mean()) if rat.isna().any() else None}
    say("   permno non-null share:", {k: (round(v, 4) if v is not None else None) for k, v in out["permno_non_null_share"].items()})
    # non-investment-grade bond value, by whether the bond carries a permno, by year (rows otherwise in the filter)
    f = ((df["country"] == cdlib.US_COUNTRY) & df["ret_vw"].notna() & df["tret"].notna() & (pd.to_numeric(df["mcap_s"], errors="coerce") > 0)
         & (rat == cdlib.HY_CODE))
    g = pd.DataFrame({"y": yr[f.to_numpy()].to_numpy(), "v": pd.to_numeric(df["mcap_s"], errors="coerce")[f].to_numpy(),
                      "has": df["permno"][f].notna().to_numpy()})
    tot = g.groupby("y")["v"].sum()
    has = g[g.has].groupby("y")["v"].sum()
    out["hy_bond_value_share_with_permno_by_year"] = {str(int(y)): float(has.get(y, 0.0) / tot[y]) for y in tot.index}
    out["hy_bond_months_in_filter_but_for_permno"] = int(f.sum())
    out["hy_bond_months_with_permno"] = int(g.has.sum())
    say("   non-investment-grade bond value carrying a permno, by year:",
        {k: round(v, 3) for k, v in out["hy_bond_value_share_with_permno_by_year"].items()})
    return out


@section("issuer_universe", needs=("panel_description",))
def _():
    im = cdlib.issuer_months(STATE["panel"])
    STATE["im"] = im
    del STATE["panel"]
    out = {"issuer_months": int(len(im)), "distinct_issuers": int(im["permno"].nunique())}
    hy = im["hy_share"] >= 0.5
    out["hy_issuer_months"] = int(hy.sum())
    out["hy_distinct_issuers"] = int(im.loc[hy, "permno"].nunique())
    out["hy_share_distribution"] = {"exactly_0": float((im["hy_share"] == 0).mean()), "exactly_1": float((im["hy_share"] == 1).mean()),
                                    "strictly_between": float(((im["hy_share"] > 0) & (im["hy_share"] < 1)).mean())}
    out["n_bonds_per_hy_issuer_month"] = quantiles(im.loc[hy, "n_bonds"])
    out["CR_all_issuer_months"] = quantiles(im["CR"])
    out["DCS_non_null_share_hy"] = float(im.loc[hy, "DCS"].notna().mean())
    per = im.assign(hy=hy).groupby("mi").agg(all_issuers=("permno", "size"), hy_issuers=("hy", "sum")).reset_index()
    per["ig_issuers"] = per["all_issuers"] - per["hy_issuers"]
    STATE["per_month"] = per
    out["months"] = int(len(per))
    out["first_month"], out["last_month"] = int(cdlib.yyyymm_from_mi(per.mi.min())), int(cdlib.yyyymm_from_mi(per.mi.max()))
    out["hy_issuers_per_month"] = {"min": int(per.hy_issuers.min()), "p5": float(per.hy_issuers.quantile(0.05)),
                                   "median": float(per.hy_issuers.median()), "max": int(per.hy_issuers.max())}
    say("issuer-months", f"{len(im):,}", "| distinct issuers", out["distinct_issuers"], "| high-yield issuer-months", f"{out['hy_issuer_months']:,}",
        "| distinct high-yield issuers", out["hy_distinct_issuers"])
    say("high-yield issuers per month:", out["hy_issuers_per_month"], "| months", out["months"], out["first_month"], "to", out["last_month"])
    by = per.assign(y=year_of(per.mi)).groupby("y")[["hy_issuers", "ig_issuers"]].mean().round(1)
    say("yearly mean issuers per month (high-yield, investment-grade):", {int(y): (float(r.hy_issuers), float(r.ig_issuers)) for y, r in by.iterrows()})
    return out


@section("stock_signals")
def _():
    client = cdlib.new_osap_client()
    sig, out = {}, {"release": cdlib.OSAP_RELEASE, "files": {}}
    for name in cdlib.SIGNALS:
        t0 = time.time()
        body, file_id = cdlib.fetch_signal_bytes(name, client)
        d, n_null = cdlib.parse_signal(name, body)
        info = {"drive_file_id": file_id, "bytes": len(body), "sha256": cdlib.sha256_bytes(body), "rows": int(len(d)), "null_rows_dropped": n_null,
                "yyyymm_min": int(d.yyyymm.min()), "yyyymm_max": int(d.yyyymm.max()), "distinct_permno": int(d.permno.nunique()),
                "values": quantiles(d[name]), "seconds": round(time.time() - t0, 1)}
        del body
        out["files"][name] = info
        sig[name] = d
        say(f"-- {name}: {info['bytes']:,} bytes, sha256 {info['sha256']}, {info['rows']:,} rows, {info['yyyymm_min']} to {info['yyyymm_max']}, "
            f"{info['distinct_permno']:,} permnos, median abs {info['values']['median_abs']:.5f}")
    u, med = cdlib.unit_of(sig["MomSeasonShort"]["MomSeasonShort"].to_numpy(), "stock")
    out["unit"] = {"unit": u, "median_abs_MomSeasonShort": med}
    say("unit of the stock return:", out["unit"])
    STATE["sig"] = sig
    return out


@section("reconstruction", needs=("stock_signals",))
def _():
    if RES["sections"]["stock_signals"]["unit"]["unit"] != "decimal":
        raise cdlib.Refusal("stock_unit_not_decimal", "the reconstruction algebra needs decimal returns")
    stk = cdlib.reconstruct(STATE["sig"])
    del STATE["sig"]
    STATE["stk"] = stk
    r, origin, mi = stk["r"], stk["origin"], stk["mi"]
    out = {"keys": int(len(r)), "passes": stk["passes"], "panel_end": int(cdlib.yyyymm_from_mi(stk["panel_end"])),
           "origin_counts": {str(int(k)): int(v) for k, v in zip(*np.unique(origin, return_counts=True))},
           "permnos": int(len(stk["last_row"])), "permnos_alive_at_panel_end": int((stk["last_row"] == stk["panel_end"]).sum()),
           "recovered_share_of_listed_months": float(np.isfinite(r)[stk["listed"]].mean()),
           "recovered_returns": quantiles(r[np.isfinite(r)]), "share_exact_zero": float((r[np.isfinite(r)] == 0).mean())}
    say("keys", f"{len(r):,}", "| passes", stk["passes"], "| origin counts", out["origin_counts"], "| panel end", out["panel_end"])
    v1 = cdlib.validate_mom12m(stk)
    v2 = cdlib.validate_roll_on_seeds(stk)
    w = (v1["key"] % cdlib.KEY_BASE) >= (2002 * 12 + 7)
    out["mom12m_published_rows"] = int(len(v1["key"]))
    out["mom12m_comparable_share"] = float(v1["complete"].mean())
    out["validation"] = {
        "mom12m_all": cdlib.error_summary(v1["err"], TOL),
        "mom12m_rolled": cdlib.error_summary(v1["err"][v1["rolled"]], TOL),
        "mom12m_all_from_2002_08": cdlib.error_summary(v1["err"][w], TOL),
        "mom12m_rolled_from_2002_08": cdlib.error_summary(v1["err"][v1["rolled"] & w], TOL),
        "roll_formula_on_seeds_all": cdlib.error_summary(v2["err"], TOL),
        "roll_formula_on_seeds_from_2002_08": cdlib.error_summary(v2["err"][(v2["key"] % cdlib.KEY_BASE) >= (2002 * 12 + 7)], TOL)}
    STATE["v1"], STATE["v2"] = v1, v2
    for k, v in out["validation"].items():
        say(f"   {k}: {v}")
    return out


@section("coverage", needs=("issuer_universe", "reconstruction"))
def _():
    im, stk = STATE["im"], STATE["stk"]
    lk = cdlib.link(im, stk)
    hy = (lk["hy_share"] >= 0.5).to_numpy()
    out = {}
    for label, mask in (("high_yield", hy), ("investment_grade", ~hy), ("all", np.ones(len(lk), dtype=bool))):
        sub = lk[mask]
        c = sub["reason"].value_counts()
        out[label] = {"issuer_months": int(len(sub)), "reasons": {k: int(c.get(k, 0)) for k in cdlib.MISS_REASONS},
                      "share_listed_at_t": float(sub["listed_t"].mean()), "share_ok": float((sub["reason"] == "ok").mean())}
        say(f"-- {label}: issuer-months {len(sub):,}, listed at t {out[label]['share_listed_at_t']:.3f}, ok {out[label]['share_ok']:.3f}")
        say("   reasons:", out[label]["reasons"])
    sub = lk[hy].copy()
    sub["y"] = year_of(sub["mi"])
    tab = sub.groupby(["y", "reason"]).size().unstack(fill_value=0)
    out["high_yield_reasons_by_year"] = {str(int(y)): {k: int(v) for k, v in row.items()} for y, row in tab.iterrows()}
    say("high-yield reasons by year:")
    for y, row in out["high_yield_reasons_by_year"].items():
        n = sum(row.values())
        say(f"   {y}: n {n:>6}, ok {row.get('ok', 0) / n:.3f}, final month lost {row.get('t1_is_final_month_lost', 0)}, {row}")
    okm = sub["reason"] == "ok"
    out["high_yield_ok_with_controls_share"] = float((np.isfinite(sub.loc[okm, "r_t"]) & np.isfinite(sub.loc[okm, "m6_t"])).mean())
    key1 = sub.loc[okm, "permno"].to_numpy(dtype="int64") * cdlib.KEY_BASE + sub.loc[okm, "mi"].to_numpy(dtype="int64") + 1
    o1 = cdlib.lookup(stk["key"], stk["origin"], key1)
    out["high_yield_ok_outcome_origin"] = {str(int(k)): int(v) for k, v in zip(*np.unique(o1, return_counts=True))}
    per = sub.groupby("mi").agg(hy_issuers=("permno", "size"), listed_at_t=("listed_t", "sum"), with_outcome=("reason", lambda s: int((s == "ok").sum()))).reset_index()
    out["per_month"] = {str(int(cdlib.yyyymm_from_mi(m))): [int(a), int(b), int(c)] for m, a, b, c in zip(per.mi, per.hy_issuers, per.listed_at_t, per.with_outcome)}
    out["per_month_columns"] = ["high_yield_issuers", "listed_at_t", "with_outcome_at_t1"]
    for col in ("listed_at_t", "with_outcome"):
        v = per[col]
        out[f"{col}_per_month"] = {"min": int(v.min()), "p5": float(v.quantile(0.05)), "p25": float(v.quantile(0.25)), "median": float(v.median()), "max": int(v.max()),
                                   "months_below_50": int((v < 50).sum()), "months_below_100": int((v < 100).sum())}
        say(f"high-yield issuers per month, {col}:", out[f"{col}_per_month"])
    # validation restricted to the stocks the test would use
    v1, v2 = STATE["v1"], STATE["v2"]
    hyp = np.unique(sub["permno"].to_numpy(dtype="int64"))
    lo = 2002 * 12 + 7
    m1 = np.isin(v1["key"] // cdlib.KEY_BASE, hyp) & ((v1["key"] % cdlib.KEY_BASE) >= lo)
    m2 = np.isin(v2["key"] // cdlib.KEY_BASE, hyp) & ((v2["key"] % cdlib.KEY_BASE) >= lo)
    out["validation_high_yield_stocks_from_2002_08"] = {
        "mom12m_all": cdlib.error_summary(v1["err"][m1], TOL), "mom12m_rolled": cdlib.error_summary(v1["err"][m1 & v1["rolled"]], TOL),
        "mom12m_comparable_share": float(v1["complete"][m1].mean()) if m1.any() else None,
        "roll_formula_on_seeds": cdlib.error_summary(v2["err"][m2], TOL)}
    for k, v in out["validation_high_yield_stocks_from_2002_08"].items():
        say(f"   validation, high-yield stocks, {k}: {v}")
    return out


RES["status"] = "failed" if RES["errors"] else "complete"
with open(os.path.join(args.out, "probe.json"), "w") as f:
    json.dump(RES, f, indent=1, sort_keys=True, default=str)
say("\nprobe", RES["status"], "| sections failed or skipped:", [e["section"] for e in RES["errors"]])
sys.exit(1 if RES["errors"] else 0)
