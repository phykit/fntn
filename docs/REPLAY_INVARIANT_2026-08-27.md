# The twelve are marked, and the class is closed rather than the instance

**27 August 2026. Phase 7 of the delegated-authority batch.**

**Three times this project has depended on material it could not produce
again.** Each was closed as an instance. **The class stayed open, which is how
it recurred twice more.**

| # | Instance | How it was closed | What the closure covered |
|---|---|---|---|
| 1 | **The raw fetched pages were never retained.** The 26 August fetch stripped chrome before writing, so what sat in the tree as `.htm` was already derived, and `raw_bytes` was a number with nothing behind it | `corpora/us/_raw` now holds what the server sent, with digests, kept by construction | **that corpus** |
| 2 | **`890a80e3a8566837`'s object is a reconstruction.** No commit carries the registration that hash was taken over | `Registration.save` refuses to overwrite a stamped registration until the prior hash is recorded | **that file** |
| 3 | **The twelve drafts' corpus is in no commit at all.** ASX and ASIC documents, swept at 23:04 on 26 August, fifteen minutes before `corpora/us` was even fetched | *this phase* | **the class** |

***The class is: material that decided something was not committed at the moment
it decided it.*** Retaining raw pages does not stop it. Recording a superseded
hash does not stop it. **Only refusing to decide over uncommitted material does.**

---

## 7a. The twelve are MARKED. Nothing is deleted.

**Twelve `population_not_replayable` refusals written to the `provenance`
surface**, one per subject, against parameter hash `a06400ef28ebb54c`.

**Marked and not deleted, and the distinction is the whole of rule 4.** The
records are retained in full and **nothing about their content is withdrawn**:
what is withdrawn is **the claim that they could be replayed.** *A draft that
cannot be reproduced is still a record of what happened; it is no longer a
record anything can be re-derived from.*

**Why a refusal row and not a column on the record.** A column would have to be
written **over** the existing row, which is the one operation this ledger does
not perform. Appending on the `provenance` surface leaves the original bytes
untouched and puts the mark where every other statement about a subject lives.

**The code's resurrection predicate is deliberately a refusal to resurrect:**

> *Not resurrectable by retention: keeping the material now would not make this
> record reproducible. Only a fresh sweep under a registration that names a
> committed corpus produces a replayable population.*

*Most resurrection predicates name a thing that would fix the record. This one
says the record cannot be fixed, because that is true, and a predicate that
offered a route where none exists would be worse than none.*

**One display-only defect, recorded rather than repaired by deletion.** The
first twelve summaries were rendered with the material string already carrying
the clause the template appends, so they read *"over ASX and ASIC documents that
no commit in this repository carries, which no commit in this repository
carries"*. **The template is corrected for every future render and the twelve
rows are left alone**, rule 4 forbidding the overwrite and §8 summaries being
display-only by construction: nothing downstream reads one back. *A doubled
clause in a display string is a smaller cost than a ledger that can be edited
when its author dislikes the wording.*

---

## 7b. The invariant: no sweep over a corpus git cannot produce again

**`corpusio.uncommitted_routes` and a refusal in `cmd_sweep`.**

**Written to fail first, and it did**, against a corpus directory that exists on
disk and in no commit: `ImportError: cannot import name 'uncommitted_routes'`.

**What it checks, and why the reason names WHICH failure.** *"Not committed"*
spans three very different states, so each is reported as itself:

| State | Reported as |
|---|---|
| The route does not exist | *"the route does not exist on disk"* |
| Not a git work tree | *"not a git work tree, so nothing here can be retrieved again by commit"* |
| Untracked content inside a tracked route | *"untracked content that no commit carries: `<names>`"* |
| Modified content | *"modified content that no commit carries: `<names>`"* |

**`--untracked-files=all` is load-bearing.** Without it an untracked **file**
inside a tracked **directory** is invisible, and **a corpus one document larger
than its last commit is exactly the silent case** this invariant exists against.

**The check runs BEFORE the master is loaded and before a document is opened.**
*A refusal that has already done the work it was refusing is not a refusal.*

**It is discriminating and not merely strict**, and the test asserts both
directions: a loose directory is refused **and** `./corpora/us`, which is
committed, passes.

***THE COST, STATED.*** A corpus fetched and swept in one sitting must now be
**committed between the two**, which is one extra step in every session that
adds material. **That is the price of being able to say afterwards what was
read**, and the sessions that discovered they could not say it paid more.

**`corpus_not_committed` is `refuse_to_score`**, and its resurrection predicate
is the ordinary kind: commit the corpus and re-run, and the sweep then carries a
hash a reader can go back to.

---

## 7c. Why three closures did not close it

**Recorded in `docs/CORRECTIONS.md` as B8, and it is the register's first row
about a PATTERN rather than an error.**

Instances 1 and 2 were each repaired at the point of failure: retain the pages,
record the hash. **Both repairs are correct and neither generalises.** They
answer *"how do we keep this particular artefact?"* when the question is
*"what may a decision be taken over?"*

**The tell was available and was not read.** After instance 2, this project
wrote a file whose whole subject is that **a hash pointing at an object nobody
can retrieve is not a record**. That is the general form. **It was written about
registrations and applied to registrations**, and the corpus sat outside its
scope for another day.

***The generalisation, stated so a fourth instance has to get past it:*** **any
input to a decision must be retrievable by commit at the moment the decision is
taken, and the check belongs at the point of decision rather than at the point
of storage.** Retention is a hope about the future. **A refusal is a fact about
the present.**
