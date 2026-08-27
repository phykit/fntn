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

## THE CLASSES, and which of them carry an invariant

***A register that only lists instances is a list. One that names classes and
installs invariants is an instrument.*** **The rule this section imposes on
itself: a class with THREE OR MORE instances must carry an invariant, and
`test_every_recurring_correction_class_has_an_invariant` refuses this file if one
does not.**

**Twenty-three rows fall into FIVE classes and six singletons.** *The
concentration is the finding: this project does not make many kinds of mistake.
It makes a few kinds, repeatedly.*

***The fourth class is opened 27 August 2026 (P133) at TWO instances, not
three.*** The register's own rule sets three as the point at which an invariant
becomes compulsory. **Three is a floor and not a ceiling**, and this class is
opened early because its second instance was created by the fix for its first:
*row 29 was what broke A7's loop, and P111's recomputation put row 29's own
ceiling inside a new one.* **A class that regenerates itself out of its own
repair does not need a third instance to be believed.**

| Class | Instances | Count | Invariant |
|---|---|---|---|
| **I. A conclusion acted on without checking the link it rests on** | A2, A5b, A8, A9, A10, B8pre, B9 | **7** | **INSTALLED at P122, STRENGTHENED at P130 and again at P131, to four clauses. **The four-clause version DID catch A10, in preparation rather than in outcome**** |
| **II. Material that decided something was not committed at the moment it decided it** | B3, B4, B5, and the registration chain's first object | **4** | **INSTALLED at P114**: `cmd_sweep` refuses over a corpus git cannot produce again, with `corpus_not_committed` |
| **III. A population pooled, mis-scoped or miscounted** | B6 (itself three), B7, the §13 table's two hand counts, and `_unexercised` at P126 | **7** | **INSTALLED at P105 and WIDENED at P126**: the invariant was applied to a METHOD when the class was about a QUERY, so it now reads **every ledger read path carries the marker the fences rely on**, and phase 2 swept every `SELECT` in the package to hold it |
| **IV. A quantity validated against something computed from that quantity** | A7, B10 | **2** | **INSTALLED at P133, and deliberately at two instances rather than three**: *a bound may not be validated against a table computed from that bound*, and a table recomputed against a registered value carries that value's name from then on |
| **V. A guard implemented WEAKER than the rule its own docstring states** | B1, B5, B11, B12 | **4** | **INSTALLED at P136**: *a presence check is not a content check*, and **every guard carries a test that supplies material it must REFUSE, present and well-formed, not merely absent** |
| Singletons, which are not a class | A1, A3, A4, A5, A6, B2 | n/a | n/a, no invariant is owed: a row belonging to no class asserts no recurrence |

---

## THE CLASS I INVARIANT

**The five instances, in one line each, so the shape is visible rather than
asserted:**

| Row | The conclusion | The link nobody checked |
|---|---|---|
| **A2** | *"tests ran and failed"* | whether `pytest` was installed |
| **A5b** | *"renaming a reason code is a change to the registry"*, therefore defer | whether the code was **in** the registry. It was not |
| **A8** | *"row 29 is the biggest release, therefore closing it moves step 3"* | which cells settle step 3. Row 29 is not among them |
| **B8pre** | *"tiered is 28.8% cheaper, therefore elect tiered"* | the published schedule, **which the same row said would refute it** |
| **B9** | *"a Form 4 exercises none of the intake points"* | **which** intake points §9.4 means. The answer was right about the wrong twelve |

***In every one, the link was checkable in minutes — in the tree, or on a page
that answers 200 — and in every one it was checked AFTER the conclusion had been
acted on.***

**The invariant, in two parts, and the second is the one with teeth.**

> **1. A decision is taken on an artefact, never on an argument alone.** The
> `§12.1` row that takes it names what was read: a path in this tree, a test
> name, or a URL with a retrieval date and a digest.
>
> **2. A decision may not be taken over a caveat its own preparation states.**
> Where the preparation names the thing that would refute it, ***that thing is
> checked before the decision, or the decision waits.*** A stated caveat is not
> a discharged one.

