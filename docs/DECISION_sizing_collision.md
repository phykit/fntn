# Prepared decision: the §0.11 sizing collision

**Status: RESOLVED 27 August 2026. The operator took resolution (i).** The
fixed £50,000 is **withdrawn**; the clip floor is **derived** against §13 row
29's tolerance and row 1's fixed cost (§13 row 30). §0.11 is rewritten as the
withdrawal, and **§4.4 and §5.4.4 are restored as derivations rather than
reinstated as constants**, which removes a rule instead of adding one.

*The analysis below is left standing as written, because it is the record the
decision was taken on. Three things are added: §1.1a, the seven-site audit
performed as part of taking the decision; the resolution note in §1.4(i); and
the applied marker in §1.3a. Nothing already written is altered.*

**Reference equity is confirmed at £100,000.**

**Read §1.0 first.** The collision the instruction names is real, and the
arithmetic below found a **prior question** that has to be answered before any
of the three resolutions means anything. Two statements inside §0.11 disagree
with each other, and the manuscript answers in favour of one of them
everywhere else.

---

## 1.0 The prior question: is the clip a FLOOR or a POSITION SIZE?

§0.11's own first sentence says **"The minimum clip moves from £2,500 to
£50,000."** Its third sentence says **"the single-name position moves from
2.5% to 50% of the book."** These are different claims and only one can be
what the manuscript does.

**Everywhere else, the clip is a minimum and nothing else:**

| Where | What it says | What that makes the clip |
|---|---|---|
| §4.4 | zero cells carry `capital_exceeds_clip_floor` | a **floor** |
| §5.2 | "a floored product still below the clip → `advisory_haircut_below_clip`, counted as a kill" | a **floor** |
| §5.9 | "Partial fills: below 60% of clip within the window → close, `liquidity_insufficient_realised`" | a **floor** |
| §5.1 | the explore arm is "accepted at the **minimum clip**" | a **floor** |
| §0.10 | "at £1,000 the fixed cost is 62.5 bps, which breaks the 25 bps rule the clip is *defined* by" | a **floor** |
| §6.7 | position size comes from the base unit and the multipliers; the clip is listed beside them, not as them | a **floor** |

**Nowhere does the manuscript size a position AT the clip.** The clip is the
notional below which a position is not worth taking, and §6.7's base unit is
what decides how large a position actually is.

**The consequence of the floor reading, computed below in §1.2, is not the one
§0.11 records.** §6.7 sizes a position between **£1,875 and £15,000** across
the stop range. **Every one of those is below a £50,000 floor**, so every
candidate that reaches sizing is killed by `advisory_haircut_below_clip`.
**The book takes no positions at all.**

**That is the opposite of the exposure §0.11 describes.** §0.11 records "a
known unbounded exposure with no refusing mechanism". Under the manuscript's
own semantics the £50,000 clip is a **total refusal mechanism**: it refuses
everything, always, for a reason that has nothing to do with the evidence.

**Why that is worse than it sounds, in the paper's own words.** §0.6 states
the failure directly: *"a funnel calibrated to reject everything returns a
null indistinguishable from **there is nothing here**"*. An empty accepted
book is the correct output when the stream contains nothing exploitable. An
empty book produced by a sizing constant is the same artefact with none of the
meaning, and **nothing downstream can tell the two apart**.

**The operator must say which reading §0.11 intended.** Everything below is
computed both ways where the reading changes the answer.

---

## 1.1a The floor audit: SEVEN sites, not six, and they agree

**Performed 27 August 2026 as part of taking the decision. The earlier count of
six was wrong and is corrected here: there are seven.** §0.1 was missed.

| # | Section | Quoted | Reads as |
|---|---|---|---|
| 1 | **§0.1** *(missed in the earlier count)* | *"At £100,000, h = 63 and 3% daily ATR, no stop both preserves the thesis and **clears the minimum clip**."* | **FLOOR.** *Clears* is a threshold word |
| 2 | **§4.4** | *"zero cells carry `capital_exceeds_clip_floor`"* | **FLOOR.** The code names one. *See the naming defect below* |
| 3 | **§5.1** | *"accepted at the **minimum clip**"* | **FLOOR, and additionally sized AT it.** The explore arm elects the smallest permissible size |
| 4 | **§5.2** | *"a floored product still below the clip → `advisory_haircut_below_clip`, counted as a kill"* | **FLOOR.** Unambiguous: below the clip kills |
| 5 | **§5.9** | *"Partial fills: below 60% of clip within the window → close"* | **FLOOR, on the fill.** Consistent with either reading of the clip itself |
| 6 | **§0.10** | *"the clip cannot simply shrink: at £1,000 the fixed cost is 62.5 bps, which breaks the 25 bps rule the clip is **defined** by"* | **FLOOR.** Defines it as the notional at which cost falls to a threshold |
| 7 | **§6.7** | *"Clip £2,500, **defined as** the notional where fixed round-trip cost falls below 25 bps"* | **FLOOR.** Same definition |

