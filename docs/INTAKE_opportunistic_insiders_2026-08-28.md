# Evidence-lane intake: the opportunistic-insider subset

**28 August 2026. §3.6 paper intake, `origin = paper`, `evidence_tier = quantified`.**

***This is the first intake in this project's history to put a number on BOTH
sides of §3.6.3 check 1.*** Every prior candidate either had no claimed effect
(the discovery layer emits pointers, which carry none by construction) or had
one that no cost table could be applied to. **Check 1 has therefore never
actually run.** It runs here, and what it returns is a bracket that straddles
zero.

---

## 1. The intake records, against §3.6.2's schema

| Field | Primary | Corroborating |
|---|---|---|
| `paper_id`, `authors`, `venue` | Cohen, Malloy and Pomorski, *Decoding Inside Information*, **Journal of Finance** 67(3) 2012 | Ali and Hirshleifer, *Opportunism as a Firm and Managerial Trait*, **Journal of Financial Economics** 2017 |
| `publication_status` | journal | journal |
| `sample_market`, `sample_population` | **US listed equities**, all Form 4 filers | US listed equities |
| `event_definition` | *An insider purchase by an insider whose trading is not on a predictable calendar* | *A purchase by an insider identified as opportunistic through the profitability of trades prior to quarterly earnings announcements* |
| `event_class` | `insider_dealing` | `insider_dealing` |
| `claimed_effect` | **82 bps per month, value-weighted abnormal return, opportunistic subset. Routine subset approximately zero** | **over 100 bps per month, value-weighted four-factor alpha** |
| `claimed_horizon_sessions` | ~21 (monthly) | ~21 (monthly) |
| `cost_treatment` | **`gross`** | **`gross`** |
| `direction_conditionality` | Purchases informative; the routine/opportunistic split is the conditioning variable, not direction | Effect present on both sides; **only the long leg is admissible here** (§4.1 direction restriction, cash account) |
| `replication_status` | **`replicated_closed`** | Three independent studies on overlapping US samples: CMP 2012, Ali and Hirshleifer 2017, Cline et al. 2017 (*Financial Management*), plus Biggerstaff et al. 2020 (*JCF*) on trade duration |
| `family_mapping` | **`existing:insider_dealing`** — a *proposal*; §3.6.4's diff decides | as primary |
| `origin` / `evidence_tier` | `paper` / **`quantified`**, computed: effect, horizon and population all populated and all `verified_secondary` | as primary |
| Provenance | **`verified_secondary`** on every claim field: abstracts read, published tables **not** read in this tree | **`verified_secondary`** |

**Provenance is `verified_secondary` and not `verified_primary`, and that
matters.** The figures are read from abstracts, not from the papers' own tables.
§14 cannot be signed while a `recollection` feeds a gate, and these are a tier
above that — but **the FGR precedent is directly on point**: the lane's first
intake found a recollected claim wrong in two places once the tables were read.
**Reading the CMP and Ali tables is a named prerequisite before any parameter is
taken from them.**

---

## 2. Check 1, cost survival. **The instrument's first real run**

`claimed_effect` × decay ladder, against the **19.5 bp midpoint break-even** for
the best US ADV bucket at GBP 5,000 notional (§5.2.2), at h = 21. On a
GBP 100,000 book at §6.7's gross cap, **one basis point of net edge is worth
GBP 120 a year at h = 21**.

| Candidate | Gross | ×0.93 costs | ×0.72 ex pre-2005 | ×0.50 post-publication |
|---|---|---|---|---|
| **CMP 2012**, 82 bp/mo | | net **+56.8** | net **+39.5** | net **+21.5** |
| **Ali & Hirshleifer 2017**, 100 bp/mo | | net **+73.5** | net **+52.5** | net **+30.5** |
| **Chen 2019 post-pub band**, 10–20 bp/mo | | net **−10.2 to −0.9** | net **−12.3 to −5.1** | net **−14.5 to −9.5** |

### The verdict, and it is a refusal to conclude rather than a pass

> ***On the papers' own figures the candidate clears cost survival at every rung
> of the ladder. On the post-publication band that Chen (2019) measures across
> 120 anomalies, it fails at every rung.*** **The bracket straddles zero and
> which end is right is a measurement, not an argument.**

