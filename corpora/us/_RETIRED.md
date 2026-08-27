# RETIRED, 27 August 2026. Kept, not deleted.

**This corpus is retired and nothing in it is deleted.**

**What it is.** Thirteen documents of US Section 16 rule text from
`law.cornell.edu`, with `_manifest.tsv` and the raw fetched pages under `_raw/`,
built as the discovery corpus for the **`insider_dealing`** family.

**Why it is retired.** §0 operator decision of 27 August 2026: the
insider-dealing family is retired on **achievability** grounds.
`discoverable_classes` no longer names it, and `Registration` re-stamped for
that field alone.

**Why it is kept.**

- **Rule 4.** Nothing is deleted and nothing is overwritten, and a corpus is a
  record of what was read.
- **The integrity invariant.** `cmd_sweep` refuses over a corpus git cannot
  produce again, and deleting a committed corpus is the same loss from the
  other end.
- **The machinery is family-agnostic and is reused.**
  `scripts_fetch_us_corpus.sh`'s pattern — adoption date per document, refusal
  where a document is not datable, raw retained under `_raw` with a
  re-extraction test, chrome-free extraction, a manifest carrying URL, adoption
  date, retrieval timestamp and both byte counts — **is the pattern every
  corpus built after it follows.**

**What retiring it costs, in full, is recorded on §13 row 22 and in
`docs/STEP4_REPOINTED_2026-08-27.md`.**

***No registration route may resolve here while it is retired.*** It is not
underscore-prefixed and is therefore not fenced by construction; **what keeps it
out of a sweep is that `discoverable_classes` no longer names the class it
serves**, which is a weaker guarantee and is said so rather than implied.
