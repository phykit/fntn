"""Fetch the inputs of tools/vrp_benchmarks/PREREG.md section 2: CBOE PUT, WPUT and CNDR, Yahoo SPY and ^IRX.
Writes data/series.csv (date, SPY, IRX, PUT, WPUT, CNDR); prints structure only."""
from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
import urllib.request

BASE = "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{}_History.csv"


def get(url: str, tries: int = 5) -> bytes:
    """Retries, as the earlier fetchers in this thread, which met slow upstream servers."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90) as f:
                return f.read()
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  attempt {i + 1} failed: {type(e).__name__}")
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"{url}: no response after {tries} attempts ({type(last).__name__})")


def cboe(index: str, col: str) -> dict[str, float]:
    print(f"{index}: fetching")
    rows = list(csv.reader(io.StringIO(get(BASE.format(index)).decode("utf-8"))))
    head = [h.strip().upper() for h in rows[0]]
    if "DATE" not in head or col not in head:
        raise RuntimeError(f"{index}: unexpected header {head}")
    di, ci = head.index("DATE"), head.index(col)
    out = {}
    for row in rows[1:]:
        if len(row) <= max(di, ci):
            continue
        try:
            m, d, y = row[di].strip().split("/")
            out[f"{int(y):04d}-{int(m):02d}-{int(d):02d}"] = float(row[ci].strip())
        except ValueError:
            continue  # a blank or non-numeric value stays missing
    return out


def yahoo(sym: str) -> dict[str, float]:
    import yfinance as yf
    df = yf.download([sym], start="2005-01-01", auto_adjust=True, progress=False, group_by="column")
    close = df["Close"]
    col = close[sym] if hasattr(close, "columns") else close
    return {i.strftime("%Y-%m-%d"): float(v) for i, v in col.items() if v == v}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    data = {"SPY": yahoo("SPY"), "IRX": yahoo("^IRX"), "PUT": cboe("PUT", "PUT"), "WPUT": cboe("WPUT", "WPUT"),
            "CNDR": cboe("CNDR", "CNDR")}
    cols = list(data)
    dates = sorted(set().union(*[set(v) for v in data.values()]))
    with open(os.path.join(a.data, "series.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + cols)
        for d in dates:
            w.writerow([d] + [repr(data[c][d]) if d in data[c] else "" for c in cols])
    print(f"series.csv: {len(dates)} rows")
    for c in cols:
        ds = sorted(data[c])
        print(f"  {c}: {len(ds)} non-missing, {ds[0] if ds else 'n/a'} to {ds[-1] if ds else 'n/a'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