***PART 3, added 27 August 2026 (P130) after the invariant fired twice in one
batch and a sixth instance arrived in the same batch.***

> **3. A borrowed quantity is a DERIVATION only where it CAUSES the thing
> derived.** Where it merely shares a unit, a name or a page, it is a
> **coincidence**, and adopting it is a preference wearing a derivation's
> clothes.

**Why part 3 was needed.** The four derivations that have worked all borrowed a
**causal** quantity: §6.7's risk budget **sizes** the position §4.4's bound
constrains; §5.2.2's break-even **is what an effect must clear**; Gate 1's lag
rule **is what kills a stale item**; row 1's schedule **is the cost**.
**Phase 8's offered derivation borrowed §9.4's tracing block size to fix the
precision of a fence's false-positive rate**, and *nothing connects them*:
tracing 100 items does not make 3% the right bound on a rate about a different
population in a different pipeline.

***Parts 1 and 2 would both have passed it.*** It cites an artefact already in
the document, and its preparation states no caveat it then overrides. **It is a
third way for the same class to produce an instance, and it needed its own
clause.**

***PART 4, added 27 August 2026 (P131), because the answer to "would the
installed invariant have caught A9?" is NO.***

> **4. A claim that changes what a phase is FOR is checked against the tree
> before the phase runs.** Where an instruction, a preparation or a handover
> asserts a fact about this repository — what a file contains, what a variable
> gates, what a step needs — **that fact is checked before work proceeds on
> it.**

**Why parts 1 to 3 all missed A9.** A9 was **not a decision**. It was an
assertion made in the framing of a task: *retiring insider dealing takes
`SEC_CONTACT` off the critical path.* **Part 1 governs `§12.1` rows that take
decisions. Part 2 governs decisions taken over caveats. Part 3 governs borrowed
quantities.** ***A9 was a claim nothing was decided on, and all three clauses
reach only decisions.***

**And it was checkable in two greps**: `scripts_fetch_us_corpus.sh` fetches only
`law.cornell.edu`, and `trace_filings.py` is the only thing that touches the SEC.
*That is how it was refuted, after the claim had already shaped a phase.*

***The mechanical support is in the session protocol, not in a test.***
`CLAUDE.md`'s opening reconciliation now requires the batch's **factual premises
about the tree** to be enumerated and each marked **checked or unchecked**.
**A9 would have appeared on that list as unchecked, and checking it costs two
greps.**

**Part 2 is what B8pre needed and part 1 would not have caught.** P112 cited its
preparation file, satisfying part 1 in full, **and its own text said 28.8% was
`74/104` restated and that every unmodelled pass-through would narrow the gap.**
*It named its refutation and took the decision anyway.*

***The cost of part 2, stated: it makes some decisions wait that would otherwise
be taken, and the delegation's whole purpose is not to make decisions wait.***
The trade is deliberate. **A decision taken over a live caveat is not faster
than one that waited; it is one that has to be taken twice**, and B8pre was
taken twice, one batch apart, at the cost of a whole phase.

*What part 2 is NOT.* It is not a bar on deciding under uncertainty. A gap that
the preparation states and **cannot** close — the auto-conversion FX rate under a
403, row 1's contracting entity before the schedules were compared — is a
different thing from a caveat that names a page nobody has opened. **The test is
whether the refuting check was available, not whether the answer was certain.**

---

## THE CLASS IV INVARIANT

**The two instances, in one line each:**

| Row | The bound | What it was validated against |
|---|---|---|
| **A7** | the £2,500 clip, *defined as* the notional at which fixed costs fall below 25 bp | §5.2.2's break-even table, computed on a £6.25 round trip that §0.7(c) records was **recovered backwards from the clip definition** |
| **B10** | §13 row 29's **12.5 bp** upper bound, drawn from §5.2.2's cheapest break-even and its 12.5 bp fixed-cost basis | **§5.2.2 as recomputed by P111 against row 29's own registered 10 bp**, so the table's basis IS the tolerance the bound was meant to constrain |

