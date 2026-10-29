"""Fetch the current S&P 500 constituents (Wikipedia), their adjusted closes and ex-dividend events
from 2000 (Yahoo via yfinance, actions=True), and the French daily factors. Structure printed only.
Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import importlib.util
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import fetch_extra as fx  # noqa: E402

WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def constituents():
    req = urllib.request.Request(WIKI, headers={"User-Agent": "Mozilla/5.0 (fntn side test)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        html = r.read().decode("utf-8", "replace")
    table = html.split('id="constituents"', 1)[1].split("</table>", 1)[0]
    syms = re.findall(r'<a [^>]*href="https://www\.nyse\.com/quote/[^"]*"[^>]*>([A-Z.\-]+)</a>|<a [^>]*href="https://www\.nasdaq\.com/market-activity/stocks/[^"]*"[^>]*>([A-Z.\-]+)</a>', table)
    out = sorted({(x or y).replace(".", "-") for x, y in syms})
    if len(out) < 400:
        raise SystemExit(f"structure: only {len(out)} constituents parsed")
    return out


def main(argv=None):
    import pandas as pd
    import yfinance as yf
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    zipname, cols = fx.FILES["ff5_daily.csv"]
    fx.french(a.data, "ff5_daily.csv", zipname, cols)
    syms = constituents()
    print(f"constituents: {len(syms)}")
    spy = yf.Ticker("SPY").history(start="2000-01-01", auto_adjust=True)
    days = [ts.date().isoformat() for ts in spy.index]
    closes, divs = {}, []
    batch = 50
    for k in range(0, len(syms), batch):
        chunk = syms[k:k + batch]
        for attempt in range(3):
            try:
                df = yf.download(chunk, start="2000-01-01", auto_adjust=True, actions=True, progress=False, group_by="ticker", threads=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"  batch {k // batch} attempt {attempt + 1}: {type(e).__name__}")
                time.sleep(15 * (attempt + 1))
        else:
            continue
        for s in chunk:
            try:
                sub = df[s] if len(chunk) > 1 else df
            except KeyError:
                continue
            if "Close" not in sub:
                continue
            c = sub["Close"].dropna()
            closes[s] = {ts.date().isoformat(): float(v) for ts, v in zip(c.index, c.values)}
            if "Dividends" in sub:
                dv = sub["Dividends"]
                for ts, v in zip(dv.index, dv.values):
                    if v == v and v > 0:
                        divs.append((s, ts.date().isoformat(), float(v)))
        time.sleep(2)
    have = [s for s in syms if s in closes]
    with open(os.path.join(a.data, "prices.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE"] + have)
        for d in days:
            w.writerow([d] + [repr(closes[s][d]) if d in closes[s] else "" for s in have])
    with open(os.path.join(a.data, "dividends.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "ex_date", "amount"])
        w.writerows(sorted(divs))
    print(f"prices.csv: {len(days)} days x {len(have)} tickers; dividends.csv: {len(divs)} events for {len({d[0] for d in divs})} tickers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
