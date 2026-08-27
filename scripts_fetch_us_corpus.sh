#!/usr/bin/env bash
# Fetch a pre-archive US discovery corpus into corpora/us/.
#
# WHAT THIS FETCHES, AND WHY IT IS THIS RATHER THAN FILINGS
#
# The agent's job is to emit class-level MECHANISMS. The material that supports
# that is the disclosure regime itself: the statute, the rules, and the staff
# guidance that says how the rules are applied in practice. That
# is how the ASX, SEDI and MAR sweeps produced their proposals, and it carries no
# episode risk at all, because a rule names no issuer and no date of an event.
#
# Individual Form 4 filings are deliberately NOT fetched. They would name
# issuers, which is exactly the material the entity fence exists to keep out of
# a proposal; putting them in front of the agent and relying on the fence to
# catch what comes back is a weaker design than not showing them at all.
#
# EVERY DOCUMENT HERE PREDATES 2023 by adoption date, which is what makes the
# `pre_archive` guarantee a fact rather than a label. The date is recorded per
# document in the manifest and asserted against the registration's
# archive_opens. A source that cannot be dated is refused rather than fetched
# on the assumption that it is probably old enough.
#
# WHAT IS WRITTEN IS EXTRACTED TEXT, NOT HTML. The 27 August fence measurement
# refused BlackBerry, Opera and API on documents that mention no company at
# all: they are genuine issuer names sitting in Cornell LII's page furniture,
# which the fetch pulled down with the rule text. That is a corpus defect and
# it belongs to §13 row 22, not to the entity fence. A first repair stripped
# <nav>, <header>, <footer> and elements whose class or id names furniture, and
# it reached none of the three: API sits in an HTML comment in <head>, and
# BlackBerry and Opera in a user-agent sniffer in an inline <script>. <head> is
# not <header>, and a comment and a <script> carry no class or id. The strip was
# doing what it was specified to do; the specification did not reach them.
#
# So the corpus stores TEXT. <script> and <style> subtrees are dropped entire,
# comments are dropped, the furniture rules above still apply, and what is
# written is the text that survives. The agent is shown a rule, not a page. The
# manifest records BOTH sizes, raw_bytes and bytes, so what was discarded is on
# the record rather than inferred from a smaller file than last time.
#
# THE COST, STATED. Markup is gone, and a table's structure and a link's target
# go with it: a document whose meaning depended on either would now be read
# wrongly rather than incompletely. These thirteen are statutory prose and do
# not, but a fetch list growing towards filings or data files would, and the
# extension changing from .htm to .txt is the warning to the next reader.
#
# Usage:  export SEC_CONTACT="you@example.com"; bash scripts_fetch_us_corpus.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

REG=discovery_registration.json
[[ -f "$REG" ]] || { echo "no registration; run: python -m fntn.scanner template"; exit 1; }

BOUNDARY=$(python3 -c "import json;print(json.load(open('$REG')).get('archive_opens') or '')")
[[ -n "$BOUNDARY" ]] || {
  echo "archive_opens is not set in $REG."
  echo "pre_archive is defined against that boundary; without it there is"
  echo "nothing to fetch material as predating. Set it first."
  exit 2
}
[[ -n "${SEC_CONTACT:-}" ]] || {
  echo "set SEC_CONTACT to your email: the SEC asks automated callers to identify themselves."
  exit 3
}

OUT=corpora/us
mkdir -p "$OUT"
MANIFEST="$OUT/_manifest.tsv"
: > "$MANIFEST"
printf 'filename\tadopted\tsource_url\tretrieved_at\traw_bytes\tbytes\n' >> "$MANIFEST"

