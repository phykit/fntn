# The tiered election, measured. **IT REVERSES TO FIXED.**

**27 August 2026. Phase 2 of the nine-phase batch.**

P101 fitted **both** schedules to the **same two readings**, giving each the same
fixed component and the same per-order minimum, so *"tiered is 28.8% cheaper"*
was **`74/104` restated**. **This phase stops fitting.** Every figure below is
read from a published IBKR page, listed with URL and digest in
`docs/IBKR_SCHEDULE_2026-08-27.md`.

---

## 2a. The asymmetry, read rather than assumed

**The stocks page states it in one table row, and it is the whole question:**

| Third Party Fees | **Tiered** | **Fixed** |
|---|---|---|
| | Regulatory Fees, **Exchange Fees**, **Clearing Fees**, **Pass-Through Fees** | Regulatory Fees **only** |

***Fixed absorbs exchange fees, NSCC/DTC clearing and pass-through fees. Tiered
passes all three through.*** **P101's model gave BOTH schedules the 0.0002 per
share NSCC/DTC clearing term. That was wrong for fixed**, which absorbs it.

**The components, as published:**

| Charge | Rate | Tiered | Fixed |
|---|---|---|---|
| Commission | tiered USD 0.0035/share min **USD 0.35**; fixed USD 0.0050/share min **USD 1.00** | ✓ | ✓ |
| SEC transaction fee | USD 0.0000206 × value of sales | passed | passed |
| FINRA trading activity fee | USD 0.000195 × quantity sold | passed | passed |
| FINRA consolidated audit trail | USD 0.000003 × quantity | passed | passed |
| **NSCC / DTC clearing** | **USD 0.00020 per share** | **passed** | **absorbed** |
| **Exchange fees** | per venue, below | **passed** | **absorbed** |
| **Pass-through** | commissions × 0.000735 | **passed** | **absorbed** |

## 2b. Taking and adding, reported separately

**Never blended.** *An average of a fee and a rebate describes no order anyone
places.*

| Case | Venue | Per share, per side |
|---|---|---|
| **REMOVE liquidity** (marketable) | NYSE, NASDAQ, ARCA, MEMX, all alike | **USD 0.0030** |
| **ADD liquidity** (resting limit) | NYSE Tape A other | **rebate (0.0012)** |
| ADD liquidity | NASDAQ | rebate (0.0013) |
| ADD liquidity | ARCA | rebate (0.0020) |
| ADD liquidity | MEMX | rebate (0.0026) |

***And a third case the question did not anticipate, which turns out to be the
one that governs.*** The venue schedules price **opening-auction orders
separately**, at the same rate whether they add or remove:

| Venue | Market-on-open or limit-on-open, either side |
|---|---|
| **NYSE** | **USD 0.0010** |
| **NASDAQ / Island** | **USD 0.0015** |
| **ARCA** | **USD 0.0015** |

## 2c. Which case is this strategy in? **Read from §4.3, not assumed.**

> **§4.3:** *"Entries and signal exits fill at the **open of the session after
> signal completion**. Stops fill by comparison: open at or beyond the stop →
> fill at the open; else fill at the stop plus half the cost-tier spread."*

**So the strategy is in neither of the two cases the question named.**

- **Entries: opening auction.** Not taking, not adding. **USD 0.0010 to 0.0015.**
- **Signal exits: opening auction.** Same.
- **Stop exits: triggered intraday and marketable, so they REMOVE. USD 0.0030.**

***The strategy never rests a limit order in the continuous book under this
convention, so it never earns an add rebate.*** *The rebate column is real and
is unreachable, which is worth knowing and is not worth averaging into
anything.*

### The crossover, derived

With both per-order minima free, tiered minus fixed is `N` times

```
(e1 + e2) + 0.0070 + 2(0.00020) + 2(0.0035)(0.000735) - 0.0100
```

**Tiered wins if and only if the two legs' exchange fees sum below USD
0.0025949, that is USD 0.0012974 per side.**

| Leg pricing | Per side | Verdict |
|---|---|---|
| NYSE opening auction | 0.0010 | **tiered** |
| NASDAQ / ARCA opening auction | 0.0015 | **FIXED** |
| Any venue, stop exit removing liquidity | 0.0030 | **FIXED** |

***The election REVERSES TO FIXED, and it is taken on delegated authority, 27
August 2026, with the operator's standing right to revise.***

**The four grounds, in order of weight.**

1. ***Every stop exit favours fixed, at every venue.*** Each of §4.1's exit
   families carries a stop, so a material share of round trips has a
   removing leg. **No routing avoids it.**
2. **Two of the three main venues' opening-auction fees are above the
   crossover.** **The strategy does not pick the venue**: IB SmartRouting does.
   A tiered election therefore prices at a venue nobody chose.
3. ***Fixed's cost is a CONSTANT and tiered's is not.*** Tiered's proportional
   term spans **96.06/p to 116.06/p** across venue and exit type; fixed's is a
   flat **102.01/p**. **A per-market cost that depends on which venue
   SmartRouting picked is not a cost this project can register**, and §13 row 30
   needs one number per market.
