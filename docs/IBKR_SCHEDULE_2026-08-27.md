# §13 row 1: the published schedule, read

**27 August 2026. Phase 1 of the nine-phase batch.** Retrieved
**2026-08-27T19:00:05Z**, by `curl` with a browser user-agent, from
Interactive Brokers' own domains.

***Every figure below was read from a page in this list. Nothing here is
recalled, inferred, or taken from a comparison site.*** The previous batch
recorded a **403** on the spot-currency page and recorded that nobody had read
it; **that page answered 200 today and was read.**

| Key | Bytes | sha256 (16) | URL |
|---|---|---|---|
| `uk` | 538,135 | `2e8fbcf6b0fe2d55` | `https://www.interactivebrokers.co.uk/en/pricing/commissions-stocks.php` |
| `ie` | 569,576 | `5a89c29a5a75d684` | `https://www.interactivebrokers.ie/en/pricing/commissions-stocks.php` |
| `lsefees` | 111,079 | `47d2f1811b52a73b` | `https://www.interactivebrokers.co.uk/en/accounts/fees/LSEstkfees.php` |
| `ptm` | 108,927 | `9b95676500827ba8` | `https://www.interactivebrokers.co.uk/en/includes/disclosures/eu-stk-ptm-levy.php` |
| `spot` | 124,360 | `ba2b0a0acbf59088` | `https://www.interactivebrokers.co.uk/en/pricing/commissions-spot-currencies.php` |

**Provenance: `verified_primary`.** The publisher's own pages, at per-trade
granularity, read in this session.

---

## 1a. THE ENTITY GAP IS IMMATERIAL. Row 1's third gap is RETIRED.

**The question was which contracting entity the account sits under**, because
row 1's figures would be read off that entity's schedule. **Both entities were
retrieved and compared mechanically rather than by eye.**

The comparison is over the two blocks row 1 actually uses, extracted from each
page's text and hashed:

| Block | UK entity | Ireland entity | Identical? |
|---|---|---|---|
| **United States** commission table, tiers, minima and maxima | 1,830 chars, sha `053442ce710bbf1a` | 1,830 chars, sha `053442ce710bbf1a` | **YES, byte-for-byte** |
| **United Kingdom** commission table, GBP/EUR/USD denominated | 2,415 chars, sha `1ad21c16928f574b` | 2,415 chars, sha `1ad21c16928f574b` | **YES, byte-for-byte** |

***The two entities publish identical figures for every component row 1 uses.
So the entity question cannot change row 1's answer, and it is retired by being
shown to be immaterial rather than by being answered.***

**This needed no operator input, and that is the point of testing materiality
before asking.** The gap stood on this register as a blocker for a fact about
the operator's account. **It was never a fact the answer depended on.**

*The honest limit of this finding.* It establishes that **the published
commission schedules are identical**, which is what row 1 reads. It does **not**
establish that the two entities are identical in every respect: investor
compensation limits, regulator and account terms differ, and **a future row that
depends on those still needs the entity named.** What is retired is this gap on
this row.

---

## The figures, as published

### United States equities, per order

| | Tiered | Fixed |
|---|---|---|
| ≤ 300,000 shares/month | **USD 0.0035** per share | **USD 0.0050** per share |
| Minimum per order | **USD 0.35** | **USD 1.00** |
| Maximum per order | 1% of trade value | 1% of trade value |

***One figure here contradicts the model P101 fitted, and it matters in phase
2.*** P101 gave **both** schedules a **USD 1.00** per-order minimum. **Tiered's
published minimum is USD 0.35.**

### United States, third-party fees (tiered passes these through)

| Charge | Published rate |
|---|---|
| SEC transaction fee | USD 0.0000206 × value of aggregate **sales** |
| FINRA trading activity fee | USD 0.000195 × quantity **sold** |
| FINRA consolidated audit trail | USD 0.000003 × quantity |
| NSCC / DTC clearing | **USD 0.00020 per share** |
| NYSE pass-through | commissions × 0.000175 |
| FINRA pass-through | commissions × 0.00056 |

*The NSCC/DTC figure of 0.0002 per share matches what P101 assumed. It is now
read rather than assumed.*

### United Kingdom equities, GBP denominated, per order

| | Tiered | Fixed, SmartRouting | Fixed, direct |
|---|---|---|---|
| ≤ GBP 40m/month | **0.05% of trade value** | 0.05% | 0.10% |
| Minimum per order | **GBP 1.00** | GBP 3.00 | GBP 4.00 |
| Maximum per order | none | none | none |

**LSE exchange and clearing fees**, from `lsefees`:

| Charge | Published rate |
|---|---|
| Exchange fee, "All Other" (non-ETF) | trade value × **0.000045**, minimum **GBP 0.11** per order |
| Clearing fee | **GBP 0.06** per order |

**PTM levy**, from `ptm`, and **it is not what this project assumed**:

> *"This flat-rate levy of **1.50 GBP** per qualifying trade applies under the
> following conditions: the company is incorporated in the UK, Channel Islands
> or Isle of Man; trades are executed on a UK regulated exchange or MTF;
> transactions are conducted on an agency basis; **the total transaction value
> exceeds GBP 10,000**."*

**GBP 1.50, not GBP 1.00**, and it applies to **buy and sell**, so **GBP 3.00
round trip** above GBP 10,000.

### FX, manual spot conversion — **the gap the previous batch could not close**