**They agree. No site reads the clip as a target or as a ceiling.** §5.1 is the
only one that additionally *sizes at* the floor, and that is a **dual use, not
a contradiction**: the explore arm elects the smallest size the rules permit,
which is the floor by definition. **So there is no disagreement defect and no
§12.1 row is taken for one.**

**One defect WAS found, and it is a legibility defect in a reason code.**
`capital_exceeds_clip_floor` marks a **zero** cell, that is one where the
position **fails to reach** the floor. **The name asserts the opposite**:
*capital exceeds the clip floor* is the passing case. Rule 4 makes a code's
legibility a first-class concern, so this is recorded with its own §12.1 row
(**P96**) and **is not renamed here**, because renaming a reason code is a
change to the registry and takes its own decision.

**One consequence of §5.1's dual use, which the decision inherits.** While the
derived floor is undetermined, **the explore arm has no size**, so the
below-floor region the funnel-depth association otherwise never observes is
unobserved as well.

---

## 1.1 The three rules, verbatim, with section and version

**Rule A, §0.11 (v1.14, §12.1 row P90, 27 August 2026).** Verbatim:

> **Operator decision, 27 August 2026.** The minimum clip moves from **£2,500
> to £50,000**. Reference equity is unchanged at approximately **£100,000**,
> so the single-name position moves from **2.5% to 50%** of the book.

