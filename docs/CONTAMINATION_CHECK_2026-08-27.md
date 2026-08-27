# Contamination check: the twelve drafts against `corpora/us/_raw`

**27 August 2026. Phase 4 of the resumed batch.**

## Verdict: RUN AND NEGATIVE

**No draft in the ledger can have read the material now held in
`corpora/us/_raw`, and nothing is marked.** A negative result is recorded as run
and negative, because "we looked and found nothing" and "we did not look" are
different claims and only the first is worth anything.

---

## The question, stated so the answer can be wrong

`corpora/us/_raw` holds **the pages the server sent**, retained because
extraction is destructive. It is underscore-prefixed, so every corpus reader
skips it, and a live defect once made a route pointed **at** an underscore
directory read its contents in full. **If a draft in the ledger had been raised
after that material became reachable, its evidence base would be unattributable
to the registered corpus.** The check is whether any of the twelve was.

---

## The evidence, in one table

| Event | Timestamp (UTC) | Source of the timestamp |
|---|---|---|
| Registration `a06400ef28ebb54c` stamped | **2026-08-26T22:54:01.850224** | `docs/REGISTRATION_HISTORY.md` row 2 |
| **All 24 proposals raised, the twelve drafts among them** | **2026-08-26T23:04:06.875366** | `proposal.raised_at`, identical to the microsecond across all 24 |
| First refusal logged | 2026-08-26T23:04:06.880437 | `refusal.at` |
| Last refusal logged | 2026-08-26T23:04:07.203328 | `refusal.at` |
| **The US corpus documents were RETRIEVED** | **2026-08-26T23:19:31 to 23:19:42** | `corpora/us/_manifest.tsv` at commit `1057c44`, the fetcher's own record |
| `corpora/us` first committed | 2026-08-26T23:19:42 | `1057c44` |
| **`corpora/us/_raw` first existed** | **2026-08-27T08:40:58** | `3293402`, *"Keep the raw pages"* |

**The drafts precede the retrieval of the material by 15 minutes and 25
seconds, and precede the existence of the path `_raw` by 9 hours 36 minutes.**

### Why the manifest settles it and git alone would not

**Git's add-date is an upper bound on when a file appeared on disk, not the
moment it appeared.** This project knows that better than most: the registration
sat untracked while its hash moved, which is the whole reason
`REGISTRATION_HISTORY.md` exists, and row 1 of that chain is a reconstruction
because of it. So *"`_raw` was committed on 27 August"* would be a weak argument
on its own; the pages could have been on disk earlier.

**`_manifest.tsv` closes that gap.** It carries `retrieved_at` per document,
written by the fetcher at fetch time. Every one of the thirteen documents was
retrieved between **23:19:31 and 23:19:42**, after the sweep had already run and
logged its refusals. **The material did not exist anywhere, tracked or
untracked, when the drafts were raised.**

## Two structural confirmations that do not rely on clocks

**One: the hashes.** All twenty-four proposals, all sixty refusals and all
twelve directives carry **exactly one** parameter hash, `a06400ef28ebb54c`. That
is row 2 of the registration chain, stamped ten minutes before the sweep. **No
ledger row anywhere carries a hash stamped after `_raw` came into being**, and
three such hashes exist. The ledger has not been written to since.

**Two: the sources.** Every `source_ref` on the eight agent-origin proposals is
an **ASX or ASIC** URL, and the four control-arm proposals carry `grid:` cell
identifiers. **Not one cites a US source.** `_raw` contains US securities rule
text and nothing else, drawn entirely from `law.cornell.edu`. The two sets do
not intersect.

---

## An observation this check surfaced, recorded because it is not nothing

**The corpus the twelve drafts were actually swept from is not in this tree.**
`query_log` holds one row: *"discovery sweep over 14 documents"* by
`discovery_agent` at the sweep timestamp. The registered corpus at that moment
was `./corpora/us`, and **`corpora/us` did not yet exist**: it was fetched
fifteen minutes later. The documents that produced these proposals were ASX and
ASIC material which **no commit in this repository has ever carried**.

**This is adjacent to a known row and is not the same as it.** §13 row 22 records
that *"UK, AU, EU and NZ [are] profiled but not registered"*, which is a
statement about the roster. **The sharper statement is about replay:** the
twelve drafts on the queue today were raised over documents that are neither
registered nor retained, so the sweep that produced them **cannot be replayed
byte-for-byte from the parameter hash**, which is what rule 1 asks of everything
on the trading path.

*The containment, stated so this is not read as worse than it is.* These are
**drafts blocked on the operator**, none registered, none carrying capital, and
§3.7's fence means agent-selected material cannot reach capital by any route.
The defect is in the *provenance* of a population used for §13 row 21a and row
23 readings, both of which are already PROVISIONAL or BLOCKED and both of which
already state that their population is not an audit stream.

**No repair is attempted here.** It is recorded, and it belongs to row 22.
