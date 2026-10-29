"""Metadata probe for Version B of the de-gross proxy, run before its pre-registration is written.

Prints availability, file names, sizes, column headers, row counts and date ranges only; never an
observation value, a price or a holding. Its purpose is that PREREG.md names inputs that exist.
Every check reports OK or MISSING and the probe never raises, so one failure does not hide the rest.

Environment: SEC_CONTACT (SEC fair-access User-Agent, required for sec.gov), EODHD_KEY.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile

SEC_UA = os.environ.get("SEC_CONTACT", "")
EOD = os.environ.get("EODHD_KEY", "")


def get(url, headers=None, data=None, tries=3, timeout=120):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {}, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    return None, repr(type(last).__name__).encode()


def sec(url):
    return get(url, {"User-Agent": SEC_UA, "Accept-Encoding": "identity"})


def section(t):
    print(f"\n== {t}")


def p13f():
    section("SEC Form 13F data sets")
    if not SEC_UA:
        print("MISSING SEC_CONTACT; sec.gov not queried")
        return
    st, body = sec("https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets")
    print("index status", st)
    links = sorted(set(re.findall(r'href="([^"]+\.zip)"', body.decode("utf-8", "replace"))))
    print("zip links", len(links))
    names = sorted(l.rsplit("/", 1)[-1] for l in links)
    print("   all names:", names)
    if not links:
        return
    latest = links[-1] if links[-1].startswith("http") else "https://www.sec.gov" + links[-1]
    # prefer the link whose name sorts as most recent by year
    st, blob = sec(latest)
    print("latest zip", latest, "status", st, "bytes", len(blob))
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for n in z.namelist():
                info = z.getinfo(n)
                head = z.open(n).readline().decode("utf-8", "replace").strip()
                print(f"   member {n} ({info.file_size} bytes) header: {head[:300]}")
    except Exception as e:  # noqa: BLE001
        print("   could not open zip:", type(e).__name__)


def pftd():
    section("SEC fails-to-deliver files (CUSIP to symbol)")
    if not SEC_UA:
        print("MISSING SEC_CONTACT")
        return
    st, body = sec("https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data")
    print("index status", st)
    links = sorted(set(re.findall(r'href="([^"]+cnsfails[^"]+\.zip)"', body.decode("utf-8", "replace"))))
    print("zip links", len(links), "first", links[:1], "last", links[-1:])
    if links:
        u = links[-1] if links[-1].startswith("http") else "https://www.sec.gov" + links[-1]
        st, blob = sec(u)
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                n = z.namelist()[0]
                lines = z.open(n).read().decode("latin-1").splitlines()
                print(f"   {n}: header {lines[0][:200]} rows {len(lines) - 1}")
        except Exception as e:  # noqa: BLE001
            print("   could not open:", type(e).__name__, "status", st)


def peod():
    section("EODHD")
    if not EOD:
        print("MISSING EODHD_KEY")
        return
    for sym in ("SPY.US", "TWTR.US", "ATVI.US", "SIVB.US"):
        st, body = get(f"https://eodhd.com/api/eod/{sym}?api_token={EOD}&fmt=json&from=2010-01-01")
        try:
            rows = json.loads(body)
            print(f"   eod {sym}: status {st}, rows {len(rows)}, first {rows[0]['date']}, last {rows[-1]['date']}, "
                  f"fields {sorted(rows[0])}")
        except Exception:  # noqa: BLE001
            print(f"   eod {sym}: status {st}, unparsed ({len(body)} bytes)")
    st, body = get(f"https://eodhd.com/api/exchange-symbol-list/US?api_token={EOD}&fmt=json&delisted=1")
    try:
        print(f"   delisted symbol list: status {st}, rows {len(json.loads(body))}")
    except Exception:  # noqa: BLE001
        print(f"   delisted symbol list: status {st}, unparsed")
    st, body = get(f"https://eodhd.com/api/id-mapping?filter[cusip]=037833100&api_token={EOD}&fmt=json")
    print(f"   id-mapping by CUSIP: status {st}, bytes {len(body)}, keys "
          f"{sorted(json.loads(body).get('data', [{}])[0]) if st == 200 and body.startswith(b'{') else 'n/a'}")


def pfinra():
    section("FINRA consolidated short interest")
    url = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
    for a, b in (("2010-01-01", "2012-12-31"), ("2013-01-01", "2014-12-31"), ("2015-01-01", "2016-12-31"),
                 ("2017-01-01", "2018-12-31"), ("2019-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31")):
        payload = json.dumps({"limit": 1, "dateRangeFilters": [{"fieldName": "settlementDate", "startDate": a, "endDate": b}]}).encode()
        st, body = get(url, {"Content-Type": "application/json", "Accept": "application/json"}, data=payload)
        try:
            rows = json.loads(body)
            print(f"   window {a}..{b}: status {st}, rows returned {len(rows)}, settlementDate {rows[0].get('settlementDate') if rows else 'none'}")
        except Exception:  # noqa: BLE001
            print(f"   window {a}..{b}: status {st}, unparsed {body[:100]!r}")
    tries = [("GET limit", url + "?limit=1", None),
             ("POST limit", url, json.dumps({"limit": 1}).encode()),
             ("POST sorted asc", url, json.dumps({"limit": 1, "sortFields": ["settlementDate"]}).encode()),
             ("POST sorted desc", url, json.dumps({"limit": 1, "sortFields": ["-settlementDate"]}).encode())]
    for name, u, data in tries:
        st, body = get(u, {"Content-Type": "application/json", "Accept": "application/json"}, data=data)
        try:
            rows = json.loads(body)
            r0 = rows[0] if isinstance(rows, list) and rows else rows
            print(f"   {name}: status {st}, fields {sorted(r0)[:20]}, settlementDate {r0.get('settlementDate') if isinstance(r0, dict) else 'n/a'}")
        except Exception:  # noqa: BLE001
            print(f"   {name}: status {st}, unparsed ({len(body)} bytes) {body[:120]!r}")


def pyahoo():
    section("Yahoo via yfinance")
    try:
        import yfinance as yf
    except Exception as e:  # noqa: BLE001
        print("yfinance import failed", type(e).__name__)
        return
    for sym in ("SPY", "AAPL", "TWTR", "ATVI", "SIVB", "GME"):
        try:
            h = yf.Ticker(sym).history(start="2012-01-01", auto_adjust=True)
            if len(h):
                print(f"   {sym}: rows {len(h)}, first {h.index[0].date()}, last {h.index[-1].date()}")
            else:
                print(f"   {sym}: no rows")
        except Exception as e:  # noqa: BLE001
            print(f"   {sym}: {type(e).__name__}")


if __name__ == "__main__":
    for f in (p13f, pfinra):
        try:
            f()
        except Exception as e:  # noqa: BLE001
            print(f"{f.__name__} raised {type(e).__name__}")
    sys.exit(0)
