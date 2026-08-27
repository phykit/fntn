# Prepared decision: §13 row 29, the maximum tolerable fixed cost

***TAKEN 27 August 2026, ON DELEGATED AUTHORITY: row 29 is SET AT 10 BASIS
POINTS.*** Registered as `max_tolerable_fixed_cost_bps` = 10.0; the object
re-stamped to row 6 of `docs/REGISTRATION_HISTORY.md`. §13 row 29 reads
**CLOSED**. **The operator's standing right to revise is unaffected**, and §8.5
below states the one word that revises it and exactly what it buys.

**The file below is the preparation, kept as the record of what was decided and
on what grounds.** §8, added after the decision, states the consequences.

---

## 8. WHAT 10 BP COSTS. Read this before the preparation

### 8.1 It is a US-only decision, and it should be called that

**At 10 bp the book is US-only.** Not *mostly*, not *initially*: **both UK
venues are excluded, and neither exclusion can be lifted by anything currently
on the register.**

### 8.2 UK Main Market: EXCLUDED, with certainty

Stamp duty is **50 bp** of consideration on the buy leg. It is statutory, it is
a percentage, **it does not decay at any size**, and it is independent of every
one of §13 row 1's open gaps. Row 1's UK tiered round trip reads **61.4 bp**.
**No citation row 1 is waiting on can move it below 10.**

### 8.3 UK AIM: EXCLUDED at about 10.3 bp, and NOT because of stamp duty

***This is the finding that matters, and it is derived rather than asserted.***

**IBKR's UK commission is 0.05% each side.** That is a **percentage**, so it is
proportional and does not decay:

```
0.0005 x 10,000 =  5 bp a side
                = 10 bp round trip, on commission alone
plus the PTM levy, GBP 1 over GBP 10,000 of consideration
                =  0.20 bp at GBP 50,000
                = 10.20 bp, before exchange fees
```

**`sizing.py` fires `clip_floor_unreachable_at_any_size` where the proportional
share MEETS OR EXCEEDS the tolerance.** At 10 bp, **commission alone reaches it
exactly**, so AIM is unreachable **on the most generous possible reading of its
cost**, before a single levy or fee is added.

***Therefore the deferred AIM growth-market tier CANNOT RESCUE THE UK.*** That
tier is a **stamp-duty** exemption. It addresses a **50 bp tax**. **AIM's
binding cost at a 10 bp tolerance is the 10.3 bp of commission that the
exemption does not touch.** *AIM fails on commission, not on tax.*

**One discrepancy, recorded rather than smoothed.** Row 1's UK readings imply an
AIM residual of **11.4 bp** (61.4 minus 50 bp stamp), whilst the bottom-up build
gives **10.20 bp** before exchange fees. The gap is about 1.2 bp and it is not
reconciled here: row 1's UK working is PROVISIONAL and no published schedule has
been read. **The conclusion is unaffected**, both readings exceeding 10 bp, and
**the qualitative claim is robust because it rests on the 0.05% rate alone**.

### 8.4 US: reachable above about USD 10.40 a share

`104/p < 10` requires `p > 10.40` on fixed pricing, `74/p < 10` requires
`p > 7.40` on tiered. **The clip floor rises steeply as price falls toward that
bound**, because the floor is `40,000 / (10 - 104/p)` in the rate regime.

| Share price | Hard floor, `104/p` | Clip floor at 10 bp, fixed |
|---|---|---|
| USD 10.40 | 10.00 bp | **none at any size** |
| USD 11.00 | 9.45 bp | USD 73,333 |
| USD 12.00 | 8.67 bp | USD 30,000 |
| USD 15.00 | 6.93 bp | USD 13,043 |
| USD 20.00 | 5.20 bp | USD 8,333 |
| USD 30.00 | 3.47 bp | USD 6,122 |
| USD 43.79 *(calibration)* | 2.375 bp | **USD 6,055** |
| USD 75.00 | 1.39 bp | USD 6,032 |
| USD 150.00 | 0.69 bp | USD 6,016 |

