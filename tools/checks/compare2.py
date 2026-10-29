"""Compare the first implementation's results_frozen21.json with verify2.json, per Check 1 of
tools/checks/PREREG.md.

Usage:
    python compare2.py --frozen results_frozen21.json --verify verify2.json

Mandated items (these decide the overall line):
  - primary (class_D, GVIP-QQQ, E0): n and verdict exactly; mean and unconditional mean to 1e-9;
    p_lower exactly, since the draw order was specified identically to both implementations;
  - every secondary series' E0 mean to 1e-9, in both episode sets (Class N being the secondary
    episode set, its GVIP-QQQ E0 mean is included).
Every other p-value, n and E+1..4 mean is printed as INFO: AGREE when exact (p) or within 1e-9
(means), AGREE~ when a p-value differs but lies within 0.005, else DISAGREE. INFO lines do not
move the overall line. Exits 0 either way: disagreement is reported, not acted on.
"""
from __future__ import annotations

import argparse
import json
import sys

SERIES = ["GVIP-QQQ", "basket-QQQ", "GVIP-SPY", "GVIP-resid-QQQ"]
TOL_MEAN = 1e-9
TOL_P = 0.005


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def cmp_exact(a, b):
    return a == b


def cmp_mean(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= TOL_MEAN


def cmp_p(a, b):
    if a is None or b is None:
        return "AGREE" if a is None and b is None else "DISAGREE"
    if float(a) == float(b):
        return "AGREE"
    return "AGREE~" if abs(float(a) - float(b)) <= TOL_P else "DISAGREE"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--verify", required=True)
    a = ap.parse_args(argv)
    with open(a.frozen) as fh:
        F = json.load(fh)
    with open(a.verify) as fh:
        V = json.load(fh)

    mandated = []

    def line(tag, label, ok, fa, va):
        print(f"{tag:<9}{label:<48} frozen={fa!r:<26} verify={va!r}")

    def item(label, ok, fa, va):
        mandated.append(ok)
        line("AGREE" if ok else "DISAGREE", label, ok, fa, va)

    print("Mandated items")
    p = ("class_D", "GVIP-QQQ", "E0")
    fn, vn = get(F, *p, "n"), get(V, *p, "n")
    item("primary n", fn is not None and vn is not None and int(fn) == int(vn), fn, vn)
    for k in ("mean", "unconditional_mean"):
        fa, va = get(F, *p, k), get(V, *p, k)
        item(f"primary {k}", cmp_mean(fa, va), fa, va)
    fa, va = get(F, *p, "p_lower"), get(V, *p, "p_lower")
    item("primary p_lower (exact)", fa is not None and va is not None and float(fa) == float(va), fa, va)
    fa, va = F.get("verdict_H_crowd"), V.get("verdict_H_crowd")
    item("verdict_H_crowd", cmp_exact(fa, va), fa, va)
    for c in ("class_D", "class_N"):
        for s in SERIES:
            if c == "class_D" and s == "GVIP-QQQ":
                continue
            fa, va = get(F, c, s, "E0", "mean"), get(V, c, s, "E0", "mean")
            item(f"{c} {s} E0 mean", cmp_mean(fa, va), fa, va)

    print("\nInformational items (no effect on the overall line)")
    for c in ("class_D", "class_N"):
        for s in SERIES:
            for w in ("E0", "E1_4"):
                for k in ("n", "mean", "unconditional_mean", "p_lower", "p_upper"):
                    if (c, s, w) == p and k in ("n", "mean", "unconditional_mean", "p_lower"):
                        continue
                    if w == "E0" and k == "mean":
                        continue
                    fa, va = get(F, c, s, w, k), get(V, c, s, w, k)
                    if k in ("p_lower", "p_upper"):
                        tag = cmp_p(fa, va)
                    elif k == "n":
                        tag = "AGREE" if fa == va else "DISAGREE"
                    else:
                        tag = "AGREE" if cmp_mean(fa, va) else "DISAGREE"
                    line(tag, f"{c} {s} {w} {k}", None, fa, va)

    bad = mandated.count(False)
    print(f"\nOVERALL: {'AGREE' if bad == 0 else 'DISAGREE'} "
          f"({len(mandated) - bad} of {len(mandated)} mandated items agree)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
