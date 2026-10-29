"""Follow-up study 1 scoring (PREREG.md section 3): the original studies 2 and 3, by the frozen
functions of tools/degross_episodes/score.py, on the combined list (primary) and on the 2016 to
2020 extension alone (secondary).

Usage: python score_ext.py --data-a DATA_A --data-b DATA_B --out OUT_DIR
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "degross_episodes"))
import score as sc  # noqa: E402  the frozen scorer


def run_set(eps, proxies, nd, npx):
    out = {"n_episodes": len(eps), "n_D": sum(e["cls"] == "D" for e in eps), "study2": {}}
    for name, (ends, D, ev) in proxies.items():
        out["study2"][name] = {"class_D": sc.hits(eps, ends, D, ev, {"D"}),
                               "class_N (no weight)": sc.hits(eps, ends, D, ev, {"N"})}
    out["study3"] = sc.timing(eps, nd, npx)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-a", required=True)
    ap.add_argument("--data-b", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    eps = sc.episodes(os.path.join(HERE, "episodes_all.csv"))
    proxies = {"A_momentum": sc.proxy_a(a.data_a), "B_13f": sc.proxy_b(a.data_b)}
    nd, npx = sc.load_ndx(os.path.join(a.data_a, "ndx.csv"))
    res = {"combined (primary)": run_set(eps, proxies, nd, npx),
           "extension 2016-2020 only (secondary)": run_set([e for e in eps if e["id"].startswith("X")], proxies, nd, npx)}
    for setname, r in res.items():
        print(f"== {setname}: {r['n_episodes']} episodes, D {r['n_D']}")
        for name, v in r["study2"].items():
            h = v["class_D"]
            p = f"{h['p']:.4f}" if h["n_scored"] else "n/a"
            print(f"  {name}: scored {h['n_scored']}, hits {h['hits']} {h['hit_ids']}, chance {h['chance_per_episode']:.3f}, p {p}, {h['verdict']}")
        s3 = r["study3"]
        for k in ("pre10", "post21_pub", "post63_pub"):
            if s3[k].get("n"):
                print(f"  {k}: n {s3[k]['n']}, mean {s3[k]['mean']:+.4f} vs {s3[k]['unconditional_mean']:+.4f}, "
                      f"median {s3[k]['median']:+.4f}, p_lower {s3[k]['p_lower']:.4f}, share neg {s3[k]['share_negative']:.2f}")
        print(f"  H-lag: {s3['verdict_H_lag']}")
    json.dump(res, open(os.path.join(a.out, "results_ext.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