# The text extractor, written out so the same code runs at fetch time and can
# be re-run over an existing corpus without re-fetching it. That is not a
# convenience: the 27 August move from stripped HTML to text was applied to the
# documents already in the tree, and being able to run the fetch's own code over
# them is what made that a re-processing rather than a second implementation.
EXTRACTOR=$(mktemp)
trap 'rm -f "$EXTRACTOR"' EXIT
cat > "$EXTRACTOR" <<'EXTRACTPY'
# Turn a fetched Cornell LII page into the text of the rule, in place.
#
# WHY AT FETCH TIME AND NOT AT READ TIME. The corpus IS the material the agent
# reads. Extracting at read time would leave the defect in the tree and oblige
# every reader to remember the workaround, and the raw byte count in the
# manifest would then describe nothing anyone reads.
#
# WHY TEXT AND NOT STRIPPED HTML. The furniture rules reach elements named nav,
# header or footer, or carrying a furniture-ish class or id. They cannot reach
# an HTML comment or an inline <script>, which carry neither, and that is where
# API, BlackBerry and Opera were: a search-endpoint comment and a user-agent
# sniffer in <head>, putting three genuine issuer names into thirteen documents
# that mention no company at all. Naming <script>, <style> and comments as three
# further things to remove would have closed those three and left the next
# member of the class to be discovered by the fence again. Text has no such
# classes: a construct that carries no text cannot put a name in the corpus.
#
# WHAT IS KEPT. The text of every element that survives the furniture rules,
# with block boundaries as line breaks and runs of whitespace collapsed. No
# text is rewritten and nothing is normalised beyond whitespace, so every word
# in the output is a word the server sent.
import html.parser
import pathlib
import re
import sys

CHROME_TAGS = {"nav", "header", "footer"}
#: Dropped with their subtrees before any text is taken. Their content is
#: program text rather than document text, and it is where the fence's three
#: residual false positives lived.
DROP_TAGS = {"script", "style"}
#: A class or id containing any of these marks the element as furniture. Matched
#: as substrings, so `navbar-collapse`, `dropdown-menu` and `breadcrumb-item`
#: are all caught by their stem.
CHROME_ATTR = re.compile(r"(nav|menu|sidebar|related|footer|breadcrumb)", re.I)
#: Void elements open no subtree, so they are dropped alone rather than starting
#: a skip that would swallow the document to its end.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
#: Block boundaries become line breaks; inline elements do not, so `the
#: <em>issuer</em> shall` stays one sentence rather than becoming three lines.
#: What that trades against is a token split across an inline boundary with no
#: whitespace either side, which in statutory prose is a section number.
BLOCK = {"address", "article", "aside", "blockquote", "body", "br", "caption",
         "dd", "div", "dl", "dt", "fieldset", "figcaption", "figure", "form",
         "h1", "h2", "h3", "h4", "h5", "h6", "hr", "html", "li", "main", "ol",
         "option", "p", "pre", "section", "table", "tbody", "td", "tfoot",
         "th", "thead", "title", "tr", "ul"}


class Extract(html.parser.HTMLParser):
    def __init__(self):
        # Character references are resolved rather than passed through: the
        # output is text, and `&amp;` in text is a defect rather than a datum.
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_tag = None
        self.depth = 0

    def _drop(self, tag, attrs):
        if tag in DROP_TAGS or tag in CHROME_TAGS:
            return True
        return any(
            k in ("class", "id") and v and CHROME_ATTR.search(v) for k, v in attrs
        )

    def handle_starttag(self, tag, attrs):
        if self.skip_tag:
            if tag == self.skip_tag and tag not in VOID:
                self.depth += 1
            return
        if self._drop(tag, attrs):
            if tag not in VOID:
                self.skip_tag, self.depth = tag, 1
            return
        if tag in BLOCK:
            self.out.append("\n")

    def handle_startendtag(self, tag, attrs):
        if self.skip_tag or self._drop(tag, attrs):
            return
        if tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.depth -= 1
                if self.depth == 0:
                    self.skip_tag = None
            return
        if tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, d):
        if not self.skip_tag:
            self.out.append(d)

    # Comments are dropped by not being handled at all. `<!-- API url -->` in
    # LII's <head> is one of the three names this repair was raised against.


def extract_file(path):
    """Rewrite ``path`` as its own text. Returns (raw bytes, text bytes).

    An unclosed dropped element would swallow the document to its end. That is
    checked DIRECTLY, by asking whether a skip is still open when the parse
    finishes, rather than inferred from how much smaller the output is. The
    ratio test the HTML strip used cannot survive the move to text: losing four
    fifths of a page is what extracting text from it looks like, and every one
    of these thirteen documents loses between 73% and 97%.
    """

    p = pathlib.Path(path)
    raw = p.read_bytes()
    parser = Extract()
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()
    if parser.skip_tag:
        raise SystemExit(
            "%s: <%s> is never closed, so everything after it was swallowed. "
            "Refusing to write a document that is mostly gone."
            % (p.name, parser.skip_tag)
        )
    lines = [" ".join(l.split()) for l in "".join(parser.out).split("\n")]
    text = "\n".join(l for l in lines if l).encode("utf-8") + b"\n"
    if not text.strip():
        raise SystemExit("%s: extracted no text at all." % p.name)
    p.write_bytes(text)
    return len(raw), len(text)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        r, t = extract_file(arg)
        print("%d\t%d" % (r, t))
