# USD through the cost model, and what it moves

**27 August 2026. Phase 1 of the eleven-phase batch.** §0 decision 0b: the
account is USD-denominated, so **there is no per-trade FX conversion**.

---

## 1a. The recomputation, and one thing it does NOT touch

***§13 row 1 is unaffected and stays CLOSED, and the reason is worth stating.***
Row 1 closed on **option A's terms, as a COMMISSION row**. **FX was never inside
its scope.** So removing per-trade FX changes **row 30's absolute input**, not
row 1's contents, and **row 1's citation, its schedule and its closure all
stand.**

*That is a consistency check on the scope decision rather than a convenience: if
row 1 had been closed on option B or C, this decision would have reopened it.*

### The model, no per-trade FX, US equities, fixed pricing

```
commission        2 x max(USD 1.00, 0.0050 x N)      max 1% of trade value
FINRA CAT         2 x 0.000003 x N
FINRA TAF         0.000195 x N                       (sell leg)
SEC fee           0.0000206 x V                      (sale value)
exchange / clearing / pass-through   ABSORBED by fixed pricing
FX                                   NONE, per 0b
```

**In basis points, two regimes and one kink at `V = 200p`:**

| Regime | Condition | Cost in bp |
|---|---|---|
| Commission minimum binds | `V ≤ 200p` | **`20,000/V + 2.01/p + 0.206`** |
| Rate binds | `V ≥ 200p` | **`102.01/p + 0.206`**, and it is **FLAT** |

**Against the superseded model, the change is confined to the absolute term:**

| | With FX | **Without FX** |
|---|---|---|
| Absolute, round trip | USD 6.00 | **USD 2.00** |
| Minimum regime | `60,000/V + 2.01/p + 0.206` | **`20,000/V + 2.01/p + 0.206`** |
| Rate regime | `40,000/V + 102.01/p + 0.206` | **`102.01/p + 0.206`** |
| Asymptote | `102.01/p + 0.206` | **unchanged** |

***The asymptote does not move, and that matters in 1c.*** The FX was an
**absolute** charge, which decays with size; the asymptote is the
**proportional** part, which does not. **Removing a decaying term cannot move a
limit that is reached as the term vanishes.**

**Recorded as a `§12.1` rule change: an input-source choice moved**, which rule
5 counts as a specification version.

---

## 1b. Row 30's floors, and row 29's universe

**Floors at the registered 10 bp:**

| Share price | Asymptote | Floor **with** FX | **Floor without FX** |
|---|---|---|---|
| USD 10.42 | 9.996 bp | USD 9,586,017 | **USD 2,083** |
| USD 11.00 | 9.480 bp | USD 76,869 | **USD 2,081** |
| USD 13.00 | 8.053 bp | USD 20,544 | **USD 2,075** |
| USD 15.00 | 7.007 bp | USD 13,363 | **USD 2,070** |
| USD 20.00 | 5.307 bp | USD 8,522 | **USD 2,063** |
| USD 43.79 | 2.536 bp | USD 6,155 | **USD 2,052** |
| USD 150.00 | 0.886 bp | USD 6,135 | **USD 2,045** |

***The floor collapses to a near-constant USD 2,045 to 2,083 across the entire
admissible price range — a spread of 1.9%.*** It fell by two thirds at the
calibration price and by three orders of magnitude at the bottom.

**The minimum share price is UNCHANGED at USD 10.42**, because it is set by the
asymptote and the asymptote did not move.

***And the second screen from P118 is GONE.*** That screen was: below USD 13.20
a share the floor exceeded §6.7's largest position. **At a floor of ~USD 2,080
that cannot happen at any admissible price.** **One screen again, and it is the
cost asymptote.**

### Does the floor still bite inside §6.7's sizing range? **Essentially NO.**

§6.7 sizes `GBP 750 / stop`, from **GBP 1,875** at a 40% stop to **GBP 15,000**
at a 5% stop.

| Position | Cost, no FX, at USD 43.79 |
|---|---|
| GBP 1,875 = USD 2,419 *(40% stop)* | **8.52 bp** |
| GBP 3,000 = USD 3,870 | 5.42 bp |
| GBP 7,500 = USD 9,675 | 2.54 bp |
| GBP 15,000 = USD 19,350 *(5% stop)* | 2.54 bp |

**Every position §6.7 will size costs at most 8.52 bp, which is below the 10 bp
tolerance.** **So the floor refuses nothing §6.7 produces.**

> ***Stated plainly, as instructed: fixed cost no longer constrains position
> size. The binding constraints are now spread, market impact and the edge.***

