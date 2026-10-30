"""Programme-level multiple-testing pass (METHOD.md). Combines the row files, keeps included rows,
treats p = NA as 1, and applies Benjamini-Hochberg (q = 0.05 and 0.10) and Holm (0.05)."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["rows_manual.csv", "rows_repos.csv", "rows_local.csv"]


def load():
    rows = []
    for f in FILES:
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            print("missing", f, file=sys.stderr)
            continue
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                r["file"] = f
                rows.append(r)
    return rows


def bh_q(ps):
    """Benjamini-Hochberg adjusted p-values (q-values), step-up, monotone."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    q = [0.0] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        prev = min(prev, ps[i] * m / rank)
        q[i] = prev
    return q


def holm(ps, alpha=0.05):
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    rej = [False] * m
    for k, i in enumerate(order):
        if ps[i] <= alpha / (m - k):
            rej[i] = True
        else:
            break
    return rej


def main():
    rows = load()
    ids = [r["id"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        print("duplicate ids:", sorted(dup))
    inc = [r for r in rows if r["include"].strip().lower() == "yes"]
    ps = [1.0 if r["p"].strip().upper() in ("NA", "") else float(r["p"]) for r in inc]
    q = bh_q(ps)
    h = holm(ps)
    for r, p, qq, hh in zip(inc, ps, q, h):
        r["p_used"] = p
        r["q"] = qq
        r["bh05"] = qq <= 0.05
        r["bh10"] = qq <= 0.10
        r["holm05"] = hh
    inc.sort(key=lambda r: r["p_used"])
    out = os.path.join(HERE, "register.csv")
    cols = ["id", "date", "test", "hypothesis", "verdict", "p", "p_basis", "p_used", "q", "bh05", "bh10", "holm05", "source", "notes"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(inc)
    print(f"rows read {len(rows)}, included m = {len(inc)}, NA = {sum(1 for r in inc if r['p'].strip().upper() in ('NA', ''))}")
    print(f"BH q<=0.05: {sum(r['bh05'] for r in inc)}; BH q<=0.10: {sum(r['bh10'] for r in inc)}; Holm 0.05: {sum(r['holm05'] for r in inc)}")
    for r in inc[:20]:
        print(f"{r['id']:<22} p={r['p_used']:<8.4g} q={r['q']:<7.3f} {'BH05' if r['bh05'] else ''} {'BH10' if r['bh10'] else ''} {'HOLM' if r['holm05'] else ''} | {r['test'][:50]}")


if __name__ == "__main__":
    main()