EXTRACTPY

echo "archive opens $BOUNDARY; fetching only material adopted before it"
echo

# filename | adopted (ISO) | url
#
# Every URL here was checked to resolve before this list shipped. Three SEC
# PDFs I had drafted (the Form 4 facsimile, its data instructions and the
# ownership XML technical spec) are deliberately absent: this container cannot
# reach sec.gov to verify them, and two of the three were my guesses at the
# path. A list that half-fails on first run is worse than a shorter list that
# works, so they are omitted with their reason rather than included on hope.
# Add them by hand if you want them, once you have confirmed the paths.
# NOTHING FROM sec.gov IS FETCHED. The page exists and carries the staff
# section 16 C&DIs, but sec.gov returns a 698-byte stub to curl rather
# than the document, reproducibly. A URL that resolves and a URL that
# returns the document are different claims. To include the C&DIs, open
# the page in a browser, save it into corpora/us/, and add a manifest
# line by hand:
#   https://www.sec.gov/divisions/corpfin/guidance/sec16interp.htm
DOCS=$(cat <<'LIST'
exchange_act_section16.txt|1934-06-06|https://www.law.cornell.edu/uscode/text/15/78p
rule_16a1_definitions.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-1
rule_16a2_persons_subject.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-2
rule_16a3_reporting.txt|2002-08-27|https://www.law.cornell.edu/cfr/text/17/240.16a-3
rule_16a4_derivative_securities.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-4
rule_16a6_small_acquisitions.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-6
rule_16a8_trusts.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-8
rule_16a13_change_in_form.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-13
rule_16b3_employee_plans.txt|1996-08-15|https://www.law.cornell.edu/cfr/text/17/240.16b-3
rule_16b6_derivative_transactions.txt|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16b-6
rule_10b5_1_trading_plans.txt|2000-10-23|https://www.law.cornell.edu/cfr/text/17/240.10b5-1
regulation_fd.txt|2000-10-23|https://www.law.cornell.edu/cfr/text/17/243.100
schedule_13d.txt|1978-01-01|https://www.law.cornell.edu/cfr/text/17/240.13d-1
LIST
)

ok=0; failed=0; refused=0
while IFS='|' read -r name adopted url; do
  [[ -n "$name" ]] || continue
  # A document adopted after the boundary is refused, not fetched and flagged.
  if [[ ! "$adopted" < "$BOUNDARY" ]]; then
    echo "REFUSED $name: adopted $adopted, not before $BOUNDARY"
    refused=$((refused+1)); continue
  fi
  if curl -fsS --max-time 45 -A "fntn research $SEC_CONTACT" "$url" -o "$OUT/$name" 2>/dev/null; then
    # Extract before the byte count is taken, so `bytes` is always the size
    # of what a reader will actually read and raw_bytes what the server sent.
    sizes=$(python3 "$EXTRACTOR" "$OUT/$name")
    raw_bytes=$(cut -f1 <<< "$sizes")
    bytes=$(cut -f2 <<< "$sizes")
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$adopted" "$url" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$raw_bytes" "$bytes" >> "$MANIFEST"
    echo "  ok       $name  ($adopted, $bytes bytes of text from $raw_bytes)"
    ok=$((ok+1))
  else
    echo "  FAILED   $name  $url"
    rm -f "$OUT/$name"
    failed=$((failed+1))
  fi
  sleep 0.4          # the SEC asks for no more than 10 requests a second
done <<< "$DOCS"

echo
echo "fetched $ok, failed $failed, refused $refused"
echo "manifest: $MANIFEST"

