"""Self-test of the four run scripts on synthetic worlds (synth.py). Touches no real observation.
null worlds (3 seeds, 18 hypothesis-worlds): criterion (a) met in at most 2 and PASS in at most 2 (two-sided 2.5%
per hypothesis gives 0.45 expected; a further 18 null worlds run on 15 October 2026 gave 0 rejections).
planted world (1 seed): every test's primary criterion (a) met with the planted sign."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = [("a", "a_expiry/run_a.py", "results_a.json"), ("b", "b_spread/run_b.py", "results_b.json"),
        ("c", "c_vix/run_c.py", "results_c.json"), ("d", "d_btc/run_d.py", "results_d.json")]


def run_world(kind, seed):
    with tempfile.TemporaryDirectory() as td:
        dd, out = os.path.join(td, "data"), os.path.join(td, "out")
        subprocess.run([sys.executable, os.path.join(HERE, "synth.py"), kind, str(seed), dd], check=True, capture_output=True)
        res = {}
        for key, script, fn in RUNS:
            subprocess.run([sys.executable, os.path.join(HERE, script), "--data", dd, "--out", out], check=True, capture_output=True)
            res[key] = json.load(open(os.path.join(out, fn)))
        return res


def hyps(res):
    out = {}
    for asset in ("ng", "ho", "rb"):
        out[f"a_{asset}"] = res["a"]["assets"][asset]["hypothesis"]
    out["b"] = res["b"]["hypothesis"]
    out["c"] = res["c"]["hypothesis"]
    out["d"] = res["d"]["hypothesis"]
    return out


def main():
    fails = []
    na = npass = total = 0
    for seed in (1, 2, 3):
        H = hyps(run_world("null", seed))
        for k, h in H.items():
            total += 1
            na += int(h["criteria"]["a_primary"])
            npass += int(h["verdict"].startswith("PASS"))
        print(f"null seed {seed}:", {k: h["verdict"] for k, h in H.items()})
    print(f"null: (a) met {na} of {total}; PASS {npass}")
    if npass > 2 or na > 2:
        fails.append("null worlds pass too often")
    H = hyps(run_world("planted", 11))
    print("planted:", {k: h["verdict"] for k, h in H.items()})
    want = {"a_ng": -1, "b": -1, "c": -1, "d": 1}
    for k, s in want.items():
        if not (H[k]["criteria"]["a_primary"] and H[k]["sign"] == s):
            fails.append(f"planted {k} not detected with sign {s}")
    print("SELFTEST", "FAILED: " + "; ".join(fails) if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
