# The §5.2.2 move, generalised: where a dimensionless bound replaces an assumption

**27 August 2026. Phase 7 of the nine-phase batch.**

**What the move is.** §13 row 29 replaced an assumed fixed cost with a **bound**:
10 bp caps any admissible position's fixed cost **by construction**, so it needs
**no share price and no FX rate**, and that is what made two tables computed on
different bases comparable for the first time.

**The question this phase asks: where else is the same move available?**

---

## 7a. The sweep. **Ten sites, and the move is available at one.**

| # | Site | Rests on | Move |
|---|---|---|---|
| 1 | §5.2.2 against §0.10 | a per-notional and a per-clip basis | **DONE at P111.** Erratum B discharged |
| 2 | **§13 row 30's floor table** | **a per-share-price figure in USD** | ***AVAILABLE. Taken below*** |
| 3 | §4.4's ATR bounds | risk budget in **GBP** ÷ clip floor in **USD** | **NOT available.** See below |
| 4 | §6.7's sizing band against the floor | the same crossing | **NOT available**, same reason |
| 5 | §6.7's participation cap, 2% of median daily notional | nothing | **already dimensionless** |
| 6 | §4.4's regime caps, 7.5% / 3.75% | nothing, since P100 derived them as fractions of equity | **already dimensionless** |
| 7 | §13 row 15, *"a stated fraction of the admissible horizon"* | nothing | **already dimensionless by construction**, and it was written that way from the start |
| 8 | §13 row 21a, `n = 3/b` | nothing | **already dimensionless**, made so at P120 |
| 9 | §0.5's per-trade break-even prose | §5.2.2 | **DONE at P111** |
| 10 | §13 row 14's *"6.4% of a whole day's traded value"* | an assumed FX rate | **DONE at P110**, recomputed FX-free |

*Four sites were already dimensionless, three were done in earlier batches, one
is available and two are not.* **That is a better ratio than this project
usually finds, and the reason is that §5.2.2's own repair prompted the previous
batches to look.**

---

## 7b. The one that is available. **TAKEN.**

### The clip floor is a dimensionless MULTIPLE of the absolute round-trip cost

Row 30's derivation, rearranged:

```
floor  =  absolute / ((t - proportional) / 10,000)
       =  absolute x K            where   K = 10,000 / (t - proportional)
```

***`K` is a pure number. It carries no currency, no share price and no FX
rate.***

**At the registered tolerance of 10 bp, in the commission-minimum regime:**

| Share price | Proportional | **`K`** |
|---|---|---|
| USD 30.84 *(the regime boundary)* | 0.271 bp | 1,028 |
| USD 43.79 | 0.252 bp | 1,026 |
| USD 75.00 | 0.233 bp | 1,024 |
| USD 150.00 | 0.219 bp | 1,022 |
| USD 500.00 | 0.210 bp | 1,021 |

***`K` spans 1,021 to 1,028 across the entire range: a spread of 0.7%.***

> **Taken: above USD 30.84 a share, the clip floor is `1,025 × the absolute
> round-trip cost`, to within one per cent, in whatever currency that cost is
> denominated.**

**At the measured absolute of USD 6.00 — USD 2.00 of commission minimum plus USD
4.00 of manual-spot FX — that is USD 6,150**, against the per-price table's USD
6,135 to USD 6,221. *One number replaces a column.*

**The regime boundary is USD 30.84**, from `t ≥ 302.01/p + 0.206`. **Below it the
rate regime governs and `K` is not constant**, because the proportional term
`102.01/p` is then large and varies fast. *That limit is stated rather than
smoothed: the move works on the upper two thirds of the admissible price range
and not on the lower third.*

### And `K`'s sign is the reachability test, which was a separate branch

```
K = 10,000 / (t - proportional)
```

| Case | `K` | Verdict |
|---|---|---|
| proportional 0.25 bp, t = 10 | 1,026 | a floor exists at 1,026 × absolute |
| proportional 2.54 bp, t = 10 | 1,340 | a floor exists |
| **AIM, proportional 10.3 bp, t = 10** | **undefined** | **`clip_floor_unreachable_at_any_size`** |
| **UK Main Market, proportional 61.4 bp, t = 10** | **undefined** | **`clip_floor_unreachable_at_any_size`** |

***So the refusal is not a separate branch bolted onto the derivation. It is the
denominator going non-positive.*** `sizing.py` tests `proportional >= tolerance`
and returns the code, which is the same condition written the other way round.
**The dimensionless form makes the refusal fall out of the expression that
computes the answer**, which is what a good form does.

---

## The two where the move is NOT available, and the reason is the same one

**§4.4's ATR bounds and §6.7's band-versus-floor check both compare a risk
budget denominated in GBP with a position cost denominated in USD.**

```
ATR_max  =  risk_budget / (multiplier x floor)
            ^ GBP, 0.75% of GBP 100,000        ^ USD
```

***No bound removes that. It is a genuine currency crossing, and it is §6.9's
object rather than an assumption to be replaced.*** The book's reference equity
is sterling and its positions are dollar-denominated, so **an FX rate is part of
what those quantities ARE**, not a convenience someone reached for.

**What replaces the assumption there is not a bound but a ROBUSTNESS RANGE**, and
one is already published: the floor stays inside §6.7's band for **any USD/GBP
rate between 0.410 and 3.283**. *That is the honest substitute when the
dimensionless move is unavailable: state the interval over which the conclusion
survives, rather than a rate over which it was computed.*

**Recorded so the pattern is not over-applied.** *A project that has just found a
good move will find it everywhere, including where the thing it is removing is
not an assumption but a fact about the world.*
