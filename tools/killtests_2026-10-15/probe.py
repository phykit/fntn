"""Structure-only probe of the data sources the four kill tests of 15 October 2026 would use.

Prints row counts, date ranges and availability. Prints no price, no return and no outcome. The one
near-exception is the roll convention of Yahoo's continuous `NG=F`: for each of the last expiries it
reports, day by day around expiry, whether the continuous close EQUALS the expiring contract's close,
the next contract's close, or neither. That is a comparison between two futures series and reveals
nothing about spot or about any outcome.

Usage: python probe.py --out out
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.request

MONTH_CODES = "FGHJKMNQUVXZ"
UA = "Mozilla/5.0 (X11; Linux x86_64) fntn-side-test/1.0"


def yf_hist(sym, period="max"):
    import yfinance as yf
    for i in range(3):
        try:
            h = yf.Ticker(sym).history(period=period, auto_adjust=False, actions=False)
            return h
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + 2 * i)
    print(f"  {sym}: failed: {type(last).__name__}: {str(last)[:100]}")
    return None


def describe(sym, h):
    if h is None or len(h) == 0:
        print(f"  {sym}: no data")
        return 0
    print(f"  {sym}: {len(h)} rows, {h.index[0].date()}..{h.index[-1].date()}")
    return len(h)


def contracts(root, exch, y0, y1, keep_from=None, keep=None):
    out = {}
    for y in range(y0, y1 + 1):
        for i, c in enumerate(MONTH_CODES):
            sym = f"{root}{c}{y % 100:02d}.{exch}"
            h = yf_hist(sym)
            n = 0 if h is None else int(len(h))
            first = "" if n == 0 else str(h.index[0].date())
            last = "" if n == 0 else str(h.index[-1].date())
            out[sym] = {"n": n, "first": first, "last": last}
            if keep is not None and keep_from is not None and n > 0 and y >= keep_from:
                keep[sym] = h
            time.sleep(0.4)
    return out


def summarise_contracts(root, out):
    by_year = {}
    for sym, v in out.items():
        y = 2000 + int(sym[len(root) + 1: len(root) + 3])
        by_year.setdefault(y, []).append(v["n"])
    print(f"  {root}: contracts with any data per year:",
          {y: f"{sum(1 for n in ns if n > 0)}/12" for y, ns in sorted(by_year.items())})
    lens = sorted(v["n"] for v in out.values() if v["n"] > 0)
    if lens:
        print(f"  {root}: rows per contract with data: min {lens[0]} median {lens[len(lens)//2]} max {lens[-1]}")
    firsts = sorted(v["first"] for v in out.values() if v["n"] > 0)
    if firsts:
        print(f"  {root}: earliest first date among contracts with data: {firsts[0]}")


def ng_expiry(y, m):
    first = dt.date(y, m, 1)
    d = first - dt.timedelta(days=1)
    n = 0
    while True:
        if d.weekday() < 5:
            n += 1
            if n == 3:
                return d
        d -= dt.timedelta(days=1)


def roll_convention(cont, con):
    """For each expiring contract with data, say on which days around its expiry the continuous
    close equals the expiring contract's close (E), the next contract's close (N), both (B), or
    neither (-). Positions are trading days of the continuous series relative to the expiry day."""
    import pandas as pd
    cont_close = cont["Close"]
    rows = []
    for y in range(2023, 2027):
        for m in range(1, 13):
            dm = dt.date(y, m, 1)
            X = ng_expiry(y, m)
            code = MONTH_CODES[m - 1]
            sym_e = f"NG{code}{y % 100:02d}.NYM"
            nm = m + 1
            ny = y
            if nm == 13:
                nm, ny = 1, y + 1
            sym_n = f"NG{MONTH_CODES[nm - 1]}{ny % 100:02d}.NYM"
            he, hn = con.get(sym_e), con.get(sym_n)
            if he is None or hn is None or len(he) == 0 or len(hn) == 0:
                continue
            idx = cont_close.index
            k = idx.searchsorted(pd.Timestamp(X), side="right") - 1
            if k < 6 or k + 3 >= len(idx):
                continue
            line = []
            for off in range(-6, 3):
                d = idx[k + off]
                c = float(cont_close.iloc[k + off])
                e = he["Close"].get(d) if d in he.index else None
                n_ = hn["Close"].get(d) if d in hn.index else None
                me = e is not None and abs(float(e) - c) < 1e-6 * max(1.0, c)
                mn = n_ is not None and abs(float(n_) - c) < 1e-6 * max(1.0, c)
                line.append("B" if (me and mn) else "E" if me else "N" if mn else "-")
            rows.append((sym_e, X.isoformat(), "".join(line)))
    print("  NG=F roll convention, offsets -6..+2 trading days around expiry (E expiring, N next, B both, - neither):")
    for r in rows:
        print(f"    {r[0]} expiry {r[1]}: {r[2]}")
    return rows


def http_probe(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            b = r.read()
        text = b.decode("utf-8", "replace")
        print(f"  {url}: HTTP 200, {len(b)} bytes, {text.count(chr(10))} lines, header: {text.splitlines()[0][:80] if text else ''}")
    except Exception as e:  # noqa: BLE001
        print(f"  {url}: {type(e).__name__}: {str(e)[:80]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = {}

    print("== Individual contracts on Yahoo (NG, HO, RB), 2015 to 2027")
    con_all = {}
    for root in ("NG", "HO", "RB"):
        out = contracts(root, "NYM", 2015, 2027, keep_from=2023 if root == "NG" else None, keep=con_all)
        rep[f"{root}_contracts"] = out
        summarise_contracts(root, out)

    print("== Continuous series")
    cont = yf_hist("NG=F")
    describe("NG=F", cont)
    if cont is not None and con_all:
        rep["ng_roll_convention"] = roll_convention(cont, con_all)

    print("== Volatility")
    for sym in ("^VIX", "^VIX3M", "^VIX9D", "VIXY", "VXX", "SVXY", "UVXY", "VX=F"):
        rep[sym] = describe(sym, yf_hist(sym))
        time.sleep(0.4)
    print("== CBOE VX historical CSVs (two recent expiries)")
    for d in ("2026-09-16", "2025-01-22"):
        http_probe(f"https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{d}.csv")

    print("== Crypto")
    for sym in ("BTC-USD", "BTC=F", "ETH-USD", "ETH=F", "MBT=F"):
        rep[sym] = describe(sym, yf_hist(sym))
        time.sleep(0.4)
    print("== CME bitcoin individual contracts (BTC, CME), 2018 to 2027")
    btc = contracts("BTC", "CME", 2018, 2027)
    rep["BTC_contracts"] = btc
    summarise_contracts("BTC", btc)

    with open(os.path.join(a.out, "probe.json"), "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True, default=str)
    print("probe complete")


if __name__ == "__main__":
    sys.exit(main())
