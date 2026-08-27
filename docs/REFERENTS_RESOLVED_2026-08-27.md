# The eight undefined referents, resolved

**27 August 2026. Phase 6 of the delegated-authority batch.**

`docs/UNDEFINED_REFERENTS_2026-08-27.md` swept specification v1.14 and found
**eight** values the document demands and never supplies. **None remains
unnamed.** Each below is **defined**, given a **§13 row**, or recorded
**non-binding with the reason**.

***One is refused rather than resolved, and it is the largest.*** See §6b.

| # | Referent | Section | Outcome |
|---|---|---|---|
| 1 | the trace stopping threshold | §9.4 | **DEFINED.** §13 row 28, CLOSED (P112) |
| 2 | "a stated count of items" | §14 | **DEFINED, and derived.** 200 |
| 3 | "a stated margin over a stated minimum sample" | §0.10, §7.6 | ***REFUSED. §13 row 31, BLOCKED on a §0 decision*** |
| 4 | "a stated coverage threshold" | §3.4 novelty | **§13 row 32, BLOCKED** |
| 5 | "a stated fallback ladder" | §5.4.2 | **Non-binding, with the reason** |
| 6 | "a stated band" | §5.4.3 | **Non-binding, by containment** |
| 7 | "a stated day, a stated source page, stated fields" | §3.6.5 | **§13 row 33, OPEN** |
| 8 | "a pre-registered audit fraction" | §7.2 | **DEFINED.** Registered (P112) |

---

## 6a. The seven that are not the live-capital gate

### #1 and #8: already discharged this batch

Row 28 is CLOSED at zero must-class defects per hundred over two consecutive
blocks of 100. `audit_fraction` = 0.10 is a registration field. Both are recorded
on their rows and neither is repeated here.

### #2, §14's "a stated count of items". **DEFINED, and it DERIVES.**

§14 requires §9.4's harness be run *"across a stated count of items spanning
source classes and catalyst types"*. **The count is no longer free**, because
row 28 fixed the stopping rule:

```
stopping rule: two consecutive blocks at zero must-class defects, n = 100
minimum items to satisfy it                         =  2 x 100  =  200
```

**§14's count is 200**, and it is the stopping rule's own count rather than a
second number beside it. *A precondition that named a different count from the
rule it invokes would let the harness satisfy one and fail the other.*

***What remains is a STRATIFICATION and not a count.*** §14 also requires the
200 to span source classes and catalyst types and to include *"a minimum sample
of the primary catalyst family's live filing flow"*. **That is an allocation of
200 items across strata**, and it cannot be allocated until it is settled **which
pipeline §9.4's requirement is written about**, which is phase 8's question.
**Recorded there and not guessed here.**

### #4, §3.4's roster coverage threshold. **§13 row 32, BLOCKED.**

*"A first-mention claim from a roster below a stated coverage threshold is
flagged rather than trusted."*

**It is not non-binding and it cannot be defined today.** Novelty feeds the
sizing multiplier, and §3.4 says the error is **systematic rather than random**:
first-mention share over-credits relay sources **in proportion to how thin the
roster is**, which is exactly the early-life condition the multiplier operates
in. **A rule that flags a claim only below a threshold nobody has stated flags
nothing.**

**Why it gets a row rather than a value.** The threshold is a share of the
outlet population the system reads, and **no roster coverage has ever been
measured**. Setting it today would be a chosen parameter with no denominator
behind it. **Row 32: BLOCKED on a measurement of roster coverage against an
enumerated outlet population.**

### #5, §5.4.2's surprise-measure fallback ladder. **NON-BINDING, with the reason.**

*"The parameter object names the surprise measure, with a stated fallback ladder
and a hard refusal at the end."*

**Non-binding because both ends of it are absent.** The registration **names no
surprise measure at all**, so there is nothing for a ladder to fall back *from*;
and no PEAD directive exists, no directive of any family being registered.
**The hard refusal at the end of the ladder, `surprise_not_computable`, is the
part that does exist and it is in `codes.py`.**

