"""Check 2 (tools/checks/PREREG.md): agreement between the original episode coding and the blind
re-coding, per article and per merged episode, and the re-coded episode list for the sensitivity
rerun of study 2. Writes tools/checks/episodes_recode.csv and prints the agreement measures.

Usage: python tools/checks/agree.py
"""
import csv
import datetime as dt
import os
from collections import Counter

H = os.path.dirname(os.path.abspath(__file__))
orig = list(csv.DictReader(open(os.path.join(H, "..", "degross_episodes", "candidates_log.csv"))))
key = {r["cand_id"]: int(r["orig_row"]) - 2 for r in csv.DictReader(open(os.path.join(H, "candidates_key.csv")))}
rec = {r["cand_id"]: r for r in csv.DictReader(open(os.path.join(H, "recode.csv")))}


def fri(d):
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return dt.date.fromisocalendar(y, w, 5)


def orig_week(o):
    spe = o["stated_period_end"]
    if spe in ("n/a", "") or not spe[:10].replace("-", "").isdigit() or len(spe) < 10:
        return fri((dt.date.fromisoformat(o["first_public"][:10]) - dt.timedelta(days=7)).isoformat())
    return fri(spe[:10])


pairs = []
for cid, r in rec.items():
    o = orig[key[cid]]
    a = o["class"] if o["decision"] == "include" else "X"
    b = r["class"] if r["decision"] == "include" else "X"
    pairs.append((cid, a, b, o, r))
n = len(pairs)
cats = ["D", "N", "X"]
po = sum(a == b for _, a, b, _, _ in pairs) / n
ca, cb = Counter(a for _, a, _, _, _ in pairs), Counter(b for _, _, b, _, _ in pairs)
pe = sum(ca[c] * cb[c] for c in cats) / n ** 2
kappa = (po - pe) / (1 - pe)
inc_a = [x for x in pairs if x[1] != "X"]
inc_b = [x for x in pairs if x[2] != "X"]
po2 = sum((a != "X") == (b != "X") for _, a, b, _, _ in pairs) / n
pa, pb = len(inc_a) / n, len(inc_b) / n
pe2 = pa * pb + (1 - pa) * (1 - pb)
kappa2 = (po2 - pe2) / (1 - pe2)
print(f"articles {n}; original D/N/X {ca['D']}/{ca['N']}/{ca['X']}; re-code D/N/X {cb['D']}/{cb['N']}/{cb['X']}")
print(f"class agreement {po:.3f}, Cohen's kappa (D/N/excluded) {kappa:.3f}")
print(f"include/exclude agreement {po2:.3f}, kappa {kappa2:.3f}")
tab = Counter((a, b) for _, a, b, _, _ in pairs)
print("cross-tab original x re-code:", {f"{a}->{b}": v for (a, b), v in sorted(tab.items())})
both = [x for x in pairs if x[1] != "X" and x[2] != "X"]
same_wk = sum(orig_week(o) == dt.date.fromisoformat(r["week_end"]) for _, _, _, o, r in both)
print(f"both include: {len(both)}; same week-end: {same_wk}")
for cid, a, b, o, r in pairs:
    if a != b:
        print(f"  {cid}: original {a} ({o['reason'][:70]}) | re-code {b} ({r['reason'][:70]})")


def merge(rows):
    rows = sorted(rows, key=lambda c: c["wk"])
    eps = []
    for c in rows:
        if eps and (c["wk"] - eps[-1]["wk"]).days <= 14:
            continue
        eps.append(c)
    return eps


inc = [{"cls": r["class"], "wk": dt.date.fromisoformat(r["week_end"]), "fp": r.get("first_public", ""), "cid": cid}
       for cid, r in rec.items() if r["decision"] == "include"]
fp = {r["cand_id"]: r["first_public"] for r in csv.DictReader(open(os.path.join(H, "candidates_blind.csv")))}
D = merge([c for c in inc if c["cls"] == "D"])
N = [e for e in merge([c for c in inc if c["cls"] == "N"]) if all(abs((e["wk"] - d["wk"]).days) > 14 for d in D)]
eps = sorted(D + N, key=lambda e: e["wk"])
with open(os.path.join(H, "episodes_recode.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["episode_id", "class", "week_end", "first_public", "source_cand"])
    for i, e in enumerate(eps, 1):
        w.writerow([f"R{i:02d}", e["cls"], e["wk"].isoformat(), fp[e["cid"]][:10], e["cid"]])
frozen = [{"cls": r["class"], "wk": dt.date.fromisoformat(r["week_end"]), "id": r["episode_id"]}
          for r in csv.DictReader(open(os.path.join(H, "..", "degross_episodes", "episodes.csv")))]
print(f"re-coded episodes: {len(eps)} (D {len(D)}, N {len(N)}); frozen 21 (D 9, N 12)")
for cls in ("D", "N"):
    f = [e for e in frozen if e["cls"] == cls]
    g = [e for e in eps if e["cls"] == cls]
    m = [e["id"] for e in f if any(abs((e["wk"] - x["wk"]).days) <= 7 for x in g)]
    extra = [x["wk"].isoformat() for x in g if not any(abs((e["wk"] - x["wk"]).days) <= 7 for e in f)]
    print(f"class {cls}: frozen matched {len(m)} of {len(f)} {m}; re-code only {extra}")
