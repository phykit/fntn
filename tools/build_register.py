#!/usr/bin/env python3
"""
build_register.py - build a delisting register from EDGAR quarterly form indices.

The span is a parameter. The paper's register covers 2023-01-01 to 2026-08-27;
extending back to 2010 removes the objection that the sample is short and
dominated by the 2020-21 blank-cheque cohort.

    export SEC_CONTACT="Your Name your@email.com"
    python3 build_register.py --start 2010-01-01 --end 2026-08-27 \
                              --out ../data/register_2010.tsv

Roughly 66 quarters at 40-60 MB each. Budget 30-60 minutes and ~3 GB of
transfer. Indices are cached, so an interrupted run resumes for free.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import pathlib
import sys
import time
import urllib.request

DELISTING = {"25", "25-NSE"}
DEREGISTRATION = {"15-12B", "15-12G", "15-15D",
                  "15F-12B", "15F-12G", "15F-15D"}
WANTED = DELISTING | DEREGISTRATION
RATE = 0.15                                   # SEC fair access


def contact() -> str:
    c = os.environ.get("SEC_CONTACT", "").strip()
    if not c:
        sys.exit('SEC_CONTACT is unset.\n'
                 '  export SEC_CONTACT="Your Name your@email.com"')
    return c


def quarters(a: dt.date, b: dt.date):
    y, q = a.year, (a.month - 1) // 3 + 1
    while (y, q) <= (b.year, (b.month - 1) // 3 + 1):
        yield y, q
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)


def parse_index(raw: str, span: tuple[dt.date, dt.date]) -> list[dict]:
    """EDGAR form.idx is fixed-width. Columns are stable across the archive."""
    out = []
    for line in raw.splitlines():
        form = line[0:12].strip()
        if form not in WANTED:
            continue
        try:
            d = dt.date.fromisoformat(line[86:98].strip())
        except ValueError:
            continue
        if not (span[0] <= d <= span[1]):
            continue
        out.append({"form": form, "cik": line[74:86].strip(),
                    "company": line[12:74].strip(),
                    "date_filed": d.isoformat(), "path": line[98:].strip()})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-08-27")
    ap.add_argument("--out", default="register.tsv")
    ap.add_argument("--log", default=None, help="default: <out>_fetch.tsv")
    ap.add_argument("--cache", default=".idx_cache")
    a = ap.parse_args()

    span = (dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end))
    out = pathlib.Path(a.out)
    log = pathlib.Path(a.log) if a.log else out.with_name(out.stem + "_fetch.tsv")
    cache = pathlib.Path(a.cache); cache.mkdir(parents=True, exist_ok=True)

    qs = list(quarters(*span))
    print(f"span {span[0]} to {span[1]}: {len(qs)} quarters")
    rows, fetches = [], []
    for i, (y, q) in enumerate(qs, 1):
        url = (f"https://www.sec.gov/Archives/edgar/full-index/"
               f"{y}/QTR{q}/form.idx")
        f = cache / f"form_{y}Q{q}.idx"
        if f.exists():
            raw = f.read_bytes()
            cached = True
        else:
            req = urllib.request.Request(url, headers={"User-Agent": contact()})
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read()
            f.write_bytes(raw)
            cached = False
            time.sleep(RATE)
        fetches.append((url, dt.datetime.now(dt.timezone.utc).isoformat(),
                        len(raw), hashlib.sha256(raw).hexdigest()))
        got = parse_index(raw.decode("utf-8", "replace"), span)
        rows.extend(got)
        print(f"  [{i:>3}/{len(qs)}] {y} Q{q}  {len(raw)/1e6:6.1f} MB  "
              f"{len(got):>5} kept{'  (cached)' if cached else ''}", flush=True)

    rows.sort(key=lambda r: (r["date_filed"], r["cik"]))
    d = [r for r in rows if r["form"] in DELISTING]
    issuers = {r["cik"] for r in d}

    with out.open("w", newline="") as fh:
        fh.write("# Delisting register. Forms 25 and 25-NSE are DELISTINGS;\n"
                 "# every 15* form is DEREGISTRATION and is never summed with them.\n"
                 f"# span: {span[0]} to {span[1]}; quarters: {len(qs)}\n"
                 f"# delisting filings: {len(d)}; distinct delisted issuers: "
                 f"{len(issuers)}; deregistration filings: {len(rows)-len(d)}\n")
        w = csv.DictWriter(fh, delimiter="\t",
                           fieldnames=["form", "cik", "company",
                                       "date_filed", "path"])
        w.writeheader(); w.writerows(rows)
    with log.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["url", "retrieved_at", "bytes", "sha256"]); w.writerows(fetches)

    print(f"\n  delisting filings      {len(d):,}")
    print(f"  distinct issuers M     {len(issuers):,}")
    print(f"  deregistration filings {len(rows)-len(d):,}")
    print(f"\n  wrote {out} and {log}")


if __name__ == "__main__":
    main()