***The condition on which it becomes binding, stated so it is not forgotten:***
**the moment the registration names a surprise measure, the ladder is required
in the same commit**, because a named measure with no fallback is a rule that
refuses on its first missing input rather than descending.

### #6, §5.4.3's concert-party band. **NON-BINDING, by containment.**

*"An aggregate concert-party holding crossing a stated band below the mandatory
offer threshold is a control-accumulation signal."*

**The family built around it sits in Annex A as capability and is deferred**, so
nothing executes the rule and no candidate can reach it. **An unset parameter
behind a deferred family is a gap in a rule nothing runs.**

***It is counted all the same, because the rule is written as though
operative***, and **the band must be set in the same commit that takes the Annex
A row**, never after.

### #7, §3.6.5's collection cadence. **§13 row 33, OPEN.**

*"Cadence is calendar-driven and pre-registered: a stated day, a stated source
page, stated fields."*

***This one is live, and this batch has already met its consequence.*** §3.6.5's
protocol exists precisely so that *"collection when something interesting
happened"* cannot masquerade as collection. **Three values are named and none is
stated.**

**Phase 4 of the resumed batch found what an unstated protocol produces**: the
twelve drafts on the queue were swept over **ASX and ASIC documents no commit in
this repository carries**, so that population cannot be replayed from its
parameter hash. **A protocol with no stated source page is a protocol that
cannot say which pages it read.**

**Row 33: OPEN, governance.** It is a decision and not a measurement: nothing
needs to be observed before the day, the pages and the fields can be written
down. *Phase 7's invariant closes the reproducibility hole from the other end,
by refusing a sweep over an uncommitted corpus; it does not state the cadence.*

---

## 6b. #3, the promotion-to-live-capital predicate. **REFUSED, and §13 row 31 opened.**

***The two blanks are NOT filled. Nothing in this batch authorises capital.***

**What the predicate says**, in both places, and the wording is nearly identical:

> §0.10: *"Promotion to live capital is pre-registered: the shadow cohort's
> realised net expectancy, after spreads measured on the design segment, must
> exceed its measured break-even by **a stated margin** over **a stated minimum
> sample**."*
>
> §7.6: *"its promotion predicate is pre-registered: realised net expectancy
> after measured spreads exceeding measured break-even by **a stated margin**
> over **a stated minimum sample**."*

**It calls itself pre-registered. It is not registered at all.**

### Why this is refused and not taken

**The operator's delegation covers prepared recommendations on calibration and
hygiene. This is neither.** It is **the gate on real capital**, and:

- **No recommendation for it has been prepared.** There is nothing to take.
- **It is the only route in the specification by which a candidate that failed a
  hard floor later receives money.** §0.10 routes sub-floor candidates to the
  shadow cohort at **zero capital**; this predicate is how they leave it.
- **Setting it would be a §0 decision by any reading**, and §0.6 is armed.

### What the row records, and it is not comfortable reading

**The specification has carried a live-capital gate with two undefined terms
since its first version.** Fourteen versions, a linter, a reference
implementation, a literature lane, a discovery layer, two harnesses and
thirty-odd register entries, and **the sentence that decides when real money is
deployed has never had numbers in it.**

***State it plainly: until the two terms are filled, nothing in this document
authorises capital, and the gate cannot be evaluated either way.*** **It cannot
pass and it cannot fail.** A predicate with an unstated margin is not a strict
gate that nothing clears; it is **not a gate**, and a reader who met it and
assumed the first would be wrong in the direction that matters.

**The containment, stated so this is not read as an active hazard.** Nothing can
reach it today: the shadow cohort requires a design segment, and there is none;
zero backtests, zero frozen designs, zero trades. **The defect is in the rule, and
the rule is unreachable. That is why this is a register entry and not an
alarm.**

**Row 31: BLOCKED on an explicit §0 operator decision.** It goes to the head of
`docs/DECISION_PACK.md`, above §13 row 29, because **it is the
highest-consequence outstanding item in the document.**
