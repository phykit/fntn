"""Fetch the VIP test's extra inputs (PREREG section 2): French daily five factors and momentum,
and SPY, QQQ and RSP adjusted closes on SPY's trading days. Structure printed, never a value.

Usage: python fetch_extra.py --data DATA_DIR
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
import zipfile

FR = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FILES = {
    "ff5_daily.csv": ("F-F_Research_Data_5_Factors_2x3_daily_CSV.zip", ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]),
    "mom_daily.csv": ("F-F_Momentum_Factor_daily_CSV.zip", ["Mom"]),
}
DATE8 = re.compile(r"^\d{8}$")


def get(url, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fntn side test)", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"{url}: {type(last).__name__}")


def french(data, out, zipname, cols):
    with zipfile.ZipFile(io.BytesIO(get(FR + zipname))) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")
    lines = text.splitlines()
    for k, line in enumerate(lines):
        c = [x.strip() for x in line.split(",")]
        if c and c[0] == "" and c[1:] == cols:
            rows = []
            for l2 in lines[k + 1:]:
                c2 = [x.strip() for x in l2.split(",")]
                if not DATE8.match(c2[0]):
                    break
                rows.append([f"{c2[0][:4]}-{c2[0][4:6]}-{c2[0][6:]}"] + ["" if v in ("-99.99", "-999") else v for v in c2[1:]])
            with open(os.path.join(data, out), "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["DATE"] + cols)
                w.writerows(rows)
            print(f"{out}: {len(rows)} rows, {rows[0][0]} to {rows[-1][0]}")
            return
    raise RuntimeError(f"{zipname}: header ,{','.join(cols)} not found")


def bench(data):
    import yfinance as yf
    with open(os.path.join(data, "spy.csv"), newline="") as fh:
        days = [r[0] for r in list(csv.reader(fh))[1:] if r[1].strip()]
    ser = {}
    for s in ("SPY", "QQQ", "RSP"):
        h = yf.Ticker(s).history(start="2012-01-01", auto_adjust=True)
        ser[s] = {ts.date().isoformat(): float(v) for ts, v in zip(h.index, h["Close"])}
        print(f"{s}: {len(h)} rows")
    with open(os.path.join(data, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "SPY", "QQQ", "RSP"])
        for d in days:
            w.writerow([d] + [repr(ser[s][d]) if d in ser[s] else "" for s in ("SPY", "QQQ", "RSP")])
    print(f"bench.csv: {len(days)} days")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    for out, (zipname, cols) in FILES.items():
        french(a.data, out, zipname, cols)
    bench(a.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
