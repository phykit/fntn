"""Combine the frozen 21 episodes with the 2016 to 2020 extension (PREREG section 2): same-class
episodes within 14 days merge into the earliest; a Class N episode within 14 days of a Class D
episode is dropped. Frozen IDs are kept; extension IDs (X..) are kept as assigned by build_ext.py.

Usage: python build_all.py
"""
import csv
import datetime as dt
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, "..", "degross_episodes", "episodes.csv")
EXT = os.path.join(HERE, "episodes_ext.csv")
COLS = ["episode_id", "class", "week_end", "first_public", "region", "sector", "outlet", "tier", "url", "phrase"]


def rows(p):
    return [{k: r.get(k, "") for k in COLS} for r in csv.DictReader(open(p, newline=""))]


def wk(r):
    return dt.date.fromisoformat(r["week_end"])


allr = rows(FROZEN) + rows(EXT)
out = []
for cls in ("D", "N"):
    kept = []
    for r in sorted((r for r in allr if r["class"] == cls), key=lambda r: (wk(r), r["first_public"])):
        if kept and (wk(r) - wk(kept[-1])).days <= 14:
            print(f"merged {r['episode_id']} into {kept[-1]['episode_id']}")
            continue
        kept.append(r)
    out += kept
dweeks = [wk(r) for r in out if r["class"] == "D"]
final = []
for r in out:
    if r["class"] == "N" and any(abs((wk(r) - d).days) <= 14 for d in dweeks):
        print(f"dropped N {r['episode_id']} (within 14 days of a D episode)")
        continue
    final.append(r)
final.sort(key=wk)
with open(os.path.join(HERE, "episodes_all.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(final)
print(f"combined: {len(final)} episodes, D {sum(r['class'] == 'D' for r in final)}, N {sum(r['class'] == 'N' for r in final)}")
for y in range(2016, 2027):
    ys = [r for r in final if wk(r).year == y]
    print(f"  {y}: D {sum(r['class'] == 'D' for r in ys)}, N {sum(r['class'] == 'N' for r in ys)}")