***The shape, stated once.*** A quantity `X` is used to recompute a table `T`.
`T` is then read as independent evidence about `X`. **It is not evidence about
`X` at all: it is `X`, rearranged.** *The first instance took fourteen versions
to find. The second was created by the repair for the first, in a single
batch, by a row whose own text says no conclusion moved.*

> **THE INVARIANT. A bound may not be validated against a table computed from
> that bound.**
>
> **Operationally, and this is the part that is checkable:** where a table,
> grid or figure is recomputed against a registered value, **the recomputed
> cells carry that value's name from then on**, and any later derivation that
> reads them must state which registered value it is thereby reading. **A
> derivation that finds its own parameter in its own inputs stops and says so.**

**Why it is installed at two instances and not three.** The register's rule
makes an invariant compulsory at three. **This class produced its second
instance out of the fix for its first**, which is a generating mechanism rather
than a coincidence, and *the third instance would by construction be created by
the fix for the second.* **The cost of installing early, stated:** one class now
carries an invariant its instance count does not require, and if no third
instance ever arrives the invariant will look like over-fitting to two events.
**That is the cheaper error.**

**What it does NOT say.** It does not forbid recomputing a table against a
registered bound: P111 was right to do it, the recomputed cells are *upper
bounds that depend on no assumption*, and §5.2.2 is better for it. **What it
forbids is reading the result back as a constraint on the bound.** *Publishing
and reading are different acts, and the loop closes only on the second.*

---

## THE CLASS V INVARIANT

***Two of its four instances arrived on the same day, in two modules, written
against two different rules, and neither was found by reading the code.***

| Row | The rule the docstring states | What the code tested |
|---|---|---|
| **B1** | the entity fence refuses proposals naming an issuer | a *pattern*, tested only against probes authored to that pattern. Real agent material refused **94%** |
| **B5** | underscore-prefixed names are bookkeeping and are not read | the *files*, not the **route**, so `_raw` was reachable by walking round it |
| **B11** | *"refuses to substitute a placeholder: a placeholder is a false statement made to a regulator's server"* | `if not contact`. **`SEC_CONTACT` set to `<name> <email>` passed** |
| **B12** | *"checked at construction, so a misconfiguration surfaces before a sweep is half-run"* | `if not key`. **A ten-character stub passed and the sweep failed at the API** |

***The shape.*** A rule is written in prose, in a docstring, correctly and often
at length. **The check beneath it tests a weaker predicate** — presence instead
of content, a pattern instead of a population, files instead of routes — **and
the gap is invisible because the prose is right.** *Every one of these modules
reads, on inspection, as though it does what it says.*

> **THE INVARIANT, in two clauses.**
>
> **1. A presence check is not a content check.** Where a docstring says what a
> value must *be*, `if not value` does not test it. **The two credential guards
> both failed exactly here**, and an environment variable set to an unedited
> template satisfies every existence test ever written.
>
> **2. Every guard carries a test that supplies material it must REFUSE,
> present and well-formed.** *Not absent, not empty, not obviously malformed:
> the case that looks right and is wrong.* **A guard tested only against
> absence is a guard tested against the one input nobody ships.**

**What the second clause costs, stated.** It is one more test per guard, and
**it is the test that is hard to write**, because writing it means naming the
plausible wrong value — which is the thing whoever wrote the guard did not
think of. *That is not an argument against it. It is the reason the class
exists.*

***Why this is not Class I.*** Class I is a conclusion acted on without
checking the link beneath it, and its four clauses reach decisions, claims and
borrowed quantities. **These are not conclusions; they are implementations**,
and no decision was taken over any of them. *A separate failure mode needed a
separate class, and the register's rule made it compulsory at three.*

***Why B1 and B5 are moved out of the singletons.*** They were filed as
singletons when the register opened, correctly, because no pattern was visible
in two rows. **B11 and B12 make it four**, and *a class is recognised when its
third instance arrives, not when its first is written down.*

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

### A10. "Removing per-trade FX moves row 29's LOWER bound"