echo
python3 - "$OUT" <<'CHECKPY'
import hashlib, pathlib, sys
from collections import defaultdict
out = pathlib.Path(sys.argv[1]); MIN_BYTES = 500
# MIN_BYTES applies to the EXTRACTED size, which is what is on disk. The floor
# asks one question, whether the document is present, and page furniture is not
# the document.
#
# WHY 500 AND NOT 4,000. The floor was 4,000 when the file held HTML. The
# standard has not relaxed; the quantity being measured has changed, and the
# same document as text is between a twentieth and a quarter of its own markup.
# 4,000 applied to text would refuse three of these thirteen, including
# Rule 16a-13, which is one sentence long, complete, and 763 bytes.
#
# Derived from both populations rather than chosen. The smallest genuine
# document extracts to 763 bytes. The two non-documents to hand extract to 54
# bytes (Cornell LII's 404 page) and 377 bytes (the sec.gov stub that made this
# script refuse sec.gov, which returns a 403 body to curl). 500 is the round
# number in the gap.
#
# THE GAP IS NARROW, AND THAT IS STATED RATHER THAN SMOOTHED. 377 and 763 are a
# factor of two apart, so a genuinely one-line rule shorter than these thirteen
# would be refused and a fuller error page would pass. The byte floor is no
# longer the main guard against a document that is not there: the extractor
# refuses an unclosed dropped element directly, which is the failure the old
# four-fifths ratio test existed to catch and which no ratio can express once
# the output is text.
files = [p for p in sorted(out.glob("*")) if p.is_file() and not p.name.startswith("_")]
problems, notes = [], []
for f in files:
    n = f.stat().st_size
    if n < MIN_BYTES:
        problems.append(
            f"{f.name}: {n} bytes of text, below {MIN_BYTES}. Not the document."
        )
by_digest = defaultdict(list)
for f in files:
    by_digest[hashlib.sha256(f.read_bytes()).hexdigest()].append(f.name)
for names in by_digest.values():
    if len(names) > 1:
        problems.append("byte-identical, so one URL served another's content: " + ", ".join(names))
by_size = defaultdict(list)
for f in files:
    by_size[f.stat().st_size].append(f.name)
for size, names in by_size.items():
    if len(names) > 1 and len({hashlib.sha256((out / n).read_bytes()).hexdigest() for n in names}) > 1:
        notes.append(f"same size ({size}), different content, which is normal: " + ", ".join(names))
print("Corpus integrity")
print(f"  documents                    : {len(files)}")
print(f"  smallest, extracted          : {min((f.stat().st_size for f in files), default=0)} bytes")
print(f"  floor (MIN_BYTES, extracted) : {MIN_BYTES} bytes")
man = out / "_manifest.tsv"
if man.exists():
    rows = [r.split("\t") for r in man.read_text().splitlines()[1:] if r.strip()]
    if rows and len(rows[0]) >= 6:
        raw_total = sum(int(r[4]) for r in rows)
        kept_total = sum(int(r[5]) for r in rows)
        print(f"  markup and furniture removed : {raw_total - kept_total} of "
              f"{raw_total} bytes ({(raw_total - kept_total) / raw_total:.0%})")
        for r in rows:
            on_disk = (out / r[0]).stat().st_size if (out / r[0]).exists() else -1
            if on_disk != int(r[5]):
                problems.append(
                    f"{r[0]}: manifest says {r[5]} extracted bytes, disk has "
                    f"{on_disk}. The manifest does not describe the corpus."
                )
for n in notes:
    print(f"  note: {n}")
if problems:
    print(f"  PROBLEMS                     : {len(problems)}")
    for pr in problems:
        print(f"    - {pr}")
    sys.exit(1)
print("  no undersized or duplicated documents")
CHECKPY
INTEGRITY=$?
if (( failed )); then
  echo
  echo "A failed fetch is recorded as failed and its file removed. A corpus is"
  echo "not silently smaller than it claims: check the manifest against what"
  echo "you expected before sweeping."
fi
if (( ok == 0 )); then
  echo "Nothing fetched. Not sweeping on an empty corpus."
  exit 4
fi
echo
if (( INTEGRITY != 0 )); then
  echo "Corpus has integrity problems, listed above. Fix before sweeping."
  exit 5
fi
echo "Next:  python -m fntn.scanner sweep"
echo
echo "The sweep produces directive drafts blocked on your delta_min, registered"
echo "sign, ratified pre-mortem and literature search. It produces no evidence:"
echo "the design segment does not exist, so nothing can be measured yet."
