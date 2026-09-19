#!/usr/bin/env python3
"""
rule_split.py - partition a delisting register by the Rule 12d2-2 paragraph
relied upon, and turn the composition into a defensible k.

This closes "Route 1" of the delisting-register note: Forms 25 and 25-NSE
carry, on their face, the paragraph of 17 CFR 240.12d2-2 under which removal
from listing is effected. That paragraph distinguishes a completed merger from
a deficiency strike, and those two have opposite signs of terminal return.

DESIGN RULE, and it is the whole point of this script:
    IT REFUSES RATHER THAN GUESSES.
Every filing is classified by exactly one strategy, the strategy that fired is
recorded per filing, and anything ambiguous lands in an explicit `unclassified`
bucket that is reported and never silently dropped. A composition table with a
hidden residual is worse than no table.

WORKFLOW
    1.  python3 rule_split.py sample --n 12
        Fetches a dozen filings and writes them to ./samples/ for you to read.
        LOOK AT THEM before trusting any parse. Adjust PATTERNS if needed.
    2.  python3 rule_split.py run --limit 400
        A 400-filing pilot. Composition to about +/- 4.8pp, enough to see
        whether the parse works and roughly where the mass sits.
    3.  python3 rule_split.py run
        The census. About 7,400 fetches, 15 to 25 minutes, 35 to 220 MB.
        Resumable: re-running skips everything already cached.
    4.  python3 rule_split.py draw --n 30
        Draws a validation sample by a registered seed for you to hand-check
        against the machine labels. Run `verify` after filling it in.
    5.  python3 rule_split.py report --k-schedule default
        Composition table, blended k, and the bound recomputed.

Usage:
    export SEC_CONTACT="Your Name your@email.com"
    python3 rule_split.py <command> [options]
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import pathlib
import random
import re
import sys
import time
import urllib.request
import zlib

# ---------------------------------------------------------------------------
# 1.  THE MAPPING, fixed before the run
# ---------------------------------------------------------------------------
# Each paragraph of 17 CFR 240.12d2-2 maps to an economic category and a prior
# on the mean ADVERSE terminal return k (positive = a loss). These priors are
# ASSUMPTIONS, flagged as such, and the point of the exercise is that a k
# assumed per category is far more defensible than one assumed across the whole.

PARAGRAPHS = {
    "a1": {
        "cite": "240.12d2-2(a)(1)",
        "meaning": "entire class called for redemption, maturity or retirement",
        "category": "redemption",
        "k_default": 0.00,
        "k_note": "Holder receives par or the call price. Not an equity loss "
                  "event. Mostly preferred, notes and trust structures.",
    },
    "a2": {
        "cite": "240.12d2-2(a)(2)",
        "meaning": "entire class redeemed or paid at maturity or retirement",
        "category": "redemption",
        "k_default": 0.00,
        "k_note": "As (a)(1).",
    },
    "a3": {
        "cite": "240.12d2-2(a)(3)",
        "meaning": "instruments now evidence other securities in substitution",
        "category": "merger_substitution",
        "k_default": -0.15,
        "k_note": "NEGATIVE k, i.e. a GAIN. This is the completed merger or "
                  "exchange. Acquisition premia are positive and the sign of "
                  "this cell is the single largest error in a flat -100% "
                  "assumption. -15% is a placeholder for a measured premium.",
    },
    "a4": {
        "cite": "240.12d2-2(a)(4)",
        "meaning": "all rights extinguished by final court order, appeals "
                   "exhausted",
        "category": "rights_extinguished",
        "k_default": 0.95,
        "k_note": "THE GENUINE WIPEOUT, and narrower than it first looks. The "
                  "rule requires a FINAL COURT ORDER with all appeal periods "
                  "expired, so this is the bankruptcy or judicial "
                  "extinguishment case and not a catch-all. k near 1 is "
                  "right here.",
    },
    "b": {
        "cite": "240.12d2-2(b)",
        "meaning": "EXCHANGE strikes the class; cases not covered by (a)",
        "category": "exchange_strike",
        "k_default": 0.60,
        "k_note": "THE INVOLUNTARY DELISTING, filed by the EXCHANGE, and the "
                  "adverse case the -100% assumption had in mind. It is the "
                  "rule's residual bucket for everything (a) does not cover, "
                  "so it is heterogeneous: deficiency strikes dominate but "
                  "not exclusively. Even here -100% overstates it; the "
                  "literature puts performance-related delisting returns well "
                  "short of total loss. THIS IS NOW THE AMBIGUOUS CELL.",
    },
    "c": {
        "cite": "240.12d2-2(c)",
        "meaning": "ISSUER voluntarily withdraws from listing and/or "
                   "registration",
        "category": "voluntary_withdrawal",
        "k_default": 0.05,
        "k_note": "VOLUNTARY, filed by the ISSUER. Going private at a premium "
                  "(a gain), a venue move (no return event), and a pre-emptive "
                  "exit ahead of a deficiency (a loss) all land here, but the "
                  "issuer chooses the timing, so the mass sits near zero.",
    },
}

CATEGORY_ORDER = ["merger_substitution", "redemption", "voluntary_withdrawal",
                  "exchange_strike", "rights_extinguished", "unclassified"]

# The residual carries the most adverse k in the schedule, so that failing to
# read a filing can never flatter the bound.
UNCLASSIFIED_K = 1.00

# ---------------------------------------------------------------------------
# 2.  EXTRACTION STRATEGIES, tried in fixed priority order
# ---------------------------------------------------------------------------
# These are written defensively because the exact serialisation of a Form 25
# on EDGAR was NOT inspected when this script was authored. Run `sample` first.
# Each strategy returns a set of paragraph keys it believes are AFFIRMATIVELY
# marked. Exactly one -> classified. Zero or more than one -> refused.

_P = r"(?:17\s*CFR\s*)?24[08]\.12d2-2"          # 240. and the common 248. typo
PARA_RE = re.compile(
    _P + r"\s*\(\s*(a)\s*\)\s*\(\s*([1-4])\s*\)"      # (a)(n)
    r"|" + _P + r"\s*\(\s*([bc])\s*\)",                # (b) or (c)
    re.I)

# TWO SERIALISATIONS, both confirmed against live filings on 19 Sep 2026.
#
#   Form 25     (455 filings, issuer-filed)  : HTML, a checkbox list using
#                                              U+2610 empty / U+2611 checked
#   Form 25-NSE (6,944 filings, exchange)    : XML, a single element
#       <ruleProvision>17 CFR 240.12d2-2(a)(3)</ruleProvision>
#
# 25-NSE is 94% of the population, so XML_VALUE_RE below is the workhorse and
# must accept a FULL CITATION inside the tag, not a bare "a3".

XML_FLAG_RE = re.compile(
    r"<\s*([A-Za-z_:]*12d2[_\-]?2[_\-]?(a[1-4]|[bc]))\s*>\s*"
    r"(true|1|x|yes|checked)\s*<", re.I)
# <ruleProvision>17 CFR 240.12d2-2(a)(3)</ruleProvision>, and the bare form
XML_VALUE_RE = re.compile(
    r"<\s*[A-Za-z_:]*rule(?:Provision|Relied|Paragraph)[A-Za-z_:]*\s*>"
    r"([^<]{0,120})<", re.I)

# Checkbox glyphs. EMPTY and CHECKED are listed separately so the nearest
# preceding box decides, rather than "any mark nearby".
# Wingdings convention, found in a live Form 25 (DigiAsia, Sep 2025): the
# boxes are a Wingdings font run, empty = "¨", checked = "x"/"X". Those
# are ORDINARY characters, so they count as boxes only when the Wingdings
# empty-box character appears somewhere in the document.
WINGDINGS_EMPTY = "¨"
EMPTY_BOX   = r"(?:☐|&#9744;|&#x2610;|\[\s*\]|\[\s*_\s*\]|¨|&#168;)"
CHECKED_BOX = r"(?:☑|☒|&#9745;|&#9746;|&#x2611;|&#x2612;|" \
              r"\[\s*[xX✓✔]\s*\])"
ANY_BOX_RE     = re.compile(f"{CHECKED_BOX}|{EMPTY_BOX}")
WING_ANY_RE     = re.compile(f"{CHECKED_BOX}|{EMPTY_BOX}|(?<![A-Za-z])[xX](?![A-Za-z])")
WING_CHECKED_RE = re.compile(f"{CHECKED_BOX}|(?<![A-Za-z])[xX](?![A-Za-z])")
CHECKED_BOX_RE = re.compile(CHECKED_BOX)

# Last-resort mark detection where the document carries no box glyphs at all
MARK = r"(?:(?<![A-Za-z])[xX](?![A-Za-z])|checked\s*=|value\s*=\s*[\"']?(?:true|1|x)[\"']?)"
MARK_BEFORE_RE = re.compile(MARK + r"[^<]{0,40}(?:<[^>]{0,120}>\s*){0,6}$")


def _norm(a: str | None, n: str | None, bc: str | None) -> str:
    return f"{a.lower()}{n}" if a and n else (bc or "").lower()


def strategy_xml_flag(doc: str) -> set[str]:
    """Primary strategy for Form 25-NSE, which is 94% of the population."""
    out = {m.group(2).lower() for m in XML_FLAG_RE.finditer(doc)}
    for m in XML_VALUE_RE.finditer(doc):
        inner = m.group(1)
        # a full citation inside the element, e.g. "17 CFR 240.12d2-2(a)(3)"
        for c in PARA_RE.finditer(inner):
            key = _norm(c.group(1), c.group(2), c.group(3))
            if key in PARAGRAPHS:
                out.add(key)
        # or the bare form, e.g. "a3" / "(a)(3)" / "c"
        v = re.sub(r"[\s().]", "", inner).lower()
        if v in PARAGRAPHS:
            out.add(v)
    return out


def strategy_marked_checkbox(doc: str) -> set[str]:
    """Primary strategy for Form 25, an HTML checkbox list.

    Confirmed live: boxes render as U+2610 (empty) and U+2611 (checked).
    The rule is NEAREST-BOX-WINS: take the last box glyph before the citation
    and count the citation only if that box is a checked one. Scanning for
    'any mark within N characters' misfires on a list, because the checked
    box belonging to one line sits inside the window of the next.
    """
    wing = WINGDINGS_EMPTY in doc or "&#168;" in doc
    any_re = WING_ANY_RE if wing else ANY_BOX_RE
    chk_re = WING_CHECKED_RE if wing else CHECKED_BOX_RE
    boxes = [(m.start(), bool(chk_re.fullmatch(m.group(0))))
             for m in any_re.finditer(doc)]
    out = set()
    for m in PARA_RE.finditer(doc):
        key = _norm(m.group(1), m.group(2), m.group(3))
        if key not in PARAGRAPHS:
            continue
        prior = [b for b in boxes if b[0] < m.start()]
        if prior:
            if prior[-1][1]:                      # nearest preceding box is checked
                out.add(key)
        elif MARK_BEFORE_RE.search(doc[max(0, m.start() - 180):m.start()]):
            out.add(key)                          # no box glyphs at all: fall back
    return out


def strategy_sole_citation(doc: str) -> set[str]:
    """If exactly ONE paragraph is cited anywhere, take it. Many 25-NSE
    filings cite only the provision relied upon and no checkbox list."""
    keys = {_norm(m.group(1), m.group(2), m.group(3))
            for m in PARA_RE.finditer(doc)}
    keys = {k for k in keys if k in PARAGRAPHS}
    return keys if len(keys) == 1 else set()


STRATEGIES = [
    ("xml_flag", strategy_xml_flag),
    ("marked_checkbox", strategy_marked_checkbox),
    ("sole_citation", strategy_sole_citation),
]


def classify(doc: str) -> tuple[str | None, str, str]:
    """-> (paragraph_key or None, strategy, reason)."""
    for nm, fn in STRATEGIES:
        hits = fn(doc)
        if len(hits) == 1:
            return hits.pop(), nm, "ok"
        if len(hits) > 1:
            return None, nm, "multiple_paragraphs_marked:" + ",".join(sorted(hits))
    cited = {_norm(m.group(1), m.group(2), m.group(3))
             for m in PARA_RE.finditer(doc)}
    cited = {c for c in cited if c in PARAGRAPHS}
    if cited:
        return None, "none", "cited_but_unmarked:" + ",".join(sorted(cited))
    return None, "none", "no_rule_citation_found"


# ---------------------------------------------------------------------------
# 3.  Fetching
# ---------------------------------------------------------------------------

BASE = "https://www.sec.gov/Archives/"
RATE = 0.13                                     # ~7.7 req/s, inside the limit


def contact() -> str:
    c = os.environ.get("SEC_CONTACT", "").strip()
    if not c:
        sys.exit('SEC_CONTACT is unset.\n'
                 '  export SEC_CONTACT="Your Name your@email.com"')
    return c


def fetch(path: str, cache: pathlib.Path, tries: int = 3) -> str | None:
    key = cache / (hashlib.sha1(path.encode()).hexdigest()[:2]) / \
        (path.replace("/", "_") + ".gz")
    if key.exists():
        return gzip.decompress(key.read_bytes()).decode("utf-8", "replace")
    req = urllib.request.Request(BASE + path, headers={
        "User-Agent": contact(), "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding", "")
                if "gzip" in enc:
                    raw = gzip.decompress(raw)
                elif "deflate" in enc:
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            time.sleep(RATE)
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_bytes(gzip.compress(raw))
            return raw.decode("utf-8", "replace")
        except Exception:                                    # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return None


def load_register(p: pathlib.Path) -> list[dict]:
    lines = [l for l in p.open() if not l.startswith("#")]
    return [r for r in csv.DictReader(lines, delimiter="\t")
            if r["form"] in {"25", "25-NSE"}]


# ---------------------------------------------------------------------------
# 4.  Commands
# ---------------------------------------------------------------------------

SEED = 20260919          # registered here, before any result exists
ACQ_RE = re.compile(r"\bacquisition", re.I)


def cmd_sample(a):
    rows = load_register(pathlib.Path(a.register))
    rnd = random.Random(SEED)
    out = pathlib.Path(a.out) / "samples"; out.mkdir(parents=True, exist_ok=True)
    picks = rnd.sample(rows, min(a.n, len(rows)))
    print(f"Writing {len(picks)} raw filings to {out}/ for inspection.\n"
          f"READ THEM before trusting any parse.\n")
    for r in picks:
        doc = fetch(r["path"], pathlib.Path(a.cache))
        if doc is None:
            print(f"  FETCH FAILED {r['path']}"); continue
        key, strat, reason = classify(doc)
        f = out / f"{r['form']}_{r['cik']}_{r['date_filed']}.txt"
        f.write_text(doc)
        print(f"  {f.name:<44} -> {key or 'REFUSED':<12} "
              f"[{strat}] {reason if key is None else ''}")


def cmd_run(a):
    rows = load_register(pathlib.Path(a.register))
    if a.limit:
        random.Random(SEED).shuffle(rows)
        rows = rows[:a.limit]
    cache = pathlib.Path(a.cache)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res_p = out / "rule_split.tsv"

    done = set()
    if res_p.exists() and not a.restart:
        with res_p.open() as f:
            done = {r["path"] for r in csv.DictReader(f, delimiter="\t")}
        print(f"resuming: {len(done):,} filings already classified")

    mode = "a" if done else "w"
    with res_p.open(mode, newline="") as f:
        w = csv.writer(f, delimiter="\t")
        if not done:
            w.writerow(["form", "cik", "company", "date_filed", "path",
                        "paragraph", "category", "strategy", "reason"])
        todo = [r for r in rows if r["path"] not in done]
        t0 = time.time()
        for i, r in enumerate(todo, 1):
            doc = fetch(r["path"], cache)
            if doc is None:
                key, strat, reason = None, "none", "fetch_failed"
            else:
                key, strat, reason = classify(doc)
            cat = PARAGRAPHS[key]["category"] if key else "unclassified"
            w.writerow([r["form"], r["cik"], r["company"], r["date_filed"],
                        r["path"], key or "", cat, strat, reason])
            if i % 200 == 0:
                f.flush()
                el = time.time() - t0
                print(f"  {i:,}/{len(todo):,}  {el/i:.2f}s/filing  "
                      f"eta {(len(todo)-i)*el/i/60:.1f} min", flush=True)
    print(f"\nwrote {res_p}")
    _summarise(res_p, a)


def _read_results(p: pathlib.Path) -> list[dict]:
    with p.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _summarise(p: pathlib.Path, a):
    rows = _read_results(p)
    n = len(rows)
    print(f"\n{'='*66}\nCOMPOSITION  (n = {n:,} filings)\n{'='*66}")
    byc = collections.Counter(r["category"] for r in rows)
    byp = collections.Counter(r["paragraph"] for r in rows if r["paragraph"])
    print(f"{'category':<24}{'n':>8}{'share':>10}")
    print("-" * 42)
    for c in CATEGORY_ORDER:
        if byc[c]:
            print(f"{c:<24}{byc[c]:>8,}{byc[c]/n:>9.1%}")
    print(f"\n{'paragraph':<24}{'n':>8}{'share':>10}   meaning")
    print("-" * 78)
    for k, v in PARAGRAPHS.items():
        if byp[k]:
            print(f"{v['cite']:<24}{byp[k]:>8,}{byp[k]/n:>9.1%}   {v['meaning'][:38]}")
    u = byc["unclassified"]
    print(f"\nUNCLASSIFIED: {u:,} ({u/n:.1%})")
    if u:
        for reason, c in collections.Counter(
                r["reason"].split(":")[0] for r in rows
                if r["category"] == "unclassified").most_common():
            print(f"    {reason:<34}{c:>8,}")
    print("\nstrategy that fired:")
    for s, c in collections.Counter(r["strategy"] for r in rows).most_common():
        print(f"    {s:<34}{c:>8,}")
    if u / n > 0.05:
        print(f"\n  *** {u/n:.1%} unclassified exceeds the 5% stopping rule. ***\n"
              "  Inspect ./samples/, tighten the patterns, and re-run before\n"
              "  reporting any composition. A residual this size can move any\n"
              "  blended k materially.")


def cmd_report(a):
    rows = _read_results(pathlib.Path(a.out) / "rule_split.tsv")
    n = len(rows)
    ks = dict(json.loads(pathlib.Path(a.k_file).read_text())) if a.k_file \
        else {k: v["k_default"] for k, v in PARAGRAPHS.items()}

    print(f"{'='*72}\nBLENDED k  (n = {n:,})\n{'='*72}")
    print(f"{'paragraph':<22}{'n':>7}{'weight':>9}{'k':>8}{'contribution':>14}")
    print("-" * 60)
    blended = 0.0
    byp = collections.Counter(r["paragraph"] for r in rows)
    for key, meta in PARAGRAPHS.items():
        if not byp[key]:
            continue
        w = byp[key] / n
        k = ks.get(key, meta["k_default"])
        blended += w * k
        print(f"{meta['cite']:<22}{byp[key]:>7,}{w:>9.1%}{k:>8.2f}{w*k:>14.4f}")
    u = sum(1 for r in rows if r["category"] == "unclassified")
    if u:
        w = u / n
        blended += w * UNCLASSIFIED_K
        print(f"{'unclassified':<22}{u:>7,}{w:>9.1%}{UNCLASSIFIED_K:>8.2f}{w*UNCLASSIFIED_K:>14.4f}")
    print("-" * 60)
    print(f"{'BLENDED k':<22}{'':>7}{'':>9}{blended:>8.3f}")
    print(f"\n  against the note's flat assumption of k = 1.00, a factor of "
          f"{1/blended:.1f} if blended k = {blended:.3f}")

    # the bound, recomputed
    M, X, SPAN_R = 2781, 0.4467, None
    print(f"\n{'='*72}\nTHE BOUND, RECOMPUTED   r_bound = (r - k*x)/(1 + x)\n{'='*72}")
    print(f"{'N covered':>10}{'x':>8}" +
          "".join(f"{('r='+str(r)+'bp'):>12}" for r in (115, 230, 500)))
    print("-" * 56)
    for N in (4000, 6000, 8000, 12000):
        x = M * X / N
        cells = "".join(f"{((r/1e4 - blended*x)/(1+x))*1e4:>12,.0f}"
                        for r in (115, 230, 500))
        print(f"{N:>10,}{x:>8.3f}{cells}")
    print("\n  cells are r_bound in bp. Compare against your break-even.")


def cmd_draw(a):
    """Ratification draw: hand-check the machine labels."""
    rows = _read_results(pathlib.Path(a.out) / "rule_split.tsv")
    rnd = random.Random(SEED)
    picks = rnd.sample(rows, min(a.n, len(rows)))
    digest = hashlib.sha256(
        "".join(sorted(r["path"] for r in picks)).encode()).hexdigest()[:16]
    p = pathlib.Path(a.out) / "ratification_draw.md"
    L = [f"# Rule 12d2-2 ratification draw",
         "", f"Seed `{SEED}`, n = {len(picks)}, draw digest `{digest}`.", "",
         "**The machine label is withheld.** Read each filing at the URL and "
         "write your own paragraph in the box. Then run `verify`.", "",
         "**Stated before any result: one disagreement in "
         f"{len(picks)} refutes the machine labels for the whole run.**", ""]
    for i, r in enumerate(picks, 1):
        L += [f"### {i}. {r['company']} ({r['form']}, {r['date_filed']})", "",
              f"<{BASE}{r['path']}>", "",
              "```", "operator_paragraph (a1/a2/a3/a4/b/c/unreadable):",
              "```", ""]
    p.write_text("\n".join(L))
    (pathlib.Path(a.out) / "ratification_key.json").write_text(json.dumps(
        {r["path"]: r["paragraph"] or "unclassified" for r in picks}, indent=2))
    print(f"wrote {p}  ({len(picks)} filings, digest {digest})")
    print("machine labels withheld in ratification_key.json")


def cmd_verify(a):
    out = pathlib.Path(a.out)
    key = json.loads((out / "ratification_key.json").read_text())
    text = (out / "ratification_draw.md").read_text()
    urls = re.findall(r"<" + re.escape(BASE) + r"(\S+?)>", text)
    labs = re.findall(r"operator_paragraph \([^)]*\):\s*([^\n`]*)", text)
    if len(urls) != len(labs):
        sys.exit(f"parse mismatch: {len(urls)} filings, {len(labs)} boxes")
    valid = set(PARAGRAPHS) | {"unreadable", "unclassified"}
    agree = dis = blank = 0
    malformed = []
    for u, l in zip(urls, labs):
        l = l.strip().lower()
        if not l:
            blank += 1; continue
        if l not in valid:
            malformed.append((u, l)); continue
        if l == key.get(u, "").lower():
            agree += 1
        else:
            dis += 1
            print(f"  DISAGREE {u}: operator={l} machine={key.get(u)}")
    done = agree + dis
    print(f"\n  labelled {done}/{len(urls)}, blank {blank}, "
          f"malformed {len(malformed)}")
    if malformed:
        print("  MALFORMED LABELS, not counted either way:")
        for u, l in malformed[:10]:
            print(f"    {u}: {l!r} is not one of "
                  f"{'/'.join(sorted(valid))}")
    if done:
        print(f"  agreement {agree}/{done} = {agree/done:.1%}")
    if dis:
        print("\n  *** THE PRE-COMMITTED RULE: one disagreement refutes the "
              "machine\n  labels for the whole run. Fix the parse and re-run "
              "the census. ***")
    elif blank or malformed:
        print("\n  INCOMPLETE. Every box must carry a valid label before this "
              "reads as a pass.")
    else:
        print("\n  RATIFIED. The composition table may be reported.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--register", default=os.environ.get("DELISTING_REGISTER",
        str(pathlib.Path(__file__).resolve().parent.parent/"data"/"register.tsv")))
    ap.add_argument("--cache", default=".rule_cache")
    ap.add_argument("--out", default="results")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sample", help="fetch a few filings to inspect")
    s.add_argument("--n", type=int, default=12); s.set_defaults(fn=cmd_sample)

    s = sub.add_parser("run", help="classify the register (resumable)")
    s.add_argument("--limit", type=int, default=None)
    s.add_argument("--restart", action="store_true")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("report", help="composition, blended k, the bound")
    s.add_argument("--k-file", default=None,
                   help="JSON {paragraph: k} overriding the defaults")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("draw", help="ratification draw for hand-checking")
    s.add_argument("--n", type=int, default=30); s.set_defaults(fn=cmd_draw)

    s = sub.add_parser("verify", help="score the ratification draw")
    s.set_defaults(fn=cmd_verify)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