| | |
|---|---|
| **Asserted** | that §0 decision 0b, which removes the per-trade FX conversion, moves the lower end of §13 row 29's derived range from 2.375 bp |
| **True** | **it does not move.** The lower bound is the asymptote `104/p`, commission plus clearing, **both per-share and both proportional**. The FX was **USD 4.00, absolute**. The lower bound is the limit the cost approaches as the absolute term is diluted to nothing by size, so **removing a decaying term cannot move a limit reached as it decays.** Measured, it is **2.536 bp**, before 0b and after |
| **Caught by** | **the Class I invariant, in PREPARATION, at P125** — before the recomputation was published and before anything was decided on it |
| **Provenance** | `verified_primary`; `docs/USD_COST_MODEL_2026-08-27.md` §1a and §1c |

***It is the SEVENTH instance of Class I, and the first the invariant caught
before the fact rather than after it.*** **A2, A5b, A8, A9, B8pre and B9 were
every one of them found after the conclusion had been acted on.** This one was
found while the phase that rested on it was being prepared, and the phase was
rewritten rather than corrected.

***What made that possible is PART 4, and it is worth being precise about
why.*** The assertion was **not a decision**. Nothing was decided on it; it was
a claim in the framing of a task, of exactly A9's shape. **Parts 1, 2 and 3
reach only decisions**, so an invariant without part 4 would have let it
through to the same place A9 reached. *The clause added because the invariant
failed its own test question is the clause that caught the next instance.*

**And the counterfactual is recorded rather than assumed.** *Had it gone
unchecked*, the phase would have re-derived the lower bound, produced a
different number for it, and published a range whose lower end had moved for a
reason that does not exist. **Nothing downstream reads the lower bound today**,
so the cost of the error would have been a wrong figure in a register rather
than a wrong trade. ***That is a statement about this instance's blast radius
and not about the class's.***

### A9. "Retiring insider dealing takes `SEC_CONTACT` off the critical path"

| | |
|---|---|
| **Asserted** | that retiring the insider-dealing family removes the dependency on `SEC_CONTACT` |
| **True** | **it does not touch it.** What retiring the family removes is a **discovery corpus**, and the discovery corpus is **thirteen documents from `law.cornell.edu`**, fetched with no SEC contact at all. What needs `SEC_CONTACT` is **step 4's ITEM-PIPELINE trace**, which needs live filings **whatever the family**, and **13D, 8-K and issuer repurchase disclosures are all EDGAR** |
| **Caught by** | the operator, in the instruction that recorded it |
| **Provenance** | `verified_primary` |

***The error was conflating the DISCOVERY corpus with the TRACE corpus.*** They
are different objects with different fences, and `corpora/_trace_filings` is
fenced out of every registration route **precisely so the two cannot be
confused**. **The conflation this error makes is the one that fence exists
against**, which is a sharper way of saying the fence is doing work the prose
around it is not.

***It is the SIXTH instance of Class I***, after A2, A5b, A8, B8pre and B9.
**So the invariant installed at P122 was installed against a class that was
still generating instances**, and §9b of this batch asks whether it would have
caught this one. *An invariant that does not catch the next instance of its own
class is not yet an invariant.*

### A8. "Row 29's closing will move binding-path step 3"

| | |
|---|---|
| **Asserted** | in the batch instruction of 27 August 2026: *"row 29 closing should move step 3"* |
| **True** | **it cannot.** Step 3 is settled by three §14 cells — θ, the δₘᵢₙ floor and the account type — and **§13 row 29 appears in none of them.** Row 29 settles nothing on step 3 at all |
| **Caught by** | the Codespace, before running the report, by reading which register cells the report's own binding-path section says settle each step |
| **Provenance** | `verified_primary` |

**The class: asserting a causal chain without reading the link.** The chain
*"row 29 is the biggest release, therefore closing it moves the path"* is
plausible, and every step of it is checkable in one file. **The link that fails
is the one nobody looked up.**

