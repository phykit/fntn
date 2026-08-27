#!/usr/bin/env bash
# Build a discovery corpus for one family, on scripts_fetch_us_corpus.sh's pattern.
#
# ONE COPY OF THE EXTRACTION RULE. The extractor is not reimplemented here: it
# is lifted out of scripts_fetch_us_corpus.sh at run time, between its own
# heredoc markers, so the two scripts cannot drift. A second copy of a
# destructive transformation is a second answer to "what was thrown away".
#
# WHY THIS DOES NOT REQUIRE SEC_CONTACT, and why that is a repair rather than a
# relaxation. scripts_fetch_us_corpus.sh refuses without SEC_CONTACT and then
# fetches only law.cornell.edu; no SEC call is made anywhere in it. That is
# `docs/CORRECTIONS.md` A9's conflation of the DISCOVERY corpus with the TRACE
# corpus, in code. This script identifies itself to the host it actually calls,
# using FNTN_CONTACT or SEC_CONTACT if either is set and a project string
# otherwise, and it does not refuse a Cornell fetch for want of a contact the
# SEC would want. The trace-filing fetcher's SEC_CONTACT refusal is untouched.
set -euo pipefail

FAMILY="${1:?usage: $0 <family>}"
REG=discovery_registration.json
BOUNDARY=$(python3 -c "import json;print(json.load(open('$REG'))['archive_opens'])")
[[ -n "$BOUNDARY" && "$BOUNDARY" != "None" ]] || { echo "archive_opens unset"; exit 2; }

CONTACT="${FNTN_CONTACT:-${SEC_CONTACT:-}}"
UA="fntn research corpus builder${CONTACT:+ $CONTACT}"

OUT="corpora/$FAMILY"
RAW="$OUT/_raw"
mkdir -p "$OUT" "$RAW"
MANIFEST="$OUT/_manifest.tsv"; : > "$MANIFEST"
printf 'filename\tadopted\tsource_url\tretrieved_at\traw_bytes\tbytes\n' >> "$MANIFEST"
RAWMANIFEST="$RAW/_fetch.tsv"; : > "$RAWMANIFEST"
printf 'filename\tsource_url\tretrieved_at\tbytes\tsha256\textracts_to\n' >> "$RAWMANIFEST"

EXTRACTOR=$(mktemp)
sed -n "/^cat > \"\$EXTRACTOR\" <<'EXTRACTPY'$/,/^EXTRACTPY$/p" scripts_fetch_us_corpus.sh \
  | sed '1d;$d' > "$EXTRACTOR"
[[ -s "$EXTRACTOR" ]] || { echo "could not lift the extractor; refusing to write a second copy"; exit 4; }

DOCS=$(cat "corpora/_sources_${FAMILY}.tsv")

echo "family $FAMILY; archive opens $BOUNDARY; fetching only material adopted before it"
ok=0; failed=0; refused=0
while IFS='|' read -r name adopted url; do
  [[ -n "$name" ]] || continue
  case "$name" in \#*) continue;; esac
  if [[ ! "$adopted" < "$BOUNDARY" ]]; then
    echo "  REFUSED  $name  (adopted $adopted, not before $BOUNDARY)"
    refused=$((refused+1)); continue
  fi
  if curl -fsS --max-time 45 -A "$UA" "$url" -o "$OUT/$name" 2>/dev/null; then
    cp "$OUT/$name" "$RAW/${name%.txt}.htm"
    sizes=$(python3 "$EXTRACTOR" "$OUT/$name")
    raw_bytes=$(cut -f1 <<< "$sizes"); bytes=$(cut -f2 <<< "$sizes")
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$adopted" "$url" "$now" "$raw_bytes" "$bytes" >> "$MANIFEST"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${name%.txt}.htm" "$url" "$now" "$raw_bytes" \
      "$(sha256sum < "$RAW/${name%.txt}.htm" | cut -d' ' -f1)" "$name" >> "$RAWMANIFEST"
    echo "  ok       $name  ($adopted, $bytes bytes of text from $raw_bytes)"
    ok=$((ok+1))
  else
    echo "  FAILED   $name  $url"
    rm -f "$OUT/$name" "$RAW/${name%.txt}.htm"
    failed=$((failed+1))
  fi
  sleep 0.4
done <<< "$DOCS"
echo "fetched $ok, failed $failed, refused $refused  ->  $MANIFEST"
