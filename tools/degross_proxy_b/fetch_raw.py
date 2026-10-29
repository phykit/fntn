"""Fetch Version B's raw inputs on the runner (PREREG section 2): the 54 Form 13F data sets, the
fails-to-deliver files from 2012, SPY daily adjusted closes and the FRED Nasdaq 100 series.

Prints file names, counts, sizes and date ranges only, never an observation value. Refuses (exit 2)
without SEC_CONTACT, because sec.gov's fair-access policy requires a real contact and a placeholder
would be a false statement to the server.

Usage: python fetch_raw.py --data DATA_DIR
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import time
import urllib.request

SEC_UA = os.environ.get("SEC_CONTACT", "").strip()
I13F = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
IFTD = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
NDX = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100"


class Refusal(Exception):
    pass


def get(url, headers, tries=5, timeout=180):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  attempt {i + 1} failed for {url.rsplit('/', 1)[-1]}: {type(e).__name__}")
            time.sleep(10 * (i + 1))
    raise Refusal(f"{url}: no response after {tries} attempts ({type(last).__name__})")


def sec(url):
    time.sleep(0.25)  # well inside sec.gov's ten requests a second
    return get(url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})


def absolute(link):
    return link if link.startswith("http") else "https://www.sec.gov" + link


def fetch_13f(d):
    os.makedirs(d, exist_ok=True)
    html = sec(I13F).decode("utf-8", "replace")
    links = sorted(set(re.findall(r'href="([^"]+_form13f\.zip)"', html)))
    print(f"13F: {len(links)} files listed")
    if len(links) < 54:
        raise Refusal(f"13F: expected at least 54 files, found {len(links)}")
    total = 0
    for l in links:
        name = l.rsplit("/", 1)[-1]
        blob = sec(absolute(l))
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(blob)
        total += len(blob)
    print(f"13F: {len(links)} files, {total / 1e9:.2f} GB")


def fetch_ftd(d):
    os.makedirs(d, exist_ok=True)
    html = sec(IFTD).decode("utf-8", "replace")
    links = sorted(set(re.findall(r'href="([^"]*cnsfails(\d{6})[ab]?\.zip)"', html)))
    keep = [l for l, ym in links if int(ym[:4]) >= 2012]
    print(f"FTD: {len(links)} files listed, {len(keep)} from 2012")
    names = set()
    for l in keep:
        name = l.rsplit("/", 1)[-1]
        if name in names:
            continue
        names.add(name)
        try:
            blob = sec(absolute(l))
        except Refusal as e:
            print("  FTD file skipped:", name, e)
            continue
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(blob)
    print(f"FTD: {len(os.listdir(d))} files written")


def fetch_spy(path):
    import yfinance as yf
    h = yf.Ticker("SPY").history(start="2012-01-01", auto_adjust=True)
    if len(h) < 3000:
        raise Refusal(f"SPY: only {len(h)} rows")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "SPY"])
        for ts, v in zip(h.index, h["Close"]):
            w.writerow([ts.date().isoformat(), repr(float(v))])
    print(f"SPY: {len(h)} rows, {h.index[0].date()} to {h.index[-1].date()}")


def fetch_ndx(path):
    text = get(NDX, {"User-Agent": "Mozilla/5.0 (fntn side test)", "Accept": "*/*"}).decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    if rows[0][1] != "NASDAQ100":
        raise Refusal("NDX: unexpected header")
    out = [[r[0], "" if r[1].strip() in ("", ".") else r[1].strip()] for r in rows[1:]]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "NASDAQ100"])
        w.writerows(out)
    print(f"NDX: {len(out)} rows, {out[0][0]} to {out[-1][0]}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    if not SEC_UA:
        print("REFUSED: SEC_CONTACT is not set")
        return 2
    os.makedirs(a.data, exist_ok=True)
    try:
        fetch_13f(os.path.join(a.data, "13f"))
        fetch_ftd(os.path.join(a.data, "ftd"))
        fetch_spy(os.path.join(a.data, "spy.csv"))
        fetch_ndx(os.path.join(a.data, "ndx.csv"))
    except Refusal as e:
        print("REFUSED:", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
