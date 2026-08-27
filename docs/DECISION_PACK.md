# Decision pack: everything waiting on the operator, in one file

**27 August 2026.** Every decision this project owes a person, prepared so it
can be answered without further analysis. **Ordered by what each releases,
descending, with the count against the heading.**

**Nothing here is resolved.** Where a recommendation is given it is argued and
it is still a recommendation. Where a figure could not be verified, the gap is
stated rather than filled.

**Two decisions have their own files because they need more room than a pack
entry:** `docs/DECISION_sizing_collision.md` (item 1 below) and this file's
item 7, which is a worksheet rather than a question.

---

## 1. Is §0.11's £50,000 a FLOOR or a POSITION SIZE? — releases **9**

*Releases: §4.4, §5.4.4, §13 rows 1, 8, 9 and 14, §0.10's microcap table,
§6.7's base-unit reconciliation, and binding-path step 1's re-derivation.*

**Prepared in full in `docs/DECISION_sizing_collision.md`.** Summarised here
because it is the largest release on the board and a reader of this pack alone
should not miss it.

**What it governs.** Whether §0.11 raised the *minimum* position size or set
*the* position size. §0.11's first sentence says one and its third says the
other.

**The defensible range.** Two readings, not a continuum. **Floor** is what the
manuscript means everywhere else: `capital_exceeds_clip_floor`,
`advisory_haircut_below_clip`, "minimum clip", the 60%-of-clip partial-fill
rule. **Position size** is what §0.11's own third sentence asserts.

**What each end implies.** Under **floor**, §6.7 sizes between £1,875 and
£15,000 across the stop range, all below £50,000, so **every candidate is
killed for being too small and the book takes no positions at all**. Under
**position size**, a 50% notional breaches §4.4 by 6.67×, §6.7's single-name
cap by 5×, and strains the total risk-at-stop cap.

**The cost of choosing wrongly, each way.** Choosing *floor* when *position
size* was meant produces an empty book that looks like a null result: §0.6's
own warning, *"a funnel calibrated to reject everything returns a null
indistinguishable from there is nothing here"*. Choosing *position size* when
*floor* was meant withdraws the cap stack without saying so.

**Recommendation: FLOOR, and then lower it.** The manuscript's semantics are
unambiguous in six places against one sentence written in this batch, and the
one sentence is the newer and the less considered. **The argument:** reading it
as a position size requires believing that §0.11 silently repealed §4.4, §6.7's
base unit and three of its caps, none of which it mentions. Reading it as a
floor requires believing only that the floor is now set too high, which is a
number to revisit rather than a structure to demolish.

---

## 2. §13 row 1's three gaps: FX route, tiered-or-fixed, contracting entity — releases **8**

*Releases: §13 rows 8, 9, 12 and 14, §5.2.2's break-even table, §0.5's
economics block, §0.10's microcap table, and binding-path step 1.*

**Row 1 runs first because every break-even denominator in the paper inherits
it.** It is PROVISIONAL: a reading exists (UK tiered 61.5 bp; US ~3 bp at an
illustrative USD 64,000) and the calibration does not.

### 2a. Tiered or fixed IBKR pricing

**What it governs.** Which commission schedule the account elects, and
therefore every bp figure downstream.

**The crossover, derived structurally rather than asserted.** A per-share
schedule costs, per side,

```
cost(V, P)  =  max( m , k · V / P )        and possibly  min( that , cap · V )
    V = trade value    P = share price    k = per-share rate    m = order minimum
```

**Two regimes, and the boundary between them is the whole answer:**

| Regime | Condition | Cost in basis points | Behaviour |
|---|---|---|---|
| **Minimum-bound** | `V < m·P/k` | `10,000 · m / V` | **Falls as the clip grows.** Independent of share price |
| **Rate-bound** | `V > m·P/k` | `10,000 · k / P` | **Flat in the clip. Falls as the share price rises** |

