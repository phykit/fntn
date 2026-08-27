# Row 29 and δₘᵢₙ, re-derived now that the premise exists

**27 August 2026. Phase 1 of the seven-phase batch.** §0.12 states reference
equity at **GBP 100,000**. P125 prepared this derivation in full and **stopped**,
because the Class I invariant forbids taking a decision over a caveat the
preparation itself states, and the caveat was that reference equity had not been
restated in a form the arithmetic could read. ***That caveat is now discharged
by the operator's own statement, so the decision is taken.***

---

## 1a. The derivation, computed rather than adopted

### The inputs, each with the artefact it comes from

| Input | Value | Artefact |
|---|---|---|
| Reference equity | **GBP 100,000** | §0.12; §0.11 |
| §6.7 risk at full size | **75.0 bps of it = GBP 750** | spec line 753 |
| Widest stop in §6.7's band | **40%** | `docs/DECISION_sizing_collision.md` |
| **§6.7's smallest position `V_min`** | **GBP 1,875** | `750 / 0.40` |
| US fixed-pricing cost model, no per-trade FX | `max(20,000/V, 100/p) + 2.01/p + 0.206` bp | §13 row 1 as read at P117, decomposed at P118, FX removed at P125 |
| Reference USD/GBP rate | **1.29**, a stated convention | see 1a(iv) |

*The commission term is `2 x max(USD 1.00, 0.0050 x N)`, so in basis points it
is `max(20,000/V, 100/p)` and **not** a minimum of the two regimes. **That is
recorded because this session's first check function wrote it as a minimum**,
which reports the rate-regime figure at every position §6.7 sizes and would have
put 2.54 bp where 8.52 belongs. The error was caught by an independent inverse,
below.*

### (i) The criterion, and there are two readings of it in the register

P125's replacement reads: *"the coherent tolerance is where the clip floor
equals §6.7's smallest position, since below it the floor refuses positions the
sizing rules produce and above it the floor binds on nothing."*

***That sentence contains two criteria and they do not agree.***

| | Criterion | Yields |
|---|---|---|
| **A** | *the floor EQUALS `V_min`* | an equality, evaluated at one share price |
| **B** | *below it the floor REFUSES positions the sizing rules produce* | a non-refusal condition, which must hold at **every** admissible price |

**Criterion B governs, on two grounds and neither is a preference.**

1. **The equality is only interesting because of the harm either side of it**,
   and the harm the sentence names is a governance floor refusing what the
   funnel admits. **That harm is a harm at any share price**, not only at the
   calibration price.
2. **Criterion A does not yield a tolerance.** Worked at each price it gives a
   different number, 8.4881 bp at USD 150 to 8.6676 bp at USD 10.42. *A
   quantity with one value per share price is not a dimensionless governance
   parameter; it is a column.* **Criterion B is price-independent by
   construction**, as shown next.

### (ii) Criterion B, worked

The floor is largest at the lowest reachable price, where it meets the kink at
`V = 200p`. Writing `p_min(t) = 102.01 / (t - 0.206)`, the condition
*floor never exceeds `V_min`* is `200 x p_min(t) <= V_min`, so

```
t*  =  0.206  +  20,402 / V_min          and share price DROPS OUT
```

**At `V_min` = GBP 1,875 converted at 1.29, that is USD 2,419:**

```
t*  =  0.206  +  20,402 / 2,419  =  0.206 + 8.4341  =  8.6409 bp
```

**Checked at the boundary, and it closes exactly:** `p_min(8.6409)` = USD
12.094, `200 x 12.094` = **USD 2,419**, which is `V_min` to the pound.

### (iii) The registered value: **8.7 bp**

**Rounded to one decimal, upward.** The parameter object carries one decimal
(`10.0`, `17.0`, `25.0` before it), and **the direction is not a preference**:
rounding down breaks the condition the value is derived from.

| Candidate | `p_min` | Largest floor | Refuses nothing §6.7 sizes? |
|---|---|---|---|
| 8.4 bp | USD 12.449 | USD 2,490 | **NO** |
| 8.5 bp | USD 12.299 | USD 2,460 | **NO** |
| 8.6 bp | USD 12.153 | USD 2,431 | **NO** |
| **8.7 bp** | **USD 12.010** | **USD 2,402** | **YES**, by USD 17 |
| 8.8 bp | USD 11.870 | USD 2,374 | yes, by USD 45 |

