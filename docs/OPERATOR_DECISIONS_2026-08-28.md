# Operator decisions, 28 August 2026

**Taken by the operator on 28 August 2026 and drafted by this session on their
instruction.** Each states what it reverses or opens, and what it costs. **The
drafting is the agent's; the decisions are the operator's**, and the distinction
is recorded because §3.6.8 turns on which party supplies what.

***What this session did NOT supply, and may not:*** δₘᵢₙ, *n*ₘᵢₙ, the registered
sign and a ratified pre-mortem remain the four inputs nothing machine-raised may
provide. **No draft on the queue has been unblocked by this batch**, and the
queue's steady state is unchanged.

---

## 1a. ROW 22 CARRIES EVERY CLASS `STREAM_TABLE` MAPS TO A STREAM

**Seven classes are declared discoverable**: `buyback`, `clinical_procurement`,
`earnings_event`, `index_reconstitution`, `insider_dealing`,
`major_holdings_change`, `short_interest_disclosure`. Registration re-stamped to
row 15 of `docs/REGISTRATION_HISTORY.md`, `79280b2b50e8fd0b`, caused by
`discoverable_classes` alone.

**What it fixes.** `STREAM_TABLE` mapped seven classes to streams and row 22
declared three. **A proposal correctly classified to one of the other four died
at intake point 9 with `scoring_mode_unsatisfiable` while no control draw could**,
because the control arm draws its class from the registered grid. *A comparison
in which only one arm can fail the check that decides it is not the comparison
§13 rows 19 and 20 register*, and four classes were funnel-reachable and
discovery-unreachable with nothing on the register saying that had been chosen.

**The §0.6 test, applied.** Does it add a gate, a family, a grammar row, a cost
tier, a sizing input, a feed, or a field the funnel reads at decision time?
**No.** It widens a registered field that already exists. Under §3.6.4 the
pointer row governs: *not computed — the tier carries no parameter and proposes
no rule, so there is no diff to take and the reachable set is unchanged by
construction.* **The hard-reachable tuple set does not move.**

**What it costs, and it is real.** §6.4's fourth family now grows faster, and it
consumes design-segment span, which is the binding constraint on this layer from
its first day. **It divides nothing**, so it costs no statistical power; it costs
segment.

## 1b. §0 DECISION 0c OF 27 AUGUST IS REVERSED. `insider_dealing` IS BACK

**This reverses a decision taken by the operator the previous day**, and the
ground for reversing it is that **the decision named no criterion.**

0c reads, in full: *"INSIDER DEALING IS OUT, on achievability grounds."* Nothing
in `OPERATOR_DECISIONS_2026-08-27.md`, `STEP4_REPOINTED_2026-08-27.md`,
`corpora/us/_RETIRED.md`, `OPEN_ITEMS.md` row 22, `ACHIEVABILITY.md` or
`DECISION_PACK.md` names which of the nine criteria it fails.

**Scored against the nine as written, it passes or is unscorable on every one:**

| # | Criterion | Insider purchases, Form 4 |
|---|---|---|
| 1 | Long only, no margin | **MET**, §4.1's direction restriction is long-only for this family by construction |
| 2 | US-listed | **MET**, Form 4 is EDGAR |
| 3 | Min share price USD 10.42 | a universe filter, not a family property |
| 4 | Min liquidity USD 40,312 | a universe filter, not a family property |
| 5 | Actionable at next open | **MET**, filings are regulator-stamped and self-corroborating |
| 6 | Effect exceeds δₘᵢₙ 15.7 bp | **MET by a factor of seven**, on §0.5's own 115 bp post-decay figure |
| 7 | Horizon in {5, 21, 63} | **MET**, §5.4 admits {5, 21} |
| 8 | Obtainable without a purchase | **MET**, EDGAR is free |
| 9 | Backtestable, survivorship included | **UNSCORABLE**, as for every candidate: no archive exists |