**The structural result, which needs no IBKR constant: above the minimum, a
per-share schedule's basis-point cost does not depend on the clip at all. It
depends only on the share price.** So "which schedule is cheaper" is decided by
the **minimum** at small clips and by the **per-share rate** at large ones, and
at £50,000 any plausible minimum is long since cleared.

**The table the answer is read off**, once the cited schedule supplies `k`,
`m` and any cap. Each cell is `10,000·k/P` basis points:

| Share price `P` | bp at `k` = 0.0035 | at 0.005 | at 0.010 |
|---|---|---|---|
| 10 | 3.5 | 5.0 | 10.0 |
| 25 | 1.4 | 2.0 | 4.0 |
| 50 | 0.7 | 1.0 | 2.0 |
| 100 | 0.35 | 0.5 | 1.0 |
| 250 | 0.14 | 0.2 | 0.4 |

***The `k` column headings are ILLUSTRATIVE PLACEHOLDERS and are not IBKR's
rates.*** They are there to show the shape and the sensitivity. **Substituting
the cited schedule's own `k` is the whole of the remaining work**, and doing it
from memory is what row 1 exists to prevent.

**A finding that argues for the citation rather than against it.** The two
figures on the record cannot be reconciled to a single schedule shape. US cost
falls from about 19 bp at the old clip to about 3 bp at USD 64,000. **A purely
rate-bound schedule would be flat in the clip and would not fall at all; a
purely minimum-bound one implies a per-side minimum near USD 3.04 at the small
clip and near USD 9.60 at the large one, which a minimum by definition does
not do.** So the true schedule has at least a third term. **Reverse-engineering
it from two points would be fitting a parameter and presenting it as a
restriction**, and it is refused here.

**Cost of choosing wrongly, each way.** Electing **fixed** when tiered is
cheaper overpays on every trade by the rate gap, which at a 50% single-name
position is the largest per-trade cost the book carries. Electing **tiered**
when fixed is cheaper exposes the account to per-venue exchange and regulatory
pass-throughs that the fixed schedule bundles, **which is exactly the class of
term the §13 row 1 scope question already before the operator is about**.

**Recommendation: none, and deliberately.** The answer is `k`, `m` and the cap
read off the cited schedule. **A recommendation here would be a guess wearing a
recommendation's clothes.**

### 2b. Which IBKR contracting entity

**What it governs.** Which regulator, which investor-compensation scheme, which
client-money regime, and which schedule applies at all. **It also decides
whether 2a's answer is even the right table.**

**The defensible range: two.** **IBKR (U.K.) Limited**, FCA-regulated; or
**IBKR Ireland Limited**, Central Bank of Ireland-regulated. UK retail clients
opened since the post-Brexit migration have generally been moved to the Irish
entity, so **the live question is usually "which one is the account actually
with", not "which should it be"** — this is a **fact to establish**, not a
preference to express.

**What each implies.**

| | IBKR (U.K.) Limited | IBKR Ireland Limited |
|---|---|---|
| Regulator | FCA | Central Bank of Ireland |
| Compensation scheme | FSCS | Irish investor compensation scheme |
| Schedule page | `interactivebrokers.co.uk` | `interactivebrokers.ie` |
| Base-currency and FX handling | per that entity's published schedule | per that entity's published schedule |

***The rows above are the shape of the answer and the specific scheme limits
are NOT stated here, because they were not read from a primary source in this
session.*** Filling them from memory is the failure §0.5's provenance
vocabulary exists to prevent.

**Cost of getting it wrong, each way.** Assuming **UK** when it is **Ireland**
means every bp in the paper is read off the wrong schedule page and the
compensation limit quoted to any future reader is the wrong one. Assuming
**Ireland** when it is **UK** has the same shape. **There is no conservative
direction: both errors are equally silent, and neither shows up as a failure
anywhere in the funnel.**

**Recommendation: establish it from the account statement, not from inference.**
It is a one-look fact and it gates 2a and 2c.

### 2c. The FX route: manual spot versus automatic conversion