**Rule B, §4.4 (present since v1.8 or earlier; carried unchanged through
v1.14, and not the subject of any §12.1 row in §12.1's table).** Verbatim:

> **Feasibility** (position = 0 where the stop exceeds 30% at full size, 15%
> at the multiplier floor) and **regime** (notional-capped below 7.5% /
> 3.75%), published separately.

*Provenance note, stated rather than implied: §12.1's change log carries no row
introducing 7.5% / 3.75%, so the version of origin cannot be established from
the register and is recorded here as **not determinable from §12.1**. It is
present in v1.14 and in the v1.13 manuscript in the tree. Treating "no row" as
"always been there" would be the assumption this file exists to avoid.*

**Rule C, §6.7 (base unit present since v1.8 or earlier; the cap stack's
current form owes rows P61, P65 and P71; the clip constant was changed by P90
this batch).** Verbatim:

> **Base unit** 75 bps of current equity at risk.

and, in the same section:

> **Caps, binding in fixed order, first-binder recorded:** position risk
> 37.5–75 bps; single name 10%; correlation cluster 3 units; ENB ≥ min(6,
> 0.75k); total risk-at-stop 12%; cross-section = min(risk budget, gross cap,
> 16) plus the explore sub-cap of 4; gross 100% ex-hedge; **participation 2%
> of median daily notional per session over ≤ 3 sessions**.

---

## 1.2 What each implies at £100,000 reference equity, as arithmetic

**Rule A.** The clip is £50,000. Under the position-size reading that is the
notional: **£50,000, or 50.0% of equity.** Under the floor reading it is not a
notional at all; it is the threshold a notional must clear.

**Rule B.** The caps are stated as percentages of equity:

```
full size        7.50% × £100,000 = £7,500
multiplier floor 3.75% × £100,000 = £3,750
```

**Rule C.** The base unit fixes the **risk**, not the notional, so the implied
notional depends on the stop:

```
risk at full size      = 75.0 bps × £100,000 = £750
risk at the cap floor  = 37.5 bps × £100,000 = £375
notional               = risk ÷ stop distance
```

| Stop distance | Notional at 75 bps risk | % of equity | Notional at 37.5 bps risk | % of equity |
|---|---|---|---|---|
| 5% | £750 ÷ 0.05 = **£15,000** | 15.00% | £375 ÷ 0.05 = **£7,500** | 7.50% |
| 10% | £750 ÷ 0.10 = **£7,500** | 7.50% | £375 ÷ 0.10 = **£3,750** | 3.75% |
| 15% | £750 ÷ 0.15 = **£5,000** | 5.00% | £375 ÷ 0.15 = **£2,500** | 2.50% |
| 20% | £750 ÷ 0.20 = **£3,750** | 3.75% | £375 ÷ 0.20 = **£1,875** | 1.88% |

**Rule C's other caps, in pounds, at this equity:**

```
single name 10%           = £10,000
total risk-at-stop 12%    = £12,000
gross 100% ex-hedge       = £100,000, so a £50,000 position permits exactly TWO
participation 2%/session × ≤3 sessions = 6% of median daily notional (MDN)
    → maximum notional = 0.06 × MDN
    → £2,500  requires MDN ≥ £41,667   (§0.10 states ~£42,000: this reproduces it)
    → £7,500  requires MDN ≥ £125,000
    → £15,000 requires MDN ≥ £250,000
    → £50,000 requires MDN ≥ £833,333
```

*The £42,000 figure §0.10 already carries is what confirms the 6% reading of
the participation cap, and it is reproduced here rather than assumed.*

---

## 1.3 Do §4.4 and §6.7 agree, and is §0.11 the outlier? Computed.

**They agree exactly, and the agreement is not a coincidence.**

```
§6.7 at 75.0 bps risk and a 10% stop  = £7,500  = §4.4's full-size cap
§6.7 at 75.0 bps risk and a 20% stop  = £3,750  = §4.4's multiplier-floor cap
§6.7 at 37.5 bps risk and a 10% stop  = £3,750  = §4.4's multiplier-floor cap
```

**§4.4's two constants are §6.7's arithmetic evaluated at a 10% stop**, once at
full risk and once at half. They are one rule written twice, and the second
writing fixes the stop the first leaves free. Where they differ they differ
only in which binds: **§4.4 binds for stops tighter than 10%** (§6.7 would
size larger), and **§6.7 binds for stops wider than 10%** (§6.7 sizes smaller
than the cap on its own). Neither ever contradicts the other; the tighter of
the two simply wins, which is what a cap stack is for.

**§0.11 is the outlier, and by these factors:**

| Compared with | §0.11 exceeds it by |
|---|---|
| §4.4 full-size cap, £7,500 | **6.67×** |
| §4.4 multiplier-floor cap, £3,750 | **13.33×** |
| §6.7 single-name cap, £10,000 | **5.00×** |
| §6.7 at a 5% stop, £15,000 | 3.33× |
| §6.7 at a 10% stop, £7,500 | 6.67× |
| §6.7 at a 20% stop, £3,750 | 13.33× |

**Two of the three rules are the same rule. The third disagrees with both by
between three and thirteen times.**

---

## 1.3a A correction that this arithmetic forced, recorded here and applied

**§0.11 states that the £50,000 clip runs with "nothing in the funnel that
refuses on participation" and "no reason code that fires when an order is
large relative to the depth available to fill it". Both are false.**

§6.7's cap stack has carried **participation 2% of median daily notional per
session over ≤ 3 sessions** throughout, and §0.10 quantifies it. A position
capped by participation below the clip is killed by
`advisory_haircut_below_clip`, which is a reason code that fires on exactly
that condition. Annex A.1's market-impact row is predicated on the book
"outgrowing the participation cap", which presumes it.

**What §0.11's decision (b) actually declined is a participation GATE**, which
would refuse a candidate outright at Gate 1. **A cap and a gate are different
instruments**: a cap shrinks the position and lets the clip floor kill it; a
gate refuses it and names the reason. Decision (b) stands as the operator took
it. **The claim that no participation constraint exists does not stand**, and
§0.11 and the Annex A.1 row are corrected in this commit to say so.

***APPLIED 27 August 2026 as §12.1 row P93.*** The correction is carried into
§0.11, §0.10 and the Annex A.1 row in both the specification and
`docs/OPEN_ITEMS.md`. **The record now says what §6.7 has always said**, and
the participation *cap* is in force whilst the participation *gate* stays
deferred.

**This changes what (b) costs.** At £50,000 the participation cap requires
**median daily notional of £833,333** before a position can be filled inside
three sessions. That is not an unbounded exposure. It is a screen most of the
universe fails, whose failures arrive as `advisory_haircut_below_clip` kills
rather than as a named liquidity refusal.

---

## 1.4 The three resolutions, each with its consequence as a cost

### (i) §4.4 binds. §0.11 becomes a target that never reaches.

> ***TAKEN, 27 August 2026, and taken in a stronger form than this section
> proposed.*** The operator did not merely let §4.4 bind: **the fixed clip is
> withdrawn outright and the floor is derived** (§13 rows 29 and 30). That
> answers Cost 1 below, which observed that (i) alone would empty §4.4 rather
> than restore it, because a capped position of £7,500 could never clear a
> £50,000 floor. **With the floor derived rather than chosen, the second
> decision Cost 1 demanded is the setting of row 29, and it is a governance
> number rather than a structural question.** §4.4 and §5.4.4 are restored as
> derivations; their ATR bounds return by arithmetic once row 29 is set and row
> 1 closes.

**The effective clip is the cap: £7,500 at full size, £3,750 at the multiplier
floor.**

**Cost 1: it does not restore §4.4. It empties it.** Under the floor reading
the clip is still £50,000 and a capped position of £7,500 never clears it, so
**every cell of the reachability matrix is zero** and every candidate carries
`capital_exceeds_clip_floor`. **Resolution (i) is not sufficient on its own**;
it requires a second decision setting the clip floor at or below the cap. That
second decision is not prepared here because it is downstream of §1.0.

**Cost 2, and it reverses the headline cost of the clip move: the PTM levy
un-crosses.** The levy's threshold is **£10,000** of consideration.

```
§4.4 full-size cap        £7,500  <  £10,000  → levy NOT payable
§4.4 multiplier floor     £3,750  <  £10,000  → levy NOT payable
```

**Under (i) the notional never reaches £10,000, so the PTM levy is never
payable, and the 61.4 → 61.5 bp rise §0.11 records as a cost of the clip move
does not occur.** Row 1's UK tiered arithmetic would be taken at £7,500, not
£50,000: the fixed-cost saving against the old £2,500 clip is a fraction of
the ~0.5 bp §0.11 tabulates, and the levy term is `n/a` as it was before.
**Row 1 would have to be re-derived a second time**, and it would move back
towards, though not to, its pre-batch reading.

**One boundary this file does not resolve.** §6.7's **single-name cap is 10%,
which is £10,000, exactly the PTM threshold.** Whether a consideration of
exactly £10,000 is above or below the threshold is a question about the levy's
own wording, which has not been read here. **A rule whose boundary case is
unknown should not be relied on at the boundary**, and under (i) §4.4's £7,500
binds first, so the boundary is not reached; it is recorded because under (ii)
or (iii) it may be.

**Cost 3: the book's stated purpose narrows.** At £7,500 per position and 16
cross-section slots, gross reaches 120% of equity before the slot cap binds,
so the gross cap becomes the operative constraint at roughly 13 positions.
Nothing about the £100,000 laboratory changes, and §0.11's stated aim of a
larger single-name position is simply not achieved.

### (ii) §0.11 overrides. The regime caps are inoperative.

**What justified the caps, and where that is recorded.** §4.4 states them and
says the two surfaces are "published separately"; it gives feasibility a
justification in the same sentence (*position = 0 where the stop exceeds 30%
at full size*) and gives the **regime** caps none. **§12.1 carries no row
introducing them**, so the justification is not on the record anywhere this
file could find it. §0.1 records the adjacent reasoning: a stop wide enough to
preserve a 63-session thesis is ≈1.6·σ·√h, and *"At £100,000, h = 63 and 3%
daily ATR, no stop both preserves the thesis and clears the minimum clip."*
That is a justification for the *relationship* between stop, clip and equity,
which is precisely the relationship a fixed notional severs.

**Cost 1: withdrawing an unjustified rule is cheap; withdrawing an
unexamined one is not, and this is the second.** The caps cannot be shown to
be wrong, because no reasoning was recorded to examine. **Withdrawing a rule
whose justification was never written down is exactly the failure
`CONVENTIONS.md` and this project's style rule warn about**: *a rule whose
justification is not written down gets relaxed by whoever meets it next.* This
resolution is that relaxation.

**Cost 2: it does not stop at §4.4.** A fixed £50,000 notional also overrides
**§6.7's base unit** (risk would become 50,000 × stop, which at a 10% stop is
£5,000, or **6.7× the 75 bps base unit**), **the single-name cap of 10%** (5×
breached), and **the total risk-at-stop cap of 12%** (two positions at a 10%
stop is £10,000 of £12,000, and at a 15% stop £15,000, which **breaches it**).
**Resolution (ii) is not a decision about §4.4. It is a decision to withdraw
the sizing rule and the cap stack together**, and it should not be taken under
a heading that names only the regime caps.

