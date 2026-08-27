# The corrections register

**Opened 27 August 2026 (P107).** One row per assertion this project has had to
withdraw, whoever made it.

**Why it exists.** §12.1 records what the *specification* changed. It does not
record what was *said and was wrong*, and those are different things: a rule
that was corrected leaves a trace, an assertion that was corrected leaves none
unless someone writes it down. **A project that counts its rule changes
mechanically and its mistaken claims not at all has an accurate change log and
an inaccurate memory.**

**Two sections, deliberately.** Errors made **to** this project by advice, and
errors made **by** this project and refuted by its own instruments. *A register
holding only the first is a grievance list. The second section is what makes it
a register.*

**Provenance is stated per row, on §0.5's vocabulary.** `verified_primary`
means the artefact is in this tree and was read. `named_unverified` means the
brief that opened this register named the error and **nothing in this tree
establishes it**, which is recorded as itself rather than dressed up.

**Nothing is deleted from this file and nothing is overwritten.**

---

## A. Errors made to this project by advice

### A1. sec.gov served a 698-byte stub, and a stub looks like success

| | |
|---|---|
| **Asserted** | that a `curl` of the SEC's site returns the document |
| **True** | it returned a **698-byte stub**, an HTTP 200 carrying no filing |
| **Caught by** | the corpus integrity check, at `1057c44`, *"drop the sec.gov source that returns a stub"* |
| **Provenance** | `verified_primary` |

**Why it cost real time:** a stub arrives as a success. Nothing in the transport
layer distinguishes it from the document, so the failure surfaces downstream as
an empty extraction rather than as a fetch error. **The standing repair** is
`trace_filings.verify_response`, which checks the response **is** the document
by a **byte floor** (1,500 for a Form 4, against the known 698) **and** a
structural marker, because the floor alone would pass a longer wrong page.

### A2. `tidy.sh` reported a cause it had not verified

| | |
|---|---|
| **Asserted** | *"tests ran and failed"* |
| **True** | `pytest` was **not installed**, so no test had run and none had failed |
| **Caught by** | reading the script; the committed version at `9f12f66` carries the repair and names the class in its own comment |
| **Provenance** | `verified_primary` |

The committed script distinguishes the two with a separate exit code and says
why: *"Reporting the second when the first is true is a message asserting a
cause it has not verified, which is the failure class this codebase is built
against."* `tidy.sh` was removed at `5fa65e6` and is in `.gitignore`.

**This is the register's charter case.** The error was not the wrong answer; it
was a **confident answer to a question that had not been asked**.

### A3. The corpus integrity check is one-directional

| | |
|---|---|
| **Asserted** | that the check establishes *"a corpus is not silently smaller than it claims"*, which is its own printed wording |
| **True** | it walks **manifest rows to disk** and detects a missing or wrong-sized file. It does **not** walk **disk to manifest**, so a file present in the corpus directory and absent from `_manifest.tsv` passes |
| **Caught by** | reading `scripts_fetch_us_corpus.sh` against R2d's both-directions requirement |
| **Provenance** | `verified_primary` for the gap; `named_unverified` for whatever the original advice said |

**Checked by hand, both directions, 27 August 2026, and both corpora are
consistent:** `corpora/us` holds 13 manifest rows and 13 files with an empty
symmetric difference; `corpora/us/_raw` holds 13 `_fetch.tsv` rows and 13 files,
likewise empty. **The gap is in the instrument, not in the corpus.** *A corpus
larger than it claims is the direction the check cannot see, and it is the
direction an interrupted fetch produces.*

### A4. A directory's mtime read as a file's mtime

| | |
|---|---|
| **Asserted** | that a directory's modification time dates the material inside it |
| **True** | it dates the **last change to the directory listing** |
| **Caught by** | the phase 4 contamination check, which needed a creation date for `corpora/us/_raw` and did not use one |
| **Provenance** | `verified_primary` for the hazard; `named_unverified` for the original advice |

**Demonstrated in this very tree.** Every directory reads the same timestamp:

```
corpora           2026-08-27 16:57:10.502
corpora/us        2026-08-27 16:57:10.514
corpora/us/_raw   2026-08-27 16:57:10.510
```

**That is the moment the workspace was created, not the moment anything was
fetched.** Read as a creation date it would have placed `_raw` on 27 August at
16:57, hours after the drafts, which happens to be the *right verdict from the
wrong instrument*: the correct dates are `_manifest.tsv`'s `retrieved_at`
(23:19:31 to 23:19:42 on 26 August) and the git commit `3293402` (27 August,
08:40:58). **An instrument that returns the right answer for the wrong reason
will return the wrong one as soon as the case changes.**

### A5. "Nothing refuses on participation"

| | |
|---|---|
| **Asserted** | §0.10, in terms: *"§0.11 resolved to (b), so there is no participation rule that refuses when the depth is absent"* |
| **True** | **§6.7's participation cap is in force**, 2% of median daily notional per session over at most three sessions. What §0.11(b) declined was a participation **gate** |
| **Caught by** | §12.1 row **P93**, which corrected it in the manuscript |
| **Provenance** | `verified_primary` |

**A cap and a gate are different instruments** and the sentence conflated them.
Adding a gate is apparatus under §0.6 and takes a §0 decision; the cap needs
none because it already exists.

### A5b. P96's stated ground for not renaming a code, which was itself an assertion

| | |
|---|---|
| **Asserted** | §4.4, in terms: the naming defect *"is left alone because renaming a reason code is a change to the registry and takes its own decision"* |
| **True** | **the name was never in the registry.** `ALL_CODES` holds forty codes and none is `capital_exceeds_clip_floor`; the string appeared in three documents and **no Python file** |
| **Caught by** | costing the rename for the decision pack, which required knowing what the registry actually held |
| **Provenance** | `verified_primary` |

**Why this row is here and not merely in §12.1.** The rule P96 stated was
sound; **the fact it rested on was not checked**. The defect was therefore
deferred for a cost that did not exist, and the deferral would have created
that cost: once §4.4's matrix is implemented the same rename does become a
registry migration plus a permanently mixed ledger. **A correct rule applied to
an unverified fact produces a decision that is wrong in the direction of
inaction**, which is the quietest way for one to be wrong.

Renamed to `position_below_clip_floor` on 27 August 2026 (P108), on delegated
authority.

### A6. The 1e cost model dropped the per-share commission

| | |
|---|---|
| **Asserted** | that §13 row 1's US cost is **absolute plus proportional**, fitted to two readings |
| **True** | the fit left **~2.16 bp** of non-decaying residual that nothing in the model could name. **It was the per-share commission**, whose per-order minimum makes it behave as a fixed charge below one size and as a rate above it |
| **Caught by** | §12.1 row **P101**, phase 1 of this batch |
| **Provenance** | `verified_primary` |

**The two published readings sat on opposite sides of that regime boundary, and
a linear model fitted across it splits the difference.** Solving the USD 64,000
reading **alone** for the share price predicts **18.84 bp** at USD 3,200 against
the ~19 bp recorded, having never been shown it.

*The correction's own limit, kept:* the **mechanism** is confirmed and the
**share price is not**, row 1's working recording no share price at all.

---

## B. Errors made by this project, and what refuted each

**The pattern is worth naming before the rows.** In every case below, the wrong
belief passed the weaker instrument and was killed by the stronger one, and the
stronger instrument was always **the rules read against a world** rather than
the rules read against each other.

### B1. The pattern-only entity fence: passed every unit test, refused 94% of real proposals

| | |
|---|---|
| **Believed** | that a fence built from patterns worked, on the evidence of a passing suite |
| **Refuted by** | `trace.py`, running real agent proposals through the real machinery: **94% refused** |
| **Repair** | the fence was rebuilt as a **lookup** (P75). *The model classifies; the table decides* |
| **Provenance** | `verified_primary` |

**This is the case `docs/CONVENTIONS.md` cites and it is the register's other
charter case.** The suite was not wrong about what it tested; it tested the
wrong thing.

