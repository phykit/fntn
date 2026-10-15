"""Self-test of run_c2.py on synthetic worlds: null (3 seeds) must not PASS; planted negative must PASS with sign -1."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
def run(kind, seed):
    with tempfile.TemporaryDirectory() as td:
        dd, out = os.path.join(td, "data"), os.path.join(td, "out")
        subprocess.run([sys.executable, os.path.join(HERE, "synth_c2.py"), kind, str(seed), dd], check=True, capture_output=True)
        subprocess.run([sys.executable, os.path.join(HERE, "run_c2.py"), "--data", dd, "--out", out], check=True, capture_output=True)
        return json.load(open(os.path.join(out, "results_c2.json")))["hypothesis"]
fails = []
nulls = [run("null", s) for s in (1, 2, 3)]
print("null:", [h["verdict"] for h in nulls])
if sum(h["verdict"].startswith("PASS") for h in nulls) > 0 or sum(h["criteria"]["a_primary"] for h in nulls) > 1:
    fails.append("null passes too often")
p = run("planted", 11)
print("planted:", p["verdict"])
if not (p["criteria"]["a_primary"] and p["sign"] == -1):
    fails.append("planted effect not detected")
print("SELFTEST", "FAILED: " + "; ".join(fails) if fails else "OK")
sys.exit(1 if fails else 0)