**Cost 3: the participation cap either survives or it does not, and both are
expensive.** If it survives, §1.3a's £833,333 median daily notional is
required and most of the universe cannot be filled. If it is withdrawn with
the rest, the exposure §0.11 describes becomes real for the first time.

### (iii) A hierarchy: size by §6.7, cap by §4.4, §0.11 as a ceiling.

**Is this a new rule or a reading of rules already present?** In two parts, and
they answer differently.

**"Size by §6.7, cap by §4.4" is a READING.** §6.7 already says *"Caps,
binding in fixed order, first-binder recorded"*, and §4.4's constants are
already caps. Stating that the tighter binds adds nothing; §1.3 shows they are
one rule.

**"Treat §0.11 as a ceiling" is a NEW RULE, and therefore apparatus under
armed §0.6.** The clip is a **floor** in every one of the six places §1.0
tabulates, and its two reason codes, `capital_exceeds_clip_floor` and
`advisory_haircut_below_clip`, both fire when a position is **too small**.
**Reading it as a ceiling inverts the operator of the rule.** That is not a
reading; it is a different rule with the same name, it changes a sizing input,
and §0.6 blocks it. *It would take an Annex A.1 row with a predicate and wait,
or an explicit §0 exception with its own §12.1 row.*

**Unless it is inert, in which case it is not apparatus and is also not
useful.** §1.2 shows §6.7 and §4.4 cap the notional at £15,000 at the very
widest, so a £50,000 ceiling **never binds**. A rule that cannot fire adds no
capability, and equally adds nothing. **Recording the clip as an inert ceiling
would leave §0.11 with no operative effect at all**, which the operator may
prefer to either alternative but should choose knowingly rather than discover.

