# §5.2.2 recomputed against a measured cost, and the sweep for others

**27 August 2026. Phase 4 of the delegated-authority batch.**

§5.2.2's break-even table was computed on **an assumed £6.25 round trip on
£5,000 notional**, that is a **12.5 bp** fixed-cost basis. §0.7(c) says so in
terms: *"the assumed £6.25 round trip was recovered backwards from the clip
definition."* **Row 1 now measures the cost and row 29 bounds it.**

---

## 4a. The recomputation

**The decomposition first, because everything rests on it.** §5.2.2's figure is
**spread plus fixed cost**, and §0.10 confirms the arithmetic independently: a
200 bp spread there gives a 225 bp break-even at a 25 bp fixed cost. Subtracting
12.5 bp from each published cell recovers the spread assumption behind it.

**The replacement is not another assumption. It is a BOUND, and it needs neither
a share price nor an FX rate.** Row 29 registers 10 bp as the maximum tolerable
fixed cost, and §13 row 30 defines the clip floor as the size at which cost
*equals* it. **So every admissible position has a fixed cost of at most 10 bp by
construction.** Each figure below is therefore an **upper bound** where the
published one was an estimate.

| ADV bucket | Implied spread *(cons. / mid.)* | Published *(12.5 bp assumed)* | **Recomputed, ≤ *(10 bp bounded)*** |
|---|---|---|---|
| > $1bn | 10.0 / 7.0 | 22.5 / 19.5 | **20.0 / 17.0** |
| $100m–$1bn | 30.0 / 20.0 | 42.5 / 32.5 | **40.0 / 30.0** |
| $10–100m | 100.0 / 70.0 | 112.5 / 82.5 | **110.0 / 80.0** |
| $1–10m | 300.0 / 200.0 | 312.5 / 212.5 | **310.0 / 210.0** |
| **< $1m** | not measured | pending §13 row 14 | **pending; the tier is now REACHABLE** |

**Every figure falls by exactly 2.5 bp**, the difference between the assumed
12.5 and the bounded 10.

**A cross-check that was not arranged.** Evaluating row 1's model directly at
£5,000 notional, at the calibration share price of USD 43.79, gives **9.39 bp**:
`60,000/6,450 + 4/43.79`, in the commission-minimum regime. That is below the
10 bp bound, as it must be, and it means the true break-evens are **slightly
below** the bounds published above. *The bound is used and the point estimate is
not, because the bound needs no share price and the estimate needs one.*

**The UK column is not recomputed. It is struck.** At the registered tolerance
UK Main Market carries `clip_floor_unreachable_at_any_size`, and unlike the AIM
Annex A.1 row it does not become live at 12.5 bp either: UK Main needs a
tolerance above **61.4 bp**, far outside row 29's derived range. **A break-even
for a venue no position can reach is a number describing nothing**, and the
column is retained with that stated rather than deleted.

## 4b. Do the conclusions change? **NO, and the check is recorded as run.**

*A check run and passed is a different record from a check not run, which is why
this section exists at all rather than being silence.*

| Conclusion | Rested on | Survives? |
|---|---|---|
| Gate 1's ceiling and Gate 7's gate read the **midpoint**, the conservative figure travelling as an advisory flag | the two columns, not their values | **Yes**, untouched |
| The **δₘᵢₙ floor of 25 bps** is justified because *"the cheapest break-even in §5.2.2 is 22.5 bps, so an effect below that could never be traded in any cell"* | 22.5 | **Yes.** The cheapest is now **20.0**, and 25 > 20.0, so the floor remains sufficient. **It is now more conservative than it needs to be, by 5 bp rather than 2.5** |
| The sub-$1m row cannot be evaluated | §13 row 14 | **Yes**, and row 14's *reachability* question is now answered |
| Ordering of the buckets | the spreads | **Yes.** A uniform 2.5 bp shift changes no ordering |

**One stale NUMBER inside a surviving argument, corrected.** The registration's
`rationale` names 22.5 as the cheapest break-even. It is now 20.0. **The
argument for `delta_min_floor` = 25 is unaffected and the value does not move.**
*Correcting the rationale moves no hash*: `Registration.hash` pops `rationale`
before hashing, because it is prose and not a parameter. **So this correction
costs no re-stamp, and that is the design working rather than a loophole.**

**A rule change all the same, and it takes a `§12.1` row.** Rule 5 counts a
change to **a grid** as a specification version, and §5.2.2's table is a grid
that Gate 1's ceiling and Gate 7's gate read. **The values moved, so the row is
taken even though no conclusion did.**

## 4c. The sweep: what else was computed against a superseded cost assumption

**Five sites, and one of them is not in the manuscript at all.**

| # | Site | The assumption | Status |
|---|---|---|---|
| 1 | **§5.2.2**, the break-even table | £6.25 round trip on £5,000 = **12.5 bp** | **Recomputed above** |
| 2 | **§0.5, line 114**, which quotes §5.2.2's figures in prose: *"22.5/19.5 bps in the most liquid AIM or US bucket, 312.5/212.5 in the least"* | the same 12.5 bp, at one remove | **Recomputed**, and it inherits the AIM correction too: **AIM is not in that bucket at 10 bp** |
| 3 | **§0.10**, the microcap break-even table | **25 bp**, the fixed cost at the withdrawn £2,500 clip | **Recomputable at last.** 200/400/600 bp spreads give **≤ 210 / 410 / 610** against the published 225 / 425 / 625. *The conclusion is unmoved and was never close: against 115 bp after the 50% post-publication rung, every row still fails* |
| 4 | **§0.7(c)**, the three-row clip table | £3.13, £5.00, £7.50 per side | **Superseded as a derivation** since P97, annotated at P110, and **deliberately not re-tabulated**: its left column is a sterling per-side commission and the derived floor is a function of row 1's US schedule and a share price |
| 5 | **`discovery_registration.json`'s `rationale`** | 22.5 as the cheapest break-even | **Corrected. Outside the hashed payload, so no re-stamp** |

**Erratum B is discharged by this phase and is recorded as discharged.** It
existed because §0.10's table was computed on a £2,500 clip and §5.2.2's on
£5,000 notional, so *"the two sets of figures are not comparable line for
line"*. **Both are now bounded by the same 10 bp**, which is a property of the
*tolerance* and not of a notional, **so the two tables are comparable for the
first time.** *That is the quiet dividend of making the tolerance explicit: a
dimensionless bound is comparable where a per-notional assumption is not.*

**What the sweep did NOT find, stated so the negative is on the record.** No
gate threshold, no sizing rule and no admissibility rule was computed against
the £6.25 assumption. It reached exactly the two break-even tables, one prose
quotation of one of them, one superseded derivation table, and one line of
registration prose.
