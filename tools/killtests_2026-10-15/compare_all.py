"""Compare every criterion figure between each run_*.py result and its independent verify_*.py.
Usage: python compare_all.py --out out. Exits 1 on any disagreement beyond 1e-6 relative."""
import argparse
import json
import math
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bad = rows = 0

    def cmp(lbl, x, y):
        nonlocal bad, rows
        rows += 1
        nx = x is None or (isinstance(x, float) and math.isnan(x))
        ny = y is None or (isinstance(y, float) and math.isnan(y))
        ok = (nx and ny) or (not nx and not ny and math.isclose(float(x), float(y), rel_tol=1e-6, abs_tol=1e-9))
        if not ok:
            bad += 1
        print(("OK  " if ok else "DIFF"), lbl, x, y)

    def verdict(lbl, va, vb, crit_b=None):
        nonlocal bad, rows
        rows += 1
        ok = str(va).split(" ")[0] == str(vb).split(" ")[0]
        if not ok:
            bad += 1
        print(("OK  " if ok else "DIFF"), lbl, va, "|", vb, crit_b if crit_b else "")

    def load(name):
        p = os.path.join(a.out, name)
        return json.load(open(p)) if os.path.exists(p) else None

    def std(lbl, H, V, hkeys):
        for h in hkeys:
            cmp(f"{lbl} h{h} n", H["by_h"][h]["n"], V["horizons"][h]["n"])
            cmp(f"{lbl} h{h} slope", H["by_h"][h]["slope"], V["horizons"][h]["b"])
            cmp(f"{lbl} h{h} nw_t", H["by_h"][h]["nw_t"], V["horizons"][h]["nw_t"])
            cmp(f"{lbl} h{h} p2", H["by_h"][h]["p2"], V["horizons"][h]["p2"])
        cmp(f"{lbl} half first", H["halves"]["first"]["slope"], V["halves"]["b_first"])
        cmp(f"{lbl} half second", H["halves"]["second"]["slope"], V["halves"]["b_rest"])
        cmp(f"{lbl} g", H["incremental"]["coef"]["signal"], V["incremental"]["g"])
        cmp(f"{lbl} g nw_t", H["incremental"]["nw_t"]["signal"], V["incremental"]["nw_t"])
        cmp(f"{lbl} r2_os", H["oos"]["r2_os"], V["oos"]["r2_os"])
        cmp(f"{lbl} cw nw_t", H["oos"]["cw_nw_t"], V["oos"]["cw_nw_t"])
        cmp(f"{lbl} Dq", H["size"]["Dq"], V["size"]["Dq"])
        verdict(f"{lbl} verdict", H["verdict"], V.get("verdict"), V.get("criteria"))

    # A
    A, VA = load("results_a.json"), load("verify_a.json")
    if A and VA:
        for asset in ("ng", "ho", "rb"):
            if asset not in A["assets"] or asset not in VA:
                continue
            H, V = A["assets"][asset]["hypothesis"], VA[asset]
            lbl = f"A {asset}"
            cmp(f"{lbl} pooled n", H["pooled"]["n"], V["pooled"]["n"])
            cmp(f"{lbl} pooled b", H["pooled"]["slope"], V["pooled"]["b"])
            cmp(f"{lbl} pooled nw_t", H["pooled"]["nw_t"], V["pooled"]["nw_t"])
            cmp(f"{lbl} pooled p2", H["pooled"]["p2"], V["pooled"]["p2"])
            for e in ("1", "2", "3", "4"):
                cmp(f"{lbl} e{e} b", H["by_e"][e]["slope"], V["by_e"][e]["b"])
            cmp(f"{lbl} e12 b", H["e12"]["slope"], V["e12"]["b"])
            cmp(f"{lbl} e34 b", H["e34"]["slope"], V["e34"]["b"])
            cmp(f"{lbl} half first", H["halves"]["first"]["slope"], V["halves"]["b_first"])
            cmp(f"{lbl} half second", H["halves"]["second"]["slope"], V["halves"]["b_rest"])
            cmp(f"{lbl} g", H["incremental"]["coef"]["signal"], V["incremental"]["g"])
            cmp(f"{lbl} g nw_t", H["incremental"]["nw_t"]["signal"], V["incremental"]["nw_t"])
            cmp(f"{lbl} r2_os", H["oos"]["r2_os"], V["oos"]["r2_os"])
            cmp(f"{lbl} cw nw_t", H["oos"]["cw_nw_t"], V["oos"]["cw_nw_t"])
            cmp(f"{lbl} Dq", H["size"]["Dq"], V["size"]["Dq"])
            verdict(f"{lbl} verdict", H["verdict"], V.get("verdict"), V.get("criteria"))
    else:
        print("A: missing a results file")
    B, VB = load("results_b.json"), load("verify_b.json")
    if B and VB:
        std("B", B["hypothesis"], VB, ("1", "3", "5"))
    else:
        print("B: missing a results file")
    C, VC = load("results_c.json"), load("verify_c.json")
    if C and VC:
        std("C", C["hypothesis"], VC, ("1", "5", "20"))
    else:
        print("C: missing a results file")
    D, VD = load("results_d.json"), load("verify_d.json")
    if D and VD:
        std("D", D["hypothesis"], VD, ("1", "5", "20"))
    else:
        print("D: missing a results file")
    print(f"COMPARE {rows - bad} of {rows} figures agree; {bad} disagree")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