From `spot`, which returned 403 last time and 200 today:

| | Published rate |
|---|---|
| Spot currency commission, ≤ USD 1bn monthly | **0.20 basis points × trade value** |
| Minimum per order | **USD 2.00** (Tier I) |

***The manual-spot decision taken at P112 rested on a dominance argument
because the rate was uncited. The rate is now cited.*** At USD 64,000 a
conversion costs `0.20 bp × 64,000 = USD 1.28`, **below the USD 2.00 minimum**,
so **USD 2.00 applies and the conversion costs 0.31 bp** — which is precisely
the figure the dominance argument used as manual's bounded downside. **The
argument is confirmed by the schedule it was made without.**

*The auto-conversion rate remains uncited and is not needed:* manual is elected,
and its cost is now a read figure rather than a bound.

---

## What row 1 now has, and what it still does not

| Component | State |
|---|---|
| US commission, both schedules, tiers and minima | **read** |
| US third-party fees, itemised | **read** |
| UK commission, all three routings | **read** |
| LSE exchange and clearing fees | **read** |
| PTM levy, rate and conditions | **read** |
| Stamp duty | 0.5%, statutory, unchanged |
| FX route and its cost | **elected and read** |
| **Contracting entity** | **immaterial for this row; retired** |
| **US exchange fees, per venue** | **NOT read here.** They are a list of venue names on this page and their rates are per venue. **Phase 2 is where that is done**, and the tiered election turns on it |

---

## 1b. The δₘᵢₙ floor, DERIVED

**It derives. 17.0 basis points.** Taken on delegated authority, 27 August 2026,
with the operator's standing right to revise.

### The derivation

**What the floor is, in the register's own words:** *the smallest effect below
which a directive is not worth a session of the design segment.* **An effect
that cannot clear the cost of trading it cannot be acted on in any cell**, so a
session spent establishing it buys nothing tradeable. **The floor is therefore
the cheapest per-trade break-even in the whole admissible universe.**

```
cheapest break-even  =  cheapest spread  +  fixed cost
                     =  7.0 bp           +  10.0 bp
                     =  17.0 bp
```

**The spread term, 7.0 bp**, is §5.2.2's most liquid bucket at the midpoint,
recovered from the published table by subtracting the 12.5 bp basis it was
computed on: `19.5 − 12.5 = 7.0`. *§0.10's table confirms the decomposition
independently: a 200 bp spread there gives a 225 bp break-even at 25 bp fixed.*

**The fixed term, 10.0 bp, is a BOUND and not an estimate.** §13 row 29
registers 10 bp as the maximum tolerable fixed cost and row 30 defines the clip
floor as the size at which cost *equals* it, so **every admissible position
carries at most 10 bp by construction.** **It needs no share price and no FX
rate**, and it is the same move that made §5.2.2 and §0.10 comparable.

### Two questions the derivation had to settle, both settled from the specification

***Which column: conservative or midpoint?*** **Midpoint, and it is not a
preference.** §5.2.2 states that *"Gate 1's ceiling and Gate 7's gate read the
midpoint; the conservative figure travels as an advisory flag."* **A floor set
on the conservative column would refuse directives that the gates themselves
would pass**, which is a governance floor refusing what the funnel admits. *That
incoherence settles the column.*

***Does §6.1's decay ladder apply?*** **No, and applying it would double-count.**
Gate 1's cost-survival check already applies the ladder to the **claimed**
effect at intake. δₘᵢₙ is a **kill criterion on a measured effect**: below it,
the directive is refuted. **Haircutting the same effect once against the claim
and again against the measurement would charge the decay twice.**

### What the derivation gives, and what it deliberately does not

**It gives a NECESSARY condition and not a sufficient one.** An effect at
exactly 17.0 bp nets zero and is not, in any useful sense, *worth* a session.
**How far above break-even a directive must sit to be worth one is a margin, and
no measurement in this project bounds it**, so **no margin is added.**

***That is the substantive change, and it is a LOOSENING.*** The registered
floor was **25.0 bp**, justified as *"the cheapest break-even in §5.2.2 is 22.5
bps, so an effect below that could never be traded in any cell"* — the same
rule, with the same necessary condition, plus **2.5 bp of unstated margin**. At
the corrected break-even the rule alone gives 17.0, so the registered value
carried **8.0 bp of margin that was never derived.**

**The cost of deriving rather than choosing, stated: directives with effects
between 17.0 and 25.0 bp are now admissible and were previously refused.** *An
undeclared 8 bp of extra strictness is a chosen parameter wearing a
derivation's clothes, and this project's rule is to derive. The alternative is
available in one word: 20.0 on the conservative column, or 25.0 retained.*

### Provenance, inherited and stated

**The floor inherits §5.2.2's spread column**, which is **not measured on this
system's data**: §13 row 14 is the row that would measure effective spreads by
bucket, and it is BLOCKED on a design segment. **The registered 25.0 rested on
exactly the same column**, so this is the same operation with corrected inputs
rather than a new provenance claim.

**Re-derivation when row 14 closes is arithmetic and costs no decision.**

### Robust to the one thing still open on row 1

**The derivation does not depend on row 1's SCOPE question.** Whether row 1 is a
commission row (option A) or the whole transaction cost (B or C), **the fixed
term here is row 29's bound, which caps the fixed cost however it is scoped.**
*A wider scope moves what row 1 measures; it cannot move a ceiling that is
already binding.*