**What it governs.** The FX term of row 1, on every US trade, in both
directions. **Under §0.11 a US position is 50% of the book, so this term is
now applied to half the book at a time.**

| Route | Rate | Minimum | Provenance |
|---|---|---|---|
| **Manual spot conversion** | **0.20 bp** of converted value | **USD 2.00** per order | Published schedule |
| **Automatic conversion** | **0.03%** = **3.0 bp** applied to the exchange rate | none stated | **NOT VERIFIED — see below** |

**The crossover, and it is decisive.** Manual is minimum-bound below the value
where 0.20 bp exceeds USD 2.00:

```
0.000020 · V  =  2.00   →   V  =  USD 100,000
```

| Converted value | Manual cost | Manual, in bp | Automatic at 3.0 bp | Cheaper |
|---|---|---|---|---|
| USD 5,000 | USD 2.00 (minimum) | 4.00 | USD 1.50 | **automatic** |
| USD 10,000 | USD 2.00 (minimum) | 2.00 | USD 3.00 | **manual** |
| USD 25,000 | USD 2.00 (minimum) | 0.80 | USD 7.50 | **manual** |
| **USD 64,000** *(the illustrative clip)* | **USD 2.00 (minimum)** | **0.31** | **USD 19.20** | **manual, by ~9.6×** |
| USD 100,000 | USD 2.00 (at the boundary) | 0.20 | USD 30.00 | **manual, by 15×** |
| USD 250,000 | USD 5.00 | 0.20 | USD 75.00 | **manual, by 15×** |

**The break-even between the two routes is USD 6,667** (`2.00 / 0.0003`), below
which automatic is cheaper. **At the £50,000 clip the trade is roughly ten
times that**, so **manual spot conversion is cheaper by about an order of
magnitude, and the gap widens with size.** At two conversions per round trip
the automatic route costs about **6 bp** of the position against about **0.6
bp** manual.

**THE ATTEMPT, AND ITS RESULT, RECORDED.** One attempt was made to find the
automatic-conversion rate in a published IBKR schedule, as instructed:

```
search, restricted to interactivebrokers.com / .co.uk / .ie
  → the 0.03% figure is reported as appearing on IBKR's own pricing pages
fetch https://www.interactivebrokers.co.uk/en/pricing/commissions-spot-currencies.php
  → HTTP 403 Forbidden. The page was NOT retrieved and NOT read.
```

**So the figure was not verified in a published schedule.** The search
restriction means the summary derives from IBKR's own domains rather than a
comparison page, which is better than the corroboration the row previously
carried and **is still not the schedule**. Nobody in this session read the
page. **Provenance: `verified_secondary`. The row's FX term stays OPEN and is
not promoted.** Promoting it would put an unread number into the denominator
of every break-even figure in the paper.

**Cost of choosing wrongly, each way.** Choosing **automatic** when manual is
cheaper costs about 5.4 bp per round trip at the illustrative clip, on half the
book, silently, for ever. Choosing **manual** when automatic is cheaper costs
at most **USD 2.00 per order**, which at a £50,000 clip is **0.31 bp**. **The
error is wildly asymmetric and the asymmetry does not depend on the unverified
0.03%:** manual's downside is bounded by a USD 2.00 minimum and automatic's is
proportional to size.

**Recommendation: manual spot conversion, and it survives the provenance gap.**
Even if the automatic rate is materially lower than 0.03%, it would have to be
below **0.0031%** to beat manual at USD 64,000, which is a tenth of the figure
reported. **The recommendation does not rest on the unverified number, only on
its order of magnitude**, and that is why it can be made whilst the row's FX
term stays open.

---

## 3. §14 governance: θ, the δₘᵢₙ floor, account type — releases **13**

*Releases: binding-path step 3, and the twelve drafts in the ledger, every one
of which is blocked on operator input and none of which is registered.*

### 3a. θ, the pairwise design-segment overlap tolerance

**What it governs.** How much two directives' design segments may overlap
before the second is refused admission. It bounds concurrency against the reuse
ledger.