**The floor is nearly flat above about USD 30 and blows up below about USD 12.**
*The practical screen is not the USD 10.40 bound but the region above it where
the floor is affordable.* At a £100,000 book, §6.7 sizes between **£1,875 and
£15,000**, roughly **USD 2,400 to USD 19,300**: the floor fits inside that band
from about **USD 15 upward** and leaves it below about USD 13.

*Every figure recomputed from the model rather than carried from the earlier
draft; four of the five rows moved, the largest by 900 USD at USD 15 a share,
because the rate regime binds at these prices and a hand calculation had used
the minimum-regime branch.*

### 8.5 THE REVISION THAT IS AVAILABLE IN ONE WORD

***12.5 bp, the derived upper bound, is the value at which AIM becomes
reachable.*** At 12.5 bp AIM's ~10.3 bp proportional cost sits below the
tolerance and a floor exists; at 10 bp it does not.

**So the choice between 10 and 12.5 is the choice of whether the UK exists in
this strategy.** It is not a choice about precision or conservatism.

**10 was taken because it sits INSIDE the derived range rather than at its
edge.** 12.5 is the point at which a trade's fixed cost alone equals the
fixed-cost basis §5.2.2's cheapest break-even was computed on, and a parameter
set at the exact edge of its own coherence bound has no margin for row 1's three
open gaps, every one of which pushes cost **up**.

**The operator can revise to 12.5 in one word and the consequence is exactly the
UK.** Nothing else in the cascade changes sign.

---

## The preparation, as it stood

**27 August 2026. Phase 2 of the resumed batch.**

**Row 29 releases TEN things.** It is the largest single release left on the
board, it is the only genuinely free parameter in the clip-floor derivation, and
**this file does not set it.**

Row 29 is a tolerance in basis points of position, round trip, **excluding
spread and market impact**, neither of which has a row and both of which scale
with participation.

---

## 1. What row 29 releases. Ten, counted and listed

| # | What | Route | Blocked on anything else? |
|---|---|---|---|
| 1 | **§13 row 30**, the derived clip floor per market | direct: row 30 *is* `absolute ÷ ((tolerance − proportional) ÷ 10,000)` | row 1's PROVISIONAL status |
| 2 | **§4.4's three ATR bounds** at full size, and their multiplier-floor halves | direct: the bounds were computed against a clip floor and the floor is the output of row 29 | row 1 |
| 3 | **§4.4's reachability matrix zero cells.** `position_below_clip_floor` (renamed from `capital_exceeds_clip_floor` by P108) acquires a threshold to test against and the zero cells can be located | direct | row 1 |
| 4 | **§5.4.4's admissibility × reachability intersection** | inherited from §4.4 entire; the table has no independent content | nothing further |
| 5 | **§0.7(c)'s two withdrawn right-hand columns**, max ATR at h=63 and h=5 | direct, by arithmetic | row 1 |
| 6 | **§0.10's microcap break-even table**, which is invalidated and today cannot even be recomputed, there being no clip to recompute it at | direct | row 1; the impact column it has never had |
| 7 | **§13 row 8**, the break-even ceiling's fixed-cost input | inherited | row 1; the design segment |
| 8 | **§13 row 9**, the Gate 1 price floor | inherited through row 8 | row 8 |
| 9 | **§13 row 14**, whether the sub-$1m cost tier is reachable at all | inherited | design segment; shadow-cohort names |
| 10 | **`sizing.py` stops refusing.** `clip_floor_tolerance_unset` clears, the book can hold a position, and **§5.1's explore arm acquires a size**, the arm having none while the floor is undetermined | code | row 1 |

**Six are specification sections restored by arithmetic, three are §13 rows,
one is code.** A stricter count that merges rows 2 and 3, the ATR bounds and the
zero cells being one operation, gives nine; the count is shown so it can be
audited rather than asserted.

***One correction to the brief this file was written against.*** The brief lists
"§4.4's constants" among what row 29 releases. **They are not blocked on it.**
P100 withdrew 7.5% and 3.75% *as constants* and derived them from §6.7's base
unit and cap stack, so they are already restored. What §4.4 still waits on is
the **ATR bounds** and the **zero cells**, which is what rows 2 and 3 name.

