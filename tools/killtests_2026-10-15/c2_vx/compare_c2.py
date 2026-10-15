"""Compare run_c2.py and verify_c2.py criterion figures. Usage: python compare_c2.py --out out"""
import argparse, json, math, os
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
A = json.load(open(os.path.join(a.out, "results_c2.json")))["hypothesis"]; B = json.load(open(os.path.join(a.out, "verify_c2.json")))
bad = rows = 0
def cmp(l, x, y):
    global bad, rows
    rows += 1
    nx = x is None or (isinstance(x, float) and math.isnan(x)); ny = y is None or (isinstance(y, float) and math.isnan(y))
    ok = (nx and ny) or (not nx and not ny and math.isclose(float(x), float(y), rel_tol=1e-6, abs_tol=1e-9))
    bad += 0 if ok else 1
    print("OK  " if ok else "DIFF", l, x, y)
for h in ("1", "5", "20"):
    cmp(f"h{h} n", A["by_h"][h]["n"], B["horizons"][h]["n"]); cmp(f"h{h} slope", A["by_h"][h]["slope"], B["horizons"][h]["b"])
    cmp(f"h{h} nw_t", A["by_h"][h]["nw_t"], B["horizons"][h]["nw_t"]); cmp(f"h{h} p2", A["by_h"][h]["p2"], B["horizons"][h]["p2"])
cmp("half first", A["halves"]["first"]["slope"], B["halves"]["b_first"]); cmp("half second", A["halves"]["second"]["slope"], B["halves"]["b_rest"])
cmp("g", A["incremental"]["coef"]["signal"], B["incremental"]["g"]); cmp("g nw_t", A["incremental"]["nw_t"]["signal"], B["incremental"]["nw_t"])
cmp("r2_os", A["oos"]["r2_os"], B["oos"]["r2_os"]); cmp("cw nw_t", A["oos"]["cw_nw_t"], B["oos"]["cw_nw_t"]); cmp("Dq", A["size"]["Dq"], B["size"]["Dq"])
rows += 1; vok = A["verdict"].split(" ")[0] == str(B.get("verdict")).split(" ")[0]; bad += 0 if vok else 1
print("OK  " if vok else "DIFF", "verdict", A["verdict"], "|", B.get("verdict"), B.get("criteria"))
print(f"COMPARE {rows - bad} of {rows} figures agree; {bad} disagree")
raise SystemExit(1 if bad else 0)