4. Tiered wins only on a **NYSE-open to NYSE-open** round trip, by **0.0006 per
   share**, and only where fixed's USD 1.00 minimum is free.

**The one region where tiered still wins, stated because it is real.** Below
**200 shares** fixed's USD 1.00 minimum binds while tiered's USD 0.35 does not,
and tiered is cheaper by up to **1.16 bp** at the clip floor at high share
prices. *That region is bounded, it does not cover the stop legs, and one
account-level election cannot take both sides of it.*

---

## The measured cost model, and it NAMES row 1's unexplained USD 4.00

**US equities, fixed pricing, per round trip:**

```
commission        2 x max(USD 1.00, 0.0050 x N)
FINRA CAT         2 x 0.000003 x N
FINRA TAF         0.000195 x N                      (sell leg)
SEC fee           0.0000206 x V                     (sale value)
exchange/clearing/pass-through   ABSORBED
FX, manual spot   2 x max(USD 2.00, 0.000020 x V)
```

***The FX minimum binds below USD 100,000 of position, so FX costs USD 4.00 per
round trip at every size this book can take.***

**Therefore, in the commission-minimum regime:**

```
absolute round trip  =  USD 2.00 commission  +  USD 4.00 FX  =  USD 6.00
```

***That is row 1's stated USD 6.00, and its composition is now known.*** P101
fitted a **USD 4.00** term of "other fixed charges" and **could not name it**.
**It is the two spot conversions at their USD 2.00 minimum** — priced on the
very page that returned **403** to the previous batch and **200** to this one.

**In basis points, the measured model against the fitted one:**

| Regime | Fitted (P101) | **Measured** |
|---|---|---|
| Commission minimum binds, `V < 200p` | `60,000/V + 4/p` | **`60,000/V + 2.01/p + 0.206`** |
| Rate binds, `V ≥ 200p` | `40,000/V + 104/p` | **`40,000/V + 102.01/p + 0.206`** |

**The fit was close and it was close for the wrong reason.** It put the whole
size-independent term on `4/p`; the measurement splits it into **2.01/p** of
per-share regulatory fees and **0.206 bp** of SEC fee, **which is proportional
to value and does not vary with share price at all.**

---

## 2d. Row 29's universe table and row 30's floors, RECOMPUTED

**At the registered 10 bp tolerance, under the fixed election:**

| Share price | Asymptote `102.01/p + 0.206` | **Clip floor** | Within §6.7's largest position? |
|---|---|---|---|
| USD 10.40 | 10.015 bp | **none at any size** | — |
| USD 11.00 | 9.480 bp | USD 76,869 | **no** |
| USD 12.00 | 8.707 bp | USD 30,932 | **no** |
| USD 13.00 | 8.053 bp | USD 20,544 | **no** |
| **USD 13.20** | 7.933 bp | USD 19,361 | **the boundary** |
| USD 15.00 | 7.007 bp | USD 13,363 | yes |
| USD 20.00 | 5.307 bp | USD 8,522 | yes |
| USD 30.00 | 3.606 bp | USD 6,256 | yes |
| **USD 43.79** | 2.536 bp | **USD 6,155** | yes |
| USD 75.00 | 1.566 bp | USD 6,143 | yes |
| USD 150.00 | 0.886 bp | USD 6,135 | yes |

**Cost at every published floor reads 10.000 bp** on the independent check,
which is the derivation checking itself.

### Two results that change what the screen is

***The cost minimum share price is USD 10.42***, from `102.01/p + 0.206 ≤ 10`,
against **USD 10.40** under the fitted model and **USD 7.40** under the tiered
election that has now been reversed. *The reversal costs about three dollars of
minimum share price and buys a cost that is a constant.*

***But USD 10.42 is not the binding screen. USD 13.20 is.*** §6.7's largest
position is **GBP 15,000 ≈ USD 19,350**, and below **USD 13.20 a share the clip
floor exceeds the largest position the sizing rules will ever take.** **The
binding screen is §6.7's cap, not the cost asymptote**, and between USD 10.42
and USD 13.20 a name is *cost-reachable and size-unreachable*, which are
different refusals.

### The book is still not empty

At the calibration price the floor is **USD 6,155 = GBP 4,771**, inside §6.7's
**GBP 1,875 to GBP 15,000** band, and **the conclusion holds for any USD/GBP
rate between 0.410 and 3.283**, so no FX assumption is load-bearing.

*Every floor rose by roughly 1.7% against the fitted model. Nothing changed
sign.*

## The UK, briefly, because the election is account-wide

UK fixed SmartRouting is **0.05% min GBP 3.00** against tiered's **0.05% min
GBP 1.00**, and fixed absorbs the LSE's 0.000045 exchange fee and GBP 0.06
clearing. **At GBP 50,000 fixed is cheaper (10.0 bp against 10.92); at GBP 5,000
tiered is (11.14 bp against 12.0).** **Neither reaches the 10 bp tolerance**
once the PTM levy is added, so **AIM stays excluded under both elections and UK
Main Market stays excluded by stamp duty.** *The election does not move the UK
answer.*
