# Phase 5: the other prepared recommendations, taken

**27 August 2026. Taken on DELEGATED AUTHORITY against recommendations prepared
in `docs/DECISION_PACK.md`, with the operator's standing right to revise.**

---

## 5a. §13 row 28, §9.4's stopping threshold. **TAKEN. CLOSED.**

**The prepared recommendation named the threshold and not the block size**, so
the block size is prepared here, on the rule of three §13 row 21a uses, and both
are taken together. *They are one decision and not two: the rule of three joins
them.*

**Threshold: ZERO MUST-CLASS defects per hundred items, for two consecutive
blocks.** Not zero defects of any class. **The distinction is what makes the
rule satisfiable at all**: §9.4 says `undecidable` *"is the harness's product;
every instance is a candidate register entry"*, so a harness working correctly
generates findings indefinitely and a zero-defects rule would never fire. §9.5
already draws the must-class line and this borrows it rather than inventing a
second.

**Block size: *n* = 100 items.** Derived, not chosen:

```
two consecutive blocks at zero must-class defects  =  2n items at zero
zero events does not estimate zero (§13 row 21a)
95% upper bound on the residual rate  =  3 / 2n
n = 100  ->  3/200  =  1.5 must-class defects per hundred
inverting, n = 150/b for a bound of b per hundred
```

| *n* | Items at zero | 95% upper bound on the residual |
|---|---|---|
| 50 | 100 | 3.0 per hundred |
| **100** | **200** | **1.5 per hundred** |
| 150 | 300 | 1.0 per hundred |
| 300 | 600 | 0.5 per hundred |
| 1,500 | 3,000 | 0.1 per hundred |

**Why 100 and not 300.** Two blocks of 100 is **200 items**, about **three times
all the tracing this project has ever done**. Doubling to 300 buys 0.75 instead
of 1.5 and costs another 400 items on an instrument that **has never once run to
completion**. *The binding constraint on §9.4 today is that it has not been run,
not that it would stop too early.*

***THE COST, STATED. The freeze is signed over a residual must-class defect rate
that could be as high as 1.5 per hundred.*** That is what 200 clean items
supports and it is not zero. **A stopping rule that claimed zero would be
claiming what no finite sample can.**

**Row 28 moves BLOCKED → CLOSED**, and binding-path step 4 becomes
**dischargeable**, which it was not at any *n* before this.

---

## 5b. §13 row 1's pricing election. **TIERED. TAKEN.**

**What it buys.** The US proportional term moves from `104/p` to `74/p`, so the
hard floor falls by **28.8%** and the minimum admissible share price at the
registered 10 bp tolerance moves from **USD 10.40 to USD 7.40**. At USD 20 a
share the clip floor falls from **USD 8,333 to USD 6,349**.

**Does tiered dominate at every size? Under row 1's model, YES, and the answer
is weaker than it looks.**

At one share price, comparing like with like:

| Share price | Position | Fixed | Tiered | Tiered wins by |
|---|---|---|---|---|
| USD 15 | USD 3,000 | 20.267 bp | 20.267 bp | **0.000** |
| USD 15 | USD 6,000 | 13.600 bp | 11.600 bp | 2.000 |
| USD 15 | USD 64,000 | 7.558 bp | 5.558 bp | 2.000 |
| USD 43.79 | USD 6,000 | 10.091 bp | 10.091 bp | **0.000** |
| USD 43.79 | USD 64,000 | 3.000 bp | 2.315 bp | 0.685 |
| USD 100 | USD 12,000 | 5.040 bp | 5.040 bp | **0.000** |
| USD 100 | USD 200,000 | 1.240 bp | 0.940 bp | 0.300 |

**There is no size at which fixed beats tiered under this model, and there is a
large region where they are IDENTICAL**: below `V = 200p` the per-order
commission minimum binds on both and the cost is the same USD 6.00 round trip.
**Tiered's advantage is exactly zero at and near the clip floor for higher-priced
names**, and appears only once the rate binds.

### ***THE COST, AND IT IS LARGER THAN THE BENEFIT IS CERTAIN***