---

## 2. The cost model this is computed on, and where it comes from

Row 1's US model was reconciled to **one** model on 27 August 2026 (P101). The
form, with `V` the trade value and `p` the share price:

```
round trip  =  USD 4.00                       fixed, both legs, from row 1's stated USD 6.00
             + 2 x max(USD 1.00, rate x V/p)  commission; rate = 0.0050 fixed, 0.0035 tiered
             + 2 x 0.0002 x V/p               NSCC/DTC clearing
```

Row 1 states a **USD 6.00** round trip. Under this model that figure is not an
input to be replaced: **it is the minimum-regime total**, USD 4.00 of fixed
charges plus USD 2.00 of commission minimum, and the only free parameter is `p`.

**In basis points the model has two regimes and one kink:**

| Regime | Condition | Cost in bp |
|---|---|---|
| Commission **minimum** binds | `V ≤ 200p` fixed, `V ≤ 285.7p` tiered | `60,000/V + 4/p` |
| Commission **rate** binds | above that | `40,000/V + 104/p` fixed, `40,000/V + 74/p` tiered |

Cost is continuous, decreasing in `V`, and **asymptotic to `104/p` bp (fixed) or
`74/p` (tiered)**. That asymptote is the hard floor: no size reaches below it.

**An internal check that was not arranged.** At the calibration price the model
puts the 3 bp clip floor at **USD 63,997**, and row 1's own reading is 3.00 bp at
**USD 64,000**. The floor column reproduces the row it was derived from.

***Two figures inherited and not verified in this tree:*** the USD 1.00
per-order commission minimum, used for both schedules, and the USD 4.00 of other
fixed charges. Both come from row 1's working, which is PROVISIONAL. **FINRA's
trading activity fee and the SEC fee are omitted**, were not read from a
published schedule, and both push every floor and every minimum share price
**up**, so every figure below is a **lower bound**.

---

## 3. The UK, and it is two claims of different strength

**Row 1's UK tiered readings are flat**: ~61.4 bp at £2,500 and ~61.5 bp at
£50,000. UK cost is dominated by percentage terms, so **it does not decay with
size and a clip floor is a US concept that does not transfer.**

- **Any tolerance below ~61.4 bp excludes UK Main Market, PROVISIONALLY.** The
  reading is row 1's arithmetic and not a cited schedule, and row 1's three gaps
  are open.
- **Any tolerance below 50 bp excludes UK Main Market WITH CERTAINTY.** Stamp
  duty alone is 50 bp of consideration on the buy leg. It is statutory, it is a
  percentage, it does not decay, and it is independent of every one of row 1's
  three gaps. **No citation row 1 is waiting on can move it.**

**The consequence is decisive and is stated here rather than buried in the
table.** §5.2.2's cheapest published break-even is **22.5 bp conservative /
19.5 bp midpoint**, and that figure is spread *plus* fixed cost. A tolerance
that admits UK Main Market must therefore exceed 61.4 bp, which is **more than
twice the entire break-even of the most liquid bucket**. **There is no tolerance
that admits UK Main Market and is coherent with §5.2.2.**

### AIM, and the answer depends on a contradiction this file found

**AIM's answer is not one column, because the paper contains two incompatible
statements about it, and both are load-bearing here.**

| Reading | Source | AIM round-trip cost | Where it puts AIM |
|---|---|---|---|
| **A. The exemption applies** | §0.5 line 114, §0.10's table and **§5.2.2's own column heading**, all of which price AIM with no stamp | **~11.4 bp**, flat, PROVISIONAL | in at any tolerance ≥ ~11.4 bp |
| **B. The exemption is deferred** | **P92**, which defers the AIM growth-market tier as apparatus under §0.6 and states that *"neither is applied to any figure in this paper"* | **~61.4 bp**, as UK Main Market | out at every coherent tolerance |

**P92's sentence is false as written.** The exemption is applied to figures in
three places in the manuscript. It is registered in `docs/CORRECTIONS.md` and as
a pending block in `docs/OPEN_ITEMS.md`, and **it is not resolved here**: which
reading is correct is an operator decision, because reading A is a cost tier that
makes a subset of names cheaper, which is exactly what §0.6's test catches.

