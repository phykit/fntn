# The delisting register, and the survivorship bound written BEFORE any backtest

**27 August 2026. Binding-path step 5's free half, and `§12.1` P141.**

***There are zero backtests. That is the only moment at which writing this down
costs nothing and proves anything***, and it is why the method below is fixed
now rather than when there is a number it could be tuned against.

---

## 1. What was built, and what it cost

**Nothing.** Forms 25, 25-NSE and 15 are filed on EDGAR and EDGAR is free.

> ***You cannot get survivorship-free prices for nothing. You CAN get, for
> nothing, a complete list of what is missing.***

| | |
|---|---|
| Span | **2023-01-01 to 2026-08-27**, read from the registration's `archive_opens` and **not chosen here** |
| Quarters read | **15**, 2023 Q1 to 2026 Q3, inclusive at both ends |
| Register | `archive/delistings/register.tsv`, 9,943 rows, 928 KB |
| Fetch log | `archive/delistings/_fetch.tsv`: URL, timestamp, byte count and SHA-256 for each of the fifteen indices |

### The counts, and they are counts rather than estimates

| Form | Filings | Kind |
|---|---|---|
| **25** | **455** | ***DELISTING***, filed by the issuer |
| **25-NSE** | **6,944** | ***DELISTING***, filed by the exchange |
| 15-12G | 1,867 | deregistration |
| 15-15D | 587 | deregistration |
| 15F-12B | 63 | deregistration |
| 15F-15D | 16 | deregistration |
| 15F-12G | 11 | deregistration |
| **15-12B** | **0** | deregistration. ***Zero, and the form is kept on the list rather than removed***: a form that returns nothing is a reading, and dropping it would hide that the reading was taken. Checked against 2024 Q2's raw index independently of the register |

> ### ***M = 2,781 distinct delisted issuers.***
> **The missing set's denominator, and it is the number nobody had.**

**7,399 delisting filings against 2,781 issuers**, because a name can be removed
from more than one listing. **The denominator the bound needs is a count of
NAMES**, so the distinct-issuer count is what enters the arithmetic and the
filing count is reported beside it, never instead of it.

### A Form 15 is NOT a delisting, and conflating them would flatter

**Deregistration usually follows a delisting and does not entail one.** A Form
15 can be filed by a company that was never listed, by one going private, or by
one whose holders fell below the statutory threshold. **Adding 2,544
deregistrations to 7,399 delistings would inflate M**, and an inflated M makes
the bound below look *tighter* than it is.

***A bound that errs towards comfort is worse than no bound.*** The two kinds
are recorded under their own form codes and the code that reads them keeps them
apart (`Register.delistings` / `Register.deregistrations`, and
`test_the_delisting_register_never_sums_deregistrations_with_delistings`).

---

## 2. ***THE BIAS-BOUNDING METHOD.*** Pre-registered, 27 August 2026

**Fixed before frozen design 1 exists, before any archive exists, and before
any backtest has produced a number.** *Every clause below is stated so that a
later reader can check the method was not chosen to suit a result.*

### 2a. The coverage fraction, reported on every run

Let **N** be the number of distinct names the archive covers over the span and
**M** the distinct delisted issuers in the same span, **M = 2,781** as measured
above.

> **coverage = N / (N + M)**

**This is a reported field on every run and never a correction.** It states
what fraction of the population that existed the result was computed on. *A
stated coverage fraction is not a repair; it is the difference between a biased
number and a biased number that says so.*

***It is NOT SCORED today and that is the honest output.*** There is no
archive, so there is no **N**, and `Register.coverage_fraction` returns `None`
rather than a number. **A coverage fraction computed against an assumed archive
size is the exact defect this register exists to prevent, wearing the
register's own clothes.**

### 2b. The worst-case expectancy bound, stated as arithmetic

Let a backtest report mean per-trade return **r̄** over **n** trades on the
**N** covered names.

**Assumption S1, the signal-rate assumption.** *The strategy would have
signalled on the missing names at the same per-name rate as on the covered
ones.* The implied extra trades are

> **m = n × (M / N)**

**Assumption S2, the outcome assumption.** *Every one of those m trades
returned **−100%**.*

Then the bounded mean is

> **r̄_bound = (n·r̄ − m) / (n + m)**, which reduces to
> ### **r̄_bound = (r̄ − M/N) / (1 + M/N)**

**with r̄ expressed as a decimal fraction, not in basis points.** *The reduced
form is written out because it makes the whole bound a function of one
measured ratio, M/N, and one reported result.*

### 2c. ***THE DECISION RULE, and it is pre-registered***

> **If `r̄_bound` still clears δₘᵢₙ, survivorship is not a live objection to
> that result.**
>
> **If it does not, the result is NOT defended by this method**, and the gap
> `r̄ − r̄_bound` is the size of what a survivorship-free price source would
> have to buy.