**Two further grounds.** `achievability.py` describes itself as reporting which
criteria are met, failed or unscorable, ***naming the failing one***; this was
the only refusal in the tree that named none. And it **cannot have rested on a
lens reading**: nothing in `src/` constructs a `Candidate`, only two test
fixtures do, so the lens has never scored a real object in either lane.

**What the reversal restores.** `corpora/us`, the only discovery corpus this
project has built; the Form 4 block and the eleven fences written around it; and
§13 row 15's only route. **And the thing that matters most: the three surviving
families had no documented effect in this paper**, so §5.4's decay priors and
Gate 1's cost-survival check were running against claims with no literature
behind them — a cost-survival check with no effect size on the other side can
neither pass nor fail.

***What the reversal does NOT do.*** **It does not re-point binding-path step
4.** `§12.1` P126's argument for 8-K Item 2.02 stands on its own ground: a
field-delimited form exercises a parser and not the model-mediated extraction
path, and a trace should be pointed where the machinery is weakest. **Choosing a
trace corpus and choosing a strategy are different decisions**, and this reversal
touches only the second. *If the retirement's unstated ground was in fact the
trace argument, then a family was dropped for being too easy to parse, which is a
fact about the instrument and not about the edge.*

## 1c. THE PROCEDURE STOPPING RULE. §13's membership rule gains a second clause

**§13's membership rule reads:** *§13 holds every quantity requiring measurement
or lookup … nothing pends elsewhere.* **It gains:**

> **No §13 row may be opened by an instrument that has not yet produced a reading
> on a real object.**

**Why.** §0.6 arms against apparatus and nothing arms against procedure, and the
27 August note says so itself: *procedure can absorb unlimited effort while the
binding path stands still.* The register moved 35 → 39 rows in a day, 44 reason
codes are defined and 7 have ever been emitted, and six rows are closed whole.
**The denominator is growing with effort rather than with knowledge**, which is
§0.3's failure mode relocated from versions to rows.

**It would have refused row 35.** That row was opened because criterion 9 of the
achievability lens needs a threshold the register does not hold — and the lens
had never scored a real object of any kind. *The row may well be right; it was
not earned by a reading.* **Row 35 is not closed by this rule**; it is flagged
for re-test against it, because retro-applying a rule to close a row would be the
rule adjudicating its own first case.

**It refuses nothing a measurement raises.** An instrument that has produced one
reading may open rows freely. The clause bites exactly once per instrument, at
the point where it is cheapest to notice.

## 1d. THE DISCOVERY-CORPUS CRITERION, registered before any corpus is chosen under it

**Recorded because its absence read as unavailable rather than unchosen.**
`docs/CANDIDATE_MECHANISMS.md` §D observes that five of six agent proposals
describe a **regulation** rather than a mechanism — Item 703, Regulation M, Rule
10b-18 — and correctly declines to offer an option, on the ground that *changing
what the layer is shown because of what it returned is fitting the input to the
output.* **That reasoning is right and it does not make the question unaskable.**

**The criterion, stated before any corpus is selected under it:**

> A discovery corpus is material that **describes behaviour**: what participants
> did, under what conditions, with what regularity. **A rulebook describes
> permissions**, and a clerk told to read one and emit mechanisms returns the
> rules, accurately. Rule text remains admissible as a corpus for *machinery*
> exercise and is not admissible as a corpus from which mechanisms are expected.

**Registering it now is a pre-registration and not a fit**, because it is written
before the roster changes and it does not name a replacement corpus. **No corpus
is added or removed by this decision.** Row 22's corpus roster is unchanged and
`corpora/us` is reinstated as-is; what changes is that the next roster decision
has a criterion to be argued against rather than a preference.

***Re-read §D after `§12.1` P142 and P143 have run, not before.*** Five of six
proposals describing regulations is **confounded** with the finding that the
clerk was never shown the class table: a clerk with no vocabulary, reading a
rulebook, has nothing to classify to and nothing to classify. **Whether the
corpus is the defect is not yet decidable, and this decision does not decide it.**
