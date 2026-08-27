# The §9.4 trace corpus: containment built, fetch REFUSED

**27 August 2026. Phase 2 of the comprehensive batch. Stopped at 2b, as
instructed, and this file is the record of where it stopped and why.**

## 2a. Containment: BUILT AND HOLDING

The corpus lives at `corpora/_trace_filings/`, underscore-prefixed. It is
**empty**, because nothing was fetched. The fences were built first, which is
the point: a fence written after the material it fences is a fence shaped to
let the material through.

**Why this corpus needs fencing at all.** A Form 4 names an issuer, a reporting
owner and a transaction date. **That is exactly the material the entity fence
exists to keep out of a proposal.** `corpora/us` is rule text and names no
company; this one names little else.

**Eleven tests were written to FAIL first, against a deliberately
mis-registered route, and all eleven did.** The refusals were added afterwards.

| Fence | How | Test |
|---|---|---|
| No registration route can resolve here | `Corpus.__post_init__` raises `CorpusInvalid` on **any** underscore-prefixed path component, so `corpora/_trace_filings/2026` is refused as well as the root | `test_no_registration_route_can_resolve_to_an_underscore_directory`, seven routes |
| A file naming it will not load | The refusal is at construction, so `Registration.load` fails on the file rather than warning about it | `test_a_registration_file_naming_the_trace_corpus_will_not_load` |
| The sweep's loader skips it | `corpusio.corpus_documents` returns `[]` for a fenced route | `test_the_corpus_loader_skips_underscore_directories_at_the_top_level` |
| `discovery.py` cannot name it | The import closure is walked and **no module in it contains the string** `_trace_filings` | `test_discovery_reaches_no_module_that_names_the_trace_corpus` |
| The fetcher is outside the closure | `fntn.scanner.trace_filings` is not reachable from `discovery.py`, and it *does* name the path, so the test above is testing something | `test_the_fetcher_is_outside_the_discovery_import_closure` |

**One defect this found, and it was live before this phase.** `cmd_sweep`
skipped underscore-prefixed **files inside** a route and read everything else.
A route pointed **at** an underscore directory therefore had its contents read
in full. `corpora/us/_raw` was reachable that way by a one-line registration
edit. The skip now covers the route itself, in one place, in `corpusio`.

**Everything produced from this corpus carries `TRACE-NON-EVIDENTIARY`** and
inherits `trace.py`'s refusal to register or admit a directive.

## 2b. Fetch: REFUSED. `SEC_CONTACT` is not set.

```
$ python -m fntn.scanner trace-filings --on 2026-08-26
REFUSED, and nothing was fetched or written:

SEC_CONTACT is not set, so this fetch will not run.
...
THE OPERATOR MUST SET IT. For example:
    export SEC_CONTACT='Your Name your.address@example.com'
exit 4
```

**The operator must set `SEC_CONTACT` and re-run.** The module refuses to
invent a value and refuses a placeholder: the SEC's fair-access policy requires
the caller to identify themselves, **a placeholder is a false statement made to
a regulator's server in order to obtain data**, and it would be written to
every manifest row as though it were the contact.

### What is built and waiting

**The sample size, chosen before fetching and derived rather than picked.**
§9.4's stopping rule reads: *"It runs in blocks; after each, the marginal
defect rate per hundred items is computed; when that falls below a stated
threshold for two consecutive blocks, tracing stops."* **The rule's own unit is
one hundred items, so a block is 100.** It is chosen because the rule that
consumes it names that denominator, not because it is a round number.

**Stated because it bears on binding-path step 4: one block cannot discharge
the stopping rule.** Two consecutive blocks are required, so **200 items is the
arithmetic minimum**, and the threshold the rate must fall below is **unstated
in §9.4 and has no §13 row**. One block buys the first block's rate.

**Endpoints are EDGAR's structured ones**, not screen-scraping: the daily form
index (`/Archives/edgar/daily-index/{yyyy}/QTR{q}/form.{yyyymmdd}.idx`) and the
submissions JSON (`data.sec.gov/submissions/CIK##########.json`). Form 4 is
field-delimited, so per CLAUDE.md's first rule the parser replaces the clerk:
**nothing here calls a model.**

**Amendments are excluded, and that is a choice rather than an accident.** A
`4/A` restates a filing already in the flow, so including it would count one
event twice in any distribution taken over the corpus. Recorded so the next
reader finds the reason and not merely the behaviour.

**Verification asserts the response IS the document, not that the URL
resolved.** A previous session found sec.gov serving `curl` a **698-byte stub
with a 200 status**. Two checks, and they are not redundant: a **byte floor**
(1,500 for a Form 4; the known stub is 698) catches that stub, and a
**structural marker** (`<ownershipDocument`) catches the class of failures the
stub is one instance of. **The size is the cheap first check and the marker is
the guard.** A failure of either raises `ResponseNotTheDocument`, which is
deliberately a different exception from a transport error: *a 200 carrying a
stub looks like success, which is why it cost a session real time, and filing
it as a network error would put it under the heading nobody re-reads.* The
actual status, size and first 200 bytes are reported. **Nothing retries into a
placeholder.**

**The manifest records** url, CIK, company, retrieval timestamp, raw bytes and
SHA-256 digest, and **the response is retained** at
`corpora/_trace_filings/_raw/`, in `corpora/us`'s own idiom. That idiom was
learned the hard way: `raw_bytes` was a number with nothing behind it until the
pages were kept.

### What is NOT built, and why it is not built

**The Form 4 extractor is not written.** It cannot be exercised against a real
filing until the fetch runs, and **an extractor tested only against my own idea
of the format is precisely the defect class §9.4 exists to find**. The
pattern-only entity fence passed every unit test and refused 94% of real
proposals; the trace is what found that. Writing a blind extractor now and
calling it done would repeat that, one layer earlier.

## 2c. The intake run: NOT RUN

**There is no corpus, so there are no subjects.** The registered intake budget
(20 s per point, 120 s per subject, one retry) is in force and unexercised by
this phase. Nothing was recorded, and nothing is reported as though it had been.

## What the operator has to do

1. `export SEC_CONTACT='<name> <email>'`
2. `python -m fntn.scanner trace-filings --on <a trading day>`
3. Report the outcome. **If the 698-byte stub recurs, it will be reported as
   itself with the actual bytes**, and the next step is a question about SEC
   access rather than a workaround.

Until then, **phase 3's four §13 rows have no new observations** and phase 3
says so rather than reading a corpus of zero as a result.
