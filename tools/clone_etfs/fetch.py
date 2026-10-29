"""Fetch the 13F-copycat ETFs of PREREG section 1, the benchmarks and the French daily factors.
Yahoo first; Stooq's daily CSV when Yahoo returns nothing. Writes data/funds.csv (DATE plus one
column per ticker, on SPY's trading days) and data/sources.json. Prints structure only (rows, first
and last date, source), never a price.

Usage: python fetch.py --data DATA_DIR
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import fetch_extra as fx  # noqa: E402  the VIP test's French-factor fetcher

FUNDS = ("GURU", "ACTX", "GURI", "ALFA", "ALFI", "IBLN")
REF = ("GVIP", "SPY", "QQQ", "RSP")


def yahoo(sym):
    import yfinance as yf
    try:
        h = yf.Ticker(sym).history(start="2010-01-01", auto_adjust=True)
    except Exception:  # noqa: BLE001
        return {}
    return {ts.date().isoformat(): float(v) for ts, v in zip(h.index, h["Close"]) if v == v}


def stooq(sym):
    url = f"https://stooq.com/q/d/l/?s={sym.lower()}.us&i=d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fntn side test)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"  stooq {sym}: {type(e).__name__}")
        return {}
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or not rows[0] or rows[0][0] != "Date":
        print(f"  stooq {sym}: no CSV returned")
        return {}
    ci = rows[0].index("Close")
    return {r[0]: float(r[ci]) for r in rows[1:] if len(r) > ci and r[ci]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    for out, (zipname, cols) in fx.FILES.items():
        fx.french(a.data, out, zipname, cols)
    ser, src = {}, {}
    for s in FUNDS + REF:
        v = yahoo(s)
        src[s] = "yahoo"
        if not v and s in FUNDS:
            v = stooq(s)
            src[s] = "stooq" if v else "none"
        ser[s] = v
        if v:
            ks = sorted(v)
            print(f"{s}: {len(v)} rows, {ks[0]} to {ks[-1]}, source {src[s]}")
        else:
            print(f"{s}: no history from either source")
    days = sorted(ser["SPY"])
    cols = FUNDS + REF
    with open(os.path.join(a.data, "funds.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", *cols])
        for d in days:
            w.writerow([d] + [repr(ser[s][d]) if d in ser[s] else "" for s in cols])
    json.dump(src, open(os.path.join(a.data, "sources.json"), "w"))
    print(f"funds.csv: {len(days)} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
