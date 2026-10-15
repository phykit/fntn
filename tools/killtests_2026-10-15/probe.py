"""Structure-only probe (second version) of the data sources for the kill tests of 15 October 2026.

The first probe established that Yahoo Finance keeps no expired futures contracts, so the curve
cannot come from Yahoo. This probe looks at EIA's daily NYMEX settlement series for contracts 1 to
4 (natural gas) and contract 1 (heating oil, RBOB), published as Excel files on eia.gov.

Prints row counts, date ranges, sheet layouts and availability. Prints no price, no return and no
outcome. The one near-exception is EIA's roll convention for "contract 1": for the last expiries it
reports, day by day around the computed expiry, whether contract 1 on day t equals contract 2 on
day t-1 (the switch), which compares two futures series and reveals nothing about spot or outcomes.

Usage: python probe.py --out out
"""
import argparse
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) fntn-side-test/1.0"
EIA = {
    "NG_C1": "https://www.eia.gov/dnav/ng/hist_xls/RNGC1d.xls",
    "NG_C2": "https://www.eia.gov/dnav/ng/hist_xls/RNGC2d.xls",
    "NG_C3": "https://www.eia.gov/dnav/ng/hist_xls/RNGC3d.xls",
    "NG_C4": "https://www.eia.gov/dnav/ng/hist_xls/RNGC4d.xls",
    "HO_C1": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2F_PE1_Y35NY_DPGd.xls",
    "RB_C1": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPMRR_PE1_Y35NY_DPGd.xls",
    "CL_C1": "https://www.eia.gov/dnav/pet/hist_xls/RCLC1d.xls",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def read_eia_xls(raw):
    """EIA hist_xls files: sheet 'Data 1' with a header row containing 'Date', then rows of date,
    value. Returns a dict date -> float and the sheet layout for the log."""
    import pandas as pd
    xl = pd.ExcelFile(io.BytesIO(raw))
    layout = {"sheets": xl.sheet_names}
    name = next((s for s in xl.sheet_names if s.lower().startswith("data")), xl.sheet_names[-1])
    df = xl.parse(name, header=None)
    hdr = None
    for i in range(min(10, len(df))):
        if str(df.iloc[i, 0]).strip().lower() == "date":
            hdr = i
            break
    layout["data_sheet"] = name
    layout["header_row"] = hdr
    layout["columns"] = [str(c) for c in (df.iloc[hdr].tolist() if hdr is not None else [])]
    out = {}
    if hdr is not None:
        for i in range(hdr + 1, len(df)):
            d, v = df.iloc[i, 0], df.iloc[i, 1]
            try:
                d = pd.Timestamp(d).date().isoformat()
            except Exception:  # noqa: BLE001
                continue
            try:
                v = float(v)
            except Exception:  # noqa: BLE001
                v = float("nan")
            out[d] = v
    return out, layout


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


def last_weekday(y, m):
    d = dt.date(y, m, 1) - dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def roll_convention(c1, c2, expiry_fn, label):
    """For the last 18 expiries: on each trading day from -3 to +3 around the computed expiry,
    '=' if c1[t] == c2[t-1] (contract 1 became yesterday's contract 2: the switch), '.' otherwise."""
    dates = sorted(d for d in c1 if d in c2 and c1[d] == c1[d] and c2[d] == c2[d])
    pos = {d: i for i, d in enumerate(dates)}
    today = dt.date.fromisoformat(dates[-1])
    rows = []
    y, m = today.year, today.month
    for _ in range(18):
        X = expiry_fn(y, m)
        import bisect
        k = bisect.bisect_right(dates, X.isoformat()) - 1
        if k >= 4 and k + 3 < len(dates):
            line = ""
            for off in range(-3, 4):
                t = k + off
                a, b = c1[dates[t]], c2[dates[t - 1]]
                line += "=" if abs(a - b) < 1e-9 else "."
            rows.append((f"{y}-{m:02d}", X.isoformat(), dates[k], line))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    print(f"  {label} roll convention, offsets -3..+3 trading days around the computed expiry ('=' means c1[t] == c2[t-1]):")
    for r in rows:
        print(f"    delivery {r[0]} computed expiry {r[1]} last data day on/before {r[2]}: {r[3]}")
    return rows


def yf_hist(sym):
    import yfinance as yf
    for i in range(3):
        try:
            return yf.Ticker(sym).history(period="max", auto_adjust=False, actions=False)
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


def http_probe(url):
    try:
        b = get(url)
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
    print("== EIA daily NYMEX settlement series (Excel)")
    series = {}
    for name, url in EIA.items():
        try:
            raw = get(url)
            data, layout = read_eia_xls(raw)
            series[name] = data
            ds = sorted(d for d, v in data.items() if v == v)
            print(f"  {name}: {len(raw)} bytes; sheets {layout['sheets']}; data sheet {layout['data_sheet']} header row {layout['header_row']} "
                  f"columns {layout['columns'][:3]}; {len(data)} rows, {len(ds)} numeric, {ds[0] if ds else 'n/a'}..{ds[-1] if ds else 'n/a'}")
            rep[name] = {"rows": len(data), "numeric": len(ds), "first": ds[0] if ds else None, "last": ds[-1] if ds else None, "layout": layout}
        except Exception as e:  # noqa: BLE001
            print(f"  {name}: {type(e).__name__}: {str(e)[:120]}")
            rep[name] = {"error": str(e)[:200]}
        time.sleep(1)
    if "NG_C1" in series and "NG_C2" in series:
        rep["ng_roll"] = roll_convention(series["NG_C1"], series["NG_C2"], ng_expiry, "NG")
    print("== Volatility (Yahoo)")
    for sym in ("^VIX", "^VIX3M", "^VIX9D", "VIXY", "VXX", "SVXY", "UVXY", "VX=F"):
        rep[sym] = describe(sym, yf_hist(sym))
        time.sleep(0.5)
    print("== CBOE VX historical CSVs (two expiries)")
    for d in ("2026-09-16", "2025-01-22"):
        http_probe(f"https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{d}.csv")
    print("== Crypto (Yahoo)")
    for sym in ("BTC-USD", "BTC=F", "ETH-USD", "ETH=F"):
        rep[sym] = describe(sym, yf_hist(sym))
        time.sleep(0.5)
    with open(os.path.join(a.out, "probe.json"), "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True, default=str)
    print("probe complete")


if __name__ == "__main__":
    sys.exit(main())
