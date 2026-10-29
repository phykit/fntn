"""Fetch FRED NASDAQ100, the French daily factors and QQQ adjusted closes. Structure printed only.
Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    import yfinance as yf
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("fetch_h", os.path.join(HERE, "..", "halloween", "fetch.py"))
    fh_ = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fh_)
    fh_.main(["--data", a.data])
    h = yf.Ticker("QQQ").history(start="1999-01-01", auto_adjust=True)
    with open(os.path.join(a.data, "qqq.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "QQQ"])
        for ts, v in zip(h.index, h["Close"]):
            if v == v:
                w.writerow([ts.date().isoformat(), repr(float(v))])
    print(f"QQQ: {len(h)} rows, {h.index[0].date()} to {h.index[-1].date()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