**The model cannot distinguish the two schedules on anything but the per-share
rate, because it was never shown anything else.** P101 fitted **both** schedules
to the **same two readings**, giving each the same **USD 4.00** of other fixed
charges and the same **USD 1.00** per-order minimum, and solving only the share
price. **So "tiered is 28.8% cheaper" is not a measurement. It is `74/104`
restated**, and it holds only if tiered's third-party pass-throughs are no
larger than whatever fixed absorbs.

**That is precisely the assumption the instruction warned against, and it is not
verified in this tree.** Fixed pricing bundles exchange and most regulatory
fees; tiered charges a lower commission and passes them through. **No published
schedule has been read here**, which is why row 1 is PROVISIONAL, and *the
election was taken on a model that assumes the difference away.*

**The direction of the error is known even though its size is not.** Every
unmodelled pass-through is charged under tiered and absorbed under fixed, so
**every one of them narrows the gap and none widens it.** **`74/p` is therefore
a LOWER bound on tiered's proportional term and `USD 7.40` is a LOWER bound on
its minimum share price.**

**Recorded as a named gap on row 1 rather than as a closure.** *If the schedule,
when read, shows pass-throughs above about 0.0015 per share, the election
reverses and every figure derived from `74/p` in this batch reverts to `104/p`.*
**The reversal is arithmetic and costs no decision.**

---

## 5c. §13 row 1's FX route. **MANUAL SPOT CONVERSION. TAKEN.**

**On the prepared dominance argument, and it survives the provenance gap.**
Automatic conversion would have to price below **0.0031%** to beat manual at USD
64,000, which is a **tenth** of the 0.03% reported on IBKR's own pages. **The
recommendation rests on the order of magnitude and not on the figure.**

**The asymmetry is what carries it.** Choosing automatic when manual is cheaper
costs about **5.4 bp per round trip, on half the book, silently, for ever**.
Choosing manual when automatic is cheaper costs **at most USD 2.00 per order**,
bounded by a minimum rather than proportional to size.

***THE GAP IS NOT CLOSED AND IS RECORDED AS SURVIVING RATHER THAN RESOLVED.***
The automatic-conversion rate is **still uncited**: the one attempt to fetch
IBKR's spot-currency pricing page returned **HTTP 403** and nobody has read it.
**Provenance stays `verified_secondary` and row 1's FX term stays OPEN.**

*The decision and the citation are different objects.* **The decision is taken
because it does not depend on the number; the row stays open because the paper
does.**

---

## 5d. §13 row 1 itself. **STAYS PROVISIONAL, on ONE named gap.**

Three gaps stood. **Two are now decided and one is not decidable by anyone here:**

| Gap | State |
|---|---|
| Tiered-or-fixed election | **DECIDED: tiered**, on a model that assumes the pass-through difference away. The assumption is recorded on the row |
| FX route | **DECIDED: manual spot**, on a dominance argument that survives the uncited rate |
| **Contracting entity** | **OPEN, and NOT DELEGABLE** |

***Why the entity gap cannot be taken here, and this is a category difference
rather than caution.*** **It is not a recommendation. It is a fact about the
operator's account**, and the prepared entry says so: *"establish it from the
account statement, not from inference."* **There is no conservative direction**:
assuming UK when it is Ireland and assuming Ireland when it is UK are equally
silent errors, and **neither shows up as a failure anywhere in the funnel**.

**Row 1 therefore stays PROVISIONAL. It is not closed.** *A row with two of three
gaps decided is not two thirds closed; it is open, on one gap, and saying so is
the whole point of the status.*

---

## 5e. `audit_fraction`. **REGISTERED. The third instance of a class closed twice.**

§7.2 calls it *"a pre-registered audit fraction"* and it was **a default argument
in `ingest.py` and `run.py`**, absent from the registration object entirely. Two
runs under one hash could audit different fractions with the difference
attributable to nothing.

**Taken exactly as 2a was.** The field enters `Registration`, the object
re-stamps, the prior row's object commit is completed first, and a new row names
`audit_fraction` as the causing field.

***Rows 21a and 21b do not move.*** They name the hash their readings were
**taken under**, which is fixed for ever. *The audit fraction changed no rule the
fence applies.*
