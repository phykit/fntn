"""Plumbing probe for the credit-drift pilot. STRUCTURE ONLY.

Why this exists: the test's two inputs (the Open Source Bond Asset Pricing monthly panel and the
Open Source Asset Pricing firm-level signals) have never been fetched by this project, and the
session that wrote the test cannot reach either host. This prints what is there (links, sizes,
schemas, row counts, date ranges, coverage of the join key) so the frozen specification names
real files and real columns. It computes no relationship between any signal and any outcome,
which is what keeps it on the right side of the freeze.
"""
import argparse, io, os, re, sys, zipfile, time
import requests

ap = argparse.ArgumentParser(); ap.add_argument("--cache", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
UA = {"User-Agent": "phykit-fntn credit-drift pilot (research; github.com/phykit/fntn)"}
PAGES = ["https://openbondassetpricing.com/data/", "https://openbondassetpricing.com/"]


def section(t): print("\n" + "=" * 8 + " " + t, flush=True)


section("OSBAP: links on the site")
links = {}
for p in PAGES:
    try:
        r = requests.get(p, headers=UA, timeout=60)
        print(p, "HTTP", r.status_code, len(r.text), "bytes")
        for h in re.findall(r'href=["\']([^"\']+)["\']', r.text):
            if re.search(r"\.(zip|parquet|csv|pdf|gz)(\?|$)", h, re.I) or "wp-content/uploads" in h:
                links[h] = None
    except Exception as e:
        print(p, "FAILED", repr(e))
for h in sorted(links):
    try:
        hd = requests.head(h, headers=UA, timeout=60, allow_redirects=True)
        links[h] = int(hd.headers.get("content-length", -1))
        print(f"{hd.status_code} {links[h]/1e6:10.1f} MB  {h}")
    except Exception as e:
        print("HEAD FAILED", h, repr(e))

section("OSBAP: download every non-PDF data file under 1.5 GB and describe it")
import pyarrow.parquet as pq
import pandas as pd
WANT = ["date", "permno", "spc_rat", "mdc_rat", "country", "ret_vw", "tret", "rfret", "cs", "md_dur", "mcap_s", "mcap_e", "ret_type", "cusip", "issuer_cusip", "tmat", "fce_val", "144a", "sze"]


def describe_parquet(path_or_buf, name):
    pf = pq.ParquetFile(path_or_buf)
    cols = pf.schema_arrow.names
    print(f"-- {name}: {pf.metadata.num_rows:,} rows, {len(cols)} columns")
    print("   columns:", ", ".join(cols))
    have = [c for c in WANT if c in cols]
    if "date" in cols and "permno" in cols and pf.metadata.num_rows < 6_000_000:
        df = pf.read(columns=have).to_pandas()
        df["date"] = pd.to_datetime(df["date"])
        print("   date range:", df["date"].min().date(), "to", df["date"].max().date(), "| distinct months:", df["date"].dt.to_period("M").nunique())
        print("   permno non-null share: %.3f | distinct permno: %d" % (df["permno"].notna().mean(), df["permno"].nunique()))
        for c in ("spc_rat", "mdc_rat", "ret_type", "144a"):
            if c in df: print(f"   {c} value counts:", df[c].value_counts(dropna=False).head(6).to_dict())
        if "country" in df: print("   country top:", df["country"].value_counts(dropna=False).head(4).to_dict())
        for c in ("ret_vw", "tret", "cs", "mcap_s", "md_dur"):
            if c in df: print(f"   {c}: non-null share %.3f" % df[c].notna().mean())
        if "spc_rat" in df:
            hy = df[(df["spc_rat"] == 11) & df["permno"].notna()]
            g = hy.groupby(hy["date"].dt.year)["permno"].nunique()
            print("   distinct HY issuers (permno) by year:", g.to_dict())
            hy[["date", "permno"]].drop_duplicates().to_parquet(os.path.join(a.cache, "_probe_hy_keys.parquet"))
    return cols


for h, size in sorted(links.items()):
    if h.lower().endswith(".pdf") or size is None or size <= 0 or size > 1.5e9: continue
    fn = os.path.join(a.cache, os.path.basename(h.split("?")[0]))
    try:
        if not os.path.exists(fn):
            t0 = time.time()
            with requests.get(h, headers=UA, timeout=600, stream=True) as r:
                r.raise_for_status()
                with open(fn, "wb") as f:
                    for chunk in r.iter_content(1 << 20): f.write(chunk)
            print(f"downloaded {fn} {os.path.getsize(fn)/1e6:.1f} MB in {time.time()-t0:.0f}s")
        if fn.endswith(".zip"):
            z = zipfile.ZipFile(fn)
            print("zip", os.path.basename(fn), "members:", [(i.filename, round(i.file_size / 1e6, 1)) for i in z.infolist()][:40])
            for i in z.infolist():
                if i.filename.endswith(".parquet") and i.file_size < 1.5e9:
                    describe_parquet(io.BytesIO(z.read(i.filename)), i.filename)
                elif i.filename.lower().endswith((".md", ".txt")) and i.file_size < 20000:
                    print("---- " + i.filename); print(z.read(i.filename).decode("utf-8", "replace")[:3000])
        elif fn.endswith(".parquet"):
            describe_parquet(fn, os.path.basename(fn))
        elif fn.endswith(".csv"):
            print(os.path.basename(fn), "head:"); print(open(fn, errors="replace").read(600))
    except Exception as e:
        print("FAILED on", h, repr(e))

section("OSAP: firm-level signals by permno-month")
try:
    import openassetpricing as oap
    try: print("releases:", oap.list_release())
    except Exception as e: print("list_release failed", repr(e))
    o = oap.OpenAP()
    for sig in ("MomSeasonShort", "Mom6m", "Mom12m"):
        t0 = time.time(); d = o.dl_signal("pandas", [sig])
        print(f"-- {sig}: {len(d):,} rows in {time.time()-t0:.0f}s; columns {list(d.columns)}; yyyymm {d['yyyymm'].min()} to {d['yyyymm'].max()}; non-null {d[sig].notna().sum():,}; distinct permno {d['permno'].nunique():,}")
        print(d.tail(3).to_string())
        d.to_parquet(os.path.join(a.cache, f"osap_{sig}.parquet"))
    k = os.path.join(a.cache, "_probe_hy_keys.parquet")
    if os.path.exists(k):
        hy = pd.read_parquet(k); hy["yyyymm"] = hy["date"].dt.year * 100 + hy["date"].dt.month; hy["permno"] = hy["permno"].astype("int64")
        s = pd.read_parquet(os.path.join(a.cache, "osap_Mom6m.parquet"))[["permno", "yyyymm"]].drop_duplicates(); s["hit"] = 1
        mm = hy.merge(s, on=["permno", "yyyymm"], how="left")
        print("JOIN KEY COVERAGE: HY issuer-months %d, with an OSAP row in the same month %d (%.1f%%)" % (len(mm), mm.hit.notna().sum(), 100 * mm.hit.notna().mean()))
        print("  by year:", (mm.groupby(mm.yyyymm // 100).hit.apply(lambda x: round(100 * x.notna().mean(), 1))).to_dict())
except Exception as e:
    import traceback; traceback.print_exc(); print("OSAP FAILED", repr(e))
print("\nprobe done")
