"""Fetch the authors' updated short interest index (Rapach's data page: Google Sheet
1DgFLrH8YJHiKFgYVimeiaXmZrOf7H9OQ, 1973:01 to 2021:12), FRED NASDAQ100 and the French daily factors.
Structure printed, never a value. Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import importlib.util
import io
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import fetch_extra as fx  # noqa: E402

SHEET = "https://docs.google.com/spreadsheets/d/1DgFLrH8YJHiKFgYVimeiaXmZrOf7H9OQ/export?format=xlsx"


def main(argv=None):
    import openpyxl
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    zipname, cols = fx.FILES["ff5_daily.csv"]
    fx.french(a.data, "ff5_daily.csv", zipname, cols)
    spec = importlib.util.spec_from_file_location("fetch_a", os.path.join(HERE, "..", "degross_proxy", "fetch.py"))
    fa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fa)
    fa.fred(os.path.join(a.data, "ndx.csv"))
    req = urllib.request.Request(SHEET, headers={"User-Agent": "Mozilla/5.0 (fntn side test)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    chosen = None
    for ws in wb.worksheets:
        rows = [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(str(c).strip() for c in r)]
        hdr = [str(c).strip() for c in rows[0]] if rows else []
        print(f"sheet {ws.title!r}: {len(rows) - 1 if rows else 0} data rows, header {hdr}")
        if chosen is None and any("sii" in h.lower() for h in hdr):
            chosen = (ws.title, rows)
    if chosen is None:
        raise SystemExit("structure: no sheet with an SII column")
    title, rows = chosen
    with open(os.path.join(a.data, "sii.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        for r in rows:
            w.writerow([(c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else c) for c in r])
    print(f"sii.csv from sheet {title!r}: {len(rows) - 1} rows; first month cell {str(rows[1][0])[:10]!r}, last {str(rows[-1][0])[:10]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