**Chen's finding is the bear case and it is not a weak one**: post-publication,
the average equal-weighted long-short anomaly nets **−3 bps per month** after
costs, and the *strongest cost-optimised* anomalies net only **10–20 bps**. CMP
was published in 2012, so fourteen years of post-publication decay sit between
the sample and today. **The ×0.50 rung is the paper's own answer to that and
Chen's band is a harsher one.**

**What separates the two ends is measurable and is already on the register**:
§13 row 12 (the joint qualifying-and-tradable rate) and row 13 (the capture
rate). *That is the whole point of the screen returning a bracket rather than a
verdict.*

### One horizon consequence that falls straight out of the arithmetic

At h = 21 the programme hurdle (row 41) is **75 bp net per trade**, and this
candidate nets 21.5 to 73.5. **It does not clear a realistic hurdle at h = 21 on
any rung.** At h = 5 the same hurdle is **17.9 bp**, and §5.4 admits insider
purchases at {5, 21}.

> ***So the family is tradable at h = 5 or not at all***, which is not a
> preference but an arithmetic consequence, and it vindicates §0.9's
> reorientation to short horizons on a ground §0.9 did not have.

The h = 5 evidence is separate and stronger: §0.5 already carries **230 bp raw
over five sessions** on post-SOX US filings and **462 bp** on the UK
materiality-filtered panel.

---

## 3. Checks 2 to 5

| # | Check | Result |
|---|---|---|
| 2 | **Population overlap** | **FLAGGED, not failed.** `measured_on` is US listed equities on **value-weighted** portfolios; `tradable_on` is US listed above USD 10.42 and USD 40,312 ADV. **Value-weighting concentrates the effect in larger names**, which is favourable for tradability and means the equal-weighted version is not established. *Importing a value-weighted magnitude to an equal-weighted book of 16 names would repeat §0.9's error exactly.* §13 row 12 measures the joint rate |
| 3 | **Event observability** | **PASS.** EDGAR Form 4, `subscribed`, self-corroborating, per-item timestamps. The filing *is* the event |
| 4 | **Horizon admissibility** | **PASS.** Monthly maps to h = 21; §5.4 admits `insider_dealing` at {5, 21}. See the h = 5 consequence above |
| 5 | **Evidence quality** | **`replicated_closed`, routes NORMALLY rather than advisory-only.** Three independent published studies on overlapping US samples, two in top-tier journals with 620 and 176 citations |

---

## 4. What this intake produces, per §3.6.1's four landings

**A restriction, and it is already specified.** §5.4.1 carries an
**opportunistic-versus-routine advisory flag**, defined as: *a purchase is
routine where the same insider filed a purchase in the same calendar month in
each of the three preceding years; otherwise opportunistic.* **That is CMP's own
classification, already in this specification, currently advisory.**

The literature says the alpha is **entirely** in the opportunistic subset and
the routine subset is **approximately zero**. Under §3.6.4's fork, restricting
the family to the opportunistic subset **strictly shrinks the hard-reachable
tuple set**, so it classifies as a **restriction** and lands as a register item
at the next version rather than as an Annex A.1 extension.

***It is NOT adopted here.*** The parameter it would need — whether the flag
becomes a hard restriction or stays advisory — is a design-segment measurement
with its kill criterion written first, in the idiom of §13 rows 16 and 17. The
paper's estimate is the prior, never the answer.

### The constraint nobody has noticed, and it binds on the archive

**CMP's classification requires three years of prior filing history per
insider.** An insider cannot be labelled routine or opportunistic until three
preceding years of their own Form 4 flow have been observed.

> ***The archive opens 2023-01-01 and spans two to three years.*** So the
> classification consumes the front of the archive before it can label anything,
> and the first tradable signal cannot precede 2026 on an archive that opens in
> 2023. **This is a hard constraint on breadth, on the design segment and on the
> evaluation window, and it is not recorded anywhere in §13.**

*It also cuts the other way and should be said: the classification is
computable **forward** from today at zero cost, because Form 4 history is free
and complete on EDGAR back well beyond three years. What it costs is archive
span, not money.*

---

## 5. What this intake does NOT do

It admits no family, creates no grammar row, supplies no parameter, sizes no
position and authorises no capital. **It moves the insider family from *a family
with a documented effect* to *a family with a documented effect, a stated
population, a cost bracket and a named measurement that would settle it*.**

That is the whole of what an intake is for, and it is the first time the lane
has produced one.
