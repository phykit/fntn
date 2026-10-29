"""Fetch HYG, IEF and QQQ adjusted closes (Yahoo via yfinance) to DATA_DIR/prices.csv. Structure
printed, never a price. Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import os
import sys


def main(argv=None):
    import yfinance as yf
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    ser = {}
    for s in ("HYG", "IEF", "QQQ"):
        h = yf.Ticker(s).history(start="2002-01-01", auto_adjust=True)
        ser[s] = {ts.date().isoformat(): float(v) for ts, v in zip(h.index, h["Close"]) if v == v}
        k = sorted(ser[s])
        print(f"{s}: {len(k)} rows, {k[0]} to {k[-1]}")
    days = sorted(set(ser["QQQ"]))
    with open(os.path.join(a.data, "prices.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "HYG", "IEF", "QQQ"])
        for d in days:
            w.writerow([d] + [repr(ser[s][d]) if d in ser[s] else "" for s in ("HYG", "IEF", "QQQ")])
    print(f"prices.csv: {len(days)} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
