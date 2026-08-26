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
printf 'filename\tadopted\tsource_url\tretrieved_at\tbytes\n' >> "$MANIFEST"

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
exchange_act_section16.htm|1934-06-06|https://www.law.cornell.edu/uscode/text/15/78p
rule_16a1_definitions.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-1
rule_16a2_persons_subject.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-2
rule_16a3_reporting.htm|2002-08-27|https://www.law.cornell.edu/cfr/text/17/240.16a-3
rule_16a4_derivative_securities.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-4
rule_16a6_small_acquisitions.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-6
rule_16a8_trusts.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-8
rule_16a13_change_in_form.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16a-13
rule_16b3_employee_plans.htm|1996-08-15|https://www.law.cornell.edu/cfr/text/17/240.16b-3
rule_16b6_derivative_transactions.htm|1991-05-01|https://www.law.cornell.edu/cfr/text/17/240.16b-6
rule_10b5_1_trading_plans.htm|2000-10-23|https://www.law.cornell.edu/cfr/text/17/240.10b5-1
regulation_fd.htm|2000-10-23|https://www.law.cornell.edu/cfr/text/17/243.100
schedule_13d.htm|1978-01-01|https://www.law.cornell.edu/cfr/text/17/240.13d-1
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
    bytes=$(wc -c < "$OUT/$name")
    printf '%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$adopted" "$url" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$bytes" >> "$MANIFEST"
    echo "  ok       $name  ($adopted, $bytes bytes)"
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
out = pathlib.Path(sys.argv[1]); MIN_BYTES = 4000
files = [p for p in sorted(out.glob("*")) if p.is_file() and not p.name.startswith("_")]
problems, notes = [], []
for f in files:
    n = f.stat().st_size
    if n < MIN_BYTES:
        problems.append(f"{f.name}: {n} bytes, below {MIN_BYTES}. Not the document.")
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
print(f"  smallest                     : {min((f.stat().st_size for f in files), default=0)} bytes")
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
