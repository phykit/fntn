"""Fetch the French daily momentum factor and MTUM/SPY closes. Structure printed, never a value.
Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import fetch_extra as fx  # noqa: E402


def main(argv=None):
    import yfinance as yf
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    zipname, cols = fx.FILES["mom_daily.csv"]
    fx.french(a.data, "mom_daily.csv", zipname, cols)
    ser = {}
    for s in ("MTUM", "SPY"):
        h = yf.Ticker(s).history(start="2010-01-01", auto_adjust=True)
        ser[s] = {ts.date().isoformat(): float(v) for ts, v in zip(h.index, h["Close"]) if v == v}
        k = sorted(ser[s])
        print(f"{s}: {len(k)} rows, {k[0]} to {k[-1]}")
    days = sorted(ser["SPY"])
    with open(os.path.join(a.data, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "MTUM", "SPY"])
        for d in days:
            w.writerow([d] + [repr(ser[s][d]) if d in ser[s] else "" for s in ("MTUM", "SPY")])
    print(f"bench.csv: {len(days)} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
