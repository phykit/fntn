"""Fetch every input of tests A to D to a data directory on the runner. Prints structure only.
Usage: python fetch_all.py --data data
"""
import argparse
import csv
import datetime as dt
import io
import os
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) fntn-side-test/1.0"
FRED = {"ng_spot": "DHHNGSP", "ho_spot": "DHOILNYH", "rb_spot": "DGASNYH", "tbill": "DTB3"}
EIA = {"ng_c1": "https://www.eia.gov/dnav/ng/hist_xls/RNGC1d.xls", "ng_c2": "https://www.eia.gov/dnav/ng/hist_xls/RNGC2d.xls",
       "ho_c1": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2F_PE1_Y35NY_DPGd.xls",
       "rb_c1": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPMRR_PE1_Y35NY_DPGd.xls"}
YAHOO_CLOSE = {"vix": "^VIX", "vix3m": "^VIX3M", "btc_spot": "BTC-USD", "btc_fut": "BTC=F"}


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise SystemExit(f"fetch failed for {url}: {last!r}")


def write_rows(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([r[0]] + ["" if v is None else repr(v) for v in r[1:]])


def describe(name, rows):
    n = len(rows)
    miss = sum(1 for r in rows if any(v is None for v in r[1:]))
    print(f"{name}: {n} rows, {rows[0][0] if rows else 'n/a'}..{rows[-1][0] if rows else 'n/a'}, {miss} with a missing field")


def fred(series, path, col):
    raw = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}").decode("utf-8", "replace")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    rows = []
    for ln in lines[1:]:
        parts = ln.split(",")
        d = parts[0].strip()
        dt.date.fromisoformat(d)
        v = parts[1].strip() if len(parts) > 1 else ""
        rows.append((d, None if v in ("", ".") else float(v)))
    rows.sort()
    if len(rows) < 500:
        raise SystemExit(f"{series}: only {len(rows)} rows")
    write_rows(path, ["DATE", col], rows)
    return rows


def eia(url, path):
    import pandas as pd
    raw = get(url)
    xl = pd.ExcelFile(io.BytesIO(raw))
    name = next((s for s in xl.sheet_names if s.lower().startswith("data")), xl.sheet_names[-1])
    df = xl.parse(name, header=None)
    hdr = next(i for i in range(min(10, len(df))) if str(df.iloc[i, 0]).strip().lower() == "date")
    rows = {}
    for i in range(hdr + 1, len(df)):
        try:
            d = pd.Timestamp(df.iloc[i, 0]).date().isoformat()
            v = float(df.iloc[i, 1])
        except Exception:  # noqa: BLE001
            continue
        if v == v:
            rows[d] = v
    rows = sorted(rows.items())
    if len(rows) < 500:
        raise SystemExit(f"{url}: only {len(rows)} rows")
    write_rows(path, ["DATE", "CLOSE"], rows)
    return rows


def yf_hist(sym):
    import yfinance as yf
    last = None
    for i in range(4):
        try:
            h = yf.Ticker(sym).history(period="max", auto_adjust=False, actions=False)
            if len(h) > 0:
                return h
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(3 + 3 * i)
    raise SystemExit(f"{sym}: no data ({last!r})")


def yahoo_close(sym, path):
    h = yf_hist(sym)
    rows = {}
    for idx, c in zip(h.index, h["Close"]):
        if c == c:
            rows[idx.date().isoformat()] = float(c)
    rows = sorted(rows.items())
    write_rows(path, ["DATE", "CLOSE"], rows)
    return rows


def yahoo_ohlc(sym, path):
    h = yf_hist(sym)
    rows = {}
    for idx, o, c, ac in zip(h.index, h["Open"], h["Close"], h["Adj Close"]):
        rows[idx.date().isoformat()] = (None if o != o else float(o), None if c != c else float(c), None if ac != ac else float(ac))
    rows = sorted((d, *v) for d, v in rows.items())
    write_rows(path, ["DATE", "OPEN", "CLOSE", "ADJCLOSE"], rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args()
    os.makedirs(a.data, exist_ok=True)
    for name, series in FRED.items():
        describe(f"{name} ({series})", fred(series, os.path.join(a.data, f"{name}.csv"), "RATE" if name == "tbill" else "VALUE"))
        time.sleep(1)
    for name, url in EIA.items():
        describe(f"{name} (EIA)", eia(url, os.path.join(a.data, f"{name}.csv")))
        time.sleep(1)
    for name, sym in YAHOO_CLOSE.items():
        describe(f"{name} ({sym})", yahoo_close(sym, os.path.join(a.data, f"{name}.csv")))
        time.sleep(1)
    describe("etp (VIXY)", yahoo_ohlc("VIXY", os.path.join(a.data, "etp.csv")))
    print("fetch complete")


if __name__ == "__main__":
    sys.exit(main())
