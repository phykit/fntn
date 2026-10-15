"""Compare every criterion figure between run.py (results.json) and verify.py (verify.json).
Usage: python compare.py --out out. Exits 1 on any disagreement beyond 1e-6 relative."""
import argparse
import json
import math
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A = json.load(open(os.path.join(a.out, "results.json")))["assets"]
    B = json.load(open(os.path.join(a.out, "verify.json")))["assets"]
    bad = 0
    rows = 0

    def cmp(lbl, x, y):
        nonlocal bad, rows
        rows += 1
        both_nan = (x is None or (isinstance(x, float) and math.isnan(x))) and (y is None or (isinstance(y, float) and math.isnan(y)))
        ok = both_nan or (x is not None and y is not None and math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-9))
        if not ok:
            bad += 1
        print(("OK  " if ok else "DIFF"), lbl, x, y)

    for asset in ("ng", "ho", "rb"):
        for hid in ("HL", "HC"):
            X, Y = A[asset]["hypotheses"][hid], B[asset][hid]
            for h in ("1", "5", "20"):
                cmp(f"{asset} {hid} h{h} n", X["by_h"][h]["n"], Y["horizons"][h]["n"])
                cmp(f"{asset} {hid} h{h} slope", X["by_h"][h]["slope"], Y["horizons"][h]["b"])
                cmp(f"{asset} {hid} h{h} nw_t", X["by_h"][h]["nw_t"], Y["horizons"][h]["nw_t"])
                cmp(f"{asset} {hid} h{h} p2", X["by_h"][h]["p2"], Y["horizons"][h]["p2"])
            cmp(f"{asset} {hid} half first", X["halves"]["first"]["slope"], Y["halves"]["b_first"])
            cmp(f"{asset} {hid} half second", X["halves"]["second"]["slope"], Y["halves"]["b_rest"])
            cmp(f"{asset} {hid} g", X["incremental"]["coef"]["signal"], Y["incremental"]["g"])
            cmp(f"{asset} {hid} g nw_t", X["incremental"]["nw_t"]["signal"], Y["incremental"]["nw_t"])
            cmp(f"{asset} {hid} r2_os", X["oos"]["r2_os"], Y["oos"]["r2_os"])
            cmp(f"{asset} {hid} cw nw_t", X["oos"]["cw_nw_t"], Y["oos"]["cw_nw_t"])
            cmp(f"{asset} {hid} Dq", X["size"]["Dq"], Y["size"]["Dq"])
            va, vb = X["verdict"].split(" ")[0], str(Y.get("verdict", "")).split(" ")[0]
            rows += 1
            if va != vb:
                bad += 1
            print(("OK  " if va == vb else "DIFF"), f"{asset} {hid} verdict", X["verdict"], "|", Y.get("verdict"), Y.get("criteria"))
    print(f"COMPARE {rows - bad} of {rows} figures agree; {bad} disagree")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
