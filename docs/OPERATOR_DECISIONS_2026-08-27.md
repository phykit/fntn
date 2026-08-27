# Operator decisions, 27 August 2026, and one advisory error

**Phase 0 of the eleven-phase batch.** These are the operator's own decisions,
not delegated ones. They are recorded here and in the register, and each states
what it invalidates.

---

## 0a. NO LIVE CAPITAL. The objective is realistic backtesting.

***§13 row 31 stays BLOCKED with its blanks empty, and it is now blocked BY
DECISION rather than by omission.***

**That is a different and better record, and the difference is worth stating.**
A gate with two blanks that nobody has noticed is a **defect**: it cannot pass,
cannot fail, and a reader may mistake it for a strict gate nothing clears. **A
gate with two blanks that the operator has decided to leave empty is a
CONSTRAINT**: it says, on the record, that no path to capital is open and that
none is being sought.

**What the decision governs.** The objective for the foreseeable period is
**realistic backtesting**, not deployment. **The freeze record's scope, when
signed, is the backtest and the two instruments** — §7.1's funnel-depth
association and §7.5's placebo — **and nothing about deployment.**

**What it does not do.** It does not fill the predicate, and it does not retire
it. **The two blanks remain the two blanks**, so that the day capital is
contemplated the gate is met unfilled rather than met unnoticed.

*The condition that would reopen it: an explicit §0 decision to deploy.*

---

## 0b. BASE CURRENCY USD. No per-trade FX conversion.

**The account is treated as USD-denominated.** A funding conversion happens
**once, at fund level**, and **is not a per-position cost.**

***What this invalidates, and it is the largest single term in row 1's absolute
cost.*** P118 decomposed the USD 6.00 round trip that row 1 has always stated:

```
USD 2.00   two commission minimums, at USD 1.00 a side on fixed pricing
USD 4.00   two manual-spot conversions, at their USD 2.00 minimum
--------
USD 6.00
```

***Two thirds of it is FX, and under this decision it comes out.*** The absolute
term becomes **USD 2.00**, and **every figure derived from USD 6.00 moves**:
§13 row 30's floors, row 29's derived lower bound, and the δₘᵢₙ floor through
row 29's bound. **Phase 1 takes it through the arithmetic.**

*The manual-spot election at P112 is not withdrawn. It stands, and it now
prices a fund-level operation rather than a per-trade one.*

---

## 0c. INSIDER DEALING IS OUT, on achievability grounds.

**Phase 2 executes it.** The cost is stated there in full, because it is
substantial: retiring the family strands `corpora/us`, the Form 4 block built
for §9.4, and **the only route §13 row 15 has ever had.**

---

## 0d. An advisory error, and it is the SIXTH instance of Class I

**Asserted:** that retiring the insider-dealing family takes `SEC_CONTACT` off
the critical path.

***FALSE.***

**What retiring the family removes is EDGAR from the DISCOVERY corpora** — and
**the discovery corpora do not come from EDGAR.** `corpora/us` is thirteen
documents from **`law.cornell.edu`**, which is rule text, fetched without any
SEC contact at all. **Retiring the family removes a Cornell corpus and touches
`SEC_CONTACT` not at all.**

**What needs `SEC_CONTACT` is step 4's ITEM-PIPELINE trace**, which needs **live
filings whatever the family**, and ***13D, 8-K and issuer repurchase disclosures
are all EDGAR.***

***The error was conflating the discovery corpus with the trace corpus.*** They
are different objects with different fences: the discovery corpus is what the
agent is shown, and `corpora/_trace_filings` is fenced out of every registration
route precisely so that the two cannot be confused. **The conflation this error
makes is the one the fence exists against.**

### Class I, and the instance count now matters

**This is the sixth instance of *a conclusion acted on without checking the link
it rests on*.** The previous five were A2, A5b, A8, B8pre and B9.

***So the invariant installed in the previous batch was installed against a class
that was still generating instances.*** **Phase 9b must say whether that
invariant would have caught this one**, and **an invariant that does not catch
the next instance of its own class is not yet an invariant.**

---

## 0e. The IBUK confirmation CORROBORATES and was not needed

**The operator's own account correspondence of 3 March 2026** — FCA Consumer
Duty language, account **U\*\*\*0932** — confirms the contracting entity is
**Interactive Brokers (U.K.) Limited**.

***It corroborates the phase-1 finding and was not needed for it.*** The finding
was that **both entities publish byte-identical commission blocks**, hashing to
`053442ce710bbf1a` and `1ad21c16928f574b`, so **the question could not change
row 1's answer.**

### Retiring by immateriality is the stronger result, and it is the preferred pattern

| | **Answering** the question | **Retiring** it by immateriality |
|---|---|---|
| What it establishes | this account is IBUK | **no account's entity could change this row** |
| What it survives | nothing: a transfer, a re-domicile or a second account reopens it | **all of those** |
| What it costs | the operator's attention | **a mechanical comparison** |
| Provenance | correspondence, which is `verified_secondary` for a fee schedule | **the publisher's own pages, `verified_primary`** |

***The pattern, stated so it is reached for first:*** **before asking whether a
gap can be filled, test whether it is material.** A gap shown immaterial is
closed for every future reader; a gap answered is closed for one account until
something moves.

*This project has now retired two blockers by immateriality — this one and, at
P120, row 21a's sample-size question, which turned out to be one number and not
a sample-size question at all.* **Both took minutes and neither needed the
operator.**