**The defensible range: 0.0 to 1.0, and the ends are both degenerate.** At
**θ = 0** no two directives may share a single observation, so the segment
admits directives serially and the reuse ledger is a queue. At **θ = 1**
overlap is unbounded, every directive sees the same data, and **the multiple
comparisons §6.4 counts are all on one sample**, which is the condition under
which a funnel-depth association is a story about one draw.

**A narrower defensible band, argued.** The quantity θ protects is the
independence of the evidence behind concurrent directives. **Below about 0.2**
the segment supports very few concurrent directives and the scanner's steady
state becomes a queue on data rather than a queue on the operator, which is a
different bottleneck from the one this design chose. **Above about 0.5** more
than half of any two directives' evidence is shared and calling them separate
tests is a courtesy.

**What each end implies.** Low θ: fewer concurrent directives, cleaner
independence, slower accumulation, and §7.1's funnel-depth association arrives
later. High θ: more directives, faster accumulation, and an association
computed over a population that is substantially one population.

**Cost of choosing wrongly, each way.** **Too low** costs time and nothing
else; the instrument still works, later. **Too high** costs the instrument:
§7.1's headline is the thing §0.6 is armed until, and an association measured
across overlapping segments cannot be distinguished from an artefact of the
overlap. **The errors are not symmetric and the conservative direction is
down.**

**Recommendation: θ = 0.2, with the cost stated.** It is at the low end of the
argued band and it will feel restrictive. **The argument:** the entire design
is built on the position that a null must be believable, and the one parameter
that decides whether §7.1's association is measured on independent evidence
should not be set for throughput at a stage where **zero** directives have ever
been registered. Throughput is not currently the binding constraint; twelve
drafts are queued on four operator inputs, not on segment capacity.

### 3b. The δₘᵢₙ floor

**What it governs.** The minimum registered effect size below which a directive
is not worth a session of the design segment.

**The defensible range, and its two anchors are already in the paper.** The
**lower** anchor is the cheapest break-even in the cost table: an effect below
the cost of trading it is not an effect this system can act on. §0.5 records
**22.5 bps** as the cheapest per-trade break-even at the old £5,000 notional
basis. The **upper** anchor is the smallest documented effect the primary
family actually shows: §0.5 records the insider-purchase five-day figures at
**~230 bps (US)** and **462 / 165 bps (UK)**. **A floor above the effects the
literature documents would refuse the one live family**, so the band is
roughly **22.5 bps to 165 bps**.

***Both anchors are currently unstable and that is stated rather than glossed.***
The lower one moves with §13 row 1, which is PROVISIONAL, and with the §0.11
clip question. **A floor set today is a floor set on a moving denominator.**

**What each end implies.** Near **22.5 bps** almost every documented effect
qualifies and the floor does no work. Near **165 bps** only the strongest
documented effect qualifies and the system tests one hypothesis.

**Cost of choosing wrongly, each way.** **Too low** spends design-segment
sessions on directives that could never clear their own cost table, and the
segment is the scarcest resource in the design. **Too high** refuses real
effects unlearned, which §0.8 already records as the more expensive error for a
laboratory: *"a false negative is unlearned permanently"*.

**Recommendation: defer until §13 row 1 closes, and say so rather than
choosing.** **This is the one §14 decision that should NOT be taken now.** Its
lower anchor is a break-even that row 1 has not fixed; setting the floor first
and the denominator afterwards is the wrong order, and §13's own ordering rule
says row 1 runs first *because every break-even denominator inherits it*.
**Recording "deferred, and here is what it waits on" is a better answer than a
number.**

### 3c. Account type, cash or margin

**What it governs.** Whether the account may borrow. §14 records it as
*"currently non-binding; binds before any short-side family or margin
simulation"*, with the note that **the settlement-bridge cost line arguably
binds it already**.

