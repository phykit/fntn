"""Fetch the three inputs of the de-gross proxy test (PREREG section 2) on the runner.

Prints structure only (section titles, column names, row counts, first and last dates), never a
value. Refuses, with a non-zero exit, if a file does not have the structure the specification
assumes, because a silently re-shaped input would be a different test.

Usage: python fetch.py --data DATA_DIR
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import urllib.request
import zipfile

FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
MOM = FRENCH + "10_Portfolios_Prior_12_2_Daily_CSV.zip"
FF3 = FRENCH + "F-F_Research_Data_Factors_daily_CSV.zip"
NDX = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100"
UA = {"User-Agent": "Mozilla/5.0 (fntn degross-proxy side test; research use)"}

MOM_COLS = ["Lo PRIOR", "PRIOR 2", "PRIOR 3", "PRIOR 4", "PRIOR 5",
            "PRIOR 6", "PRIOR 7", "PRIOR 8", "PRIOR 9", "Hi PRIOR"]
FF3_COLS = ["Mkt-RF", "SMB", "HML", "RF"]
DATE8 = re.compile(r"^\d{8}$")


class Refusal(Exception):
    pass


def get(url, tries=5):
    """Fetch with retries. Added after run 1, in which FRED timed out once on the runner; the
    precedent fetcher (futures-residual-2026-10-15) retries the same endpoint four times."""
    import time
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  attempt {i + 1} failed: {type(e).__name__}")
            time.sleep(10 * (i + 1))
    raise Refusal(f"{url}: no response after {tries} attempts ({type(last).__name__})")


def unzip_text(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
        print("  zip members:", names)
        if len(names) != 1:
            raise Refusal(f"expected one member, found {len(names)}")
        return z.read(names[0]).decode("latin-1")


def first_table(text, want_cols, label):
    """Return (titles, rows) for the first table whose header is ',<want_cols>'."""
    lines = text.splitlines()
    titles = []
    for k, line in enumerate(lines):
        cells = [c.strip() for c in line.split(",")]
        if cells and cells[0] == "" and cells[1:] == want_cols:
            rows = []
            for line2 in lines[k + 1:]:
                c2 = [c.strip() for c in line2.split(",")]
                if not c2 or not DATE8.match(c2[0]):
                    break
                if len(c2) != len(want_cols) + 1:
                    raise Refusal(f"{label}: a row has {len(c2)} cells")
                rows.append(c2)
            return titles, rows
        if line.strip():
            titles.append(line.strip())
    raise Refusal(f"{label}: header ,{','.join(want_cols)} not found")


def iso(d8):
    return f"{d8[0:4]}-{d8[4:6]}-{d8[6:8]}"


def missing(v):
    try:
        x = float(v)
    except ValueError:
        return True
    return x <= -99.99 + 1e-9 or x == -999


def write(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def french(url, cols, label, path, require_vw):
    print(f"{label}: {url}")
    text = unzip_text(get(url))
    titles, rows = first_table(text, cols, label)
    print(f"  title lines before the first table (last 3): {titles[-3:]}")
    if require_vw and not any("value weight" in t.lower() for t in titles[-3:]):
        raise Refusal(f"{label}: the first table is not labelled value-weighted")
    out = [[iso(r[0])] + ["" if missing(v) else v for v in r[1:]] for r in rows]
    n_missing = sum(1 for r in out for v in r[1:] if v == "")
    print(f"  rows {len(out)}, first {out[0][0]}, last {out[-1][0]}, empty cells {n_missing}")
    write(path, ["DATE"] + cols, out)


def fred(path):
    print(f"NDX: {NDX}")
    text = get(NDX).decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]
    print(f"  header {head}")
    if len(head) != 2 or head[1] != "NASDAQ100":
        raise Refusal("NDX: unexpected header")
    out = []
    for r in rows[1:]:
        v = r[1].strip()
        out.append([r[0], "" if v in ("", ".") else v])
    n_missing = sum(1 for r in out if r[1] == "")
    print(f"  rows {len(out)}, first {out[0][0]}, last {out[-1][0]}, empty {n_missing}")
    write(path, ["DATE", "NASDAQ100"], out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    try:
        french(MOM, MOM_COLS, "MOM10", os.path.join(a.data, "mom10_daily.csv"), True)
        french(FF3, FF3_COLS, "FF3", os.path.join(a.data, "ff3_daily.csv"), False)
        fred(os.path.join(a.data, "ndx.csv"))
    except Refusal as e:
        print("REFUSED:", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
