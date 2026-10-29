"""Fetch FRED NASDAQ100 (header observation_date,NASDAQ100) and the French daily factors.
Structure printed, never a value. Usage: python fetch.py --data DATA_DIR"""
import argparse
import csv
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vip_premium"))
import fetch_extra as fx  # noqa: E402


def fetch_ndx(data):
    spec = importlib.util.spec_from_file_location("fetch_a", os.path.join(HERE, "..", "degross_proxy", "fetch.py"))
    fa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fa)
    fa.fred(os.path.join(data, "ndx.csv"))
    rows = list(csv.reader(open(os.path.join(data, "ndx.csv"), newline="")))
    rows[0] = ["observation_date", "NASDAQ100"]
    with open(os.path.join(data, "ndx.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data, exist_ok=True)
    zipname, cols = fx.FILES["ff5_daily.csv"]
    fx.french(a.data, "ff5_daily.csv", zipname, cols)
    fetch_ndx(a.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