**On that note, because it is the substance.** A long-only cash account settles
T+2 (UK) or T+1 (US); a sale's proceeds are not available to fund a purchase
until settlement. **With a £50,000 clip against a £100,000 book, at most two
positions fit, so rotating one position into another means waiting for
settlement or borrowing across it.** §0.11 has therefore made this decision
materially more binding than when §14 filed it, and the settlement bridge is no
longer arguable: **at two positions, every rotation crosses it.**

**The defensible range: two, and they are not symmetric.** **Cash** cannot
borrow, cannot short, and pays no financing; every rotation waits for
settlement. **Margin** can bridge settlement, can short later, pays financing,
and **introduces a leverage the §6.7 cap stack was not written against**.

**Cost of choosing wrongly, each way.** **Cash** when margin was needed costs
idle days between rotations, which at a two-position book is a real drag on the
number of observations the design segment ever sees. **Margin** when cash would
do introduces a borrowing facility into a laboratory whose stated purpose is
the ledger and not returns, and **§0.8's error asymmetry was set for a
laboratory, not a fund**.

**Recommendation: cash, and revisit if and only if a short-side family is
admitted.** **The argument:** the book is explicitly a laboratory at zero
expected capital-derived edge (§0.5, §9.6), the grammar is long-only for the
one live family, and a margin facility adds a failure mode that no gate in the
stack refuses on. The settlement drag is a cost in *time*, and time is the one
thing this project has consistently been willing to spend. **If §0.11's clip is
read as a floor and lowered per item 1, the two-position constraint relaxes and
this decision reverts to non-binding**, which is a further reason not to take
it under the pressure §0.11 created.

---

## 4. Pre-calibration fixings — releases **5**

*Releases: binding-path step 2, §13 rows 22 and 25 beyond the US, §0.7(a)'s
partition boundaries, §0.7(b)'s benchmark gap, and the archive the design
segment is cut from.*

**For each: decision or data acquisition, and if data, what it costs and where
it comes from.**

| Fixing | Kind | What it needs |
|---|---|---|
| **Archive identity and span** | **DECISION** | Already partly taken: `archive_opens` is set to **2023-01-01** in the registration and has been since 26 August. What remains is the **closing** boundary and whether the span is the one the design segment is cut from. **No purchase.** |
| **Partition boundaries** | **DECISION**, with a documented search | §0.7(a) requires boundaries at *observable structural breaks in the corpus*, and proportional points **only where a documented search finds none**. *"We looked and found no break" and "we did not look" are different claims*, so the deliverable is the search, not the boundary. **No purchase; it costs reading time over the corpus.** |
| **Universe constituents** | **DATA**, largely acquired | §13 row 25 is CLOSED for the US: **10,388 issuers from the SEC's own file, 100% by construction**, free. **UK, AU, EU and NZ each need a listing file with a known total** and are outstanding. LSE and AIM listing files are published; the others are per-venue. **Cost: nil to low, and it is retrieval rather than purchase.** |
| **Source roster** | **DECISION** | Which sources are in, at which §3.1 regulatory rank. §0.7(g) already fixes the *rule* (regulatory status, not delivery channel); what is missing is the enumerated list. **No purchase.** |
| **Borrow snapshot date** | **DATA**, and **currently not binding** | §0.7(e): a timestamped broker snapshot, erring in both directions with the anti-conservative direction likely dominant. **The insider family is long-only by grammar, so this binds nothing today.** It becomes a real dependency only alongside item 3c's margin question and a short-side family. **Cost: a broker report, free, but it must be taken forward from today rather than reconstructed.** |

**One acquisition that IS a purchase and is not in the list above**, recorded
so it is not mistaken for a fixing: §0.7(d)'s **ICB point-in-time vintage
vendor**. Until procured, peer sets are not point-in-time and every pooled
estimate carries that qualification. **It is a §14 open decision with a price
attached and it is the only one of these that costs money.**

**Recommendation: take the four decisions, retrieve the two free data items,
defer the borrow snapshot and the ICB vendor.** None of the four decisions
waits on anything, and step 2 is the second-cheapest step on the binding path.