***Recorded rather than satisfied quietly, and that is the point of the row.***
The convenient response was to take θ and the account type, watch step 3's cells
move, and let the movement line appear to vindicate the expectation. **What was
done instead was to say the expectation was mis-attributed, and then take the
two §14 decisions on their own merits** — which moved two of step 3's three
cells and still did not close it, the δₘᵢₙ floor being deferred until row 1
closed. *Step 3 closed one batch later, and it closed on the δₘᵢₙ floor, not on
row 29.*

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

### A7. Two break-even tables computed against assumed costs, one of them recovered backwards from the thing it was supposed to justify

| | |
|---|---|
| **Asserted** | §5.2.2's break-evens (cheapest 22.5 / 19.5 bp) and §0.10's microcap break-evens (225 / 425 / 625 bp) |
| **True** | both rest on **assumed** fixed costs: §5.2.2 on an assumed £6.25 round trip on £5,000, and §0.10 on the 25 bp implied by the withdrawn £2,500 clip. **§0.7(c) records that the £6.25 was *"recovered backwards from the clip definition"***, and the clip was *defined as* the notional at which fixed costs fall below 25 bp |
| **Caught by** | §13 row 29 being set, which replaced the assumption with a bound and made the recomputation possible |
| **Provenance** | `verified_primary` |

**The circularity is the point.** The commission justified the clip and the clip
justified the commission, and the pair then justified a break-even table that
Gate 1's ceiling reads. **Nothing in that loop was ever measured.** It took
fourteen versions and an explicit tolerance to break it, and what broke it was
not a better estimate but a **bound**: row 29 caps the fixed cost of any
admissible position at 10 bp by construction, so the table can be published as
an upper bound that depends on no assumption at all.

**Recomputed 27 August 2026 (P111): §5.2.2 falls by 2.5 bp everywhere, §0.10 by
15 bp, and no conclusion moves.** *A check run and passed is a different record
from a check not run.*

---

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

### B11. `SEC_CONTACT` was set to `<name> <email>` and the guard admitted it

| | |
|---|---|
| **Asserted** | by `trace_filings.user_agent`'s own docstring: it *"refuses to invent one and refuses to substitute a placeholder: a placeholder is a false statement made to a regulator's server to obtain data"* |
| **True** | the function tested `if not contact` and nothing else. **This session's environment had `SEC_CONTACT` set to the literal string `<name> <email>`**, which passed, and which would have been sent to `sec.gov` in a `User-Agent` header on every request of a hundred-filing fetch |
| **Caught by** | the opening reconciliation's premise enumeration, part 4 of the Class I invariant. *Not by reading `trace_filings.py`, which reads correctly* |
| **Provenance** | `verified_primary`; the environment, and `src/fntn/scanner/trace_filings.py` before P136 |

**The consequence had it not been caught.** Phase 4 of this batch fetches 100
8-K filings from EDGAR. **The SEC's fair-access policy is enforced by
rate-limiting and blocking on the `User-Agent`**, so the outcome would have
been a hundred requests carrying a false identity, and plausibly a blocked
address — *for a project whose entire product is that every refusal is legible.*

**Repaired at P136:** three refusals, unset, placeholder markers, and no email
address. *`example.com` is refused with the brackets, RFC 2606 reserving it for
documentation, and the test that asserted `a.person@example.com` was ACCEPTED
is corrected: it was asserting the defect.*

---

### B12. `ANTHROPIC_API_KEY` was a ten-character stub and the guard admitted it

| | |
|---|---|
| **Asserted** | by `AnthropicClient`'s own docstring: *"Both are checked at construction rather than at first call, so a misconfiguration surfaces before a sweep is half-run"* |
| **True** | it tested `if not key`. **The key was `sk-ant-` plus three characters** and the API returns **401**. The sweep loaded the registration, the security master and three corpora, and then failed at the model call |
| **Caught by** | the same reconciliation pass, the same day, in the same enumeration |
| **Provenance** | `verified_primary`; a live probe of `/v1/models` returning 401, and `src/fntn/scanner/clients.py` before P136 |

