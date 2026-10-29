"""Self-test of build.py and run.py for Version B, before any input is fetched (PREREG section 6).

(a) build.py on hand-built 13F and FTD files with a known answer; (b) run.py's basket returns on a
hand-built price table; (c) 40 null and 8 planted worlds through the outcome test. Exits non-zero on
any failure, so the workflow stops before fetching.
"""
from __future__ import annotations

import datetime as dt
import io
import os
import sys
import tempfile
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402
import run  # noqa: E402

FAILS = []
SUB_H = "ACCESSION_NUMBER\tFILING_DATE\tSUBMISSIONTYPE\tCIK\tPERIODOFREPORT"
INF_H = ("ACCESSION_NUMBER\tINFOTABLE_SK\tNAMEOFISSUER\tTITLEOFCLASS\tCUSIP\tFIGI\tVALUE\tSSHPRNAMT\t"
         "SSHPRNAMTTYPE\tPUTCALL\tINVESTMENTDISCRETION\tOTHERMANAGER\tVOTING_AUTH_SOLE\t"
         "VOTING_AUTH_SHARED\tVOTING_AUTH_NONE")


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def cu(i):
    return f"C{i:08d}"


def write_zip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for n, t in files.items():
            z.writestr(n, t)


def synthetic(d):
    """Period 2021-03-31. Filers: H1..H12 hedge-fund-like (12 longs, one put); X1 long-only (no
    options); B1 too many longs (250); A1 an amendment; L1 filed late; F1 holds only funds."""
    os.makedirs(os.path.join(d, "13f"))
    os.makedirs(os.path.join(d, "ftd"))
    sub, inf = [SUB_H], [INF_H]
    k = 0

    def row(acc, issuer, title, cusip, value, typ="SH", pc=""):
        nonlocal k
        k += 1
        inf.append("\t".join([acc, str(k), issuer, title, cusip, "", str(value), "1", typ, pc,
                              "SOLE", "", "1", "0", "0"]))

    for h in range(1, 13):
        acc = f"H{h}"
        sub.append(f"{acc}\t10-MAY-2021\t13F-HR\t{1000 + h}\t31-MAR-2021")
        # holdings: CUSIPs 1..12, value descending with index, so the top 10 are 1..10 for all
        for i in range(1, 13):
            row(acc, f"CO {i}", "COM", cu(i), 1000 - i)
        # each filer also holds a fund long (must be ignored) and a put on 100+h%3
        row(acc, "SPDR S&P 500 ETF TR", "TR UNIT", "78462F103", 5000)
        row(acc, f"CO {100 + h % 3}", "COM", cu(100 + h % 3), 10, pc="Put")
        row(acc, f"CO 1", "COM", cu(1), 10, pc="Put")  # put on a long-basket name: excluded from short
    sub.append("X1\t10-MAY-2021\t13F-HR\t2001\t31-MAR-2021")
    for i in range(200, 215):
        row("X1", f"CO {i}", "COM", cu(i), 999)
    sub.append("B1\t10-MAY-2021\t13F-HR\t2002\t31-MAR-2021")
    for i in range(300, 550):
        row("B1", f"CO {i}", "COM", cu(i), 999)
    row("B1", "CO 300", "COM", cu(300), 1, pc="Call")
    sub.append("A1\t12-MAY-2021\t13F-HR/A\t2003\t31-MAR-2021")
    sub.append("L1\t20-MAY-2021\t13F-HR\t2004\t31-MAR-2021")  # 50 days after the period: late
    for acc in ("A1", "L1"):
        for i in range(400, 415):
            row(acc, f"CO {i}", "COM", cu(i), 999)
        row(acc, "CO 400", "COM", cu(400), 1, pc="Put")
    write_zip(os.path.join(d, "13f", "2021q2_form13f.zip"),
              {"SUBMISSION.tsv": "\n".join(sub) + "\n", "INFOTABLE.tsv": "\n".join(inf) + "\n"})
    # FTD: map all CUSIPs 1..12 and 100..102 on 2021-04-01; CUSIP 12 only in 2019 (stale)
    ftd = ["SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE"]
    for i in list(range(1, 12)) + [100, 101, 102]:
        sym = f"S{i}" if i != 5 else "BRK.B"
        ftd.append(f"20210401|{cu(i)}|{sym}|10|X|1")
    ftd.append(f"20190401|{cu(12)}|S12|10|X|1")
    write_zip(os.path.join(d, "ftd", "cnsfails202104a.zip"), {"cnsfails202104a.txt": "\n".join(ftd) + "\nTrailer"})
    days = [dt.date(2021, 5, 14) + dt.timedelta(days=i) for i in range(10)]
    days = [x for x in days if x.weekday() < 5]
    with open(os.path.join(d, "spy.csv"), "w") as fh:
        fh.write("DATE,SPY\n" + "".join(f"{x},100\n" for x in days))