---

## 5. §9.4's stopping rule: the threshold and the stated count — releases **1**, and it is step 4

*Releases: binding-path step 4 and §14's trace precondition.*

**This item is here because phase 3 found that step 4 cannot be discharged by
any amount of work.** §9.4 says tracing stops when the marginal defect rate per
hundred items *"falls below a stated threshold for two consecutive blocks"*.
**The specification does not state the threshold and it has no §13 row.** §14's
precondition separately requires *"a stated count of items spanning source
classes and catalyst types"*, and **no count is stated**.

**What each governs.** The threshold decides when tracing is finished. The
count decides how much tracing is enough breadth.

**The defensible range for the threshold.** The unit is **defects per hundred
items**. **Zero** is the review harness's own standard (§9.5 stops at *two
consecutive passes at zero must-class defects*) and is defensible here by
analogy. **Above about 5 per hundred** the rule stops a harness that is still
finding a defect every twenty items, which is not a stopping rule so much as a
budget.

**Cost of choosing wrongly, each way.** **Too low**, and especially zero on
*all* defect classes rather than must-class only, makes the rule unsatisfiable
for a harness whose product is `undecidable` findings: §9.4 says *"`undecidable`
is the harness's product; every instance is a candidate register entry"*, so a
harness working correctly generates findings indefinitely. **Too high** stops
tracing while the instrument is still productive, which is the *"indefinite
improvement cycle wearing a test harness's clothes"* §9.4 warns of, inverted.

**Recommendation: mirror §9.5 and set the threshold at zero MUST-CLASS defects
per hundred items, not zero defects.** The distinction is what makes it
satisfiable, and §9.5 already draws it. **This makes the threshold a rule
change and it takes a §13 row and a §12.1 row when taken.**

**For the count: no recommendation.** It is a breadth judgement over source
classes and catalyst types, and the current corpus covers three non-US classes
and **zero US filings**, so any count stated today would be stated over a span
that does not include the primary family.

---

## 6. The FX exposure budget (§0, OPEN) — releases **1**, and it now governs half the book

*Releases: §6.9's currency treatment.*

**What changed, and it is why this is no longer a small item.** Under §0.11 a
single US position is **50% of the book in USD, unhedged**. At the £2,500 clip
it was 2.5%. **A governance judgement that could be deferred as second-order at
2.5% is a judgement about half the book at 50%**, and the row's status has not
moved whilst what it decides has.

**What it governs.** The share of the book that may sit in a non-base currency,
and whether any of it is hedged.

**The defensible range: 0% to 100%, and §0.11 has already pinned the practical
lower bound above zero.** If a US position is 50% of the book by construction,
**an FX budget below 50% forbids US positions entirely** — which is a coherent
choice and should be recognised as the choice it is, because the primary
catalyst family's best-documented evidence and the entire §9.4 filing flow are
US.

**What each end implies.** A **low** budget (under 50%) makes the system UK-only
in practice, halving the universe and removing the family's own live filing
flow from reach. A **high** budget (at or near 100%) accepts that the book's
value moves with GBP/USD by as much as the position moves with the thesis,
**which means the measurement §7.1 takes is contaminated by a currency the
grammar never mentions**.

**Cost of choosing wrongly, each way.** **Too low** costs the US universe and,
with it, the only live filing flow the trace precondition names. **Too high**
puts an unhedged currency exposure of up to half the book behind every reading,
and **§6.9's currency treatment is not a hedge**, so nothing in the system
removes it.

**Recommendation: none, and this one genuinely turns on item 1.** If §0.11's
clip is a floor and is lowered, a US position is a normal-sized position and
this reverts to an ordinary governance judgement. If it is a position size,
**this decision and item 1 are the same decision wearing two headings**, and
answering them apart risks answering them inconsistently.

---

## 7. Row 21b ratification — releases **1 row, outright. The cheapest item here**