***And a second defect sat behind it, which the first one hid.*** The call
carried `temperature=0`, and **`messages.create` in `anthropic` 1.x does not
accept `temperature`**; the current models reject sampling parameters outright.
**The real first failure was `TypeError`, before authentication was ever
reached**, so ***the sweep could not have run even with a working key.***

**What the withdrawal of temperature zero costs, checked rather than assumed.**
**Lost:** two sweeps over identical material may return different proposals.
**Not lost:** replay is served by `TranscriptClient`, `ProposalCache` is keyed
on the prompt's content hash and not on the reply, and the control arm is drawn
from a registered seed with no model in its path. ***Rule 1's guarantee is over
LOGGED data and is untouched.*** *Run-to-run stability was a convenience the
docstring oversold as determinism, and the oversell is the correction.*

**Repaired at P136:** a preflight `models.retrieve` at construction, which
costs no tokens and settles the key and the model identifier together. *A shape
or length test was considered and rejected: it encodes a guess about how keys
are formatted, and the question is not what the key looks like.*

---

### B10. The 12.5 bp ceiling was recomputed into circularity, by this project, in one batch

| | |
|---|---|
| **Asserted** | that §13 row 29's defensible range has a **DERIVED** upper bound of **12.5 bp**, being §5.2.2's cheapest break-even of 22.5 bp less the 12.5 bp fixed-cost basis that table was computed on. Stated as *"the finding"* at P102 and carried through P109's decision |
| **True** | **it was derived when it was written and is not derived now.** P111 recomputed §5.2.2 **against row 29's own registered 10 bp**, so the table's fixed-cost basis **is** the tolerance. A ceiling drawn from that table constrains nothing: it returns the tolerance it was given |
| **Caught by** | P125's re-derivation, which went looking for what 0b had moved and found that the thing that had moved was not the thing the instruction named |
| **Provenance** | `verified_primary`; `§12.1` P102, P109, P111; `docs/USD_COST_MODEL_2026-08-27.md` §1c |

**The sequence, because the ordering is the whole defect.**

1. **P102** derives the ceiling from §5.2.2's *published* column. **Sound**: the published basis, 12.5 bp, was an assumption made years before row 29 existed and was independent of it.
2. **P109** sets row 29 at 10 bp, inside a range whose upper end is that 12.5.
3. **P111** recomputes §5.2.2 against the registered 10 bp, discharges Erratum B, and records that **no conclusion moved**.

***Step 3's check was real and it was run on the wrong thing.*** It asked
whether any published *conclusion* changed value, and none did. **It did not
ask which conclusions had just acquired a dependency on row 29**, and the
answer is: row 29's own upper bound. *A recomputation that leaves every number
where it was can still destroy the independence of one of them.*

**The consequence, and it is not cosmetic.** **Row 29 has had no valid upper
bound since P111**, so between P111 and P133 the register carried a range
`2.4 to 12.5` of which the upper end described only itself, and P109's
justification — *"the value sits inside its derived range rather than at an
edge"* — **rested on it.** *The decision was not thereby wrong; it was less
supported than it said it was, which is a different defect and the one worth
recording.*

**What replaces it.** A tolerance derived from **§6.7's smallest position**,
which is `75.0 bps of reference equity at the widest stop` and **reads no cost
table at all** (§13 row 29, as re-derived at P134). *Chosen because it is the
one input in the neighbourhood that row 29 has never been used to compute.*

***It is the SECOND instance of Class IV, and the first was closed by the very
row this one is about.*** A7 records that row 29's bound is *"what broke the
loop"*. **It broke that loop and opened this one**, which is why the invariant
is installed at two.

### B9. The Form 4 answer was correct about the wrong set

| | |
|---|---|
| **Believed** | that the Form 4 block would exercise **none** of the intake points, the entity fence stopping filings at the first one |
| **True** | that answer is correct about the **discovery layer's twelve** and the question was about **§9.4's requirement**, which is written about the **§3.5 item pipeline**. Against the item pipeline's eleven points a Form 4 block exercises **four directly**, a fifth for some filings, and makes two others pass |
| **Refuted by** | reading §9.4's nouns instead of accepting the inventory: **gates**, **items**, **feed**, **source class**, **catalyst type**, **filing flow**, and not one **intake point** |
| **Provenance** | `verified_primary` |