def part_a():
    with tempfile.TemporaryDirectory() as d:
        synthetic(d)
        out = os.path.join(d, "out")
        build.main(["--data", d, "--out", out])
        import csv
        rows = list(csv.DictReader(open(os.path.join(d, "baskets.csv"))))
        longs = [r for r in rows if r["leg"] == "long"]
        shorts = [r for r in rows if r["leg"] == "short"]
        # 12 hf-like filers; top-10 = CUSIPs 1..10 (12 each); 11 and 12 are held but in no top 10
        check("long basket is CUSIPs 1..10 in order (11, 12 never in a top 10)",
              [r["cusip"] for r in longs] == [cu(i) for i in range(1, 11)])
        check("FTD symbol with '.' becomes '-'", any(r["symbol"] == "BRK-B" for r in longs))
        # puts: 100 (h%3==0: 4 filers), 101 (4), 102 (4); cusip 1 excluded as a long-basket name
        check("short basket is the three put names, CUSIP order on ties",
              [r["cusip"] for r in shorts] == [cu(100), cu(101), cu(102)])
        check("effective date is the first SPY day after period + 45 days (2021-05-17)",
              all(r["effective"] == "2021-05-17" for r in rows))
        import json
        summ = json.load(open(os.path.join(out, "build_summary.json")))
        check("kept filings exclude the amendment and the late filing (14 kept)", summ[0]["n_kept_filings"] == 14)
        check("hf-like filings exclude long-only and 250-position filers (12)", summ[0]["n_hf_like"] == 12)


def part_b():
    days = [dt.date(2021, 1, 4) + dt.timedelta(days=i) for i in range(8)]
    days = [x for x in days if x.weekday() < 5]  # 6 days
    col = {"SPY": 0, "A": 1, "B": 2, "C": 3}
    px = np.array([[100, 10, 20, np.nan],
                   [101, 11, 20, 5],
                   [102, 11, 22, 5],
                   [103, 12.1, 22, 5.5],
                   [104, 12.1, np.nan, 5.5],
                   [105, 12.1, 22, 5.5]], float)
    bk = {days[1]: {"long": ["A", "B", "C"], "short": ["C"]}, days[3]: {"long": ["B"], "short": ["A"]}}
    W, L, M, cov = run.daily_legs(days, col, px, bk)
    check("no return before the first basket earns", np.isnan(W[0]) and np.isnan(W[1]))
    check("day 2: mean of A (0%) and B (+10%), C entered at E (5.0 present)",
          abs(W[2] - np.mean([0.0, 0.1, 0.0])) < 1e-12)
    check("day 3 (next effective day) still earned by the first basket", abs(W[3] - np.mean([0.1, 0.0, 0.1])) < 1e-12)
    check("day 4 earned by the second basket (B only; B missing): undefined", np.isnan(W[4]))
    check("short leg day 5: A from 12.1 to 12.1", abs(L[5] - 0.0) < 1e-12)
    check("coverage counts", cov[0]["long_entered"] == 3 and cov[1]["long_entered"] == 1)


def bdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def world(seed, planted):
    rng = np.random.default_rng(seed)
    pdays = bdays(dt.date(1986, 1, 2), 10_300)
    ret = rng.normal(0.0003, 0.015, len(pdays))
    ends = [pdays[i] for i in range(25, len(pdays) - 70, 5)]
    trig = rng.random(len(ends)) < 0.012
    if planted:
        ords = np.array([d.toordinal() for d in pdays])
        for t in np.where(trig)[0]:
            i = int(np.searchsorted(ords, ends[t].toordinal(), side="right") - 1)
            ret[i + 1:i + 31] = np.log(0.85) / 30
    px = 100 * np.exp(np.cumsum(ret))
    return run.outcome_test(ends, trig, np.ones(len(ends), bool), pdays, px, 63, -0.10, n_perm=2000)


def part_c():
    null_pass = sum(world(1000 + s, False)["verdict"] == "PASS" for s in range(40))
    plant = [world(2000 + s, True) for s in range(8)]
    plant_pass = sum(r["verdict"] == "PASS" for r in plant)
    print(f"null worlds passing: {null_pass} of 40; planted worlds passing: {plant_pass} of 8")
    check("null worlds pass at most 4 of 40", null_pass <= 4)
    check("planted worlds pass 8 of 8", plant_pass == 8)


if __name__ == "__main__":
    part_a()
    part_b()
    part_c()
    if FAILS:
        print(f"SELFTEST FAILED: {len(FAILS)} checks")
        sys.exit(1)
    print("SELFTEST PASSED")