***8.7 is the smallest one-decimal value at which the derived condition
actually holds***, and the 0.059 bp between 8.641 and 8.7 is the rounding and
is named as such. *The register has been burned once by unearned margin, δₘᵢₙ's
8.0 bp at P117. This is 0.059 bp and it is arithmetic, not judgement.*

### (iv) The FX dependency, stated and not buried

**`t*` moves with the USD/GBP rate**, because the absolute cost term is in
dollars and `V_min` is in pounds. §0.12 records that this withdraws a property
row 29 claimed for itself at P98.

```
t*(R)  =  0.206  +  10.8811 / R
```

| USD/GBP `R` | `V_min` USD | `t*` |
|---|---|---|
| 1.10 | 2,062 | 10.098 |
| 1.20 | 2,250 | 9.274 |
| 1.25 | 2,344 | 8.911 |
| **1.29** | **2,419** | **8.641** |
| 1.30 | 2,438 | 8.576 |
| 1.35 | 2,531 | 8.266 |
| 1.40 | 2,625 | 7.978 |
| 1.50 | 2,812 | 7.460 |

***What does NOT depend on the rate, and it is the load-bearing half of this
decision: the DIRECTION.*** `t*` equals the registered 10.0 bp at **R =
1.1110**, and exceeds it only below that. **At every rate above 1.111, the
tolerance falls.** *Sterling has closed below 1.11 against the dollar on a
handful of days in forty years.* **So the finding that row 29 is too high is
robust; only its third significant figure is not.**

**Is this a caveat the decision is being taken over?** ***No, and the invariant
itself says why.*** Part 2's own text distinguishes *"a gap that the preparation
states and CANNOT close"* from *"a caveat that names a page nobody has opened"*,
and names the auto-conversion FX rate under a 403 as an instance of the first.
**Under §0 decision 0b the conversion happens once, at fund level, and the
account is not funded**, so the rate that will apply does not exist to be looked
up. *The refuting check is not available, which is the invariant's stated test.*
**What is available is the sensitivity, and it is published above rather than
collapsed into one figure.**

---

## 1b. The §5.2.2 upper bound is NOT used, and is not needed

**It is circular and the circularity is now a corrections class of its own**
(`docs/CORRECTIONS.md` B10, Class IV, `§12.1` P133). §5.2.2's 12.5 bp basis was
recomputed against row 29's own 10 bp at P111, so a ceiling drawn from that
table returns the tolerance it was given.

***And the range is no longer needed for this purpose.*** The replacement
derivation returns **a single value**, not an interval: `t*` is where the floor
meets `V_min`, and there is one such tolerance. **A range was needed when the
tolerance was being chosen from a defensible band; it is not needed when the
tolerance is computed.**

**The lower bound survives and is not load-bearing.** `102.01/p + 0.206` at the
calibration price is **2.536 bp**, the cost no size can get below. It is a
property of the schedule, it did not move under 0b (A10), and **nothing reads
it**: at 8.7 bp the binding screen is the minimum share price, not the
asymptote at one price.

***No upper bound is derived here, and the absence is recorded rather than
filled.*** An upper bound would have to come from something the tolerance does
not compute, and the only candidate in the neighbourhood — §5.2.2 — is the one
Class IV forbids. **A bound that cannot be derived is left absent.**

---

## 1c. δₘᵢₙ re-derived. **15.7 bp. IT IS A LOOSENING.**

```
delta_min  =  cheapest midpoint spread  +  row 29's bound
           =  7.0 bp                    +  8.7 bp     =  15.7 bp
```

> ***STATED PLAINLY, AS THE DIRECTION IT IS. A LOWER δₘᵢₙ ADMITS MECHANISMS
> THAT ARE REFUSED TODAY.*** **Every mechanism whose claimed effect falls
> between 15.7 bp and 17.0 bp is admissible after this change and was
> inadmissible before it.** *This is a loosening of the floor that gates every
> directive this project will ever consider, and it is the second loosening of
> that floor in one day: 25.0 to 17.0 at P117, and 17.0 to 15.7 here.*