**The shape of this error is worth naming because it is not a wrong answer.**
Every step of the reasoning was sound and the conclusion follows. **What was
wrong was the referent**, and a wrong referent produces a confident, internally
consistent, checkable answer to a question nobody asked. *`tidy.sh` in A2 made
the same shape of error from the other end.*

**And it cost more than a paragraph.** The conclusion drawn was that *"the one
point the block would light up is the one whose firing would mean the fence had
failed"*, which reads as an argument for **not fetching filings at all**. The
correct reading is the opposite: **the filings are correctly conceived and were
pointed at the wrong intake**, and position 5, `ingestion_lag_exceeds_window`,
is the **only** route to a §13 row 15 observation that row has ever had.

### B8pre. The tiered election was FITTED, not measured, and the Codespace caught its own prior work

| | |
|---|---|
| **Asserted** | P112: elect **tiered**, because it moves the US proportional term from `104/p` to `74/p`, a 28.8% saving |
| **True** | **`74/104` restated.** P101 had fitted **both** schedules to the **same two readings**, giving each the same fixed component and the same USD 1.00 per-order minimum and solving only the share price, **so the model could not distinguish the schedules on anything but the per-share rate.** The published schedules differ on three further things: **tiered's minimum is USD 0.35, not USD 1.00**; **fixed absorbs exchange, clearing and pass-through fees and tiered passes them through**; and the strategy's own fill convention puts it at the **opening auction**, priced separately again |
| **Refuted by** | reading the schedule instead of the fit. **The election reverses to fixed** (P118) |
| **Provenance** | `verified_primary` |

***The defect was found by this Codespace against its own prior work, one batch
later, and that is the part worth recording.*** P112 **named the weakness in the
same row that took the decision**: it wrote that 28.8% was *"`74/104` restated,
not a measurement"* and that *"every unmodelled pass-through narrows the gap and
none widens it"*. **It then took the decision anyway, because the delegation was
over prepared recommendations and this one was prepared.**

**So the failure was not in the analysis. It was in acting on a recommendation
whose own text said what would refute it, without first doing the thing the text
named.** *A stated caveat is not a discharged one, and a decision taken over a
live caveat is a decision taken on a fit.*

**The invariant this suggests is in §6c.**

### B8. One class closed three times, which means it was never closed at all

| | |
|---|---|
| **Believed** | that each of three retrievability failures had been closed |
| **True** | **the same class recurred three times**: the raw fetched pages were never retained; `890a80e3a8566837`'s object is a reconstruction no commit carries; and the corpus the twelve queued drafts were swept from is in no commit at all |
| **Refuted by** | the third instance, found in the phase 4 contamination check that was looking for something else entirely |
| **Provenance** | `verified_primary` |

***This is the register's first row about a PATTERN rather than an error, and
that is why it is here.*** The first two repairs are both correct and **neither
generalises**: retain the pages, record the hash. They answer *"how do we keep
this particular artefact?"* when the question is *"what may a decision be taken
over?"*

**The tell was available and was not read.** After the second instance this
project wrote `docs/REGISTRATION_HISTORY.md`, whose entire subject is that **a
hash pointing at an object nobody can retrieve is not a record.** That is the
general form of the class. **It was written about registrations and applied to
registrations**, and the corpus stayed outside its scope for another day.

**Closed at the class on 27 August 2026 (P114)**: `cmd_sweep` refuses over a
corpus git cannot produce again, with `corpus_not_committed`. **The
generalisation, stated so a fourth instance has to get past it: any input to a
decision must be retrievable by commit at the moment the decision is taken, and
the check belongs at the point of DECISION rather than at the point of storage.**
*Retention is a hope about the future. A refusal is a fact about the present.*

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