*Three of those have no register row carrying a measurement: §13 row 14 would
measure spreads, market impact has never had a column, and the edge is what §7.1
exists to find.* **Removing the constraint that was measurable leaves the three
that are not.**

---

## 1c. Row 29 re-derived. ***AND NOT TAKEN. The Class I invariant stops it.***

**The instruction's premise, checked rather than accepted.** It reads: *"2.375
was the physical floor WITH FX included. Without FX that lower bound moves."*

***It does not move.*** 2.375 was `104/p` at the calibration price — commission
plus clearing, **both per-share and both proportional.** The FX was **USD 4.00
absolute**. **Removing an absolute term cannot move a proportional asymptote.**
Measured, the lower bound is **2.536 bp**, and it is 2.536 before and after 0b.

### What DOES move, and it is the upper bound

***The upper bound has quietly become circular, and P111 is what made it so.***

Row 29's ceiling of 12.5 bp came from §5.2.2's cheapest break-even of 22.5 bp,
*"computed at a £6.25 round trip on £5,000 notional, that is a 12.5 bp fixed
cost."* **P111 then recomputed §5.2.2 against row 29's own 10 bp bound.**

**So the table's fixed-cost basis IS the tolerance now, and a ceiling derived
from that table can no longer constrain the tolerance.** *The independence that
made 12.5 bp a derivation is gone, and it was this project that removed it.*

### The replacement, derived from something that did not move

**The tolerance's job is to place the clip floor.** The coherent place is where
**the floor equals the smallest position §6.7 will size**: below that the floor
refuses positions the sizing rules themselves produce, and above it the floor
binds on nothing.

*That is the same argument that settled δₘᵢₙ's column at P117 — a governance
threshold must not refuse what the funnel admits.*

```
t*  =  20,000 / V_min  +  2.01/p  +  0.206        where V_min is §6.7's smallest position
```

| Reading of reference equity | `V_min` | **`t*`** |
|---|---|---|
| **GBP 100,000**, converted at 1.29 | USD 2,419 | **8.5 bp** *(8.49 to 8.61 across the price range)* |
| **USD 100,000** | USD 1,875 | **10.9 bp** |

### ***And here the recommendation stops.***

***0b makes the account USD-denominated and does NOT restate reference equity,
which §0.11 confirmed at GBP 100,000.*** **The two readings give 8.5 bp and
10.9 bp, and the registered 10 bp lies between them.**

**The Class I invariant binds: a decision may not be taken over a caveat its own
preparation states.** *This preparation states one.* **Row 29 is NOT re-taken.**

**What is recorded instead, and it is a usable answer rather than a shrug:**

- **The current 10 bp is inside the bracket** the two readings produce, so
  **leaving it is defensible under either**, and nothing downstream is wrong
  today.
- **The operator's one word settles it.** *Reference equity in GBP → 8.5 bp.
  Reference equity in USD → 10.9 bp.*
- **The change is small either way**, ±1.5 bp against 10, and the direction
  differs by reading, **so there is no conservative default to fall back on**.

***The instruction anticipated an unearned margin of the kind δₘᵢₙ carried. The
comparison does not hold, and the reason is worth recording.*** δₘᵢₙ's 8 bp of
margin was slack against a **boundary** it was supposed to equal. **Row 29's
apparent slack is against the cost at a TYPICAL position (2.5 bp), and the
tolerance's job is not to describe a typical position: it is to place a
boundary.** *Measured at the boundary, the cost is 8.5 to 10.9 bp and the
tolerance is 10. There is little margin, earned or otherwise.*

---

## 1d. The δₘᵢₙ floor. **UNCHANGED at 17.0 bp, because row 29 did not move.**

```
delta_min  =  cheapest midpoint spread  +  row 29's bound
           =  7.0 bp                    +  10.0 bp     =  17.0 bp
```

***The direction, stated explicitly because a lower floor ADMITS MORE.*** If row
29 is later set at **8.5**, δₘᵢₙ falls to **15.5**, which **admits mechanisms
with smaller effects that are refused today** — a **loosening**. If row 29 is set
at **10.9**, δₘᵢₙ rises to **17.9**, a **tightening**.

**Neither is taken, for the same reason row 29 is not.**

---

## 1e. Steps 1 and 3 remain CLOSED

| Step | Cells | State |
|---|---|---|
| **1** | §13 row 1: **CLOSED** | **unchanged**, FX never being in row 1's option-A scope |
| **3** | θ CLOSED, δₘᵢₙ floor CLOSED, account type CLOSED | **unchanged**, δₘᵢₙ not having moved |

**Neither re-opens.** *Had row 1 been closed on option B or C, 0b would have
reopened it and this batch would have stopped here.*
