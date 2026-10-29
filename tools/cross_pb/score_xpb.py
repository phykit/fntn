"""Follow-up study 3 scoring (PREREG.md section 3): agreement between the frozen Goldman list and
the Morgan Stanley / JPMorgan list, both ways, and the timing test on the other banks' Class D
episodes by the frozen timing() of tools/degross_episodes/score.py.

Usage: python score_xpb.py --data-a DATA_A --out OUT_DIR
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "degross_episodes"))
import score as sc  # noqa: E402

START, END = dt.date(2021, 1, 1), dt.date(2026, 10, 23)
MIN_OTHER = 5


def weeks():
    d = START
    while d.weekday() != 4:
        d += dt.timedelta(days=1)
    n = 0
    while d <= END:
        n += 1
        d += dt.timedelta(days=7)
    return n


def agree(src, tgt, T, gate_n):
    b = len(tgt) / T
    q = 1 - (1 - b) ** 3
    hit = [e["id"] for e in src if any(abs((t["week_end"] - e["week_end"]).days) <= 7 for t in tgt)]
    n, k = len(src), len(hit)
    p = sc.binom_tail(k, n, q) if n else float("nan")
    rate = k / n if n else float("nan")
    if gate_n < MIN_OTHER or n == 0:
        v = "INSUFFICIENT"
    elif rate >= 0.5 and p <= 0.05:
        v = "CORROBORATED"
    else:
        v = "NOT CORROBORATED"
    return {"n": n, "matched": k, "rate": rate, "density": b, "chance_per_episode": q, "p": p, "verdict": v, "matched_ids": hit}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-a", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    gs = [e for e in sc.episodes(os.path.join(HERE, "..", "degross_episodes", "episodes.csv")) if START <= e["week_end"] <= END]
    ot = [e for e in sc.episodes(os.path.join(HERE, "episodes_other.csv")) if START <= e["week_end"] <= END]
    T = weeks()
    res = {"weeks": T, "n_goldman": len(gs), "n_other": len(ot),
           "n_other_D": sum(e["cls"] == "D" for e in ot)}
    res["G_to_O (primary)"] = agree([e for e in gs if e["cls"] == "D"], ot, T, len(ot))
    res["O_to_G"] = agree([e for e in ot if e["cls"] == "D"], gs, T, len(ot))
    res["G_DN_to_O (no weight)"] = agree(gs, ot, T, len(ot))
    nd, npx = sc.load_ndx(os.path.join(a.data_a, "ndx.csv"))
    res["timing_other_D"] = sc.timing(ot, nd, npx)
    print(f"weeks {T}; Goldman episodes {len(gs)}; other-PB episodes {len(ot)} (D {res['n_other_D']})")
    for k in ("G_to_O (primary)", "O_to_G", "G_DN_to_O (no weight)"):
        r = res[k]
        p = f"{r['p']:.4f}" if r["n"] else "n/a"
        print(f"{k}: {r['matched']} of {r['n']} {r['matched_ids']}, chance {r['chance_per_episode']:.3f}, p {p}, {r['verdict']}")
    s3 = res["timing_other_D"]
    for k in ("pre10", "post21_pub", "post63_pub"):
        if s3[k].get("n"):
            print(f"timing {k}: n {s3[k]['n']}, mean {s3[k]['mean']:+.4f} vs {s3[k]['unconditional_mean']:+.4f}, p_lower {s3[k]['p_lower']:.4f}")
    print("timing H-lag on other-PB D:", s3["verdict_H_lag"])
    json.dump(res, open(os.path.join(a.out, "results_xpb.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
