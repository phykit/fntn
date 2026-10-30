"""Self-test for the frozen intra-week persistence test: a planted world in which the first two days'
spread continues into the rest of the week must read SUPPORTED; iid worlds must not. Synthetic
bench.csv files are generated here; no real data is touched.

Usage: python selftest.py
"""
from __future__ import annotations

import csv
import datetime as dt
import importlib.util
import json
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("run_intraweek", os.path.join(HERE, "run.py"))
_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_run)


def trading_days(rng, start=dt.date(2012, 1, 2), end=dt.date(2026, 10, 28)):
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    drop = set(rng.choice(len(days), size=9 * 15, replace=False).tolist())
    return [x for i, x in enumerate(days) if i not in drop]


def spreads(rng, days, planted, sd=0.005, load=0.6):
    s = rng.normal(0, sd, len(days))
    if planted:
        weeks = _run.weeks_of(days)
        for _, idx in weeks:
            if len(idx) >= 3:
                S = s[idx[0]] + s[idx[1]]
                for i in idx[2:]:
                    s[i] += load * S / (len(idx) - 2)
    return s


def world(seed, planted, data):
    rng = np.random.default_rng(seed)
    days = trading_days(rng)
    n = len(days)
    r_spy = rng.normal(0.0004, 0.01, n)
    r_qqq = r_spy + rng.normal(0, 0.004, n)
    r_mtum = r_spy + spreads(rng, days, planted)
    r_gvip = r_qqq + spreads(rng, days, planted)
    px = {k: 100 * np.cumprod(1 + v) for k, v in (("SPY", r_spy), ("QQQ", r_qqq), ("MTUM", r_mtum), ("GVIP", r_gvip))}
    start = {"MTUM": dt.date(2013, 4, 18), "GVIP": dt.date(2016, 11, 2), "SPY": days[0], "QQQ": days[0]}
    blanks = set(rng.choice(n, size=6, replace=False).tolist())
    with open(os.path.join(data, "bench.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "GVIP", "QQQ", "MTUM", "SPY"])
        for i, d in enumerate(days):
            row = [d.isoformat()]
            for k in ("GVIP", "QQQ", "MTUM", "SPY"):
                row.append("" if d < start[k] or (i in blanks and k == "GVIP") else repr(float(px[k][i])))
            w.writerow(row)
    # a synthetic episode file: eight Fridays
    with open(os.path.join(data, "episodes.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["episode_id", "class", "week_end"])
        for j, y in enumerate(range(2018, 2026)):
            w.writerow([f"X{j:02d}", "D", dt.date(y, 3, 2 + (j % 5)).isoformat()])


def main():
    failures = 0
    for seed, planted in ((1, True), (2, True), (3, False), (4, False), (5, False), (6, False)):
        with tempfile.TemporaryDirectory() as tmp:
            world(seed, planted, tmp)
            out = os.path.join(tmp, "out")
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                _run.main(["--data", tmp, "--episodes", os.path.join(tmp, "episodes.csv"), "--out", out])
            r = json.load(open(os.path.join(out, "results.json")))
            P1, P2 = r["pairs"]["P1"], r["pairs"]["P2"]
            want = "SUPPORTED" if planted else "NOT SUPPORTED"
            ok = r["verdict"] == want
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} planted {planted}, seed {seed}: {r['verdict']} "
                  f"(P1 n_sig {P1['n_signal']}, d {P1['d']*100:+.2f}%, p {P1['p_shift']:.4f}; "
                  f"P2 n_sig {P2['n_signal']}, d {P2['d']*100:+.2f}%, p {P2['p_shift']:.4f}; "
                  f"daily slope1 {P1['daily']['slope1']:+.3f} t {P1['daily']['t1']:+.2f}; "
                  f"episodes n {P1['episodes']['n']} hit {P1['episodes']['hit_rate']}; trade n {P1['trade']['n']} mean {P1['trade']['mean']*100:+.2f}%)")
    print("SELFTEST PASSED" if failures == 0 else f"SELFTEST FAILED ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
