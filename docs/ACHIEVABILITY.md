# Achievability, derived

**27 August 2026. Phase 4 of the eleven-phase batch.**

**The operator wants strategies that are *achievable*.** That word was prose.
***Every component of it is implied by a decision already registered***, so it is
**derived here and not chosen**, and each criterion below cites the decision it
comes from.

***This file specifies a LENS, not a fence.*** `src/fntn/scanner/achievability.py`
**reads** the registered parameter object and a candidate's declarations and
**reports** which criteria are met, failed or unscorable, **naming the failing
one**. It refuses nothing, gates nothing, and **no funnel step consults it at
decision time**, so it is **procedure** under armed §0.6. *The fence version is
apparatus and is prepared in §4c below, not taken.*

---

## 4a. The nine criteria, each with its authority

| # | Criterion | Threshold | Registered authority |
|---|---|---|---|
| 1 | **Long only, no margin** | none needed | **§14 account type: CASH** (P116). A cash account cannot borrow. **§5.4.1**: the grammar is long-only for every live family |
| 2 | **US-listed** | none needed | **§0 decision 0b**, base currency USD; **§13 row 29 at 10 bp**, which excludes UK Main Market on **stamp duty at 50 bp** and AIM on **commission at ~10.3 bp** |
| 3 | **Minimum share price** | ***USD 10.42*** | **§13 rows 29 and 1**: `102.01/p + 0.206 ≤ 10`. Below it **no position size reaches the tolerance** |
| 4 | **Minimum liquidity** | ***USD 40,312 of median daily notional*** | **§6.7's participation cap**: 2% per session over at most 3 sessions, so a name supports at most **6% of ADV**, and the smallest position §6.7 sizes is GBP 1,875 ≈ USD 2,419 |
| 5 | **Actionable at the next open** | none needed; it is a property | **§4.3**: entries and signal exits fill at the open of the session after signal completion. **§13 row 13** measures the capture rate and is BLOCKED |
| 6 | **Effect exceeds δₘᵢₙ** | ***17.0 bp*** | **§14's δₘᵢₙ floor**, derived at P117 as the cheapest per-trade break-even |
| 7 | **Holding period admissible** | ***{5, 21, 63} sessions*** | **§4.1's fixed horizons.** §14's manual-observation capacity is **OPEN** and would tighten this |
| 8 | **Obtainable without a purchase** | none needed | **No vendor feed is authorised.** §0.7(d)'s ICB vintage is the only purchase on the register and is not taken |
| 9 | **Backtestable, survivorship included** | ***a coverage fraction nobody holds*** | **§0.7(a)**'s archive; **P127**'s survivorship condition; **§13 row 35**, opened below |

### Two thresholds that are derived rather than stated, and one that is not stated at all

**Criterion 3 derives**: `102.01/p + 0.206 ≤ t` inverts to `p ≥ 102.01/(t − 0.206)`,
which at `t = 10` is **USD 10.42**. *It moves if row 29 moves, and the lens
computes it from the registered tolerance rather than holding it.*

**Criterion 4 derives, and it carries an unsettled premise honestly.**
`ADV ≥ position / 0.06`. The **position** is the smallest §6.7 will size, which
depends on whether reference equity is **GBP 100,000** or **USD 100,000** — a
premise §0 decision 0b did not settle and phase 1 declined to settle for it.

| Reading | Smallest position | **Required ADV** |
|---|---|---|
| GBP 100,000 at 1.29 | USD 2,419 | **USD 40,312** |
| USD 100,000 | USD 1,875 | **USD 31,250** |

*The lens takes the position as an argument rather than holding a constant,
precisely so the unsettled premise cannot be buried inside it.*

***Criterion 7's real bound is not stated anywhere.*** §14's
**manual-observation capacity per period** is OPEN. **The link between a holding
period and that capacity is not written down in the specification**, and it is
**not invented here**: the criterion is scored against §4.1's admissible
horizons, which *are* registered, and the capacity bound is named as the thing
that would tighten it.

---

## 4b. The lens. Implemented, and the third state is the point

`achievability.score()` returns, per criterion, one of **three** results:

| Result | Meaning |
|---|---|
| `MET` | the candidate's declaration clears the registered threshold |
| `FAILED` | it does not, **and the criterion is named** |
| ***`UNSCORABLE`*** | **the criterion is real, the candidate is real, and the register does not hold the number needed to judge it** |

***`UNSCORABLE` is never counted as `MET`.*** A not-applicable check may never be
read as a pass, and **an absent declaration is not a failure**: *"this mechanism
does not say" and "this mechanism does not qualify" are different claims about a
candidate and are reported apart.*

**Today every candidate is `UNSCORABLE` on criterion 9**, because the archive
does not exist. **That is the honest reading and it is visible in every row.**

## 4c. The FENCE version. ***Prepared, and NOT taken.***

**A screen that REFUSES is a gate, and a gate is apparatus.**

**§0.6 test, applied:** *does it add a gate, a family, a grammar row, a cost
tier, a sizing input, a feed, or a field the funnel reads at decision time?*
***YES: a gate.*** It would refuse candidates at intake on achievability grounds
and its verdict would be read at decision time.

**So it takes an Annex A.1 row with a predicate and waits.** *The lens lands
today because it reads and reports; the fence waits because it refuses.* **The
distinction is the whole of why §0.6 can stay armed while this work proceeds.**

**Recorded in Annex A.1 with the §0.6 instruments report as its predicate.**

## 4d. What the register does not hold. **§13 row 35 opened.**

Three criteria need a number the register does not hold, and **they are not the
same case.**

| Criterion | The number | Where it lives | Action |
|---|---|---|---|
| 5, actionable at next open | the capture rate | **§13 row 13, BLOCKED** | **none.** The register holds it |
| 7, holding period | manual-observation capacity | **§14, OPEN** | **none.** The register holds it, and opening a §13 row would put one decision on the board twice |
| 9, backtestable | ***the minimum archive coverage fraction*** | **nowhere** | ***§13 row 35 opened, BLOCKED*** |

***Row 35 is the one that did not exist.*** P127 established that a backtest can
**bound** its survivorship bias by counting the delisted names it is missing and
reporting a **coverage fraction**. **Nothing says how low that fraction may go
before a backtest is inadmissible.**

**A criterion with an unstated threshold is exactly the defect class §9.4's
stopping rule was**: the rule exists, the parameter does not, and the check
therefore passes everything.