**Cost, common to (iii): it leaves the floor question unanswered.** Whatever
§0.11 becomes as a ceiling, something must still be the floor, and if the
floor stays £50,000 the outcome is §1.0's: nothing is ever sizable.

---

## 1.5 What §4.4 and §5.4.4 need in order to be restored

**§5.4.4 is not an independent question.** Every cell of it is the
intersection of an admissibility class with §4.4's boundary constants, so
**§5.4.4 is restorable exactly when §4.4 is, and never before.** It needs
nothing of its own.

| Resolution | What §4.4 needs before its constants can be recomputed | Also required |
|---|---|---|
| **(i) §4.4 binds** | **A second decision setting the clip floor at or below £7,500.** Without it every cell is zero and the matrix is restored only in the sense that it is fully computable and entirely empty | §13 row 1 re-derived at £7,500, with the PTM levy back at `n/a` |
| **(ii) §0.11 overrides** | **An explicit statement of what replaces §6.7's base unit**, since a fixed notional makes the risk a consequence rather than a control. The ATR bounds then follow from feasibility alone, *position = 0 where the stop exceeds 30%*, which is stop-based and computable | A decision on the single-name cap, the total risk-at-stop cap and the participation cap, each of which a £50,000 notional breaches or strains |
| **(iii) hierarchy** | **Nothing beyond §1.0's answer**, if the ceiling is inert: §4.4's constants are then recomputable from §6.7 exactly as they were, because nothing about the sizing rule has changed. This is the only resolution under which §4.4 and §5.4.4 come back **without a new number being chosen** | The floor question answered separately |

**Stated plainly, because it is the practical content of this section:
resolution (iii) with an inert ceiling is the only one of the three that
restores two sections of the paper without requiring the operator to invent a
constant.** That is an observation about what each choice unblocks, which is
what §1e asked for. **It is not a recommendation and this file does not make
one.**

---

## 1.6 What is being asked, in one place

1. **Is §0.11's £50,000 a floor or a position size?** The manuscript says
   floor in six places; §0.11 says both, one sentence apart.
2. **If a floor:** it is currently above everything §6.7 can size, so the book
   accepts nothing for a sizing reason. Is that intended?
3. **If a position size:** which of (i), (ii), (iii) governs, knowing that
   (ii) withdraws the cap stack and not merely the regime caps, and that
   (iii)'s ceiling reading is apparatus unless it is inert?
4. **Under (i) only:** row 1 must be re-derived at £7,500 and the PTM levy
   returns to `n/a`. Is that understood as reversing the cost §0.11 records?

**Nothing in this file is applied. §4.4 and §5.4.4 remain withdrawn.**
