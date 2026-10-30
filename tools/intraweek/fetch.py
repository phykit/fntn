"""Fetch GVIP, QQQ, MTUM and SPY adjusted closes (Yahoo) for the intra-week persistence test.
Writes bench.csv (DATE,GVIP,QQQ,MTUM,SPY on SPY trading days, blank where missing). Structure
printed, never a value.

Usage: python fetch.py --data DATA_DIR
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

TICKERS = ("GVIP", "QQQ", "MTUM", "SPY")


def main(argv=None):
    import yfinance as yf

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    ser = {}
    for s in TICKERS:
        h = yf.Ticker(s).history(start="2012-01-01", auto_adjust=True)
        ser[s] = {ts.date().isoformat(): float(v) for ts, v in zip(h.index, h["Close"]) if v == v and v > 0}
        if not ser[s]:
            print(f"{s}: no rows returned", file=sys.stderr)
            return 2
        k = sorted(ser[s])
        print(f"{s}: {len(k)} rows, {k[0]} to {k[-1]}")
    days = sorted(ser["SPY"])
    with open(os.path.join(a.data, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", *TICKERS])
        for d in days:
            w.writerow([d] + [repr(ser[s][d]) if d in ser[s] else "" for s in TICKERS])
    print(f"bench.csv: {len(days)} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