*Why this is not academic.* The **only** window in which AIM's answer differs
from UK Main Market's is a tolerance between ~11.4 bp and the coherence ceiling
derived below, **11.4 to 12.5 bp**. Inside that window the contradiction decides
whether the UK sleeve exists at all. Outside it, AIM is out either way.

---

## 4. The single universe table

Tolerance down the side. **Minimum share price** is the price below which the
hard floor `104/p` or `74/p` exceeds the tolerance, so **no position size gets a
name**. **Clip floor** is the smallest position at which the cost falls to the
tolerance, computed at the calibration prices USD 43.79 (fixed) and USD 31.16
(tiered), and it is a function of the candidate's own price in general.

| Tolerance | US min share price, **fixed** | US min share price, **tiered** | US clip floor, fixed | US clip floor, tiered | UK Main Market | AIM (A: exempt) | AIM (B: P92) |
|---|---|---|---|---|---|---|---|
| **2 bp** | USD 52.00 | USD 37.00 | **none at any size** | **none at any size** | out, certain | out | out |
| **2.5 bp** | USD 41.60 | USD 29.60 | USD 319,927 | USD 319,590 | out, certain | out | out |
| **3 bp** | USD 34.67 | USD 24.67 | USD 63,997 | USD 63,984 | out, certain | out | out |
| **4 bp** | USD 26.00 | USD 18.50 | USD 24,615 | USD 24,613 | out, certain | out | out |
| **5 bp** | USD 20.80 | USD 14.80 | USD 15,238 | USD 15,237 | out, certain | out | out |
| **6 bp** | USD 17.33 | USD 12.33 | USD 11,034 | USD 11,034 | out, certain | out | out |
| **8 bp** | USD 13.00 | USD 9.25 | USD 7,587 | USD 7,622 | out, certain | out | out |
| **10 bp** | USD 10.40 | USD 7.40 | USD 6,055 | USD 6,078 | out, certain | out | out |
| **11.4 bp** | USD 9.12 | USD 6.49 | USD 5,306 | USD 5,323 | out, certain | **in** | out |
| **12.5 bp** *(coherence ceiling)* | USD 8.32 | USD 5.92 | USD 4,835 | USD 4,850 | out, certain | **in** | out |
| **15 bp** | USD 6.93 | USD 4.93 | USD 4,025 | USD 4,035 | out, certain | in | out |
| **20 bp** | USD 5.20 | USD 3.70 | USD 3,014 | USD 3,019 | out, certain | in | out |
| **25 bp** *(the withdrawn implicit rule)* | USD 4.16 | USD 2.96 | USD 2,409 | USD 2,412 | out, certain | in | out |
| **50 bp** | USD 2.08 | USD 1.48 | USD 1,202 | USD 1,203 | out, certain | in | out |
| **61.5 bp** | USD 1.69 | USD 1.20 | USD 977 | USD 978 | **in**, provisional | in | in |

**What the table says in one sentence.** At every tolerance that is coherent
with §5.2.2, **the book is US-only**, unless AIM reading A holds and the
tolerance sits in the 11.4 to 12.5 bp window.

*`CLAUDE.md` describes the universe as "long-only UK Main Market / AIM and US
equities". Writing the tolerance down collapses it to US-only across most of the
defensible range. That is a consequence of the derived floor, and it is reported
as one rather than smoothed.*

**A correction to §13 row 30, found by this arithmetic.** Row 30 records "at USD
6.00 round trip a 10 bp tolerance implies USD 6,000, a 5 bp tolerance USD
12,000". The 10 bp figure survives (USD 6,055). **The 5 bp figure does not:** the
correct floor is **USD 15,238**, because at 5 bp the commission *rate* regime
binds and row 30's model had no rate term. Row 30's number is **too low by 27%**,
in the direction that flatters the floor.

---

## 5. The defensible range, and both ends are DERIVED