**It is not circular, and the distinction matters after B10.** δₘᵢₙ is
`spread + tolerance` by definition, and the spread term is recovered from
§5.2.2's **published** column, which predates row 29. *Reading the tolerance
back out of a sum it was put into is not a validation; drawing a bound on the
tolerance from that sum would be, and 1b declines to.*

**§5.2.2's recomputed column moves with it**, being `published − 12.5 + bound`:

| ADV bucket | published | at 10.0 bp | **at 8.7 bp** |
|---|---|---|---|
| >$1bn | 22.5 / 19.5 | 20.0 / 17.0 | **18.7 / 15.7** |
| $100m–$1bn | 42.5 / 32.5 | 40.0 / 30.0 | **38.7 / 28.7** |
| $10–100m | 112.5 / 82.5 | 110.0 / 80.0 | **108.7 / 78.7** |
| $1–10m | 312.5 / 212.5 | 310.0 / 210.0 | **308.7 / 208.7** |

*The cheapest recomputed midpoint is 15.7, which is δₘᵢₙ, as it must be.*

---

## 1d. THE COST, STATED BEFORE THE BENEFIT

***A tighter tolerance SHRINKS the tradeable universe, and this is the price of
the change.***

| Screen | at 10.0 bp | **at 8.7 bp** |
|---|---|---|
| **Minimum US share price** | USD 10.42 | ***USD 12.01*** |
| Clip floor at USD 43.79 | USD 2,052 | USD 2,367 |
| Clip floor at USD 15.00 | USD 2,070 | USD 2,392 |
| Clip floor at USD 12.50 | USD 2,076 | USD 2,400 |

**Every US name between USD 10.42 and USD 12.01 a share becomes unreachable at
any position size.** *That is a real exclusion of a real part of the universe,
taken in exchange for a tolerance that is derived rather than chosen.*

**Three things do NOT move.**

- **UK Main Market stays excluded with certainty**, stamp duty being 50 bp.
- **AIM stays excluded on commission**, its 0.05% a side being 10.3 bp round
  trip; **a lower tolerance moves further from AIM, not towards it.** *The
  Annex A.1 growth-market row stays moot and stays not-withdrawn, and the
  tolerance at which AIM returns is still above 10.3 bp.*
- **The floor still refuses nothing §6.7 sizes**, which is the condition the
  value was derived from. *The margin is USD 17 at the tightest point, and it
  is zero by construction: a boundary has no margin, which is what makes it a
  boundary.*

---

## 1e. Binding-path steps 1 and 3 after the change

| Step | Cells | State |
|---|---|---|
| **1** | §13 row 1 | **CLOSED, unchanged.** Row 1 is a COMMISSION row closed on option A's terms; a tolerance is not one of its inputs. *Row 29 reads row 1, not the reverse.* |
| **3** | θ, the δₘᵢₙ floor, account type | **CLOSED, unchanged.** δₘᵢₙ **moved in value and not in status**: it was CLOSED at 17.0 and is CLOSED at 15.7. θ and account type are untouched |

***Neither re-opens, and the check was run rather than assumed.*** A8 in the
corrections register is the instance of this project asserting that row 29's
movement moves step 3; **it does not, and the cells were re-read rather than
recalled.** *What would have re-opened step 3 is δₘᵢₙ becoming underivable, and
it does not: its derivation is `spread + bound` and both terms exist.*

---

## 1f. What this decision does NOT settle, listed so it cannot be read as settled

- **The 7.0 bp spread term is not measured.** Phase 2 opens a row for it.
  *δₘᵢₙ is therefore a derived number over an unmeasured input, and 8.7 of its
  15.7 is arithmetic whilst 7.0 of it is inheritance.*
- **The tolerance has no upper bound.** 1b declines to derive one.
- **Reference equity in USD is not determined** and will not be until funding.
- ***`src/fntn/scanner/sizing.py` still implements the SUPERSEDED cost model***
  — `104/p` with a USD 4.00 FX term — which P118 replaced and P125 halved. It
  is a finding of this phase, it is recorded in `docs/OPEN_ITEMS.md`, and **no
  figure in this document comes from it.** *Every figure here is computed from
  the measured model and cross-checked by an independent inverse.*
