"""Fetch the inputs of test C2 to a data directory on the runner. Prints structure only.
Usage: python fetch_c2.py --data data
"""
import argparse
import csv
import datetime as dt
import io
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cal  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) fntn-side-test/1.0"
BASE = "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{}.csv"


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(2 * (i + 1))
    raise SystemExit(f"fetch failed for {url}: {last!r}")


def prev_bday(d):
    d -= dt.timedelta(days=1)
    while not cal.is_business_day(d):
        d -= dt.timedelta(days=1)
    return d


def next_bday(d):
    d += dt.timedelta(days=1)
    while not cal.is_business_day(d):
        d += dt.timedelta(days=1)
    return d


def vx_expiry(y, m):
    """Thirty days before the third Friday of the following month (or the business day before that
    Friday if it is a holiday); if the result is a holiday, the preceding business day."""
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    f3 = cal.nth_weekday(ny, nm, 4, 3)
    if not cal.is_business_day(f3):
        f3 = prev_bday(f3)
    x = f3 - dt.timedelta(days=30)
    if not cal.is_business_day(x):
        x = prev_bday(x)
    return x


def yf_hist(sym):
    import yfinance as yf
    last = None
    for i in range(4):
        try:
            h = yf.Ticker(sym).history(period="max", auto_adjust=False, actions=False)
            if len(h) > 0:
                return h
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(3 + 3 * i)
    raise SystemExit(f"{sym}: no data ({last!r})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args()
    os.makedirs(a.data, exist_ok=True)
    today = dt.date.today()
    months = cal.months_between(dt.date(2013, 1, 1), (today + dt.timedelta(days=32)).replace(day=1))
    rows = []
    found = []
    for (y, m) in months:
        x0 = vx_expiry(y, m)
        cands = [x0, prev_bday(x0), prev_bday(prev_bday(x0)), next_bday(x0)]
        got = None
        for x in cands:
            raw = get(BASE.format(x.isoformat()))
            time.sleep(0.3)
            if raw is not None and len(raw) > 100:
                got = x
                break
        if got is None:
            print(f"{y}-{m:02d}: no file for computed expiry {x0} (tried {[c.isoformat() for c in cands]})")
            continue
        text = raw.decode("utf-8", "replace")
        rd = csv.DictReader(io.StringIO(text))
        n = 0
        for r in rd:
            d = (r.get("Trade Date") or "").strip()
            s = (r.get("Settle") or "").strip()
            try:
                dd = dt.date.fromisoformat(d)
                v = float(s)
            except Exception:  # noqa: BLE001
                continue
            rows.append((dd.isoformat(), got.isoformat(), v))
            n += 1
        found.append(got)
        print(f"{y}-{m:02d}: expiry file {got} ({'as computed' if got == x0 else 'shifted from ' + x0.isoformat()}), {n} rows")
    rows.sort()
    with open(os.path.join(a.data, "vx.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "EXPIRY", "SETTLE"])
        for r in rows:
            w.writerow([r[0], r[1], repr(r[2])])
    print(f"vx.csv: {len(rows)} contract-days, {len(found)} monthly contracts, expiries {found[0] if found else 'n/a'}..{found[-1] if found else 'n/a'}")
    h = yf_hist("^VIX")
    with open(os.path.join(a.data, "vix.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "CLOSE"])
        for idx, c in zip(h.index, h["Close"]):
            if c == c:
                w.writerow([idx.date().isoformat(), repr(float(c))])
    print(f"vix: {len(h)} rows, {h.index[0].date()}..{h.index[-1].date()}")
    h = yf_hist("VIXY")
    with open(os.path.join(a.data, "etp.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "OPEN", "CLOSE", "ADJCLOSE"])
        for idx, o, c, ac in zip(h.index, h["Open"], h["Close"], h["Adj Close"]):
            w.writerow([idx.date().isoformat()] + ["" if v != v else repr(float(v)) for v in (o, c, ac)])
    print(f"etp (VIXY): {len(h)} rows, {h.index[0].date()}..{h.index[-1].date()}")
    print("fetch complete")


if __name__ == "__main__":
    main()
