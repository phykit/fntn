"""Fetch the inputs named in PREREG.md section 2 to a data directory on the runner.

Prints structure only (row counts, date ranges, missing counts): never a value.
Usage: python fetch.py --data data
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zoneinfo

FRED = {"ng_spot": "DHHNGSP", "ho_spot": "DHOILNYH", "rb_spot": "DGASNYH", "tbill": "DTB3"}
YAHOO = {"ng_fut": "NG=F", "ho_fut": "HO=F", "rb_fut": "RB=F"}
UA = "Mozilla/5.0 (X11; Linux x86_64) fntn-side-test/1.0"


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
        for d, v in rows:
            w.writerow([d, "" if v is None else repr(v)])


def describe(name, rows):
    n = len(rows)
    miss = sum(1 for _, v in rows if v is None)
    first = rows[0][0] if rows else "n/a"
    last = rows[-1][0] if rows else "n/a"
    print(f"{name}: {n} rows, {first}..{last}, {miss} missing")


def fred(series, path):
    raw = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}").decode("utf-8", "replace")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    hdr = lines[0].split(",")
    if len(hdr) < 2:
        raise SystemExit(f"{series}: unexpected header {hdr!r}")
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
    write_rows(path, ["DATE", "VALUE" if series != "DTB3" else "RATE"], rows)
    return rows


def yahoo_chart(sym):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
           f"?range=max&interval=1d&includeAdjustedClose=false")
    j = json.loads(get(url).decode("utf-8"))
    res = j["chart"]["result"][0]
    tz = zoneinfo.ZoneInfo(res["meta"]["exchangeTimezoneName"])
    ts = res["timestamp"]
    close = res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(ts, close):
        d = dt.datetime.fromtimestamp(t, tz).date().isoformat()
        if c is None:
            continue
        rows[d] = float(c)        # a later bar for the same date overwrites an earlier one
    return sorted(rows.items())


def yahoo_yf(sym):
    import yfinance as yf
    h = yf.Ticker(sym).history(period="max", auto_adjust=False, actions=False)
    rows = {}
    for idx, c in zip(h.index, h["Close"]):
        if c != c:
            continue
        rows[idx.date().isoformat()] = float(c)
    return sorted(rows.items())


def yahoo(sym, path):
    rows, how = None, None
    for fn, label in ((yahoo_chart, "chart api"), (yahoo_yf, "yfinance")):
        try:
            rows = fn(sym)
            how = label
            if len(rows) >= 500:
                break
            print(f"{sym}: {label} returned only {len(rows)} rows, trying the next route")
            rows = None
        except Exception as e:  # noqa: BLE001
            print(f"{sym}: {label} failed: {type(e).__name__}: {str(e)[:120]}")
            rows = None
    if rows is None:
        raise SystemExit(f"{sym}: no route returned data")
    write_rows(path, ["DATE", "CLOSE"], rows)
    print(f"{sym}: via {how}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args()
    os.makedirs(a.data, exist_ok=True)
    for name, series in FRED.items():
        describe(f"{name} ({series})", fred(series, os.path.join(a.data, f"{name}.csv")))
    for name, sym in YAHOO.items():
        describe(f"{name} ({sym})", yahoo(sym, os.path.join(a.data, f"{name}.csv")))
    print("fetch complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