### B2. A legal-form designator taken for a firm

| | |
|---|---|
| **Believed** | that patterns were safe *for closed grammars*, a designator suffix being a reliable marker |
| **Refuted by** | the trace: **a designator suffix is not on its own a firm** (P80), and the branch was narrowed at `e955d2b` |
| **Provenance** | `verified_primary` |

**The narrowing is the interesting part**: the general argument survived and the
one branch that relied on it did not. *A rule kept for a good reason can still
have a member that fails.*

### B3. Corpus contamination: suspected, checked, **negative**

| | |
|---|---|
| **Believed possible** | that the twelve ledger drafts had been contaminated by `corpora/us/_raw` |
| **Refuted by** | the phase 4 check: the drafts were raised at **23:04:06.875366** on 26 August; the material was **retrieved at 23:19:31 to 23:19:42**, and `_raw` did not exist until 27 August at 08:40:58 |
| **Provenance** | `verified_primary` |

**Recorded as run and negative**, because *"we looked and found nothing"* and
*"we did not look"* are different claims. The check found a different defect
instead: the corpus the drafts were **actually** swept from is in no commit, so
that population cannot be replayed from its hash (P104).

### B4. The raw pages were never retained, and `raw_bytes` had nothing behind it

| | |
|---|---|
| **Believed** | that what sat in the tree as `.htm` was what the server sent |
| **True** | the 26 August fetch **stripped chrome before writing**, so the stored `.htm` was already derived, and the 27 August extraction overwrote it again. **`raw_bytes` was a number with nothing behind it**, and a change to the extractor could be tested only against itself |
| **Refuted by** | the reproducibility repair at `3293402` |
| **Provenance** | `verified_primary` |

**The honest residue, kept:** the 26 August raw pages **are gone**. What is
retained is the 27 August fetch, and the agreement between the two *"is evidence
they were the same pages rather than the pages themselves"*.

### B5. `_raw` was reachable, and the fence had a hole the route walked round

| | |
|---|---|
| **Believed** | that skipping underscore-prefixed **files inside** a route fenced the bookkeeping out |
| **True** | a route pointed **at** an underscore directory had its contents read **in full**. `corpora/us/_raw` was reachable by a **one-line registration edit** |
| **Refuted by** | building the §9.4 trace corpus fence, whose eleven tests were written to fail first and did |
| **Repair** | the skip now covers **the route itself**, in one place, in `corpusio` |
| **Provenance** | `verified_primary` |

**The rule was right and its scope was wrong**, which is the failure a fence
tested only against the files it expects will not find.

### B6. The pooled abort-position distribution, three times

| | |
|---|---|
| **Believed** | that one distribution could describe two arms |
| **Refuted** | **three times**: §13 row 21 pooling a drawn arm with an authored one (P77, P79); row 23 doing the same (P95); and `RunReport._abort_positions` pooling the **agent** arm with the **random-control** arm it exists to be compared against (P105) |
| **Provenance** | `verified_primary` |

**The third is the one that matters most and was found last**, because the first
two were readings published in a document and **this one was in code, rendered
from the ledger on every run**. It hid an agent arm at 4/12 and a control arm at
8/12 whose failures **share no position at all**, behind a pooled 50% describing
neither.

*The lesson this register takes from a defect found three times: a correction
applied to a published number does not travel to the code that produces it.*

### B7. Six floor sites, and there were seven

| | |
|---|---|
| **Believed** | that the manuscript read the clip as a floor in six places |
| **True** | **seven**, and all seven agree |
| **Refuted by** | the floor audit performed for the §0.11 sizing collision (P96) |
| **Provenance** | `verified_primary` |

**A miscount in the direction of a weaker claim is still a miscount**, and the
seventh site is §5.1's explore arm, which is the one that additionally **sizes
at** the floor and is therefore the site the derived-floor resolution costs the
most. *Counting is mechanical because intent flatters the denominator, and it
flatters it in both directions.*

---

## What this register is for, in one line

**Every row above was found by an instrument, never by re-reading.** That is
the argument for keeping it.
