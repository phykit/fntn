"""Fetch daily adjusted closes for every basket symbol (PREREG section 2) and write data/prices.csv
on SPY's trading days. Prints counts only, never a price.

Usage: python fetch_prices.py --data DATA_DIR
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time


def main(argv=None):
    import yfinance as yf

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    with open(os.path.join(a.data, "spy.csv"), newline="") as fh:
        spy = [r for r in list(csv.reader(fh))[1:] if r[1].strip()]
    days = [r[0] for r in spy]
    with open(os.path.join(a.data, "baskets.csv"), newline="") as fh:
        syms = sorted({r["symbol"] for r in csv.DictReader(fh)} - {"SPY"})
    print(f"symbols to fetch: {len(syms)}")
    series = {}
    batch = 40
    for k in range(0, len(syms), batch):
        chunk = syms[k:k + batch]
        for attempt in range(3):
            try:
                df = yf.download(chunk, start="2013-01-01", auto_adjust=True, progress=False,
                                 group_by="ticker", threads=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"  batch {k // batch} attempt {attempt + 1}: {type(e).__name__}")
                time.sleep(15 * (attempt + 1))
        else:
            continue
        for s in chunk:
            try:
                col = df[s]["Close"] if len(chunk) > 1 else df["Close"]
            except Exception:  # noqa: BLE001
                continue
            col = col.dropna()
            if len(col):
                series[s] = {ts.date().isoformat(): float(v) for ts, v in col.items()}
        time.sleep(2)
    missing = [s for s in syms if s not in series]
    print(f"priced: {len(series)} of {len(syms)}; without any price: {len(missing)}")
    cols = ["SPY"] + sorted(series)
    with open(os.path.join(a.data, "prices.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE"] + cols)
        for d, r in zip(days, spy):
            w.writerow([d, r[1]] + [repr(series[s][d]) if d in series[s] else "" for s in cols[1:]])
    print(f"prices.csv: {len(days)} days, {len(cols)} columns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