**Lower end: 2.375 bp.** Below `104/p` bp no position size of any kind reaches
the tolerance. At the calibration price that is **2.375 bp**, and it is the same
number on both schedules because both were solved against the same reading. Any
tolerance at or below it makes `clip_floor_unreachable_at_any_size` the universal
verdict for the US, and the accepted book is empty by arithmetic.

**Upper end: 12.5 bp, and this is the finding.** §5.2.2's break-even is spread
plus fixed cost, and §0.10's table confirms the decomposition (a 200 bp spread
gives a 225 bp break-even at a 25 bp fixed cost). The cheapest published
break-even, **22.5 bp conservative** at £5,000 notional, was computed at a
**£6.25 round trip = 12.5 bp** fixed cost, leaving 10 bp of spread. **A tolerance
above 12.5 bp therefore permits a trade whose fixed cost alone exceeds the fixed
cost that Gate 1's own ceiling was calibrated on.**

***So the withdrawn implicit rule was never coherent.*** The clip was *defined
as* the notional at which fixed costs fall below **25 bp**. That is **double** the
12.5 bp embedded in the break-even table it feeds. The incoherence was invisible
for fourteen versions because the tolerance was implicit; **writing it down is
what exposed it**, and that is the case for row 29 existing at all.

**Defensible range: 2.4 bp to 12.5 bp.** Both ends are arithmetic over published
tables. The choice inside it is governance.

---

## 6. Row 29 cannot be derived, and this names what would derive it

**Row 29 is a ratio question wearing an absolute number's clothes:** how much
fixed cost is tolerable *relative to the edge that remains after everything
else*. Deriving it needs two measurements, and **neither exists**:

1. **The post-decay realised net effect per family, measured on the design
   segment.** That is §7.1's funnel-depth association. It has never run. Zero
   backtests, zero frozen designs.
2. **Measured effective spreads by ADV bucket**, which is §13 row 14's input and
   is BLOCKED on the design segment and the shadow-cohort names.

With both, row 29 falls out: the tolerance is what remains under the break-even
ceiling once the measured spread is subtracted from the measured post-decay
effect, and nothing is left to choose. **Without them there is no measurement to
derive it from, and the alternative is prohibited**: fitting the tolerance on the
archive would be a restriction parameter fitted on the archive, which is a fitted
parameter wearing a restriction's clothes.

**What is derivable today, and has been derived above, is the RANGE, not the
value.** That is the honest boundary between the two.

---

## 7. Recommendation, which is a recommendation and not a setting

**Recommended: 10 bp, fixed schedule assumed pending row 1's election.**

**The argument.**
- It sits inside the derived range with headroom below the 12.5 bp coherence
  ceiling, so Gate 1's ceiling stays calibrated on a trade at least as cheap as
  the one the floor permits.
- The clip floor is **USD 6,055**, roughly £4,500, about **4.5% of a £100,000
  book**. That is sizable under §6.7 and inside §4.4's regime cap, and it is
  small enough that §6.7's 2% participation cap is clearable by a wide US
  universe.
- The minimum share price is **USD 10.40 fixed / USD 7.40 tiered**, which
  retains essentially the whole liquid US universe and excludes only the sub-ten
  dollar tail, where the exclusion is a *derived* fact rather than a preference.

**The cost of 10 bp, stated rather than the benefit.** It puts **AIM out under
both readings**, by 1.4 bp. The UK sleeve disappears entirely, and the project
becomes a US-only book at a stroke. **A tolerance of 12 bp would keep AIM in
under reading A** at a clip floor of USD 5,038 and a minimum share price of USD
8.67, and is still inside the coherent range. *If the UK sleeve matters, 12 bp is
the defensible choice and the AIM contradiction must be settled first; if it does
not, 10 bp is cleaner and the 1.4 bp is not worth an argument about a statute
nobody in this tree has read.*

**What is NOT recommended, and why each is named.** **2 bp** is unreachable at
any size for any US name under USD 52.00 and produces an empty book by
arithmetic, which looks like the project's own failure mode and would be
mistaken for one. **25 bp**, the withdrawn implicit rule, is incoherent with
§5.2.2 by a factor of two, and reinstating it would restore the defect that
writing the tolerance down uncovered.

**Row 29 stays OPEN. Nothing here sets it.**