*Releases: §13 row 21b, from PROVISIONAL to CLOSED. It waits on nothing but an
hour's reading.*

**This is the only item on the board that closes a row outright**, needs no
data, no purchase, no prior decision and no further analysis. **It is prepared
as a worksheet, not as a question.**

**The worksheet is `docs/ratification_draw_2026-08-27.md`**, already in the
tree, drawn by the registered seed `20260826` with salt `ratification-draw-v1`,
draw digest `65e688a67fc0054e`. It contains:

- **Twelve of the thirty-six drawn subjects, with the clerk's labels
  WITHHELD**: `sweep-023`, `sweep-035`, `sweep-026`, `sweep-003`, `sweep-036`,
  `sweep-031`, `sweep-018`, `sweep-007`, `sweep-015`, `sweep-013`, `sweep-032`,
  `sweep-019`. Each carries its event class, corpus, event definition,
  measured-on intention and mechanism note, and an empty box for the operator's
  own label and reason.
- **All six authored probes, shown in full**, because they are the object row
  21b is about rather than a sample of it: `plant-01` legal-form designator,
  `plant-02` bare ticker in capitals, `plant-03` title-case bare ticker *(the
  one open route)*, `plant-04` exchange-prefixed identifier below the ticker
  rule's length, `plant-05` ISIN, `plant-06` one-word issuer name equal to its
  own ticker.

**Why the labels are withheld on the twelve, restated because it is the point.**
An operator shown the answer beside the question is being asked to agree rather
than to label, and **agreement obtained that way measures deference and not
accuracy**.

**The stopping condition, registered before any result exists: one
disagreement in twelve refutes the clerk's labels for the whole drawn arm.**
Not *reduces confidence in*. Row 21a compares the fence's verdict against a
clerk label on every one of the thirty-six; if the operator and the clerk part
company on any subject, those labels are not the operator's classifications and
**the arm has no denominator anyone has checked**. Twelve is a third of the
arm, so one disagreement implies about three across it.

**Two questions, and only the second closes row 21b.**

1. **On the twelve** (this is row **21a**'s labels, not 21b's): *is this a
   class-level mechanism, naming no issuer, no instrument and no dated
   episode?*
2. **On the six** (this closes row **21b**): *does each probe exercise the
   route it claims, and are six routes the routes that matter?*

**What it does and does not do.** Ratifying the six **closes row 21b**.
Ratifying the twelve does **not** close row 21a: 21a is blocked on the design
segment, and what the twelve settle is whether its labels are the operator's.
**Coverage does not become a rate by being ratified, and only a drawn
episode-level sample could make it one.**

**Recommendation: do this first, today.** It is the only item that converts an
hour into a closed row, and it is the only one whose cost is bounded and known.

**Then run** `python -m fntn.scanner ratify-reveal`.

---

## 8. §13 row 1's SCOPE — already with the operator, NOT re-opened here

Recorded so the pack is complete. The pending block under §13 row 1 in
`docs/OPEN_ITEMS.md` asks whether *fixed round-trip commission* should become
*fixed round-trip transaction cost*, and whether AIM and the Main Market are
separate tiers. **It is with the operator and this batch was instructed not to
act on it. Nothing here does.**

---

## What this pack recommends doing, in order

1. **Item 7**, the ratification worksheet. An hour, closes a row.
2. **Item 1**, the floor-or-position-size reading. Nine things wait on it and
   several of the other items in this pack change shape once it is answered.
3. **Item 2b**, the contracting entity. One look at a statement, and it gates
   2a and 2c.
4. **Item 4**'s four decisions and two free retrievals.
5. **Item 2c**, the FX route, on the asymmetry argument, whilst leaving the
   row's FX term open.
6. **Items 3a and 3c**, θ and account type.
7. **Item 5**, the stopping-rule threshold.
8. **Deferred on purpose: item 3b** (δₘᵢₙ waits on row 1), **item 6** (the FX
   budget waits on item 1), **item 2a** (waits on the cited schedule).
