"""Fetch the inputs of tools/single_name_vrp/PREREG.md section 2 and write data/vx.csv and
data/prices.csv. Prints structure only (first and last date and non-missing count per column),
never a value, so that nothing about the outcome is seen before the frozen test runs."""
from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import urllib.request

FRED = {"AAPL": "VXAPLCLS", "AMZN": "VXAZNCLS", "GOOG": "VXGOGCLS", "GS": "VXGSCLS",
        "IBM": "VXIBMCLS", "MKT": "VIXCLS"}
TICKERS = ["AAPL", "AMZN", "GOOG", "GS", "IBM", "SPY"]


def get(url: str, tries: int = 5) -> bytes:
    """Fetch with retries. Added after run 1, in which FRED timed out on the runner before any
    data was read; the precedent is tools/degross_proxy/fetch.py on degross-proxy-2026-10-29."""
    import time
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


def fred(series: str) -> dict[str, float]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    print(f"{series}: fetching")
    text = get(url).decode("utf-8")
    out = {}
    rows = list(csv.reader(io.StringIO(text)))
    for row in rows[1:]:
        if len(row) < 2:
            continue
        d, v = row[0].strip(), row[1].strip()
        if v in ("", "."):
            continue  # FRED's missing marker stays missing (PREREG section 2)
        out[d] = float(v)
    return out


def prices() -> dict[str, dict[str, float]]:
    import yfinance as yf
    df = yf.download(TICKERS, start="2009-01-01", auto_adjust=True, progress=False, group_by="column")
    close = df["Close"]
    out = {t: {} for t in TICKERS}
    for idx, row in close.iterrows():
        d = idx.strftime("%Y-%m-%d")
        for t in TICKERS:
            v = row.get(t)
            if v is not None and v == v:
                out[t][d] = float(v)
    return out


def write(path: str, cols: list[str], data: dict[str, dict[str, float]]) -> None:
    dates = sorted(set().union(*[set(data[c]) for c in cols]))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + cols)
        for d in dates:
            w.writerow([d] + [repr(data[c][d]) if d in data[c] else "" for c in cols])
    print(f"{os.path.basename(path)}: {len(dates)} rows")
    for c in cols:
        ds = sorted(data[c])
        print(f"  {c}: {len(ds)} non-missing, {ds[0] if ds else 'n/a'} to {ds[-1] if ds else 'n/a'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    vx = {k: fred(s) for k, s in FRED.items()}
    write(os.path.join(a.data, "vx.csv"), list(FRED), vx)
    px = prices()
    write(os.path.join(a.data, "prices.csv"), TICKERS, px)
    return 0


if __name__ == "__main__":
    sys.exit(main())
