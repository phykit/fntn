"""Build Version B's long and short baskets from the raw 13F data sets (PREREG section 3).

Frozen with PREREG.md. Reads data/13f/*.zip, data/ftd/*.zip and data/spy.csv (for SPY trading
days); writes data/baskets.csv and OUT/build_summary.json (derived counts only).

Usage: python build.py --data DATA_DIR --out OUT_DIR
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import glob
import io
import json
import os
import sys
import zipfile

FUND_WORDS = ["ETF", "ETN", "FUND", "SPDR", "ISHARES", "PROSHARES", "POWERSHARES", "INVESCO QQQ",
              "SELECT SECTOR", "VANGUARD", "DIREXION", "VANECK", "WISDOMTREE", "GLOBAL X"]
MONTHS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
BASKET = 50
DEADLINE = 45


def pdate(s):
    s = s.strip()
    if len(s) == 11 and s[2] == "-":
        return dt.date(int(s[7:11]), MONTHS[s[3:6].upper()], int(s[0:2]))
    if len(s) == 10 and s[4] == "-":
        return dt.date.fromisoformat(s)
    raise ValueError(f"unparsed date {s!r}")


def lines_of(z, member):
    with z.open(member) as fh:
        for raw in io.TextIOWrapper(fh, encoding="utf-8", errors="replace", newline=""):
            yield raw.rstrip("\r\n")


def member(z, name):
    for n in z.namelist():
        if n.rsplit("/", 1)[-1].upper() == name:
            return n
    return None


def is_fund(issuer, title):
    s = (issuer + " " + title).upper()
    return any(w in s for w in FUND_WORDS)


def kept_filings(zips):
    """(CIK, period) -> (filing date, accession), latest within the deadline; then acc -> period."""
    best = {}
    for p in zips:
        with zipfile.ZipFile(p) as z:
            m = member(z, "SUBMISSION.TSV")
            it = lines_of(z, m)
            head = next(it).split("\t")
            ix = {h.strip(): i for i, h in enumerate(head)}
            for line in it:
                c = line.split("\t")
                if len(c) < len(head):
                    continue
                if c[ix["SUBMISSIONTYPE"]].strip() != "13F-HR":
                    continue
                try:
                    q, f = pdate(c[ix["PERIODOFREPORT"]]), pdate(c[ix["FILING_DATE"]])
                except (ValueError, KeyError):
                    continue
                if (f - q).days > DEADLINE:
                    continue
                key = (c[ix["CIK"]].strip(), q)
                val = (f, c[ix["ACCESSION_NUMBER"]].strip())
                if key not in best or val > best[key]:
                    best[key] = val
    return {acc: q for (cik, q), (f, acc) in best.items()}


def scan_infotables(zips, acc_period):
    """Per kept accession, reduced file by file (a filing's rows lie in one data set file):
    n_long (distinct non-fund long CUSIPs), has_option, and, only for filings with 10 to 200 long
    CUSIPs, the long CUSIP set, the top 10 and the non-fund put CUSIPs. A filing seen in an earlier
    file is not re-read."""
    summ = {}
    for p in zips:
        longs, opt, puts = {}, set(), {}
        with zipfile.ZipFile(p) as z:
            m = member(z, "INFOTABLE.TSV")
            it = lines_of(z, m)
            head = next(it).split("\t")
            ix = {h.strip(): i for i, h in enumerate(head)}
            ia, icu, iv = ix["ACCESSION_NUMBER"], ix["CUSIP"], ix["VALUE"]
            it_, ii, ipc, ity = ix["TITLEOFCLASS"], ix["NAMEOFISSUER"], ix["PUTCALL"], ix["SSHPRNAMTTYPE"]
            for line in it:
                c = line.split("\t")
                if len(c) < len(head):
                    continue
                acc = c[ia].strip()
                if acc not in acc_period or acc in summ:
                    continue
                pc = c[ipc].strip().upper()
                if pc in ("PUT", "CALL"):
                    opt.add(acc)
                if is_fund(c[ii], c[it_]):
                    continue
                cusip = c[icu].strip().upper()
                if not cusip:
                    continue
                if pc == "PUT":
                    puts.setdefault(acc, set()).add(cusip)
                elif pc == "" and c[ity].strip().upper() == "SH":
                    try:
                        v = float(c[iv].strip() or 0)
                    except ValueError:
                        continue
                    d = longs.setdefault(acc, {})
                    d[cusip] = d.get(cusip, 0.0) + v
        seen = set(longs) | opt | set(puts)
        for acc in seen:
            d = longs.get(acc, {})
            n = len(d)
            rec = {"n_long": n, "opt": acc in opt}
            if 10 <= n <= 200:
                rec["held"] = set(d)
                rec["top"] = [cu for cu, _ in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
                rec["puts"] = puts.get(acc, set())
            summ[acc] = rec
        print(f"  {os.path.basename(p)}: filings summarised {len(seen)}")
    return summ


def baskets_by_period(acc_period, summ):
    periods = {}
    for acc, q in acc_period.items():
        periods.setdefault(q, []).append(acc)
    out, summary = {}, {}
    for q in sorted(periods):
        accs = periods[q]
        hf = [a for a in accs if a in summ and summ[a]["opt"] and 10 <= summ[a]["n_long"] <= 200]
        top_count, hold_count, put_count = {}, {}, {}
        for a in hf:
            r = summ[a]
            for cu in r["held"]:
                hold_count[cu] = hold_count.get(cu, 0) + 1
            for cu in r["top"]:
                top_count[cu] = top_count.get(cu, 0) + 1
            for cu in r["puts"]:
                put_count[cu] = put_count.get(cu, 0) + 1
        long_b = sorted(top_count, key=lambda cu: (-top_count[cu], -hold_count.get(cu, 0), cu))[:BASKET]
        lset = set(long_b)
        cand = [cu for cu, n in put_count.items() if n >= 2 and cu not in lset]
        short_b = sorted(cand, key=lambda cu: (-put_count[cu], cu))[:BASKET]
        out[q] = (long_b, short_b)
        summary[q] = {"n_kept_filings": len(accs), "n_hf_like": len(hf)}
    return out, summary


def spy_days(data):
    with open(os.path.join(data, "spy.csv"), newline="") as fh:
        rows = list(csv.reader(fh))[1:]
    return [dt.date.fromisoformat(r[0]) for r in rows if r[1].strip()]


def effective_dates(periods, days):
    eff = {}
    for q in periods:
        cut = q + dt.timedelta(days=DEADLINE)
        i = bisect.bisect_right(days, cut)
        if i < len(days):
            eff[q] = days[i]
    return eff


def yahoo(sym):
    return sym.strip().upper().replace(".", "-").replace("/", "-")


def ftd_map(data, wanted):
    """CUSIP -> sorted list of (settlement date, symbol) for wanted CUSIPs only."""
    rec = {}
    for p in sorted(glob.glob(os.path.join(data, "ftd", "*.zip"))):
        try:
            z = zipfile.ZipFile(p)
        except zipfile.BadZipFile:
            print("  unreadable FTD file:", os.path.basename(p))
            continue
        with z:
            for n in z.namelist():
                with z.open(n) as fh:
                    for raw in io.TextIOWrapper(fh, encoding="latin-1", newline=""):
                        c = raw.rstrip("\r\n").split("|")
                        if len(c) < 3 or len(c[0].strip()) != 8 or not c[0].strip().isdigit():
                            continue
                        cu = c[1].strip().upper()
                        if cu not in wanted or not c[2].strip():
                            continue
                        s = c[0].strip()
                        try:
                            d = dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
                        except ValueError:
                            continue
                        rec.setdefault(cu, []).append((d, yahoo(c[2])))
    for cu in rec:
        rec[cu].sort()
    return rec


def symbol_at(rec, cu, e):
    lst = rec.get(cu)
    if not lst:
        return None
    i = bisect.bisect_right(lst, (e, "￿")) - 1
    if i < 0:
        return None
    d, s = lst[i]
    return s if (e - d).days <= 365 else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    zips = sorted(glob.glob(os.path.join(a.data, "13f", "*.zip")))
    print(f"13F files: {len(zips)}")
    acc_period = kept_filings(zips)
    print(f"kept 13F-HR filings: {len(acc_period)}")
    summ = scan_infotables(zips, acc_period)
    bk, summary = baskets_by_period(acc_period, summ)
    days = spy_days(a.data)
    eff = effective_dates(bk, days)
    wanted = {cu for lb, sb in bk.values() for cu in lb + sb}
    rec = ftd_map(a.data, wanted)
    rows, summ = [], []
    for q in sorted(bk):
        if q not in eff:
            continue
        e = eff[q]
        lb, sb = bk[q]
        n_l = n_s = 0
        for leg, lst in (("long", lb), ("short", sb)):
            for r, cu in enumerate(lst, 1):
                s = symbol_at(rec, cu, e)
                if s is None:
                    continue
                rows.append([q.isoformat(), e.isoformat(), leg, r, cu, s])
                if leg == "long":
                    n_l += 1
                else:
                    n_s += 1
        summ.append({"period": q.isoformat(), "effective": e.isoformat(), **summary[q],
                     "long_cusips": len(lb), "short_cusips": len(sb), "long_n": n_l, "short_n": n_s})
        print(f"  {q} eff {e}: filings {summary[q]['n_kept_filings']}, hf-like {summary[q]['n_hf_like']}, "
              f"long {n_l}/{len(lb)}, short {n_s}/{len(sb)}")
    with open(os.path.join(a.data, "baskets.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["period", "effective", "leg", "rank", "cusip", "symbol"])
        w.writerows(rows)
    with open(os.path.join(a.out, "build_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=1)
    print(f"basket rows: {len(rows)}, symbols: {len({r[5] for r in rows})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
