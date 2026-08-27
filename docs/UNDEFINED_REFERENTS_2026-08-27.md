# The undefined-referent sweep of specification v1.14

**27 August 2026. Phase 3 of the resumed batch.** §13 row 28 exists because
§9.4 requires *"a stated threshold"* and the document states none. **The
question this sweep asks is how many more there are.**

**The answer is EIGHT**, of which one becomes row 28 and **seven were not
previously named anywhere.**

## Method, so the count can be checked rather than believed

Every line of `docs/spec/from_narrative_to_null_v1_14.md` matched against:

```
\b(a|an|the)\s+(stated|agreed|appropriate|suitable|specified|pre-?registered
   |nominated|chosen|designated|declared|named)\s+<up to three words>
```

**62 raw hits.** Each was read in context and placed in one of three classes.
The pattern is stated here so the sweep can be re-run and disagreed with.

***Hits are not referents and the counts below are of referents.*** One line can
yield three hits and one referent (§9.4's line yields both *"a pre-registered
stopping rule"* and *"a stated threshold"*, which are one missing number), and
one referent can appear on four lines (§9.4's threshold does). **The classes
therefore count 8, 9 and the remainder, and only the first two are counted
exactly**, because those are the two a reader needs to check.

*The honest limit of the instrument.* It finds referents that announce
themselves with a determiner and an adjective. **A rule that simply omits its
parameter without saying "stated" is invisible to it**, and this sweep offers
no estimate of how many of those exist. It is a lower bound on a count, in the
same way the fence's route coverage is a coverage and never a rate.

---

## Class 1: GENUINE. A value the specification demands and never supplies

**Eight. Each with the section that demands it and the line that shows it.**

| # | Section | The referent, verbatim | What it governs | Row? |
|---|---|---|---|---|
| 1 | **§9.4**, L1061 (also §0.6 L156, §0.5 L298) | *"falls below **a stated threshold** for two consecutive blocks"* | when tracing stops, and therefore whether **binding-path step 4** can ever be discharged | **row 28, opened by P103** |
| 2 | **§14**, L1590 | *"across **a stated count of items** spanning source classes and catalyst types"* | how much **breadth** the trace exercise needs before the freeze precondition is met | **none** |
| 3 | **§0.10**, L220 and **§7.6**, L1012 | *"must exceed its measured break-even by **a stated margin** over **a stated minimum sample**"* | promotion of the shadow cohort **to live capital** | **none** |
| 4 | **§3.4 novelty**, L346 | *"A first-mention claim from a roster below **a stated coverage threshold** is flagged rather than trusted"* | when a first-mention claim is trusted, and it feeds the **sizing multiplier** | **none** |
| 5 | **§5.4.2**, L858 | *"names the surprise measure, with **a stated fallback ladder**"* | which surprise measure PEAD drift direction is taken against when the first is not computable | **none** |
| 6 | **§5.4.3**, L860 | *"crossing **a stated band** below the mandatory-offer threshold"* | what counts as a control-accumulation signal | **none**, and see the containment note below |
| 7 | **§3.6.5**, L502 | *"**a stated day**, **a stated source page**, stated fields"* | the manual-collection cadence, whose whole purpose is to stop collection happening when something interesting happened | **none** |
| 8 | **§7.2 / §3.6**, L668 | *"**a pre-registered audit fraction** runs the full panel regardless of early failures"* | which subjects escape fail-fast censoring; **every attribution statistic computes on that sample exclusively** | **none, and it is worse than none.** See below |

### Three of these deserve more than a table row

**#3 is a promotion predicate that calls itself pre-registered and is not.**
§0.10 and §7.6 both say the shadow cohort's promotion to **live capital** is
"pre-registered", and the predicate contains **two** unstated numbers. It is
the only route in the specification by which a candidate that failed a hard
floor later receives money, and the gate on that route is two blanks. *Nothing
can reach it today, the design segment not existing, which is why this is
recorded and not escalated.*

**#8 is a live instance of a defect class this project has already closed
twice, and the sweep is what found it.** `audit_fraction = 0.10` is a **default
argument in `src/fntn/scanner/ingest.py` and `run.py`**. It is **not a field of
the registration object**: `discovery_registration.json` does not contain it and
`src/fntn/scanner/params.py` does not define it. So:

- The specification calls it **pre-registered**. **It is not registered at all.**
- **Two runs under one parameter hash can audit different fractions**, and the
  difference is attributable to nothing. That is word for word the reason
  `rulebook_stopwords`, `lexicon` and the intake budget were each re-stamped,
  at rows 3, 4 and 5 of `docs/REGISTRATION_HISTORY.md`.
- It is **not inert**: §7.2's censoring antidote depends on it, and every
  attribution statistic computes on the audit sample **exclusively**.

**The repair is known, because it has been made twice.** Add the field, re-stamp,
complete `REGISTRATION_HISTORY.md` row 5's object commit, take a §12.1 row.
**It is prepared and NOT taken here**, for a stated reason: a re-stamp moves the
current hash, and §13 rows 21a and 21b name the hash their readings were taken
under, so a re-stamp during a diagnostic phase is exactly the operation that
produced the superseded-hash defect the reconciliation of 27 August had to
repair. **It is written as a pending block in `docs/OPEN_ITEMS.md` instead.**

**#6 is contained and the containment is worth recording.** The concert-party
family "sits in Annex A" as capability, so the missing band cannot be reached by
anything: an unset parameter behind a deferred family is a gap in a rule nothing
executes. It is counted because the rule is written as though operative.

---

## Class 2: COVERED. The referent is named and something carries it

**Nine referents.** These are what the pattern is *supposed* to find and what a healthy
specification looks like: a referent with a register row or a registration field
behind it.

| Section | Referent | Carried by |
|---|---|---|
| §3.4 Gate 1, L382 | *"a stated fraction of the tuple's admissible horizon"* | **§13 row 15**, ingestion-lag threshold, BLOCKED |
| §3.6.7, L563 | *"the pre-registered tolerance θ"* | registered, `theta` = 0.25 placeholder; §14 open decision |
| §3.6.7, L566 | *"a default floor for δₘᵢₙ"* | registered, `delta_min_floor` = 25.0; §14 open decision |
| §6.9, L976 | *"a pre-registered budget"* for currency exposure | §13's one §0 decision, OPEN |
| §3.7, L1217 | *"a pre-registered seed"* | registered, `control_arm_seed` = 20260826 |
| §5.4.1, L852 and P41, L1271 | *"a pre-registered design-segment test"* | **§13 row 16**, news-adjacency magnitude threshold |
| §0.5, L84 and §0.7(c), L164 | *"a named broker schedule"* | **§13 row 1**, PROVISIONAL |
| §13, L1373 and L1376 | *"a stated floor"*, *"a stated range"* | **rows 30 and 29** |
| §14, L1588 | *"producible as a specified entry"* | closed in v1.12 on §12.8's terms |

---

## Class 3: EXCLUDED as prose. Not parameters at all

**The remainder of the 62 hits.** The pattern catches ordinary English, and the exclusions are
listed by shape rather than one by one so the triage can be argued with:

- **A requirement on the evidence, not on the system.** §3.6.1's *"an effect on
  a stated population"* requires the **argument** to state its own population;
  there is no number for the specification to supply.
- **Defined immediately in situ.** §3.6.8's *"six steps, each with a stated
  exit"* is followed by the six exits.
- **Reason-code language.** *"a named reason code"*, *"a stated reason"* and
  their variants describe the registry's contract, and `codes.py` is the
  referent.
- **Change-log and commentary prose.** §12.1 rows describing what a past
  decision chose, including every *"a chosen sizing input"* about the withdrawn
  clip, and §0.6's own argument about *"a chosen set estimates nothing"*.

---

## What the sweep says about the document

**Eight undefined referents in a fourteenth version is not a document falling
apart; the ratio to Class 2 is roughly one to one.** What it does say is that
**"stated" has been doing work that "registered" should have done.** Six of the
eight sit in sections nothing can currently reach, so they are cheap to leave.
**Two are not:** #8 is live in code today, and #3 is the only path from a failed
hard floor to live capital.

*Every one of the eight was found by a pattern in a text editor, in a document
that has had two full review-harness passes over it. That is the argument for
mechanical sweeps over careful reading, made again.*