**δₘᵢₙ is §14's registered floor, 15.7 bp today**, and the comparison is made
against whatever value the register carries **at the time the backtest runs**,
read from the parameter object and not from this document. *A floor copied into
a document goes stale; a floor read from the register cannot.*

### 2d. What this bound IS, and what it is NOT

| | |
|---|---|
| **It IS** | a hard lower bound **under S1 and S2**, computable from two counts and one reported mean, with no free parameter and nothing fitted |
| **It IS** | conservative in its outcome assumption. **−100% is worse than the §4.4 stop** would ordinarily allow, and it is chosen precisely because **a delisting can gap through a stop**: a halt followed by removal leaves no session at which the stop could fill |
| **It is NOT** | a correction. Nothing is added back, no return is imputed, and no result is adjusted. **The biased number stands and is reported beside its bound** |
| **It is NOT** | a defence of S1. *Names heading for delisting may be MORE likely to trigger a distress-adjacent signal than the covered population, in which case m is understated and the bound is too generous.* **Named here rather than discovered later** |
| **It is NOT** | tight. See §3 |

---

## 3. ***THE TWO WAYS THIS BOUND COULD BE LOOSENED, PRE-COMMITTED AGAINST***

***Both would move the result in the strategy's favour. Both are named now, so
that taking either later is a visible act rather than a refinement.***

### 3a. Restricting M to the tradeable universe

**M as measured is EDGAR-wide.** The 6,944 `25-NSE` filings include **ETFs,
warrants, units, notes, preference shares and SPAC securities**, and §5.4.1's
grammar is **long-only common equity on NYSE and Nasdaq**. *So M is certainly an
over-count of the names this strategy could ever have traded, and the bound is
correspondingly loose.*

> ***Any restriction of M is a specification version and takes a `§12.1` row.***
> The restriction rule must be **written and registered BEFORE it is applied**,
> and **the unrestricted M = 2,781 is reported for ever alongside any restricted
> figure.**

*The reason is P80's, not pedantry: a filter on the missing set is a parameter
that moves the bound, and a parameter chosen after seeing which side of δₘᵢₙ the
bound lands on is a fitted parameter wearing a restriction's clothes.*

### 3b. Replacing −100% with an empirical delisting return

**CRSP publishes delisting returns and the true mean is not −100%.** Using one
would tighten the estimate and loosen the bound.

> ***It requires a purchase, it is on no Annex A.1 row, and it is not assumed
> here.*** **The −100% stands until a delisting-return source is acquired and
> registered**, and if one ever is, the bound computed under it is reported
> **beside** the −100% bound and never in place of it.

---

## 4. What is retained, and the Class II weakening stated plainly

**The register is retained. The fifteen quarterly indices are not**, at roughly
5.5 MB each and 80 MB in total.

***Class II's invariant says any input to a decision must be retrievable by
commit at the moment the decision is taken, and these are not.*** What stands in
its place is the fetch log: **URL, retrieval timestamp, byte count and SHA-256
digest** of every index read, so a later reader can re-fetch and establish
byte-identity, or establish that it has changed.

> **That is weaker than retention and it is named as weaker. It is not offered
> as equivalent.**

*If the operator would rather pay the 80 MB, the change is one line and the
argument for it is Class II's own.*

---

## 5. §0.6, applied explicitly

| Element | Added? |
|---|---|
| Gate | **no** |
| Family | **no** |
| Grammar row | **no** |
| Cost tier | **no** |
| Sizing input | **no** |
| Feed | **no.** *The closest call on the table, and the answer turns on direction:* a feed supplies material the funnel acts on. **This register supplies a count of what is ABSENT**, it admits nothing, and **it cannot make a name tradeable** |
| Field the funnel reads at decision time | **no** |

> ***ANSWER: procedure.*** A ledger of absence and a bound computed from it.
> **§0.6 does not block it.**

**And the containment is architectural rather than conventional.** The module
sits at **`fntn.data`**, which is on `fences.FORBIDDEN_TO_DISCOVERY`, and it is
there *precisely so the import fence has a name to match*: **a delisting is an
OUTCOME**, and an agent able to read which names left the market could select
mechanisms on survival. **The same content under `fntn.scanner` would have been
reachable by `discovery.py` without tripping any fence**, because the fence
matches module names and would have had no name to match.

> ***A consequence worth stating: `assert_reverse_import_fence` returned
> `NOT_APPLICABLE` until today, none of the forbidden modules existing. This is
> the first one that exists, so the reverse fence now walks a real closure and
> returns `CLEAN`.*** *A fence that has never had anything to walk is a fence
> nobody has tested.*

---

## 6. What this does NOT unblock

**Binding-path step 2's archive identity and span is not closed by this.** The
register bounds a survivorship bias in an archive that does not exist; it
supplies **M** and nothing else. **N, and therefore the coverage fraction and
therefore the bound, wait on the archive.**

*What changed today is that the number nobody had is now on the record, free,
and the method that will consume it is fixed before there is anything to tune
it against.*
