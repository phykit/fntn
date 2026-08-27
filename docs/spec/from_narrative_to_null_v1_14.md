# From Narrative to Null: A Falsification-First Architecture for Trading Ideas Extracted from Financial Media

**Working paper, draft v1.14, August 2026. Fourteenth specification version; no design frozen yet.**

*This document is standalone: it supersedes all prior versions, drop-in files, review artefacts and register documents, and can be read without them. As of v1.12 it is also the **register of record**: each register entry's authoritative specification is its change-log row in §12 plus the governing section text (§12.8).*

***v1.14 does one thing, and withdraws one figure.*** *The one thing is a **matching rule for bare tickers** inside §3.7.3's entity fence. v1.13 made the fence a lookup and handed it the security master's names and tickers as a single set; 7,268 of the 10,388 US tickers are four characters or fewer, and the loader applied its minimum-length and lexicon filters to issuer names only, so `Note`, `Are`, `For`, `Law`, `Help` and the single letters entered the fence as tradeable entities, where sentence-initial capitalisation was enough to trip them. Over the thirteen documents of the US pre-archive corpus that is 257 hits across 41 distinct tokens, essentially all false. A bare ticker is now matched **only in the shape a symbol takes, all capitals and three characters or more**, with names and tickers held in separate lookup sets because sixty-five US issuers have a one-word name identical to their own ticker. **The rule takes a false negative, and the cost is stated rather than implied**: a bare ticker written in lower or title case is now invisible, so `purchases at Aapl` passes where `purchases at AAPL` is refused. That cost was taken over the alternative, a common-word filter on the ticker set, which would have made at least ninety-five real US issuers invisible in capitals as well and would still have left five legal-citation tokens needing a lexicon row.*

*The withdrawn figure is v1.13's **"zero false positives and zero false negatives"**. It was measured against six plants defined inline in a shell that was never committed, and it is not reproducible from the repository; an error rate that cannot be reproduced is an assertion about a fence rather than a measurement of one. The labelled set now sits in the tree, the reading is locked by tests, and the replacement is stated **per arm, and the two arms are not the same kind of thing**: the drawn class-level arm refuses **0 of 36 (0%)**, against **3 of 36** on the fence as v1.13 left it, whilst the authored probe arm reports **5 of 6 routes closed**, the open one being a title-case bare ticker. Two repairs sit behind that. The measuring harness first divided both rates by the union of the arms, reporting one probe of six as 2%, a figure divided by a population neither error can be drawn from, inside the instrument that measures the fence. Correcting the denominator to 1 of 6 left the **frame** wrong, which is the more expensive half: **the six are authored probes, one per named route into the fence, so they are chosen and not sampled and what they yield is coverage rather than a rate.** A percentage over a chosen set estimates nothing, and doubling the probe set to twelve routes would halve it whilst leaving the fence untouched. The probe arm therefore names its open routes and prints no percentage. §13 row 21 remains **PROVISIONAL** at 42 subjects against the 200 it specifies, and its labels carry provenance `model_clerk`: they are the clerk's classifications against the taxonomy, not the operator's hand labels, and ratification is outstanding.*

*v1.13 specified the **agent discovery layer** (§3.7), made intake **fail-fast** with an audit fraction against the censoring that induces, settled the **exclusivity construction**'s default as `cross_market`, added the **random-mechanism control arm** to §Σ.4's instruments, rebuilt the **entity fence as a lookup** after a trace refuted its pattern-only first design, and landed two errata on §0.5's basis-point conversion and on the differing notional bases of §0.10's and §5.2.2's break-even tables. Its full row set is §12.2. v1.12 split an over-coarse constraint into a **manual-observation tier**, decided pointer verdicts by **equivalence against a registered abandonment threshold**, added design-segment search as a **fourth counting family** with a computed directive budget, made a plain-language **rejection summary** mandatory on every refusal, and demoted the beta hedge to a **measurement** after the operator's eligibility for futures dealing was checked and failed. v1.11 extended the evidence lane to a **pointer tier**, a second origin and an unclassified branch mapped by hand rather than refused. v1.10 landed the **literature lane** (§3.6), its **first verified intake** (Fidrmuc, Goergen and Renneboog, 2006) and the **review harness** (§9.5). (A drafting-process fault meant v1.11 circulated under a v1.10 header; §12.7 records it, and the review harness now checks the header against the change log.)*

***No apparatus is added in this version either; §0.6 remains armed and there is no second amendment.*** *v1.14 adds none of its own: it **narrows a matching rule inside an existing fence** and **corrects a denominator in the instrument that measures that fence**, adding no gate, no family, no grammar row, no cost tier, no feed, no sizing input and no field the funnel reads at decision time. A lexicon row and a rule that refuses more narrowly than it did are both still refusals.* *The discovery layer is procedure at the intake surface: the runner, the screen, the three fences, the reuse ledger and the rejection summaries are of the same class as §9.4's trace harness and §9.5's review harness, and they add no gate, no family, no grammar row, no cost tier and no field the funnel reads at decision time. Two things in it are apparatus and are treated as such: a **production ingestion adapter for a discovery corpus** and **standing automation of the layer**, each taking an Annex A.1 row with its dependency named. §12 maps every change. §14 is the freeze record, still a form.*

---

## Σ. The approach in summary

*This section is orientation, not specification. Every claim in it is discharged by a numbered section later, and where the two disagree the numbered section governs.*

### Σ.1 The inversion

A language model reading financial media can be used as an **analyst** or as a **clerk**. As an analyst it selects parameters, judges magnitudes and issues verdicts, and it hallucinates numbers, leaks hindsight through memorised price history, and cannot be audited, because the reasoning that produced a number is not the number's provenance. As a clerk it does one thing: it turns unstructured text into structured fields against a fixed schema, and classifies those fields against a fixed taxonomy.

**This system uses the model only as a clerk.** Every number, date, threshold and verdict on the trading path is deterministic arithmetic over logged data, replayable byte-for-byte from the parameter hash. The model's output is an *input* to that arithmetic and never an authority over it. Where a regulatory form is field-delimited, even the clerk is replaced by a parser (§3.5.2).

The design consequence runs through everything: **the model classifies; the table decides.** It governs the anomaly taxonomy (§5.4), peer-set construction (§4.2), the amendment fork in the literature lane (§3.6.4), and the review harness's own adjudication (§9.5).

**Every claim made for the clerk above holds on the trading path and stops at the trading path's edge.** The discovery layer specified in §3.7 is the first place in this architecture where a model *selects* rather than classifies, and the paper should say so in the section that makes the opposite claim rather than leaving a reader to discover the exception in §3.7.

The containment is not that the agent is somehow prevented from selecting; it is that **selection cannot reach capital by any route**. A discovery agent's output is a proposal; a proposal that survives ingestion becomes a pointer-tier intake record; a pointer's only reachable output is an observation directive; a directive runs at zero capital; and a surviving directive re-enters as a quantified intake with machine provenance, taking the ordinary route through §3.6.4 and Annex A.1 behind §0.6. Five stages, each of which the manuscript already specifies, and none of which the discovery layer is permitted to shorten. What §3.7 adds is the volume; what it must not add is a shortcut.

### Σ.2 The pipeline, end to end

| Stage | What happens | Model involved? |
|---|---|---|
| **Source ranking** (§3.1–3.4) | Streams treated as hypotheses, ranked by regulatory status then by the exogeneity of the publication clock; scored on four measured axes and allocated by Thompson sampling | No |
| **Ingestion** (§3.5) | Four timestamp anchors extracted with provenance; running documents excluded from anchor roles; ingestion lag measured and gated | Anchor extraction only |
| **Extraction** (§3.5.2) | One schema-enforced call, temperature zero, cached by content hash, with per-field accuracy floors and suspension on failure | Yes: this is the clerk's whole job |
| **Evidence intake** (§3.6) | Papers *and the operator's own hypotheses* enter as family-level evidence, never as items; a merit screen that refuses to score on unverified provenance; amendments classified by reachable-set diff; unquantified ideas enter a **pointer tier** whose only output is a directive naming the feed that would exercise them | Extraction only |
| **Grammar** (§4) | Candidates instantiated only as tuples from a closed, pre-registered grid; reachability published before evaluation | No |
| **Gate stack** (§5) | Eight sequential gates, hard or advisory, each writing the size of the set it measured beside its verdict, each kill carrying a named reason code and a resurrection predicate | No |
| **Verification** (§6) | Expectancy against block-permutation and buy-and-hold nulls, minimum samples below which gates refuse, three-family multiplicity control, coarse shrink-only sizing | No |
| **Validation** (§7) | Funnel depth versus forward return across the *entire* intake, with an equivalence-tested placebo | No |

### Σ.3 Four control surfaces, and what each is for

1. **Refusal semantics.** Wherever an input is missing, below a sample floor, or carries unverified provenance, the consuming check **refuses to score** rather than guessing or falling back to a default. A refusal is a state with a reason code and, from v1.12, a plain-language rejection summary, not an absence. This runs from Gate 5's conditional-sample floor (§5.6) through §6.7's source-lead multiplier to §3.6.3's merit screen.
2. **Population declaration.** A verdict answers *did what I measured pass*, never *did I measure what I said*. Every figure states the set it was measured on, and any mismatch between the population an effect was measured on and the population the system can trade is flagged at the rule (§0.9, §6.6, §3.6.3).
3. **Provenance tags.** Every load-bearing external claim carries `verified_primary`, `verified_secondary` or `recollection`, at row level where it sits in a table. §14 cannot be signed while a `recollection` tag feeds a gate, a boundary or a published table.
4. **Mechanical counting.** Specification versions, configurations and search paths are counted by a hash over the parameter object rather than by the author's account of what changed, because a rule adjudicated by intent gets adjudicated in the direction that flatters the denominator (§0.3).

### Σ.4 The falsification instruments

The system is built to be *killed*, and names in advance what would kill it:

- **§7.1: the headline.** Spearman association between funnel depth and forward return across accepted, rejected, zero-sized, explore and shadow cohorts. If depth does not order returns, the funnel is not doing anything.
- **§7.5: the placebo.** Timestamp randomisation evaluated by **equivalence**, so it fails for want of power rather than passing by it.
- **§7.4: the control arm.** The same catalyst posed to an unconstrained model, to test whether the constraints are earning their cost.
- **§3.7.5: the random-mechanism control arm.** Mechanisms drawn uniformly at random from the same reachable grid the discovery agents search, registered and scored identically, so the difference between the arms *is* the selection effect. If two one-sided tests demonstrate that difference lies within ±δ, the discovery layer is refuted and switched off rather than tuned.
- **§7.6: the shadow frontier.** Zero-capital verdicts on candidates below the tradability floor, testing the liquidity–asymmetry premise and the microcap question at no risk.
- **§0.6: the ordering rule, binding.** Until §7.1 and §7.5 report, **no version may add capability.** This is the constraint that stops the architecture growing indefinitely on unfalsified premises, and it has been amended exactly once, on the record.

### Σ.5 What it claims, and what it does not

It does not claim returns. At £100,000, even excellent alpha is a few thousand pounds a year, less than the engineering time. **The product is the ledger**: every unit of capital withheld was withheld for a stated reason, and the reason is machine-checkable. If the stream contains nothing exploitable, the correct output is an empty accepted book, visibly empty.

### Σ.6 Where the design currently stands

**Fourteen specification versions. Zero frozen designs. Zero backtests run. Zero trades.** No gate has been exercised against calibrated thresholds, so the absence of signals to date is structural, not evidential. The binding path is short and ordered: verify the commission schedule (§13 row 1), run the trace harness (§9.4) to its stopping rule, populate §13, hash the parameter object (that act creates frozen design 1), then run the retrospective deployment and let §7.1 and §7.5 return a verdict.

---

### Σ.7 One page: what this system is trying to achieve

**The problem.** Financial media contains occasional genuine information inside a stream of hindsight narrated as foresight. Language models can read all of it. But a model used as an *analyst* hallucinates parameters and leaks hindsight through memorised price history, and a media corpus is saturated with theses published after the move they describe.

**The design answer.** The model is a **clerk**: it extracts structure and classifies against a fixed taxonomy, and nothing else. Every number, date and verdict in the trading path is deterministic arithmetic on logged data, replayable byte-for-byte. Candidates are drawn from a **closed, pre-registered grammar** and pass a **sequential gate stack** (data sanity, cost viability, staleness, prior art, correlation, regime, expectancy against permutation nulls, robustness under costs), where every kill carries a named reason and a machine-checkable resurrection predicate.

**What it claims and what it does not.** It does not claim returns: at £100,000 even excellent alpha is a few thousand pounds a year, less than the engineering time. The product is the **ledger**, and the headline measurement is whether **funnel depth orders forward returns**, guarded by a timestamp-randomisation placebo that must positively demonstrate no association survives randomised time. If the stream contains nothing exploitable, the correct output is an empty accepted book, made visible.

**What v1.8 changed, and what v1.9 and v1.10 do to it.** v1.8 reoriented the grammar towards breadth at short horizons and added an insider-purchase catalyst family, under a one-time amendment to the ordering rule. v1.9 leaves that direction intact and corrects its arithmetic: the effect size was measured on open-market discretionary insider purchases while the volume estimate counted every regulatory notification, and the two populations are not the same. Alongside that, tracing exposed a class of defect no audit had found: **rules that were wrong because nothing had ever reached them**: an exit rule that fired on its own entry event, a universe rule with no enforcing gate, a permissive taxonomy default that became a fast lane once the horizons moved, a forward-catalyst rule with a ceiling and no floor. v1.10 adds the route by which published research may amend a family (§3.6) and runs a mechanical review harness over the result (§9.5); v1.11 extends the lane to the operator's own hypotheses through a pointer tier; v1.12 adds the containment that extension demanded and demotes the beta hedge to a measurement.

**What happens next, in order.** (1) Verify the commission assumption against a named broker schedule. (2) Build the trace harness (§9.4) and run it to its stopping rule. (3) Fix the archive, partitions, roster and universe; complete §13's calibrations; hash the parameter object, and that act creates **frozen design 1**. (4) Run the retrospective deployment. (5) The funnel-depth association and the placebo return verdicts. Until they do, no capability may be added.

---

## 0. Decisions, stated before the paper resumes

### 0.1 The protective stop, and why sizing and honesty were one problem

Early drafts sized stopless fixed-horizon positions by a 95th-percentile adverse move, making any asset above ~1.43% daily volatility unsizable at h = 63 at this capital. The replacement, a flat 4.0 × ATR(14) stop, was breached before the horizon roughly 48% of the time at h = 63, silently converting the family into a stop-out family. These are two horns of one constraint: a stop wide enough to preserve a 63-session thesis is ≈1.6·σ·√h, the denominator removed for being too large to size. **At £100,000, h = 63 and 3% daily ATR, no stop both preserves the thesis and clears the minimum clip.**

The decision is to refuse rather than fudge: the stop scales with the horizon to hold breach probability constant (§4.1.1), and cells that cannot then be sized are declined by name (§4.4). The constructive corollary: the same arithmetic that closes long horizons opens short ones (§0.9).

### 0.2 The event-anchored family estimates cross-sectionally

Estimating an event family on one asset's history cannot meet any minimum sample. The family is estimated on a **pre-registered peer set** (§4.2): industry first, then listing market, catalyst type and notional bucket, membership and classification vintage read as of the observation timestamp. Gate 6 therefore measures a population base rate, not an asset-specific edge. Pooling induces dependence, which §6.4 handles. A reader who believes drift is asset-specific should reverse this and expect the family unusable at this capital.

### 0.3 Specification versions are counted; a design is frozen only when complete

A **specification version** is any change to a grid, threshold, convention, gate membership, anchor assignment, cost tier, sizing rule, admissibility rule, input-source choice, extraction schema field, or the estimation span of a derived artefact. Versions are the trial family §6.4 counts. **This document is the fourteenth.**

A **frozen design** is a version whose parameter set is *complete*: every value populated, canonically serialised, hashed. **No design has yet been frozen; the count is zero.** **Initial calibration completes a freeze rather than opening a design**: populating §13 is the act by which v1.14 becomes frozen design 1.

Boundary cases: a correction to a *justification* is not a version; a correction to a *rule* is, however small; an artefact recomputed from unchanged constants is not a version, recomputed on a different estimation span it is (§9.1). The classification is mechanical, because a rule adjudicated by intent gets adjudicated in the direction that flatters the denominator, an error this paper's author committed once, between v1.7 and v1.8, and records here.

### 0.4 The book is the automatic-plus-manual population

Escalated candidates the operator accepts **trade**; the deployed book is automatic-plus-manual. The **research record** replays byte-for-byte; the **book** does not, and the unreplayable share of positions and open risk is continuously displayed. Manual acceptance writes a hashed checklist artefact (§5.1.1). A reader who wants no discretionary channel closes it by making manual acceptances non-trading.

### 0.5 The economics are a hypothesis, and one now has a mechanism behind it

**Per-trade break-even** (conservative / midpoint, £5,000 notional): 22.5/19.5 bps in the most liquid AIM or US bucket, 312.5/212.5 in the least; UK main-market longs add 50 bps stamp duty, from which **AIM is exempt**. **Documented drift**, single 63-session leg: ~6 bps in the most liquid quintile, ~365 bps in the most illiquid, and transaction costs consume 70–100% of the illiquid end's paper profits (Chordia, Goyal, Sadka, Sadka and Shivakumar, 2009), because **illiquidity is what sustains the drift**. ***Recomputed 27 August 2026 (P111): **≤ 20.0/17.0 bps** in the most liquid bucket and **≤ 310.0/210.0** in the least, every figure 2.5 bps lower, the assumed 12.5 bp fixed cost being replaced by §13 row 29's registered 10 bp bound. **And the bucket is no longer "AIM or US": it is US.** AIM is excluded at the registered tolerance on COMMISSION, IBKR's UK schedule being 0.05% a side, which is 10 bp round trip on its own, so the stamp-duty exemption does not reach it.***

*Superseded, v1.13 erratum A: the sentence below read "10.5 bps per 63-session leg", which halved the conversion of 7 bps per month over three months. The stale wording is annotated here rather than rewritten silently, per §12.7.*

The generalisation: across 204 published anomalies, the average nets 4 bps per month after spreads and post-publication effects, the strongest 10, combinations around 20 (Chen and Velikov, 2023); the gross median for post-2005 non-micro stocks is 7 bps per month, i.e. **21 bps per 63-session leg** against a 22.5 bps cheapest break-even. **The corrected figure still fails that break-even**, by a narrower margin than this paper previously implied. **The published cross-sectional anomaly literature fails this system's own cost table**, which is why Annex A excludes that category.

**What survives, and the theory that explains why.** Insider purchase filings at h = 5 meet a documented five-day effect against an 82.5 bps midpoint break-even. **Every figure below names its population and carries a provenance tag at row level** (§14's precondition applies to published tables, not merely to prose):

| Measured effect, five sessions | Population | Sample | Provenance |
|---|---|---|---|
| ~230 bps | US insider purchases, filing-window | post-SOX US filings | `verified_secondary` |
| **462 bps** | **UK directors' purchases ≥ 0.1% of market capitalisation** | LSE, 1991–1998 | `verified_primary` (FGR Table) |
| 165 bps | UK directors' purchases, **all trades** | LSE, 1991–1998 | `verified_primary` (FGR Table) |
| −1.27% / −2.01% | **Pre-purchase run-up**, large panel / all trades | as above | `verified_primary` |

**The provenance vocabulary, and one addition.** `verified_primary` is read from the source's own tables; `verified_secondary` from a reliable report of them; `recollection` from neither, and it **blocks the freeze signature**. *New in v1.14 (P83):* `reconstructed_hash_verified` names an artefact that **is not the original** and that **reproduces the original's hash under the dataclass of the commit the record names**. Both halves bind. A reconstruction that does not reproduce the hash is a guess, and a hash reproduced under a different schema answers a different question, the hash being taken over the field set as well as the values. It is a positive verification and it is still not the artefact, so it **blocks the freeze signature exactly as `recollection` does whilst meaning something quite different**, and it may never make an intake quantified. It exists because the discovery layer's first registration hash, `890a80e3a8566837`, names an object that was overwritten before it was ever committed; `docs/REGISTRATION_HISTORY.md` carries it under this tag and under no other. **The classification is total over the vocabulary and tested to be**, because the freeze-blocking decision was previously a comparison against the single string `recollection`, under which a tag added here would have been read as harmless by every consumer that had never heard of it.

The two UK rows are the first figures in this paper measured on a UK population, and the gap between them is the point: **the 462 bps row is a materiality-filtered panel and the 165 bps row is not**, which is the same distinction §5.4.1's economic-substance test already draws. Importing the former's magnitude to a population selected like the latter would repeat §0.9's error. The negative run-up is logged rather than glossed: the typical qualifying purchase *follows* a price fall, which bears directly on whether Gate 2's staleness kill binds on this family at all (§5.3).

**Why the US and UK figures differ, and why that matters here.** Brochet (2010) reconciles low US filing-window returns in the pre-SOX literature with the high UK figures: purchase filings became significantly more informative once prompt disclosure was imposed. The operative variable is **disclosure speed**, which is direct evidence for anchoring capture on the regulator-stamped filing rather than on the trade (§4.3, §13 row 13). The mechanism is **extraction cost, not trading cost**. Bloomfield's incomplete revelation hypothesis holds that public and *usable* are different: the harder a fact is to extract from a filing, the less completely it is priced. Extraction cost is the one barrier a clerk reading filings at scale actually lowers. Mitchell and Pulvino's limits-of-arbitrage work supplies the complement: the participants who can see a mispricing often cannot hold the position long enough to collect it. Together these give the architecture a stated reason why filings should differ from the anomaly cross-section, which it previously lacked.

This does not raise any expected value. It explains where to look. The liquidity–asymmetry claim survives as a hypothesis tested by §7.6's shadow frontier at zero capital, and **the justification for the £100,000 book remains the ledger**.

### 0.6 Evidence of edge is not a downstream deliverable: BINDING, armed

**The rule.** While §7.1's funnel-depth association and §7.5's placebo remain unrun, no specification version may add apparatus. Remediation, governance, and the calibration sequence that completes the freeze proceed normally. The rule discharges when both instruments return a verdict, whatever it is.

**Why.** Every gate measures whether the *machinery* is correct; none can fail because the *signal* is absent. A system in which every check passes and no edge exists looks, from inside, exactly like one that works. Deferral is self-sustaining: each layer raises the cost of a negative answer.

**First amendment, August 2026, standing record.** v1.8 admitted a single enumerated one-time pre-run expansion: the alpha review's capability items. The cost was stated then and is restated now: **if the run returns null, those additions were layers on nothing.** The rule re-armed immediately.

**Neither v1.9 nor v1.10 takes a second amendment.** v1.9's changes were remediation of defects found by tracing, or decisions about *which population an existing rule reads*. v1.10's are of three kinds, and each is tested against the rule rather than asserted past it:

- **§3.6, the literature lane, is procedure.** A manual clerk call, a checklist and register entries are the same class of object as the pending-updates register itself. It adds no gate, no family, no field the funnel reads at decision time.
- **§9.5, the review harness, is procedure** on identical grounds, and is a *reviewing* instrument rather than a *trading* one.
- **§3.6.8's pointer tier is procedure, and the rule is enforced at the feed.** A pointer produces a directive; a directive over an already-ingested stream is a filter and adds nothing; a directive requiring a **new subscription is apparatus** (new ingestion code, a new parser, a new anchor-provenance question) and takes an Annex A.1 row with its dependency named. That is where §0.6 bites on this extension. v1.12 narrows the bite honestly: hand collection under §3.6.5's manual-observation protocol is not apparatus (it is the same class as §9.4's tracing), so what remains governed is machine ingestion and backfill depth, which is the part that genuinely is code in the funnel path.

**A second amendment, drafted and not taken: standing record, v1.12.** The one thing the evidence lane cannot have early is a new production feed. The amendment that would buy it is drafted here so that taking it is a §0 decision with its shape already fixed, rather than an improvisation: *a pre-paid budget of N new subscriptions before the instruments report, the N feeds chosen by the declined-directive distribution (§3.6.5) and named at the decision, each with ingestion cost and parser scope stated, the budget exhausted rather than extended.* Its cost is v1.8's cost restated: **if the run returns null, the feeds were plumbing on nothing.** It is not taken in this version, and nothing in the lane's design assumes it ever is.
- **The remediations** (two reason codes named, one field name settled, six cross-references supplied) are corrections to rules that already exist.

What the lane *produces* is governed, not exempt: extensions and new families take Annex A.1 rows with predicates and wait for the instruments, and the lane's own Tier 2 automation is apparatus and takes a row of its own. Predicates in Annex A fire and log throughout; acting on them waits.

**A note on the remediation exercise itself.** Tracing produced thirty-two register entries in three days and could produce more. It is productive, generates a visible artefact, and **moves the falsifying instrument no closer to running**: the same shape as the pattern this rule was written against. §9.4's harness therefore carries a pre-registered stopping rule, and §14 requires it.

### 0.7 Standing decisions on inputs the system does not calibrate

**(a) The archive is partitioned on corpus breaks, not proportions.** Boundaries sit at observable structural breaks *in the corpus* (source-composition shifts, platform-volume migrations, disclosure-timing changes) and at proportional points only where a documented search finds none ("we looked and found no break" and "we did not look" are different claims). The literature's canonical market break, end-2005 (Chen and Velikov, 2023), **falls outside a 2023+ media archive** and is cited as the rationale for regime logic, not as an operative boundary, with the corollary that this system is calibrated and evaluated entirely inside the post-collapse regime. Cost: a three-way split of a two-to-three-year archive leaves ~9–12 evaluation months. Underpowered and clean is preferred to powered and contaminated.

**(b) The benchmark panel reads published factor return series, per listing market.** Fama–French research factors and momentum, not ETF proxies: longer history, no inception truncation, no composition vintage. Since §5.5 *measures* exposure and never hedges it, a long-short research factor is the correct object. **Open dependency:** the standard UK daily factor library (Gregory, Tharyan and Christidis) ends December 2017, five years before this archive opens. Operative for the US sleeve, **open for the UK**, and the gap prints on every book-level exposure report.

**(c) The commission is verified against a named broker schedule before the break-even table freezes.** The assumed £6.25 round trip was recovered backwards from the clip definition. The clip *was defined as* the notional where fixed costs fall below 25 bps, and it propagates into the feasible band, the reachability matrix, §5.4.1 and §0.5:

| Per side | Round trip | Clip | Max ATR at h=63 | Max ATR at h=5 |
|---|---|---|---|---|
| £3.13 *(assumed)* | £6.25 | £2,500 | 3.16% | 12.0% |
| £5.00 | £10.00 | £4,000 | 1.97% | 7.5% |
| £7.50 | £15.00 | £6,000 | 1.32% | 5.0% |

***Superseded as a derivation, 27 August 2026 (§0.11, P90, P91 and P97). Annotated rather than rewritten, per §12.7.*** **The arrow still runs commission → clip, and it now runs through a stated tolerance.** The table above derived the clip from a fixed 25 bps rule written into the definition. §0.11 briefly replaced it with a chosen £50,000, which derived from nothing; **that number is withdrawn.** The clip floor is now derived from **§13 row 1's fixed cost and §13 row 29's tolerance**, which is the same arrow with the 25 bps made explicit, governed and per-market instead of implicit and universal. **Every figure in the three rows above is retained as the record of what the old definition produced**, and the two right-hand columns are **withdrawn until row 29 is set**, at which point they return by arithmetic (§4.4). ***Row 29 was set at 10 bp on 27 August 2026 (P109), so they return (P110), and they return as a FUNCTION of share price rather than as a column of numbers***, the derived floor being one. At USD 43.79 a share the max ATR is **6.39% at h = 5** and **1.68% at h = 63**, against 12.0% and 3.16% under the withdrawn £2,500 clip. **The table above is not re-tabulated**, because its left-hand column is a per-side commission in sterling and the derived floor is not a function of that: it is a function of row 1's US schedule and the candidate's price. *Re-tabulating it would put a US derivation into a sterling table and invite the two to be read as one.*

This row runs **first** in §13.

**(d) Industry classification is ICB; the point-in-time vintage is an open vendor dependency.** Until procured, peer-set construction is **not** point-in-time and every pooled estimate carries that qualification.

**(e) Borrowability is a timestamped broker snapshot, and it errs in both directions.** A current shortable list applied retrospectively is a **look-ahead** where the list has grown and conservative where it has shrunk; broker lists tend to grow, so the anti-conservative direction may dominate, and the net direction is unknown. Short-side expectancy is an upper bound on two counts. *(Not currently binding: the insider family is long-only by grammar.)*

**(f) The intended universe is enumerated by rule, and enforced.** Common equities on the LSE (main market and AIM) and NYSE/Nasdaq, above the Gate 1 floor, resolved at calibration and recorded in the parameter object. **Gate 1 asserts membership and emits `outside_universe`**: v1.8 stated the rule and provided no gate and no reason code, so a Frankfurt listing or an over-the-counter depositary receipt would have died four gates later for want of inputs, each reporting a different reason, none of them the true one.

**(g) Source class is determined by regulatory status, not by delivery channel.** An exchange's non-regulatory service carries voluntary corporate communications through the same infrastructure as compelled disclosure, timed and worded entirely at the issuer's discretion, and sometimes wholly commissioned by the issuer. §3.3 previously named the *channel*, which would have ingested marketing at the exogeneity rank reserved for filings. The distinction exists as a machine-readable field in the feed; the paper simply never read it.

### 0.8 The error asymmetry is set for a laboratory, not a fund, and is reversible

A false positive risks ≤75 bps on one clipped position; a false negative is unlearned permanently, and under §0.6 a funnel calibrated to reject everything returns a null indistinguishable from *there is nothing here*. **The decision:** accept a higher false-positive rate for detection power. Instruments: the explore arm (§5.1), the two-hurdle Gate 6 (§6.1), midpoint cost gating (§5.8), and the filing-anchored staleness carve-outs (§5.3). Bounds: minimum clip, multiplier floor, full §6.7 cap stack. **A fund operator reverses this** by restoring the third Gate 6 hurdle, conservative-end gating and the hard staleness tier, and closing the explore arm: each a single switch, listed in the parameter object.

### 0.9 The grammar is oriented towards breadth, with its populations named

IR ≈ IC·√breadth (Grinold, 1989). Sixteen positions at h = 63 is **64 bets a year**, requiring an IC of 0.063 for IR 0.5. The same book at h = 5 is **806 bets**, requiring 0.018. §5.4.1 shows h = 5 is also the *most sizable* cell. The most reachable, highest-breadth and least-analysed cell were the same cell.

**The decision:** short horizons are the centre of gravity wherever the catalyst's documented effect is short; the caveat is priced, not hidden: per-trade break-even is horizon-independent, so short horizons trade hit rate for breadth and are correct only where a specific catalyst produces a large, fast move; and the source scorecard is promoted from ingestion allocation into position sizing (§6.7).

**The populations, stated: this is v1.9's correction.** v1.8 paired an effect size measured on **open-market discretionary purchases by insiders** with a volume estimate counting **every regulatory notification**. Those are different sets, and the breadth table rested on the larger. A day's AIM flow contains roughly 14% insider-class notifications, of which, before any admissibility test, persons closely associated, involuntary account operations and scheme grants must be removed. Every figure in §6.6 now names the population it was measured on, and §13 carries the joint rate as a calibration.

**Two consequences of that correction.** *Breadth is probably adequate*: the qualifying pool plausibly exceeds the 806 the book requires. *Selectivity may not be.* If the pool is only modestly larger than annual capacity, the system must accept nearly every qualifying filing to stay invested, which leaves Gate 6's floor with little to reject and the explore arm with no below-floor region to sample. **Breadth and selection are different requirements and the design must not treat them as one.** A funnel whose product is disciplined refusal cannot refuse if refusing leaves it empty; §13's joint-rate row is what settles whether that tension is real.

**What §0.9 cost, stated.** Reorienting to regulator-stamped filings at short horizons demoted the video and social substrate the architecture was originally built to read. Those sources now enter only through the roster and the exploration slice, and their role has moved from *signal* to *pointer*: upstream traces and control-arm test items. That is a deliberate narrowing and it should not be discovered by a reader arriving with the founding use case.

### 0.10 Microcaps route to the shadow frontier, not to capital, pending evidence

**Operator requirement, August 2026:** the system must be able to trade microcaps. The analysis that requirement produced is recorded here because it changes what the decision is.

**The Gate 1 liquidity floor is not what excludes microcaps.** At the £2,500 clip the participation cap needs only ~£42,000 of median daily notional, which most AIM microcaps clear. The binding constraints are elsewhere:

| Assumed round-trip spread *(illustrative, `assumed`)* | Break-even (AIM, no stamp) *(computed)* | Versus a 230 bps raw insider effect |
|---|---|---|
| 200 bps | 225 bps *(published)*; **≤ 210 bps recomputed** | Exceeds the **undecayed** figure |
| 400 bps | 425 bps *(published)*; **≤ 410 bps recomputed** | Fails ~2× |
| 600 bps | 625 bps *(published)*; **≤ 610 bps recomputed** | Fails ~3× |

***RECOMPUTABLE AT LAST, and recomputed 27 August 2026 (P111).*** This table was computed at a **25 bp** fixed cost, that being the round-trip cost at the withdrawn £2,500 clip, and P91 and P97 recorded that it could not be recomputed because there was no clip to recompute it at. **§13 row 29 supplies a bound instead of a clip:** every admissible position carries at most **10 bp** of fixed cost, so each break-even falls by 15 bp. ***The conclusion is unmoved and was never close:*** against 115 bps after the 50% post-publication rung, **every row still fails**, by margins of 95, 295 and 495 bps. *A recomputation that changes no verdict is still worth taking, because the alternative is a table whose numbers nobody can attribute to a cost anybody measured.*

***Erratum B is DISCHARGED, 27 August 2026 (P111): both tables are now bounded by the same dimensionless 10 bp, which is a property of the TOLERANCE and not of a notional, so they are comparable line for line for the first time. That is the dividend of making the tolerance explicit.*** *Erratum B, v1.13: this table is computed on the **£2,500 minimum clip**, at which the fixed round-trip cost is 25 bps; §5.2.2's break-even table is computed on **£5,000 notional**. The two sets of figures are therefore not comparable line for line, and no number in either table is changed by this erratum.*

***Invalidated as a live reading, 27 August 2026 (§0.11, P91 and P97).*** This table is computed on a £2,500 clip. **The clip is no longer a number at all**: it is derived per market from §13 rows 1 and 29, and until row 29 is set it does not derive. So the break-even column describes a clip the system no longer has, and **it cannot be recomputed either**, there being nothing to recompute it at. *The £50,000 that briefly stood here is withdrawn with the rest.* **What does not change with the clip, and is the operative point for microcaps: market impact, which this table has never had a column for, scales with participation and grows with size**, so any recomputation that shrank the break-even column whilst leaving impact out would make microcaps look cheaper at a size that makes them dearer to trade. **The opening sentence of this section is also superseded**: at £2,500 the participation cap needed about £42,000 of median daily notional, and it scales with whatever the derived floor turns out to be. *Corrected 27 August 2026 (P93): this sentence continued "and §0.11 resolved to (b), so there is no participation rule that refuses when the depth is absent", which was false. §6.7's cap is in force; what (b) declined was a participation gate.*

Against 115 bps after the 50% post-publication rung, every row fails. **The break-even ceiling (§13) is the operative gate, not the liquidity floor**, so lowering the floor alone produces candidates Gate 1's other component rejects immediately. Reachability compounds it: at h = 5 the stop is 2.5 × ATR against a 30% feasibility bound, so ATR above 12% zeroes the position irrespective of liquidity, and many microcaps sit above that. And the clip cannot simply shrink: at £1,000 the fixed cost is 62.5 bps, which breaks the 25 bps rule the clip is *defined* by.

**One population caution.** The small-company insider literature covers issuers of roughly $30–500m market capitalisation, which typically trade well above $1m a day. **"Microcap" in the literature and "below this system's floor" are different sets**, and importing the former's effect size to justify the latter would repeat §0.9's error one bucket lower.

**The decision.** The Gate 1 floor becomes a **shadow-routing threshold rather than a hard kill**. Sub-floor candidates clear every other gate, receive full verdicts, are tracked forward, and take **zero capital**, the instrument §7.6 already provides. **Promotion to live capital is pre-registered**: the shadow cohort's realised net expectancy, after spreads measured on the design segment, must exceed its measured break-even by a stated margin over a stated minimum sample. Live admission additionally requires a new sub-$1m cost tier (§5.2.2), an explicit and bounded relaxation of the break-even ceiling reported on every microcap verdict, a recomputed §5.4.1 intersection on a microcap ATR distribution, and survivorship-complete delisting-inclusive data: **a microcap backfill on an incomplete feed is worse than none, because it will produce an attractive result.**

A reader who wants live microcap capital now reverses this and takes the ceiling relaxation as a §0 decision with its arithmetic on the record.

### 0.11 The fixed clip is WITHDRAWN and replaced by a derived floor

**Operator decision, 27 August 2026, superseding the decision this section
first carried.** Reference equity is confirmed at **£100,000**.

***What this section said before, recorded because it is the reason the
replacement is written as it is, per §12.7.*** It moved the minimum clip from
£2,500 to £50,000 and stated that the single-name position moved from 2.5% to
50% of the book. **That number is withdrawn in full.** The arithmetic prepared
in `docs/DECISION_sizing_collision.md` established that §4.4's two regime
constants **are** §6.7's own sizing arithmetic evaluated at a 10% stop, so two
of the three rules in the collision were one rule written twice and **£50,000
was the outlier by between 3.3 and 13.3 times**. The operator has taken
**resolution (i)**.

**The decision. The clip floor is DERIVED and is no longer chosen.**

> **The clip floor for a market is the smallest position at which §13 row 1's
> fixed round-trip cost falls at or below §13 row 29's maximum tolerable fixed
> cost.**

**One free parameter survives and the derivation cannot eliminate it**: row
29's tolerance, which is governance and is **OPEN**. Everything else follows
from a measurement. Row 30 carries the derived floor per market, **BLOCKED** on
row 29 and inheriting row 1's **PROVISIONAL** status.

**The cost, in the house style, and it is not small.**

**Until the floor derives, position size is UNDETERMINED. The funnel refuses to
score on size, and the book takes no positions.** Row 29 is OPEN and row 1 is
PROVISIONAL, so this is the state today, for every market. `sizing.py` returns
`clip_floor_tolerance_unset` and not a number, and it is a **refusal to
score**: *a size of zero would say the position was evaluated and came out
small.*

**That refusal is the POINT, and it is the whole gain from the decision.** A
£50,000 floor would have produced **the same empty book**: §6.7 sizes between
£1,875 and £15,000 across the stop range, every one of which falls below
£50,000, so every candidate would have been killed for being too small.
**§0.6 names exactly why that would have been worse:** *"a funnel calibrated to
reject everything returns a null indistinguishable from **there is nothing
here**"*. **The two empty books are not the same artefact.** One is empty
because a constant was set too high and says so nowhere; the other is empty
because a named parameter is unset, carries a reason code that names it, and
carries a resurrection predicate saying what would fill it. **The emptiness is
now legible, and legibility is the product.**

**A second cost, stated rather than left to be discovered.** §5.1's explore arm
is *"accepted at the minimum clip"*, which sizes that arm **at** the floor.
While the floor is undetermined the explore arm has no size either, so **the
below-floor region the association otherwise never observes is unobserved
too.** That is a consequence of the decision and not an objection to it.

**What this decision does NOT do.**

- **It does not close §13 row 1**, which remains PROVISIONAL on three gaps the
  clip never touched: the FX route absent from any published schedule, the
  tiered-or-fixed election unmade, and the contracting entity unestablished.
- **It does not resolve the participation question.** §0.11's earlier text
  claimed the clip ran with *"nothing in the funnel that refuses on
  participation"*; **that was false and was corrected by P93.** §6.7's cap
  stack has always carried **participation at 2% of median daily notional per
  session over ≤ 3 sessions**, and §0.10 quantifies it. What decision (b)
  declined was a participation **gate**, which remains deferred in Annex A.1.
- **It adds no apparatus.** Row 29 and row 30 **remove** a chosen sizing input
  and replace it with a derived one. The set of admissible positions is
  narrower, not wider, so this is a **restriction** and §0.6 does not block it.

---

---

## Abstract

Financial media is dense in narrative and sparse in edge. This paper confines a language model to extraction and classification; constrains strategy specification to a closed, pre-registered grammar with machine-observed or calendar-corroborated anchors; and passes candidates through a sequential gate stack with two-tier semantics. Verification rests on expectancy with standard errors, minimum samples below which gates refuse to score, thresholds calibrated against measured base rates in the form each statistic admits, block-permutation nulls, three named archive partitions with a Gate 0 separation assertion, and multiplicity control counting specification versions mechanically while attributing results only to completed, hashed freezes. System validity is the Spearman association between funnel depth and forward return across the entire intake (including a pre-registered explore cohort below the acceptance floor and a shadow cohort below the tradability floor), guarded by an equivalence-tested placebo that fails for want of power rather than passing by it. The grammar centres on regulator-stamped event families at short horizons, led by insider purchase filings admitted on a change in beneficial economic interest rather than on a headline. Breadth arithmetic is published with the population each figure was measured on. Every rejected idea and declined capability carries a predicate or a recorded reason (Annex A). A specified evidence lane (§3.6) admits research papers **and the operator's own hypotheses** as family-level evidence only, classifying amendments by reachable-set diff and refusing to score claims whose provenance is unverified; unquantified ideas enter a pointer tier whose sole output is an observation directive naming the feed that would exercise them, actionable at zero capital where that feed already flows, by calendar-driven manual observation where it does not, and deferred behind a predicate only for production ingestion; pointer verdicts are decided by equivalence against a registered abandonment threshold, and the design-segment search they consume is counted as its own multiplicity family, dividing nothing. Every refusal anywhere in the system carries a plain-language rejection summary rendered from the record's own fields. The book is unhedged: residual beta is measured and displayed rather than removed, following a failed eligibility verification whose consequences are priced in the text. Two harnesses test the specification before it is frozen and each carries a pre-registered stopping rule: a trace harness (§9.4) that runs real items through the funnel, and a review harness (§9.5) that runs mechanical checks over the document itself: the first tests rules against a world, the second against each other, and the paper records that the first is the stronger instrument.

---

## 1. Introduction

Media produces commentary faster than any person can read. The obvious design (let a model read everything and trade the good theses) fails on three counts: **numeric hallucination**, **weight-borne hindsight** (a model choosing a lookback for a famous asset gravitates to what worked in the history it memorised, and no data split cures a leak inside the model), and **narrated hindsight** in the source itself.

The architecture inverts the division of labour: the model extracts and classifies; everything else is deterministic arithmetic on logged data. The paper's claim discipline follows: it cannot credibly demonstrate returns, so it demonstrates **legible rejection** and, over time, whether funnel depth *orders* forward returns.

Contributions: (i) a closed grammar with a published reachability matrix intersected with per-class admissible horizons; (ii) a staleness gate calibrated to the base rate of the corpus it filters, with named carve-outs where its causal model does not hold; (iii) two-tier semantics with the sizing, discretionary, explore and shadow channels each bounded and measured; (iv) validation by funnel-depth rank association with an equivalence-tested placebo; (v) three-family multiplicity control with mechanical version counting; (vi) a source layer ranked by regulatory status and the exogeneity of the publication clock, whose measured lead also sizes positions; (vii) an event-anchored family led by insider purchases admitted on economic substance; (viii) a binding ordering rule, amended once and re-armed; (ix) published breadth arithmetic naming its populations; and (x) a specification trace harness that tests rules against a world rather than against each other.

---

## 2. Design principles

**Fail fast, ordered by kill rate per second, with the cost of each test stated.** Gates are sequenced by expected rejections per unit of compute. Where a family's admissibility cannot be determined cheaply, that is recorded rather than assumed: the insider family's test requires parsing the body of every notification, because regulatory headline categories are standardised and deliberately uninformative: *Director/PDMR Shareholding* covers purchases, sales, option grants, vesting, custody transfers and automatic account operations alike. The parse is deterministic, so the cost is throughput, not accuracy.

**Determinism first.** The model acts only where classification over unstructured text is unavoidable. **A date is a number** (§3.5.3); a model-mediated similarity score upstream of a hard gate is a probabilistic dependency in a deterministic coat (§4.2). Field-delimited regulatory forms are parsed, never inferred.

**Pre-registration.** All grids, thresholds, conventions, cost tiers, peer-set axes, anchor assignments, input sources, schema fields and estimation spans are contents of the hashed parameter object.

**Hypothesis accounting.** Every configuration and every specification version is counted, mechanically.

**Feasibility before evaluation.** Constraints are solved for their feasible regions before candidates are seen; a published region is itself a claim requiring recomputation; and **a region is only as useful as its intersection with the other constraints acting on the same cell.** This paper has now published three pairs of correct constraints without crossing them: admissibility against reachability (§5.4.1), the horizon table against the sizing arithmetic, and the qualifying-filing rate against the tradability floor (§13). The intersection is the default deliverable, not an afterthought.

**Hindsight containment through independent mechanisms.** Observation-timestamp anchoring for the analyst; the grammar for the model.

**Untrusted input.** Transcripts and articles are adversarial data, never instructions; raw text is quarantined after extraction.

**A check measures a population, and the population is a separate claim from the verdict.** A verdict answers *did what I measured pass*, never *did I measure what I said*. Every gate reports the size of the set it measured at its own measurement point; presence-checks anchor to definitions, not mentions; predicates assert transitions, not end states. **The corollary v1.9 adds: a rule never answers *did anything ever reach me*.** A rule no candidate has exercised is untested regardless of how many times it has been read, and §9.4 exists to find those.

---

## 3. Targeting and ingestion

### 3.1 Sources as hypotheses, ranked by regulatory status then by clock

A source is a hypothesis: *this stream emits exploitable information before it is priced.* The primary axis is **regulatory status** (mandated or voluntary), and the secondary axis is the exogeneity of the publication clock. Class priors: mandated primary disclosures; scheduled primary events; specialist trade press; expert commentary; general financial media; retail social.

**Voluntary announcements delivered through regulatory infrastructure rank as discretionary media** (§0.7g), regardless of the channel they arrive on.

**§3.1.1 Diffusion half-life per (source class × catalyst type).** Measured on the calibration segment; anything with sub-session half-life is excluded at the *pair* level, never the class level. This bounds latency spend: milliseconds buy nothing for a daily-bar instrument.

### 3.2 The source scorecard

Per source: **funnel depth**; **lead profile**; **novelty**; **forward attribution**, empirical-Bayes shrunk with precision proportional to call count. A frozen regression from the three fast proxies to realised attribution priors new sources. The four are never hand-weighted, and the lead profile and first-mention flag feed sizing (§6.7).

**Novelty reports the roster coverage it was computed against.** First-mention share can only detect prior mentions *inside the corpus the system reads*. A relay of another outlet's reporting scores as a first mention, and the error is systematic rather than random: it over-credits relay sources in proportion to how thin the roster is, which is exactly the early-life condition the sizing multiplier operates in. A first-mention claim from a roster below a stated coverage threshold is flagged rather than trusted.

**Excluded from the scorecard entirely:** running documents (§3.5.1); machine-generated sources; wholly commissioned items; and items whose attributed party is a competitor or adversary of the subject. A lead profile measured on issuer-paid research measures a publication schedule the issuer bought.

### 3.3 Discovery and allocation

**Enumerable universes** are subscribed: EDGAR forms and full text including Form 4; the LSE regulatory service including PDMR dealing and TR-1 notifications; transcript providers; clinical and procurement calendars. **Base rates are measured against the primary feed, never an aggregator**: intermediaries filter announcement classes silently, and takeover-related disclosures are among the classes commonly removed. Where an intermediary is used, its stated filter policy is recorded in the parameter object and every base rate is reported as conditional on it.

**Upstream tracing** hunts the earliest articulation of theses with strong forward returns; **citation expansion** follows links from high-scoring sources; **popularity charts** enter only as exploration seeds under an inverse prior. Probation replays twenty-five recent items. Allocation is Thompson sampling on the attribution posterior, implemented as weekly re-ranking with a **fixed 20% exploration slice**.

### 3.4 Source-selection endogeneity

Scoring on the calibration segment; rosters frozen per evaluation period, the initial roster fixed at freeze; every probed source in the ledger; every per-source statistic shrunk.

### 3.5 Ingestion and extraction

**§3.5.1 Anchors and consumers.** Four anchors, `t_pub_earliest`, `t_pub_observed`, `t_cat_claimed`, `t_cat_confirmed`, and every consumer names one:

| Consumer | Anchor | Safe-error direction |
|---|---|---|
| Gate 2 windows, k ∈ {5, 20} | `t_pub_earliest` | Early anchor widens the window: stricter |
| Gate 2 catalyst window | `t_cat_claimed`, `t_pub_earliest` | Both early; empty where forward-dated |
| Lead profile, novelty | `t_pub_earliest` | Articulation order |
| Event-anchored entry | `t_pub_observed` or `t_cat_confirmed` | Never before this system could act |
| Peer membership, ICB vintage | `t_pub_observed` | No post-observation composition |
| Fill convention | signal-completion bar | No external anchor |
| Walk-forward and Gate 6 estimation | `t_pub_observed` | Strictly pre-actionable |
| Forward ledger, §7.1 | `t_pub_observed` | Excludes pre-observation segments |
| Partition assignment | `t_pub_earliest` | Never by arrival (§7.5) |
| Median daily notional | trailing 63 sessions to `t_pub_observed` | Point-in-time |
| Drawdown governor HWM | first simulated position of the evaluation segment | No cross-segment state |

**Anchor provenance is recorded with each value**: `visible_date | feed_timestamp | cms_metadata | inferred`. Content-management metadata routinely predates publication for embargoed releases, and a creation date three days before an issuer's results would otherwise set `t_pub_earliest` to a moment when the information did not exist, running Gate 2's window over a period before the catalyst and making a primary disclosure look stale on its own publication day.

**Running documents carry no publication moment.** A continuously updated article has a stable topic and unstable content, so `t_pub_earliest` becomes a republication timestamp. `document_type ∈ {static, running}`; running documents may seed upstream tracing and take no anchor role.

**Ingestion lag is measured and gated.** `ingestion_lag = t_pub_observed − t_pub_earliest` is a property of *this system*, distinct from §3.1.1's diffusion half-life, which is a property of the market. Gate 1 rejects where the lag exceeds a stated fraction of the tuple's admissible horizon, with reason code **`ingestion_lag_exceeds_window`**; at h = 5 that admits roughly one session. *The rule was specified in v1.9 without a code, which left it invisible to §9.4's headline ratio: a rule whose kills cannot be counted cannot be shown to have been reached.* The realised lag distribution is reported per source class. **§0.9's breadth case depends on the entry window still existing when the item arrives, and nothing previously measured that.**

**§3.5.2 Extraction.** One schema-enforced call, temperature zero, cached by content hash. Accuracy floors: direction 0.95 and `t_cat_claimed` 0.90 on 200 hand-labelled items per class; other fields 0.85 on 50. A class below floor is suspended; **suspensions lift on the quarterly calendar, on a freshly drawn set**: never on the existing set, never on demand, never gated on review-point throughput. Fields:

- `issuer` and `instrument_referenced`, separately: **these are the canonical names**, and they are stated as such because the same field was called `issuer_id`/`instrument_id` in one register copy and `issuer`/`instrument` in another, neither of which matches the manuscript. The superseded names are recorded here rather than deleted (§12), and the parameter object carries no alias. An article may reference an issuer through an instrument outside §0.7(f) while the primary listing is inside it. The issuer resolves to its **primary listing** unconditionally; where that primary listing is outside the enumerated universe the candidate dies at Gate 1 with `outside_universe` rather than at resolution, so the two rules do not overlap. The referenced instrument is recorded; where quoted price data belongs to the non-primary instrument, it is flagged, because an after-hours depositary-receipt print may bear little relation to the next primary-market open.
- `direction` **and `direction_basis ∈ {stated, inferred}`**, with `inferred` carrying an automatic advisory flag. A source can marshal uniformly bearish evidence and then decline the bearish conclusion; a single direction field emits confidently on tone and the mismatch travels invisibly. Divergence cases route to §7.4's control arm.
- `attributed_party`, `party_interest ∈ {self, competitor, adversary, counterparty, none}` and `genre ∈ {report, analysis, opinion}`. §3.1 ranks the *outlet*; these rank the *speaker* and the *form*. A competitor and litigation adversary chooses when to speak, what to say, and benefits from being believed: the maximally endogenous case on an axis the class taxonomy does not have.
- `source_generation ∈ {human, machine_assisted, machine}` and `item_sponsorship ∈ {none, segment, wholly_commissioned}`. Sponsor *segments* within an item were already quarantined; a wholly commissioned item has no segment to excise because the whole thing is the placement.

For field-delimited regulatory forms, extraction is a **parser**, not a model call.

**§3.5.3 Anchor and catalyst provenance.** `t_cat_confirmed` exists only where the claimed date is **corroborated against a subscribed machine-readable calendar or a regulator-stamped filing**; otherwise the tuple anchors on `t_pub_observed`, the (event × `t_cat`) cell is inadmissible, and the graveyard (§8) records `catalyst_date_corroborated`. Filings are self-corroborating: the filing *is* the event.

Forward-dated catalysts carry a **ceiling and a floor**. The observation-to-confirmation lag may not exceed 63 sessions; Gates 0 and 2 re-run immediately before any deferred fill. And a catalyst must have **duration**: one resolving inside a single session is inadmissible to every fixed-horizon family, however exogenous its clock. §3.1.1 already excludes information that diffuses inside a session on the grounds that speed buys nothing for a daily-bar instrument; the identical logic applies to the event, and previously went unwritten.


### 3.6 The evidence lane: papers and hypotheses as family-level evidence

*Introduced v1.10 as the literature lane; extended in v1.11 to a second evidence tier and a second origin. Procedure, not apparatus (§0.6), with one exception, stated in §3.6.5.*

**§3.6.1 What enters, and what it is.** The lane admits **family-level evidence**: an argument that an event class carries an effect on a stated population. It has no asset, no tradeable tuple, and no `t_pub` that means anything to Gate 2. **Nothing entering this lane ever enters the item pipeline.**

Two axes classify every intake, and they are independent:

| Axis | Values | Consequence |
|---|---|---|
| `origin` | `paper` \| `operator` \| `agent` \| `random_control` | Determines which endogeneity applies (§3.6.6) and which provenance tier the resulting evidence carries. The two machine origins are siblings by construction (§3.7.5) |
| `evidence_tier` | `quantified` \| `pointer` | Determines which outputs are reachable (§3.6.4) |

A **quantified** intake states a magnitude, a window and a measured population; it can reach every output the lane has. A **pointer** states an event class and a mechanism and quantifies nothing: a paper that is suggestive rather than estimated, or a hypothesis of the operator's own. **A pointer's only reachable output is an observation directive.** It cannot amend a family, cannot restrict one, cannot update a prior, and cannot carry a parameter, because it contains no number to carry.

Outputs land in exactly four places: a **restriction or prior update** to an existing family (a register item), an **extension or new family** (an Annex A.1 row with a predicate), an **observation directive** naming the stream that would exercise the claim, and, for pointers, **nothing else**.

This formalises the path the insider-purchase family already took (alpha review → Annex A.2 → §5.4 row → §4.1 direction restriction), performed once, ad hoc, and made repeatable here under stated rules.

The lane is falsification-first, not confirmation-first: the observation directive exists to **exercise** a candidate, including killing it on the design segment, and its kill criteria are written before any data is examined. *Find evidence for the idea* is not an output this lane can emit, and the pointer tier is where that rule is under the most pressure, because a pointer arrives with nothing but its author's interest in it.

**§3.6.2 Intake extraction.** One schema-enforced call per intake, temperature zero, cached by content hash (§3.5.2 conventions). The clerk extracts and classifies; it holds no authority over merit, landing or activation. **Operator-origin intakes are written by hand into the same schema**: the operator drafts the record, not the argument for it, and the fields below are the whole of what the lane will read.

| Field | Content |
|---|---|
| `paper_id`, `title`, `authors`, `venue` | DOI or SSRN identifier; bibliographic record |
| `publication_status` | ∈ {journal, working_paper, preprint} |
| `publication_date`, `sample_period` | Both drive the decay prior: post-publication and post-sample decay are distinct quantities |
| `sample_market`, `sample_population` | Market, cap range, filters: the `measured_on` population, stated explicitly |
| `event_definition` | The mechanism in one sentence, mirroring item extraction |
| `event_class` | Classified against the fixed table in §3.6.5 |
| `claimed_effect` | Magnitude, units and measurement window as the paper states them |
| `claimed_horizon_sessions` | The documented effect horizon |
| `cost_treatment` | ∈ {gross, net_stated, net_modelled} |
| `direction_conditionality` | Any directional asymmetry the paper documents |
| `replication_status` | ∈ {replicated_open_data, replicated_closed, single_study}; **deterministic lookup**, never clerk judgement |
| `family_mapping` | ∈ {existing:⟨family⟩, amends:⟨family⟩, new_family}: a **proposal**; §3.6.4's diff decides |
| `origin` | ∈ {paper, operator, agent, random_control} |
| `evidence_tier` | ∈ {quantified, pointer}; **computed, not asserted**: an intake is `quantified` only where `claimed_effect`, `claimed_horizon_sessions` and `sample_population` are all populated and all carry a verified tag. Anything else is a `pointer`, including a paper whose figures the operator has not yet read |

The two machine origins are siblings by construction, the control arm being identical to the agent arm in every respect except the thing under test. Evidence produced by either carries `agent_generated` provenance, routing advisory-only under §3.6.3 check 5 exactly as `self_generated` and `single_study` do.

**A pointer's record is shorter and the omissions are not defects.** `claimed_effect`, `claimed_horizon_sessions`, `cost_treatment` and `replication_status` are empty by definition; `event_definition`, `event_class` and a stated `measured_on` intention are mandatory, because without them there is nothing for §3.6.5 to look up. **`registered_at` is mandatory for every pointer** and is the timestamp before which no observation on that directive may be counted (§3.6.8).

**Every claim field carries a provenance tag**: `verified_primary | verified_secondary | recollection`. Intake volume is low enough that hand verification is feasible, and §3.6.3 makes it mandatory in effect.

**§3.6.3 The merit screen.** Merit is deterministic checks, not editorial judgement. Every screened paper, pass, fail or blocked, **enters the hypothesis ledger**, exactly as probed sources do; an unlogged screen silently inflates the search space §6.4 counts.

| # | Check | Rule | Existing machinery |
|---|---|---|---|
| 1 | **Cost survival** | `claimed_effect` × the applicable decay-ladder factor clears the per-trade break-even at `claimed_horizon_sessions` | §0.5; §5.2.2; the 50/72/93 ladder (§6.1) |
| 2 | **Population overlap** | `measured_on` versus `tradable_on` declared; any mismatch flagged at intake; the joint qualifying-and-tradable rate **measured before activation, never assumed** | §0.9's error class, made a mandatory field; §13 row 12 |
| 3 | **Event observability** | A machine-readable, timestamped, corroborable stream carries the event class | §3.5.3: no corroborable anchor, no family |
| 4 | **Horizon admissibility** | The documented horizon maps into {5, 21, 63} | §5.4 |
| 5 | **Evidence quality** | `single_study` routes advisory-only; journal plus replication routes normally | Mirrors the source scorecard: papers are sources with a slow clock |

**The pointer tier's screen is shorter, and check 3 is the whole of it.** Checks 1 and 4 have no input to consume (there is no claimed effect and no claimed horizon), so they report `not_applicable_pointer_tier` rather than passing or failing, and **a not-applicable check may never be read as a pass.** Check 2 records `measured_on` as an intention and `tradable_on` as unmeasured. Check 5 assigns `pointer` provenance, which routes advisory-only by construction. **Check 3, event observability, is mandatory and binding**: a pointer whose event class has no machine-readable, timestamped, corroborable stream is refused outright, because a directive that names no stream is not a directive. This is the one screen a pointer can fail, and it is the one that matters: it is the difference between *an idea worth watching* and *an idea nothing can watch*.

**Refusal semantics.** A check whose input carries `recollection` provenance **refuses to score**, consistent with gate semantics everywhere else. A blocked screen is a to-do, not a verdict, and the refusal **migrates** to a named §13 row rather than lingering.

**§3.6.4 The amendment fork: classification by reachable-set diff.** The clerk proposes `family_mapping`; the classification that matters is **computed**. Recompute §4.4's reachability under the proposed change and diff the hard-reachable tuple set:

| Kind | Diff condition | Landing |
|---|---|---|
| **Restriction** | Set strictly shrinks; **or** the change is confined to advisory tiers, which cannot admit anything new | Register item. Pre-freeze: lands at the next version. Post-freeze: confined to §7.7 review points |
| **Prior update** | Set unchanged; a data-vintage change (decay priors, taxonomy vintage) | Register item, vintage logged as for ICB; sensitivity displayed via the decay ladder |
| **Extension** | Set enlarges; **or** the diff is non-comparable (adds and removes), which is the conservative default | Annex A.1 row with a predicate; activates only after the §0.6 instruments report, identically to a new family |
| **Pointer** | **Not computed.** The tier carries no parameter and proposes no rule, so there is no diff to take and the reachable set is unchanged by construction | Observation directive only (§3.6.5, §3.6.8). No register item, no A.1 row, no version increment |

**Parameters inside restrictions.** Any numeric parameter a restriction requires, an adjacency window, a size band, is taken **from the paper's own specification**, with provenance, fixed before contact with this system's data. This is the §4.1 precedent of a theory-driven restriction. *A restriction parameter fitted on the archive is a fitted parameter wearing a restriction's clothes, and is inadmissible.*

**Multiplicity.** Every adopted amendment is part of a specification version and is counted by §6.4's third family. No new counting machinery: that is the point of routing through versions.

**§3.6.5 The observation directive.** The *which feeds to follow* output, and the lane's primary product for the pointer tier. It is a **lookup, not a model opinion**: the clerk classifies `event_class`; a fixed table maps class → stream. `stream_status ∈ {subscribed, category_filter, manual_observation, new_subscription}`, and a `new_subscription` is a new dependency flagged as the ICB vintage is. *(v1.12 cleans a v1.11 muddle: `operator_mapped` was briefly both a status and a provenance. It is provenance only (`stream_provenance ∈ {table, operator_mapped}`), and a mapped stream then takes whichever of the four statuses describes it.)* Base rates are measured against the primary feed, never an aggregator (§3.3). **The table is in the parameter object**, so adding a row is a specification version.

| Event class | Stream | Status |
|---|---|---|
| Insider dealing | RNS PDMR notifications; EDGAR Form 4 | subscribed |
| Major holdings changes | RNS TR-1; EDGAR 13D/G full text | subscribed / category_filter |
| Buybacks | RNS Transaction in Own Shares | category_filter |
| Earnings events | RNS results categories; earnings calendars | subscribed |
| Index reconstitution | FTSE Russell review calendar | **new_subscription** |
| Short-interest disclosure | FCA net short positions register | **new_subscription** |
| Clinical / procurement events | Subscribed calendars | subscribed |
| **Unclassified** | operator names the stream, see below | resolved to one of the four; `stream_provenance = operator_mapped` |

**The unclassified branch, new in v1.11.** An event class outside the table is **not refused**. Refusing on unclassified would make the table's current contents a ceiling on what the system can ever investigate, and the table's contents are an artefact of which papers have been read so far, which is the endogeneity §3.6.6 exists to contain, hard-coded into the machinery instead. Instead:

1. The clerk emits `event_class = unclassified` and **proposes no stream**: it has no authority to invent one.
2. The **operator names the stream by hand**, recording publisher, access route, machine-readability, whether timestamps are per-item, and whether the class is corroborable. This is check 3 of §3.6.3 performed manually and it is binding: an operator mapping that cannot answer those five questions is a refusal, and the refusal is on **observability**, never on novelty.
3. The mapping enters the ledger with `stream_provenance = operator_mapped` and its own timestamp, and it is **reusable**: the next intake classifying to the same event class inherits it. The table therefore grows by use rather than by anticipation.
4. Adding the row to the parameter object's table is a **specification version**, counted by §6.4. Naming a stream in the ledger is not. The two are deliberately separated so that investigation is cheap and commitment is counted.

**What may be acted on, and when.** This is the rule v1.10 left `undecidable`: the lane emitted directives and never said whether they could be followed while §0.6 is armed. It is settled by **what the directive costs**, not by what it might find:

| `stream_status` | May observation begin? | Why |
|---|---|---|
| `subscribed`, `category_filter` | **Yes, immediately, at zero capital** | A filter over a feed already ingested. No new dependency, no ingestion code, no capability. Runs through §7.6's existing shadow instrument |
| `operator_mapped`, where the named stream is one already subscribed | **Yes, immediately** | Same as above; the mapping is a lookup, not a feed |
| `manual_observation` | **Yes, immediately, under a collection protocol** | Hand collection of the same class as §9.4's tracing, which processed ~70 items without amending anything. Nothing it records ever feeds a gate |
| `new_subscription`, a **production ingestion adapter** | **No.** Annex A.1 row with the dependency named | Code in the funnel path: a parser, anchor semantics, failure modes, a parameter-object footprint. **This is apparatus, however modestly it is described**, and §0.6 governs it |

**The manual-observation tier, new in v1.12: the split that removes most of the friction.** v1.11's rule conflated two different objects under `new_subscription`: a production adapter, which is unambiguously apparatus, and *the operator looking at a public register on a calendar and writing down what is there*, which is not. The tier's protocol:

1. **Cadence is calendar-driven and pre-registered**: a stated day, a stated source page, stated fields. Collection when something interesting happened is not collection; it is the endogeneity of §3.6.6 wearing a clipboard. A missed collection is logged as missed, and **a gap is recorded as a gap, never as an absence of events**.
2. **Records carry `stream_status = manual_observation` on every derived figure**, and nothing so tagged may feed a gate, an anchor, a base rate used by the funnel, or a peer set. The records exist to decide whether a production adapter is worth its predicate, nothing else.
3. **Manual backfill carries the survivorship caveat of §0.10, printed on every figure it produces.** A hand-assembled history of a source discovered because it looked interesting is precisely the incomplete-feed setup that produces an attractive result, and forward hand-collection is slow: one observation a week accumulates little before the instruments report. Both limits are stated on the record rather than discovered later.
4. **Promotion to a production adapter takes the Annex A.1 predicate regardless** of how well the manual series behaves.

**The declined-directive log, and what it buys.** Every directive declined or deferred (`new_subscription` rows, displaced directives, refused mappings) is logged **with the feed it named**. At freeze, the distribution of named-but-unsubscribed feeds is reported beside the §0.7 roster decision: **if the operator's best ideas persistently point at streams the roster lacks, that is evidence the roster is mismatched to the hypothesis space, and the freeze is where rosters change.** The friction is thereby converted from an irritation into a design input, which is the only honest use for it.

**For amendments to families whose stream already flows, the directive collapses to a design-segment measurement task**: cheaper than a new feed, and identical in form to §13's pre-build sequence: run once on the design segment, kill criteria written before the data is examined.

**The remaining friction, and its stated size.** After the manual tier, what is actually declined shrinks to one thing: machine ingestion of a new feed before the instruments report. Investigation of any observable event class proceeds, by filter where the stream flows, by hand where it does not. What cannot be had early is automation and backfill depth, and a reader who wants those now takes the drafted second amendment in §0.6 as a §0 decision, with its cost on the record.

**§3.6.6 Endogeneity and ledger.** Three entries join §6.3's catalogue as siblings of §3.4, and they sharpen in order: a paper has passed someone else's referees, an operator hypothesis has passed nothing, and an agent raises hypotheses at a rate no operator could match.

**Paper-selection endogeneity.** Which papers the operator feeds in is a choice conditioned on realised history and on what the literature has already celebrated. Containment is procedural: every screened paper in the ledger, screen results recorded pass or fail, published anomalies carrying the decay prior **precisely because publication is itself a selection event**.

**Operator-hypothesis endogeneity, new in v1.11 and stronger.** A paper has at least passed through someone else's referees and someone else's sample. **An operator hypothesis has passed through nothing.** It is generated by a person who has lived through the price history the system will be evaluated on, who knows which sectors have moved and which narratives have worked, and who cannot introspect the difference between a mechanism and a memory. This is the same defect the architecture attributes to the model in §1 (weight-borne hindsight), relocated to the operator, where no data split reaches it either.

Containment is four rules and none of them is a solution:

1. **`registered_at` precedes observation.** A directive is timestamped in the ledger before any data is examined, and observations dated before it are inadmissible. This does not stop hindsight; it stops hindsight being *added* after the fact, and it makes the ordering auditable.
2. **Kill criteria written first.** As for every design-segment measurement: sign, minimum count and threshold committed before scoring.
3. **Every raised pointer is counted**, including the ones the operator loses interest in (§6.4). A pointer abandoned before observation is still a search path taken.
4. **Evidence produced by an operator directive carries `self_generated` provenance**, which routes advisory-only under check 5 exactly as `single_study` does. It is not weaker evidence about the *world* (it is measured on the actual tradable population, which a US-measured published anomaly is not); it is weaker evidence about the *search*, and check 5 is the only place the distinction can be recorded.

Two further rules, added in v1.12, are of a different kind: they are enforceable fences rather than records.

5. **The query fence.** The contaminating knowledge is not that the operator lived through the period; that knowledge is coarse. It is granular, archive-conditional knowledge: *this class, on this population, moved this much*. The rule is therefore about **which queries may be run before a directive is registered**: class-level and mechanism-level queries are open; conditional-return queries on the directive's own target population are closed until `registered_at` is stamped. Enforcement is the research stack's **query log, which is part of the ledger**: a fence over auditable actions, where *the operator should be careful* is a fence over nothing. A directive whose target population was queried for conditional returns pre-registration is inadmissible, and the inadmissibility is mechanical.
6. **Literature first.** Before registration, a literature search is run and its result recorded. Either the idea is already published (in which case it enters as a **paper intake**, with a decay prior and someone else's referees, which is strictly better evidence), or it is not, and *why not* is recorded. *Tried and does not work* is a real answer, and it is the answer the published literature systematically declines to supply.

A third entry, added in v1.13, joins §6.3's catalogue as the third sibling of §3.4, after paper selection and operator hypothesis, and carries its containment as a seventh rule.

7. **Agent-discovery endogeneity.** The containment is six rules and, as with the operator's, none of them is a solution: i) structural blinding by schema, refusing episodes; ii) partition or market disjointness, recorded per directive in `scoring_mode`; iii) the query fence extended to machine reads; iv) the import fence, checked at process start; v) every proposal counted, including those abandoned at the first ingestion point; and vi) the random-mechanism control arm, which is the only one of the six that *measures* rather than *constrains*. **What is unreachable, stated plainly.** The weights are not partitionable, so the agent's recollection of price history cannot be fenced, only diluted by requiring mechanism-level emission. This is the same defect §1 attributes to the model and §3.6.6 relocates to the operator, and it is unsolved in all three locations.

**The honest limit, revised.** Rules 1–4 and 6 make the search legible; rule 5 and §3.6.8's equivalence verdicts change what can pass. None of it makes the search unbiased, because the system cannot observe the operator's priors, and §10 carries that as a limitation rather than a solved problem. What has changed since v1.11 is that the containment now has teeth in two places instead of none.

**§3.6.7 First intake, and what it demonstrated.** The lane's first run took Fidrmuc, Goergen and Renneboog (2006), chosen because it was already a carried citation, is UK-measured, and exercises the amendment fork rather than the new-family path. The run is recorded because two of its outputs are evidence about the lane itself:

- The cost-survival check **refused to score** on first pass, because `claimed_effect` carried `recollection` provenance. Verification against the paper's own tables then **contradicted the recollected claim in two places**: general news adjacency does *not* reduce the purchase reaction (only M&A news within the paper's windows does, driving it to approximately zero), and the ownership result is a **sign structure rather than a scalar**: corporate blockholders negative, individuals and families negative but weaker, **institutional positive**, director blocks negative.
- Both recollection errors would have entered the specification had the screen scored on memory. **A recorded recollection error is a first-class output of this lane**, not an embarrassment to be tidied, because it is the direct evidence that the refuse-to-score rule earns its cost.

The intake produced one restriction (§5.4.1's news-adjacency flags), one prior update (§0.5's evidence block), one reclassification (the trade-size *threshold* collapses into §5.4.1's existing economic-substance test rather than standing as a new amendment), and one Annex A.1 row for the parts that enlarge the reachable set.

**§3.6.8 The pointer tier: directed observation without a family.** *New in v1.11. This is the answer to "an idea has merit, start looking for tradeable evidence in that area".*

**The life of a pointer, in six steps, each with a stated exit.**

| # | Step | Exit condition |
|---|---|---|
| 1 | **Raise.** Intake record written to §3.6.2's schema; `evidence_tier` computes to `pointer`; `registered_at` stamped | Ledger entry exists. Counted by §6.4 whatever happens next |
| 2 | **Observability screen.** §3.6.3 check 3, binding | No corroborable stream → refused, reason `no_observable_stream`, logged |
| 3 | **Directive.** §3.6.5 lookup, or operator mapping for `unclassified` | `new_subscription` → Annex A.1 row, stop here |
| 4 | **Pre-registration, four parts.** (i) The measurement, the sign, the minimum actionable count *n*ₘᵢₙ, **and the abandonment threshold δₘᵢₙ, the smallest effect worth pursuing**, stated in the units the measurement reports. (ii) A **pre-mortem**: the most plausible reason the observation would show the effect *even if the mechanism is false*, written before any data is seen; **and if that confound is unmeasurable on available data, the pointer is refused here**, reason `confound_unmeasurable`, before it consumes a session of the segment. (iii) The §3.6.6 **query-fence declaration**, checked against the query log. (iv) The **literature-search record** | Any part missing → no observation. There is no advisory tier for registration |
| 5 | **Observe on the design segment**, zero capital, via §7.6's shadow instrument, and decide by **equivalence, not by significance against zero**: §7.5's discipline applied to pointers. Three verdicts and only three: **promoted**, where the effect exceeds δₘᵢₙ with the registered sign at *n*ₘᵢₙ; **killed_negligible**, where two one-sided tests demonstrate the effect lies within ±δₘᵢₙ, a *positive demonstration* of nothing there, recorded in the graveyard (§8) with a resurrection predicate; **undetermined_at_budget**, where the segment allocation exhausts before either, recorded as undetermined, never as a quiet pass or a quiet kill | A verdict that fails for want of power says so. *The registered sign was the endogeneity in one line under v1.11's rule: the operator supplied both the hypothesis and its pass condition. δₘᵢₙ moves the pass condition to a magnitude the operator must commit to before knowing whether it flatters them* |
| 6 | **Promotion.** A surviving pointer does not become a family. It becomes a **quantified intake with `self_generated` provenance** and re-enters at §3.6.2 | From there the ordinary rules apply: §3.6.4's fork, A.1 predicate, §0.6 |

**Step 6 is the load-bearing one.** A pointer that survives observation has produced a magnitude, a window and a population measured on the actual tradable universe, which is *better* evidence than most of what the literature supplies. It still does not activate anything, because the route from evidence to capability runs through §0.6 and nothing in this lane is permitted to shortcut it. **A pointer is a way to have evidence waiting when the instruments report; it is not a way to act before they do.**

**The directive budget is computed from design-segment power, not chosen.** v1.11 capped concurrency at six, a number defended by nothing. The real constraint was never tidiness: it is that **the design segment is short** (a three-way split of a two-to-three-year archive leaves perhaps twelve to eighteen design months), directives measuring on it overlap, and an exhausted or over-reused segment quietly stops being out-of-sample for anything. The replacement:

- Every directive registers *n*ₘᵢₙ and its **segment span**: the sessions and populations it will consume.
- The **design-segment reuse ledger** records, per directive, the span consumed and the pairwise overlap with every other open or closed directive. It is displayed with the funnel, in the same spirit as the manual and explore shares.
- **Concurrency is bounded by arithmetic**: a new directive is admissible only while its span keeps every pairwise overlap within the pre-registered tolerance *θ* and the segment's cumulative unconsumed span above the floor the pending §13 calibrations themselves require: the calibrations have first claim on the segment, and directives take the residual.
- A pointer raised when the arithmetic refuses must **displace** an open directive, with the displacement recorded and summarised (§8's rejection-summary rule applies).

**Two governance numbers survive, honestly named**: the overlap tolerance *θ*, and a default floor for δₘᵢₙ below which a directive is not worth a session of the segment. Both are §14 open decisions (governance in a stated range, like the FX budget), and both are what remains after the arbitrary part of v1.11's six has been replaced by arithmetic.

**What a pointer may never do**, stated as a list because each has been reachable at some draft of this lane: it may not amend a family; it may not supply a parameter; it may not create a grammar row; it may not size a position; it may not enter the item pipeline; and its observations may not be pooled with a quantified family's peer set, because the two were selected differently.

**Registration inputs the machine may not supply.** *New in v1.13; amends step 4. The four parts are unchanged; what changes is who may supply them.*

Neither an agent nor any automated process may supply δₘᵢₙ, *n*ₘᵢₙ, the registered sign, or a ratified pre-mortem. An agent may **draft** a pre-mortem, which is recorded with `author = agent, ratified = false` and blocks registration until the operator ratifies or rewrites it; the ledger records the author beside the text, per §8.

**The consequence, and it is the design working rather than a defect.** The scanner's steady-state output is a queue of registration-ready drafts blocked on exactly the two things only the operator may supply. **Widening the search does not shorten the fence**, and a layer that produced registered directives without the operator would have moved the pass condition to the party that raised the idea.

Registration is deliberately **not** fail-fast, and reports every missing part at once. Fail-fast exists to stop spending compute on an idea that has already died; registration spends no compute and its output is a worklist for a person, and handing someone one blocker at a time when four are known is a worse deliverable rather than a purer one.

### 3.7 The agent discovery layer

*New in v1.13. Procedure at the intake surface; apparatus in one respect, stated in §3.7.7. The §0.6 test is applied in §3.7.7 rather than asserted here.*

**§3.7.1 What it is, and what it inverts.** §3.3 discovers by subscription: enumerable universes are subscribed, every item in them enters, and the funnel decides. That design has one property worth naming before it is changed, which is that **the intake population is not chosen by anything with a view about it**; therefore §7.1's headline association, measured across the entire intake, measures the funnel's depth and nothing else.

The discovery layer inverts the order for the *evidence* lane only. Agents read permitted material, locate candidate mechanisms, and emit them as proposals; each proposal is then run fail-fast through intake ingestion, screened, mapped to a stream and turned into an observation directive. Two things about that sentence are load-bearing. First, the layer feeds §3.6, not §3.5; nothing it produces enters the item pipeline, so the intake population §7.1 measures on is untouched. Second, the agents emit **mechanisms and never episodes** (§3.7.3), so what is selected is a class of event, which is the level at which the published literature also operates.

**§3.7.2 The problem the layer creates, stated before its solution.** An agent that goes looking for promising ideas is doing selection conditioned on knowledge of what has already moved, and it is doing so at volume. This is the defect §1 attributes to the model and §3.6.6 relocates to the operator, relocated a third time and made cheap to repeat. It is worse than the operator's version in two respects and better in one.

Worse, because: i) the model's weights contain the price history the system will be evaluated on, and no data split reaches a leak inside the model; and ii) an operator raises perhaps a dozen hypotheses a year, whilst an agent raises that many in an afternoon, so the search widens by an order of magnitude and §6.4's fourth family must see the whole of it.

Better, because the agent's search is **auditable in a way the operator's is not**. Every document it read is a logged query; every proposal it made is a ledger row, including the ones that died at the first ingestion point; and its selection can be compared against a random draw from the same grid, which is an experiment that cannot be run on a person.

**§3.7.3 The exclusivity construction: keeping finding and evaluation disjoint.** The design requirement is that the material an agent selects *from* and the material a directive is scored *on* share no observations. The leak does not run through documents; it runs through the underlying price path, so a split by source or by document type is weaker than it appears. Two items describing the same issuer over the same weeks are not independent however different their text.

Four mechanisms, composable, and each of a different kind.

**i) Structural blinding, enforced by schema and by lookup.** The proposal type carries no field for an issuer, an instrument, a ticker or a dated episode, and the intake runner refuses any proposal whose text contains one, discarding the whole proposal rather than stripping the names from it. A proposal may say *clusters of open-market purchases by two or more directors of one issuer settled within five sessions*; it may not say what happened to a named company in a named month.

**The detector's first design was wrong, and the trace is what found it.** It flagged any two-to-five-letter capitalised token and any bare four-digit year, on the stated theory that bluntness was the safe direction: a false positive costs one re-raise, whilst a false negative costs the exclusivity guarantee. Run over thirty-six proposals drawn by discovery agents from live ASX, SEDI and MAR primary sources, it refused **thirty-four of thirty-six, a 94% false-positive rate, with no true positive among the refusals.** It tripped on `ASX`, `TSX`, `MAR`, `SEDI`, `ESMA`, `AFM`, `CIRO`, `UMIR`, `DAX` and on the years inside regulatory citations, for a reason no amount of tuning removes: **a regulator's name and an issuer's name are both proper nouns, and a pattern over an open vocabulary cannot separate them.** A filter refusing 94% of clean input is not a conservative filter; it is a filter that would have silently shaped the search to whatever survived it, which is the endogeneity §3.6.6 exists to contain, arriving through the containment.

**The repair is the architecture's own principle rather than a better pattern.** *The model classifies; the table decides.* A tradeable entity is a member of an enumerable set, namely the security master and the discovery markets' listing lists, so the binding layer is a **lookup against a closed list**. Patterns are retained only where the grammar genuinely is closed: instrument identifiers (ISIN, exchange-prefixed ticker) and legal-form designators, which attach to firms and never to regulators. A seeded regulatory lexicon carries the vocabulary that is not an issuer, and it grows by operator mapping in the same idiom as §3.6.5's stream table, by use rather than by anticipation, each addition recorded.

**Dates are demoted from hits to context.** An episode is an entity bound to a time; a mechanism referring to a review month, a statutory deadline or a regulatory calendar is doing its job. Dates are therefore reported beside an entity hit and never constitute one alone, and removing that single rule removed the largest share of the false-positive rate.

**A ticker is a symbol, and is matched only in a symbol's shape.** *New in v1.14 (P76), after the trace of 27 August.* The lookup's first build passed names and tickers to the fence as one set. Tradeable tickers are not words, but they are spelled like them: 7,268 of the 10,388 US tickers are four characters or fewer, and the loader's minimum-length and lexicon filters were applied to issuer names only, so the ticker half entered unfiltered and the fence read `Law`, `Are`, `For`, `Help`, `Note`, `Any`, `Such`, `When` and the single letters `B`, `C`, `D`, `E`, `F`, `H`, `J` as tradeable entities. Over the thirteen documents of the US pre-archive corpus it recorded 257 hits across 41 distinct tokens, essentially all of them false. **The binding rule is therefore split by kind, because the two kinds are matched by different rules.** An issuer *name* is a word and keeps the span lookup unchanged. A bare *ticker* is a symbol and matches only in a symbol's shape: **all capitals, three characters or more.** Two characters is too short to carry the signal, `FR`, `IT` and `ON` being tickers and also ordinary prose, and any other case is a word. Exchange-prefixed and explicitly labelled forms (`ASX:BHP`, `(ticker: BHP)`) are closed grammars and are unaffected. The two sets are held apart rather than merged because sixty-five US issuers have a one-word name identical to their own ticker, `Ball`, `Dole`, `Coty`, `Angi`; merging them would have made the stricter ticker rule govern their names as well.

**The cost, stated rather than implied.** A bare ticker written in lower or title case is now invisible to the fence: `purchases at Aapl` and `purchases at aapl` pass where `purchases at AAPL` is refused. That is a false negative, and under §0.8's reversed asymmetry a false negative is the expensive direction, paid in the exclusivity guarantee rather than in a re-raise. It is taken here because the alternative measured worse. A common-word filter over the ticker set would have removed at least ninety-five real US issuers from the fence in capitals as well, and would still have left `CFR`, `LII`, `III` and `VII` needing a lexicon row. The issuer's *name* remains matched in any case, so the residual is confined to a proposal that names a ticker and never its issuer. Five lexicon rows land with the rule (`CFR`, `LII`, `ACT`, `III`, `VII`): legal-citation and hosting-site vocabulary that collides with real tickers, added by operator mapping in §3.6.5's idiom, by use rather than by anticipation.

*Superseded, v1.14 (P77). The sentence below read: "on the same corpus plus six labelled plants, the repaired fence recorded **zero false positives and zero false negatives**, catching every planted issuer name, ticker and identifier whilst passing every regulatory citation." That reading is withdrawn as unreproducible: the six plants were defined inline in a shell that was never committed, and no labels survive in the corpus file. The stale wording is annotated here rather than rewritten silently, per §12.7.*

**Without a master the check refuses to score.** Patterns alone are not a fence, so a run with no security master loaded does not fall back to the weaker half; it emits `security_master_unavailable` on every machine-origin proposal. §0.8's asymmetry is still reversed here, but it now buys something: against the committed labelled set at `docs/labelled_proposals.json` and the US security master, the fence with P76's rule refuses **0 of 36 drawn class-level mechanisms**, against **3 of 36** on the fence as v1.13 left it, on `Note`, `T` and `It`. The labels carry provenance `model_clerk` and are not the hand labels §13 row 21 specifies, so the reading is provisional in two respects and is recorded in that row rather than claimed here.

**The two arms of the audit are not the same kind of thing, and reporting them as one was itself a defect.** *New in v1.14 (P79).* The class-level arm is **drawn**: it is what the discovery agents actually swept, so the share of it the fence refuses is a rate, divided by its own n and by nothing else. The second arm is **authored probes**, six subjects written one per route into the fence: a legal-form designator, a bare ticker in capitals, a bare ticker in title case, an exchange-prefixed identifier too short for the ticker rule, an ISIN, and a one-word issuer name equal to its own ticker. **A chosen set has no sampling frame, so a proportion over it estimates nothing.** Reported as "1 of 6 (17%)", it reads as the fence's error rate on real episode-level material, which it is not and cannot be; change the probe set from six routes to twelve and the percentage halves whilst the fence is untouched. The probe arm therefore reports **coverage**, namely which routes are closed and which are open by name, and prints no percentage. On the committed set: **5 of 6 routes closed, the open one a title-case bare ticker**, which is the residual named above. The term *episode-level* is not used of this arm anywhere, because it implies a sample of episode-level material and there is none. **A drawn episode-level sample would yield a rate**, and row 21's eventual 200 may supply one; until it does, this arm is coverage.

**A designator suffix is not on its own a firm.** *New in v1.14 (P80).* Patterns were retained for closed grammars on the argument that a legal-form suffix attaches only to a named firm. It attaches to a rulebook heading too: `Trust Holdings and Transactions` is the heading of Rule 16a-8 and matched the designator grammar exactly as `Vodafone Group Holdings` does. The branch therefore fires only where two further conditions hold on the span's **leading token**: it is **proper-noun-shaped**, having an initial capital, two or more characters and letters throughout, which excludes a bare initial and a section number; and it is **absent from a registered rulebook stopword set**. The set is separate from the lexicon because it answers a narrower question, not *is this token an entity* but *may this token head a legal-form span in a rulebook without a firm being named*, and it is **seeded from evidence rather than from anticipation**, at one token, because one is what the corpus produced. It grows by operator mapping and each addition is recorded, exactly as the lexicon does.

**The set is registered, and that is the load-bearing part.** It sits in the discovery layer's parameter object and reaches its hash. A value that changes what the fence refuses whilst living in a module constant cannot be attributed to a registration: the same corpus would give two different refusal sets under one hash, and a row added to widen what a sweep lets through would leave nothing on the record. Adding a stopword is therefore a re-stamp, which is the cost and also the point. **The lexicon sits in the same object on the same argument** (P81): it was the defect one level up, recorded here when P80 landed and closed before the version shipped, so a run's fence is now attributable to its hash in both of its vocabularies rather than one.

**The cost, stated rather than implied.** A firm whose name *begins* with a stopword loses this branch: `Trust Holdings Inc` would not be flagged by it, and would have to be caught by the name lookup instead. The span matcher is greedy, so a stopword anywhere but first is harmless and `Northern Trust Holdings` leads on `Northern`. The residual is confined to a firm whose first word is a rulebook noun and whose name is absent from the security master.

**The residual, stated.** A paraphrase that identifies an issuer without naming it (*the large iron-ore producer*) defeats a lookup exactly as it defeated a pattern. Nothing here reaches it, and §10 carries it.

**ii) Disjoint return paths, by partition or by market.** `scoring_mode` is recorded on every directive and printed beside every verdict, taking one of three values. **The registered default is `cross_market`**, settled here rather than left as a §14 open decision; the alternative is available per class and overrides the default where declared.

| `scoring_mode` | Construction | Cost |
|---|---|---|
| `cross_market` **(registered default)** | The agent reads only markets outside §0.7(f) and material predating the archive's opening boundary. Mechanisms generalise across markets; specific episodes do not | Generalisability is assumed rather than proven, and the assumption prints on every verdict and is measured by §13 row 24 |
| `disjoint_partition` | A fourth archive partition, **Discovery**, readable by agents and by nothing else. Gate 0 asserts the separation exactly as it does for manually injected items | Archive span, from a two-to-three-year archive that already leaves only nine to twelve evaluation months |
| `forward_only` | The agent read in-universe material, so the directive scores only on items dated after `registered_at` | Slow. Forward-only collection accumulates little before the §0.6 instruments report |

The field is not decoration. §Σ.3's second control surface holds that a verdict answers *did what I measured pass* and never *did I measure what I said*; `scoring_mode` is that surface applied to the exclusivity claim itself, and it answers the question *what kept the finder out of the measurement*.

**Why `cross_market` is the default, and what the choice costs.** The archive is short: a three-way split of a two-to-three-year corpus already leaves nine to twelve evaluation months, and a fourth Discovery partition takes its span from the same total. `cross_market` costs nothing in span; therefore it is the default, and `disjoint_partition` is retained as a per-class override for any class where the generalisability assumption is implausible. **The cost is that the saving is bought with an assumption**, namely that a mechanism observed on one market's disclosure regime holds on another's, whilst the episodes do not carry across. That assumption is disclosed on every verdict and measured by §13 row 24 wherever both markets are readable; where they are not, it stands as an assumption, and saying so is the whole of what this paragraph is for.

**The default settles which construction is used, never whether one exists.** An event class must be positively declared discoverable, per §13 row 22; a class absent from that declaration is refused with `scoring_mode_unsatisfiable`, default or no default. A directive with no separation between finding and evaluation measures the finder, and a default that silently supplied one would be the fallback-into-a-default this architecture refuses at every other refusal point.

**iii) The query fence, extended to machine reads.** P59 closes conditional-return queries on a directive's target population until `registered_at`. The discovery agent has no path to returns and therefore cannot log such a query; nevertheless every sweep is logged as a mechanism-level query with the corpus it read, so that the query log is a complete record of the search rather than a record of the operator's half of it. A population already carrying a pre-registration conditional-return query refuses the proposal at intake with `registered_at_unstampable`, whichever party ran the contaminating query.

**iv) The import fence.** The discovery module reaches no module carrying prices, forward returns, gate verdicts or graveyard outcomes; the check walks the transitive import closure and is run at process start as well as in the test suite, because a fence checked only in tests is a fence that holds only in tests. Annex A.2 already uses an import fence to keep model-mediated similarity out of peer construction, so the instrument is not new, only newly pointed.

**The honest limit.** Exclusivity of *data* is achievable and is enforced mechanically. Exclusivity of *knowledge* is not, because the weights are not partitionable. Mechanism-level emission lowers the resolution at which recalled price history can be exploited; it does not remove it, and no rule in this section pretends otherwise. What remains is measured rather than argued, in §3.7.5.

**§3.7.4 Fail-fast ingestion, and the obligation attached to it.**

**The rule.** Intake applies an ordered sequence of ingestion points; as soon as one fails, the idea is abandoned and the next one starts. §2 already sequences gates by kill rate per unit of compute, and this is the same principle applied to the surface upstream of the gates, where an agent scanner makes throughput the binding constraint for the first time.

**The ordering is pre-registered and sits in the parameter object**, because a different order produces a different reason-code distribution over the same corpus and §7.2's attribution would read the difference as a change in the world. It is ordered by kill rate per unit of compute, subject to one override: the three fences run before anything opens a document, since a cheap refusal that has already read the thing it refuses is not cheap.

| # | Intake ingestion point | Reason code |
|---|---|---|
| 1 | Reserved-field check: the proposal populates nothing the agent has authority over | `agent_overreached_schema` |
| 2 | Entity fence: no issuer, instrument, ticker, corporate designator or dated episode | `proposal_names_entity` |
| 3 | Partition fence: the source sits in a partition a discovery agent may read | `discovery_partition_violation` |
| 4 | A mechanism is stated in one sentence | `event_definition_absent` |
| 5 | An intended population is stated | `measured_on_absent` |
| 6 | The (class, population) pair carries no open pointer | `duplicate_of_open_pointer` |
| 7 | The query log shows no pre-registration conditional-return query on the population | `registered_at_unstampable` |
| 8 | Some exclusivity construction exists for the class | `scoring_mode_unsatisfiable` |
| 9 | The cited document retrieves | `source_inaccessible` |
| 10 | Every populated claim field carries a provenance tag | `provenance_tag_absent` |
| 11 | No load-bearing claim carries `recollection` provenance | `claim_provenance_recollection` |

Point 9 closes the `source_inaccessible` gap the week plan of 17 August recorded as outstanding in §3.6.3's taxonomy.

The same discipline applies on the second surface, where items arriving from a stream a registered directive names run the §3.5 path in the order: retrieval; `document_type`; anchor provenance; observation anchor; ingestion lag; extraction-class suspension; extraction schema completeness; issuer resolution; catalyst corroboration; catalyst duration; and registration precedence. Each carries the manuscript's existing code where one exists, and a new code where the branch was previously unnamed.

**The obligation, which is not optional.** An abort that writes nothing shrinks §7.1's denominator silently. The headline instrument measures funnel depth against forward return across the *entire* intake; therefore an idea that vanishes at ingestion without a ledger row does not make the funnel look clean, it makes the funnel unmeasurable. Every abort writes i) its reason code, ii) the set it was measured on, and iii) a rendered §8 rejection summary, before the next idea begins. **Fail-fast is a compute discipline and never a bookkeeping one.**

**The censoring, and its antidote.** Stopping at the first failure censors the reason-code distribution; a code that only ever fires at position nine is invisible whilst position three keeps firing. §7.2's answer for gates applies unchanged: a pre-registered audit fraction runs the **full panel** regardless of early failures, and every attribution statistic computes there exclusively. The audit sample is drawn deterministically from a hash of the subject identity and the parameter hash, so that it is replayable and cannot be redrawn once the answer is known. §9.4's trace harness runs full-panel always, for the reason it already gives.

**§3.7.5 The random-mechanism control arm.** *This is the instrument that makes the discovery layer falsifiable, and it belongs in §Σ.4's list beside the placebo and the unconstrained-model control arm.*

For every *N* agent proposals, *M* mechanisms are drawn uniformly at random from the reachable event-class by population grid, are registered identically, are scored identically, and carry `origin = random_control`. The difference between the two arms on the evaluation partition **is** the selection effect, measured jointly with any genuine skill.

The draw is seeded, the seed is pre-registered and recorded with the draw, and the ratio *M/N* is fixed before the first sweep; the same discipline §7.5 applies to the placebo, for the same reason, which is that a control redrawn after the treatment's result is known is not a control.

**A ratio of zero is refused rather than floored.** A sweep with no control arm produces directives whose selection effect nothing can attribute, which makes the discovery layer unfalsifiable and therefore makes running it worse than not running it. The implementation raises rather than substituting a working value for a broken one; (n.b., this is the same rule as the refuse-to-score semantics of §Σ.3, applied to a configuration rather than to an input).

**The kill criterion, pre-registered.** Reported in §3.6.8's three-verdict idiom, so that failing for want of power says so rather than passing by it:

| Verdict | Condition | Consequence |
|---|---|---|
| Agent selection carries information | Separation exceeds the registered δ at *n*ₘᵢₙ in both arms | The layer stays on, and its cost is justified on measurement rather than on plausibility |
| `killed_negligible` | Two one-sided tests demonstrate separation within ±δ | **The discovery layer is refuted and switched off.** Not tuned, not extended, not given a second prompt |
| `undetermined_at_budget` | Either arm is below *n*ₘᵢₙ | Recorded as undetermined, never as a quiet pass |

**What a positive result means, stated so that it is not over-read.** It means the agent beats a random draw. It does not mean the agent is unbiased, and the two are not the same claim; an agent whose recalled price history is genuinely informative would also beat a random draw, and this instrument cannot separate that from skill. §10 carries the point in those words.

**§3.7.6 Capacity, queueing and the counting family.** A machine raises registrable pointers faster than a short design segment can absorb them, so §3.6.8's admission arithmetic binds immediately rather than eventually. Two rules follow.

**Admission is by smallest registered span first**, ties broken by registration time. This maximises directives per unit of segment; more importantly, neither the agent nor the operator scores merit at admission, since a proposed priority would return ranking to the party that raised the idea.

**Machine-origin drafts queue and may not displace.** Only operator-origin pointers retain the displacement right v1.11 gave them. Without this rule the scanner evicts the operator's own directives simply by out-producing them, which converts a capacity rule into a takeover; (n.b., the displacement summary remains operator-authored under §8, and the implementation refuses a template-rendered one).

**§6.4's fourth family gains a three-tier counter.** A scanner makes the proposal count and the registration count differ by orders of magnitude, so reporting one number would mislead in whichever direction the author preferred. All three are disclosed on every published result: i) **proposals raised**, including every one abandoned at the first ingestion point; ii) **pointers registered**, which is the subset consuming design-segment span and entering the reuse ledger; and iii) **promoted**, which is the subset crossing into an evaluation-scored cohort. None divides anything. Only the third enters the Benjamini-Hochberg step, with its provenance displayed beside its percentile.

**§3.7.7 The §0.6 test, applied.** The rule is tested rather than asserted past, and the answer splits in the way P55's answer split.

**Procedure.** The intake runner, the screen, the fences, the reuse ledger and the rejection summaries are of the same class as §9.4's trace harness and §9.5's review harness: they add no gate, no family, no grammar row, no cost tier and no field the funnel reads at decision time. Directives over streams already flowing were settled as procedure by P52 and remain so; a machine raising the pointer changes the counting, not the cost.

**Apparatus, in one respect, and it is the respect that matters.** Cross-market discovery requires *reading* material from markets outside §0.7(f). Hand collection of that material under §3.6.5's manual-observation protocol is not apparatus, being of the same class as §9.4's tracing. **A production ingestion adapter for a discovery corpus is apparatus**, however modestly it is described, and takes an Annex A.1 row with its dependency named. The discovery agent itself, being new code that makes model calls at volume, likewise takes an Annex A.1 row for its **automation**, on the same terms as the literature lane's Tier 2 row: automation follows demonstrated value and not the reverse.

**What this permits before the instruments report.** An operator running sweeps over hand-assembled corpora, at zero capital, producing directives that measure on streams already subscribed. **What it does not permit**: subscribing to a discovery corpus feed, and running the layer as a standing automated process. The asymmetry will be irritating in precisely the cases that feel most promising, which is the rule working rather than failing.

---

## 4. A closed strategy grammar

### 4.1 The grammar

A strategy is a tuple *(bucket, entry, exit, direction, asset)*; each exit family carries exactly **one** stop.

| Component | Pre-registered grid |
|---|---|
| Entry: moving-average crossover | (10/50), (20/100), (50/200) |
| Entry: channel breakout | N ∈ {20, 55} |
| Entry: RSI reversion | (14; 20/80), (14; 30/70) |
| Entry: gap continuation/fade, T+1 | {2%, 4%} |
| Entry: realised-vol breakout | σ₂₀/σ₁₂₀ above {1.5, 2.0} |
| Entry: event-anchored | offset {0, 1, 2} sessions after the anchor |
| Exit: fixed horizon + horizon-scaled stop | (5; 2.5), (21; 5.5), (63; 9.5) × ATR(14) |
| Exit: trailing stop *(is its own stop)* | {1.5, 2.5, 3.5} × ATR(14) |
| Exit: opposite signal + stop | inversion per family; **provisional** 5.5 × ATR |
| Fill convention | fixed; §4.3 |
| Sizing | fixed-fractional, stop-normalised; outside the searchable space |

**Direction restriction.** For the insider-filing catalyst type only *purchases* admit tuples, and only long ones: the literature finds purchases informative and sales not. This is a theory-driven restriction, not a fitted parameter.

**§4.1.1 The horizon-scaled protective stop.** Constant breach probability requires k ∝ σ√h; with the ATR-to-volatility ratio measured on the calibration segment, the multiples 2.5 / 5.5 / 9.5 × ATR(14) deliver ≈ 12% / 9% / 9% at h = 5 / 21 / 63. The flat 4.0 × ATR they replaced delivered ≈ 1% / 22% / 48%.

**§4.1.2 Opposite-signal exits.** Inversions per family; event-anchored is **inadmissible** (nothing recurring to invert). The 5.5 × ATR multiple is **provisional**, traceable to a frozen per-family realised median that does not yet exist (§13).

### 4.2 The event-anchored family on a peer set

Same ICB industry, listing market, catalyst type and median-notional bucket, vintage as of `t_pub_observed`. Industry precedes size because drift after a catalyst is a property of business exposure. Construction **errs narrow**, widening on a fixed ladder with each widening logged; market and catalyst type never widen. Failure at the broadest step → `peer_set_insufficient`. Own-asset history is a reported diagnostic and never gates.

### 4.3 The execution convention

Entries and signal exits fill at the **open of the session after signal completion**; broker eligibility, instrument selection and live locate sit outside this convention and outside the research boundary entirely (§5.9). Stops fill by comparison: *open at or beyond the stop → fill at the open; else fill at the stop plus half the cost-tier spread.* Gap families are named **T+1**. Gate 0 asserts no entry price at or before the tuple's anchor. §7.5 reports expectancy under this convention and a same-session-close alternative. The convention forgoes part of any front-loaded event window, which §13's capture-rate row measures rather than assumes.

### 4.4 Reachability

**Feasibility** (position = 0 where the stop exceeds 30% at full size, 15% at the multiplier floor) and **regime** (notional-capped below 7.5% / 3.75%), published separately. The matrix is indexed (exit family × ATR decile × multiplier regime) over the §0.7(f) universe; zero cells carry `position_below_clip_floor`. At the assumed commission, fixed-horizon exits are sizable to ATR ≈ 12.0% / 5.45% / 3.16% at full size; all four boundary constants inherit §0.7(c)'s verification.

***RESTORED as a derivation, 27 August 2026 (§0.11, P100). The §0 decision that blocked this section has been taken, and restoring it removes a rule rather than reinstating one.***

**The two regime constants are withdrawn as constants and are not replaced by new constants.** They were never independent of §6.7:

```
§6.7 at 75.0 bps of £100,000 and a 10% stop  =  £750 / 0.10  =  £7,500  =  7.50%
§6.7 at 37.5 bps of £100,000 and a 10% stop  =  £375 / 0.10  =  £3,750  =  3.75%
```

**7.5% and 3.75% ARE §6.7's arithmetic evaluated at a 10% stop**, once at full risk and once at the cap floor. Carrying them here as separate numbers stated one rule twice and invited the two copies to drift. **This section now states the derivation and §6.7 states the rule**, which is one rule and a derivation where there were two rules.

**The regime cap is therefore:** `notional_cap = risk_budget / stop_distance`, with `risk_budget` from §6.7's base unit and cap stack, evaluated at the regime's stop. **Feasibility is unchanged and was never clip-dependent:** position = 0 where the stop exceeds 30% at full size, 15% at the multiplier floor.

**What is still withdrawn, and now for a stated reason rather than an undecidable one.** The three ATR bounds **12.0% / 5.45% / 3.16%** were computed against a clip floor of £2,500 and an assumed commission. **The floor is now derived (§13 row 30) and does not derive today**, so `position_below_clip_floor` has no threshold to test against and the matrix's zero cells cannot be located. **The bounds return the moment §13 row 29 is set and row 1 closes**, by arithmetic and with no further decision, which is precisely what was not true before this decision was taken.

***RESTORED as a derivation, 27 August 2026 (P110), row 29 being set at 10 bp. They return as a FUNCTION and not as three constants, and the reason is a defect in this section.***

**The derivation was recovered from the published trio rather than asserted.** A position is `risk_budget / stop_distance`, the stop is `multiplier x ATR`, and the position must reach the clip floor, so

```
ATR_max  =  risk_budget / (multiplier x clip_floor)
```

**Evaluated at the withdrawn GBP 2,500 clip floor with §6.7's GBP 750 and GBP 375 and multipliers 2.5 / 5.5 / 9.5, it reproduces 12.00% / 5.45% / 3.16% at full size and 6.00% / 2.73% / 1.58% at the cap floor. Six of six, exactly.** That is what makes what follows a derivation and not a new rule.

**Against the derived floor the bounds are a function of SHARE PRICE**, because the floor is. At the calibration price of USD 43.79 the floor is USD 6,055, that is about GBP 4,694, and the bounds are **6.39% / 2.91% / 1.68%** at full size and half of each at the cap floor. At USD 15 a share they are 2.97% / 1.35% / 0.78%; at USD 150, 6.43% / 2.92% / 1.69%.

***THE COST, STATED: the reachable ATR range roughly HALVES***, from 12.0% to about 6.4% at h = 5, because the derived floor is nearly twice the withdrawn clip. **A higher floor admits fewer volatile names, and that is the price of deriving the floor from a real cost rather than choosing it.**

***A DEFECT IN THIS SECTION THAT ROW 29 EXPOSES AND DOES NOT REPAIR.*** The matrix is indexed **(exit family x ATR decile x multiplier regime)** and **a price-dependent bound does not fit in that index**. Publishing three constants again would require fixing a reference share price, and **a chosen reference price is a chosen parameter wearing a derivation's clothes**. So the bounds are evaluated **per candidate**, and adding a price dimension to the matrix would be **apparatus** under armed §0.6 and takes a §0 decision. Recorded, not taken.

*Everything here inherits §13 row 1's PROVISIONAL status.*

**The paragraph below is the record of what was withdrawn, kept rather than replaced.**


***A naming defect recorded and deliberately not repaired here (P96).*** `capital_exceeds_clip_floor` marks a **zero** cell, that is one where the position **fails to reach** the floor, and the name reads as the opposite: *capital exceeds the floor* is the passing case. The name is left alone because renaming a reason code is a change to the registry and takes its own decision; it is recorded so the next reader meets the defect rather than the behaviour. ***One premise of that sentence is false, found 27 August 2026 (P106) and recorded beside it rather than over it.*** **It is not in the registry.** `ALL_CODES` holds forty codes and none is this one; the string appears in three documents and in **no Python file**. So renaming it today is a find and replace over prose, and renaming it once row 29 sets the floor and the code enters `codes.py` costs a registry entry, an emitting branch, a test, a §8 template, a resurrection predicate and **every ledger row already stamped with the old string, which rule 4 forbids overwriting**. ***TAKEN 27 August 2026 (P108), on delegated authority, and this sentence is the only place in §4.4 that still carries the superseded name.*** The zero cells now carry **`position_below_clip_floor`**, which names the subject, the relation and the object and cannot be read as its own negation. **The window was the whole argument for taking it now.** The name was prose on 27 August; it becomes a registry entry the moment §4.4's matrix is implemented against a derived floor, and the same rename after that costs an emitting branch, a test, a §8 template, a resurrection predicate **and every ledger row already stamped with the old string, which rule 4 forbids overwriting**, leaving two names for one state for ever. `clip_floor_unreached` was rejected because it collides in the eye with `clip_floor_unreachable_at_any_size`, a **market-level** fact against a **cell-level** one, which is how the original defect was made. **It does NOT enter `codes.py` today**: §4.4's matrix is not implemented, and a code defined with no branch that emits it is the untested branch `test_every_defined_code_is_emitted` exists to refuse.

---

## 5. The gate stack

### 5.1 Two-tier semantics, escalation, explore and shadow

**Hard** gates terminate batch processing with a named reason; **advisory** gates annotate. The advisory multiplier product is **floored at 0.5**; a floored product still below the clip → `advisory_haircut_below_clip`, counted as a kill by the flagging gate.

**Escalation.** Trigger: ≥ 2 advisory flags and a Gate 6 percentile between the acceptance floor and the 95th. Cap initially 10% per review period. **The cap moves both ways with a floor:** halves when the override cohort underperforms, doubles (ceiling 10%) when it outperforms or is indistinguishable, no comparison below twenty completed override observations, never below 2.5% without a §0 decision.

**The explore arm.** A pre-registered 10% random sample of candidates clearing every hard gate but falling below Gate 6's percentile floor is accepted at the **minimum clip**, tagged, capped at **four concurrent positions**, excluded from headline acceptance statistics, reported as its own series, and counted in full by §6.4. It populates the below-floor region the association otherwise never observes.

**The shadow cohort.** Candidates clearing every gate except the **tradability floor** run with full verdicts, forward tracking and zero capital (§7.6, §0.10).

**§5.1.1 The manual-acceptance checklist.** Mechanical combination beats informal judgement almost invariably; the licensed exception is the **broken-leg countervailing**. Four questions, serialised and hashed before the outcome is known: **name the fact** (source and timestamp strictly prior to `t_pub_observed`, verified against its source before acceptance, failures surfaced as stated-versus-found); **establish invisibility** (which gate would have used it and why the pipeline structurally cannot); **establish relevance**; **pre-commit to falsification**. The override cohort carries its own forward series.

### 5.2 The gates

Every gate writes the size of the set it measured beside its verdict; a verdict over an empty set is not a verdict.

| # | Gate | Tier | Mechanism |
|---|---|---|---|
| 0 | Data sanity | Hard | Completeness, corporate actions; crisis-window coverage; peer-event completeness; no entry price at or before the anchor; notional as of `t_pub_observed`; ICB at observation vintage; **partition separation, including manually injected items** (§7.5) |
| 1 | Tradability & cost | Hard | **Universe membership** (§0.7f); ticker and issuer resolution; point-in-time notional against the floor, **shadow-routing, not a kill** (§0.10); full-size reachability; clip economics; price floor; history span; grammar membership; **ingestion lag** (§3.5.1); **break-even ceiling at midpoint cost** |
| 2 | Staleness | Hard / advisory by thesis and anchor | Percentile-calibrated abnormal return (§5.3) |
| 3 | Prior art | Advisory | Taxonomy; decay prior; admissible horizons; family admissibility tests (§5.4) |
| 4 | Correlation & benchmark fit | Hard above ceiling | Strategy-return correlations incl. crisis windows; panel R²; ENB |
| 5 | Regime | Advisory | Per-market deterministic classifier |
| 6 | Expectancy | Hard on floor + minimum sample | Permutation and buy-and-hold nulls (§6.2); deflated Sharpe; survivor risk profile reported alongside (§6.5) |
| 7 | Robustness | Hard on enrichment | Full grid under cost tiers, gated at midpoint |

**§5.2.1 Crisis windows by rule.** Any ≥ 20% drawdown of the listing market's benchmark index, the same series §5.6 names, from a 250-session rolling peak to half-recovery, minimum 20 sessions, on completed history.

**§5.2.2 Break-even before compute.** Required gross per round trip, £5,000 notional, conservative / midpoint bps. Gate 1's ceiling and Gate 7's gate read the **midpoint**; the conservative figure travels as an advisory flag.

| ADV bucket | US *(published)* | **US, recomputed ≤** | UK main, long *(published)* | UK main, recomputed |
|---|---|---|---|---|
| >$1bn | 22.5 / 19.5 | **20.0 / 17.0** | 72.5 / 69.5 | **struck** |
| $100m–$1bn | 42.5 / 32.5 | **40.0 / 30.0** | 92.5 / 82.5 | **struck** |
| $10–100m | 112.5 / **82.5** | **110.0 / 80.0** | 162.5 / 132.5 | **struck** |
| $1–10m | 312.5 / 212.5 | **310.0 / 210.0** | 362.5 / 262.5 | **struck** |
| **< $1m** | **pending §13 row 14: measured, not assumed** | pending; **the tier is now REACHABLE** | **pending §13** | **struck** |

***RECOMPUTED 27 August 2026 (P111), against a measured cost and a registered bound. The published columns are retained beside the recomputed ones and no cell is edited in place.***

**What changed.** The published figures rest on **an assumed £6.25 round trip on £5,000 notional**, a **12.5 bp** fixed-cost basis that §0.7(c) records was *recovered backwards from the clip definition*. **The replacement is a BOUND and not another assumption:** §13 row 29 registers 10 bp as the maximum tolerable fixed cost and §13 row 30 defines the clip floor as the size at which cost *equals* it, so **every admissible position carries at most 10 bp of fixed cost by construction**. Each recomputed figure is therefore an upper bound where the published one was an estimate. **Every figure falls by exactly 2.5 bp.**

**A cross-check that was not arranged:** row 1's model evaluated directly at £5,000 notional at the calibration share price gives **9.39 bp**, below the 10 bp bound as it must be. *The bound is published rather than the point estimate, because the bound needs neither a share price nor an FX rate.*

**The UK column is STRUCK and not recomputed.** At the registered tolerance UK Main Market carries `clip_floor_unreachable_at_any_size`, and unlike the AIM Annex A.1 row it does not return at 12.5 bp either: it needs a tolerance above 61.4 bp, far outside row 29's derived range. **A break-even for a venue no position can reach is a number describing nothing.** It is retained with that stated rather than deleted.

**The column heading changes too.** It read *"AIM / US / short legs"*. **AIM is excluded at the registered tolerance on COMMISSION** (0.05% a side is 10 bp round trip on its own), and the short legs are not currently traded, the insider family being long-only by grammar. **The column is the US column and is now named one.**

**No conclusion moved, and the check is recorded as run.** Gate 1's ceiling and Gate 7's gate still read the midpoint; the bucket ordering is unchanged by a uniform shift; and `delta_min_floor` = 25 bps stands, its stated ground being that the cheapest break-even could never be traded below it, which held at 22.5 and holds at **20.0**. *The floor is now more conservative than it needs to be by 5 bp rather than 2.5.* Worked in `docs/BREAKEVEN_RECOMPUTE_2026-08-27.md`.

***Erratum B is DISCHARGED, 27 August 2026 (P111): both tables are now bounded by the same dimensionless 10 bp, which is a property of the TOLERANCE and not of a notional, so they are comparable line for line for the first time. That is the dividend of making the tolerance explicit.*** *Erratum B, v1.13: this table is computed on **£5,000 notional**, as its opening sentence states; §0.10's microcap break-even table is computed on the **£2,500 minimum clip**, at which the fixed round-trip cost is 25 bps. The two are not comparable line for line, and no number in either table is changed by this erratum.*

The sub-$1m row exists because §0.10 routes those candidates to the shadow cohort; **it is not populated, and no microcap cell can be evaluated until it is.**

### 5.3 Staleness (Gate 2), percentile-calibrated, with two named carve-outs

AR_k over the k ∈ {5, 20} sessions ending at `t_pub_earliest`, beta-scaled, with spike ratio S = σ₂₀/σ₁₂₀. **A threshold at its own base rate is not a threshold**: media covers movers. The kill is at a **stated percentile of the AR₂₀ distribution among covered names**, measured on the design segment, the percentile committed **before** the distribution is scored. Per-candidate output: base-rate distribution, candidate percentile, verdict. An enrichment test is not used here: enrichment is a set statistic and Gate 2 judges one observation.

Tier: **hard** for anticipation theses, **advisory** for trend expressions, and advisory in two named cases where the gate's causal model does not hold:

- **Filing-anchored event theses.** A pre-publication run-up may be leakage that predicts continuation rather than evidence of completion. Run-up magnitude and its sign relative to thesis direction are logged; the percentile is computed; the kill is withheld.
- **Live offer periods.** Where a firm offer under the takeover rules is live and unlapsed, the price is not drifting on decayed information; it is pinned near a cash offer, and the residual spread is compensation for deal-break risk, which is forward-looking and unpriced by the run-up. Gate 2 reports and does not kill. This is narrow: the state is regulator-governed and machine-detectable, and it lets the candidate reach the gate that should decide it: Gate 4, whose crisis-correlation delta is designed to detect exactly the return profile risk arbitrage carries.

Both cohorts are separable in §7.1.

### 5.4 Prior art (Gate 3): taxonomy, decay priors, horizons, and family admissibility

The model classifies; the table decides; the extracted claimed horizon is a consistency check. The taxonomy and per-signal categorisation derive from the open-source cross-sectional dataset (Chen and Zimmermann, 2022), consumed as **data**, not derived from its GPL-licensed code, with the caveat that its decay evidence is US-measured. Decay priors follow McLean and Pontiff (2016).

| Anomaly class | Admissible horizons |
|---|---|
| **Insider purchase (PDMR / Form 4)** | **{5, 21}** |
| Short-term reversal | {5, 21} |
| Trend / momentum | {21, 63} |
| Post-earnings drift | {21, 63} |
| Seasonality | {21, 63} |
| Low volatility / carry | {63} |
| Relative value | {21, 63} |
| Event-driven (other) | {5, 21, 63} |
| **Unclassified** | **{63}, the narrowest set** |

**The unclassified default is inverted.** It previously admitted all three horizons, which meant the least-understood catalysts inherited the *widest* admissibility, and after §0.9's reorientation, that made the permissive branch a fast lane into the most reachable cell in the grammar. Unclassified now takes the narrowest set and retains its advisory flag.

**§5.4.1 Insider-purchase admissibility.** A candidate admits only where **all** of the following hold, each a deterministic read of a field the notification form already carries:

1. **Net increase in beneficial economic interest.** Custody transfers between accounts, involuntary round trips executed by a broker rather than instructed, and scheme awards all leave exposure unchanged and carry no information. The literature's finding rests on an insider voluntarily increasing exposure with their own capital.
2. **Open-market acquisition.** Save-as-you-earn grants, partnership-share purchases and option vesting are compensation.
3. **Qualifying filer.** Directors and senior managers. Persons closely associated are flagged and excluded from the primary cohort pending their own base rate (an Annex A.1 predicate): the literature finds abnormal returns for insider purchases and none for large shareholders.

Headline categories cannot decide any of these (§2), so the body parse is mandatory.

**Materiality of the economic change.** Test 1 is a change in beneficial economic interest, not merely a non-zero one. The literature supplies a **paper-sourced candidate parameterisation** (a trade of at least 0.1% of market capitalisation, the filter separating the 462 bps panel from the 165 bps panel in §0.5), recorded as the prior for §13's threshold row. It is **not adopted as a fitted constant**: the threshold is a calibration row with the paper's estimate as its prior, and a threshold fitted on this archive would be inadmissible under §3.6.4.

**News-adjacency flags (advisory, paper-sourced windows).** Two flags, both advisory, both with windows taken from the source paper's own design and fixed before contact with this system's data:

- `insider_purchase_ma_adjacent`: a merger or offer announcement within the paper's stated window of the filing. The documented effect on this cohort is approximately zero.
- `insider_purchase_ceo_change_adjacent`: a chief-executive replacement within the paper's stated window; documented as a weak reduction.

**No general news-adjacency flag exists, and its absence is deliberate.** A recollection-tier version of this restriction would have flagged all proximate price-sensitive news; verification found that general news, including prospects news, does **not** reduce the reaction (§3.6.7). The flags are advisory, so they cannot enlarge the hard-reachable set and the change classifies as a **restriction** under §3.6.4. Both cohorts are separable in §7.1, and **adoption of any magnitude threshold on these flags is gated on a pre-registered design-segment test**: Gate 6's minimum count, the sign taken from the paper, the kill criterion written before the data is examined (§13).

**Opportunistic-versus-routine flag (advisory).** A purchase is **routine** where the same insider filed a purchase in the same calendar month in each of the three preceding years; otherwise **opportunistic**. Counted by §6.4 as a within-signal trial.

**Dealing-restriction flag.** Directors cannot deal during offer periods and close periods. Where the flag is set (derived from the takeover announcement and the reporting calendar), **the absence of purchases carries no information**, and the family's absence-of-signal reading is suppressed and logged.

**§5.4.2 Post-earnings drift direction.** Drift is defined relative to a surprise measure, and the fundamentals and the announcement return disagree exactly where direction matters. The parameter object **names the surprise measure**, with a stated fallback ladder and a hard refusal at the end: where no surprise measure is computable, the flag **`surprise_not_computable`** is emitted, the drift classification is unavailable, and the candidate falls to `event-driven (other)`. *As with the ingestion-lag rule, v1.9 specified the refusal and omitted the code, so the branch could not appear in a coverage report.* A `mechanism_consistency` advisory flag fires where the sign of the reported fundamentals and the sign of the announcement reaction disagree, and those observations are **excluded from pooled peer-set estimation** while still scored in §7.1: a relief rally on the removal of a feared outcome is not the mechanism a surprise-sorted estimate measures.

**§5.4.3 Concert-party accumulation.** An aggregate concert-party holding crossing a stated band below the mandatory-offer threshold is a **control-accumulation signal**, mechanically unrelated to insider conviction. Detected deterministically and routed to `event-driven (other)`. A family built around it is capability and sits in Annex A.

**§5.4.4 The admissibility × reachability intersection** (at the assumed commission). ***Restored to a derivation and still not to numbers, 27 August 2026 (§0.11, P100).*** Every cell is the intersection of an admissibility class with §4.4's bounds, so **this table has no independent content and needs no decision of its own.** §4.4's regime cap is now derived from §6.7 rather than carried as a constant, and its ATR bounds return when §13 rows 29 and 1 resolve. **Until then the cells below are retained as the record of what was published under the £2,500 clip and no cell in it is a reading.** ***RESTORED 27 August 2026 (P110), and the restored cells are correct at ONE NAMED SHARE PRICE and no other.*** At USD 43.79 the bounds are 6.39% (h=5), 2.91% (h=21) and 1.68% (h=63) at full size, half of each at the multiplier floor, so **insider purchase reads ATR ≤ 6.39% or ≤ 2.91%**, **short-term reversal and event-driven (other) ≤ 6.39%, ≤ 2.91% [, ≤ 1.68%]**, and **trend, PEAD, seasonality and relative value ≤ 2.91% or ≤ 1.68%**. **This table inherits §4.4's defect entire**: it has no independent content, so a bound that is a function of share price makes every cell one too, and the price is named rather than implied. Worked in `docs/CASCADE_2026-08-27.md`. *The blocker is no longer a §0 decision; it is one governance number and one citation.*

| Class | Full size | Multiplier floor |
|---|---|---|
| **Insider purchase** | **ATR ≤ 12.0% (h=5)** or ≤ 5.45% (h=21) | ≤ 6.0% or ≤ 2.73% |
| Short-term reversal / event-driven (other) | ≤ 12.0%, ≤ 5.45% [, ≤ 3.16%] | ≤ 6.0%, ≤ 2.73% [, ≤ 1.58%] |
| Trend / PEAD / seasonality / relative value | ≤ 5.45% or ≤ 3.16% | ≤ 2.73% or ≤ 1.58% |
| Low vol / carry / unclassified | ≤ 3.16% | ≤ 1.58% |

### 5.5 Correlation and benchmark fit (Gate 4)

Correlations on the candidate strategy's return stream against each position and the book, full-sample and within crisis windows, crisis delta reported; hard ceiling |ρ| > 0.8; refuses below 250 overlap sessions. The panel (published factor return series per listing market) reports **R²** to sizing, with the UK series gap printed on every exposure report. ENB = 1/Σw̃ᵢ² on realised risk contributions.

### 5.6 Regime (Gate 5)

Per market: trend (index versus 200-session moving average), volatility (σ₂₀/σ₁₂₀ against a five-year percentile), curve (10-year minus 2-year sovereign spread sign). UK: FTSE All-Share and the gilt curve. US: S&P 500 and the Treasury curve. Advisory; refuses below a minimum conditional sample.

### 5.7 Expectancy (Gate 6): see §6.

### 5.8 Robustness (Gate 7), enrichment-gated at midpoint

Full grid under tiers keyed to the point-in-time bucket. Statistic: **survival fraction at the midpoint**, with the conservative-end fraction beside it as an advisory flag. Gate: **enrichment over the random-grid base rate**, with a binomial p-value and a threshold fixed on the design segment before scoring. The full surface is reported, never the best cell.

### 5.9 The execution layer

Broker eligibility, instrument selection, live locate and borrow, margin simulation: survivors only, at deployment, outside the research boundary.

---

## 6. Statistical verification

### 6.1 Estimated edge: two hard hurdles

E = p·W̄ − (1−p)·L̄ ≡ μ̂, SE = s/√N over N non-overlapping trades. Hard: **minimum sample** (< 30 non-overlapping trades → refuse) and **percentile floor**, a screening threshold calibrated permissive so §6.4's FDR step receives an uncensored distribution. **μ̂ − SE > 0 is advisory**, feeding escalation: at N ≈ 30 it was the tightest of three serial hurdles on the same evidence, with the least justification, applied first.

**Decay sensitivity is a mandatory display, not a sizing input.** Expectancy is re-reported under the published ladder, 50% post-publication, 72% excluding pre-2005 data, 93% after costs (Chen and Velikov, 2023), beside the un-haircut figure. Sizing reads only the coarse §6.7 multiplier.

### 6.2 Nulls and holding-period semantics

Block permutation, 500 resamples, blocks within the pooled event set for peer-estimated candidates; **block length fixed from the observed sequence and held constant across resamples**. Second null: buy-and-hold over identical windows. Four consumers of "holding period": block length = **realised** median; break-even index = **intended** horizon for fixed-horizon exits and the **frozen per-family realised median** otherwise; hedge rebalancing realised by construction; stop multiple intended by construction.

### 6.3 Hindsight containment

Analyst: pre-`t_pub_observed` estimation, the fill convention, point-in-time admission and estimation populations, §7.5's partitions. Model: the grammar, anchor provenance, deterministic peer construction. Selection endogeneity: Gate 2, the ledger, §3.4, §6.4, and §3.6.6's three entries: paper selection; the stronger one, **operator hypothesis**; and **agent discovery** (§3.7), which is the same defect again at volume.

### 6.4 Multiplicity, four families

**Within-candidate**: deflated Sharpe at the candidate's own restricted grid size; PBO by combinatorially symmetric cross-validation. The opportunistic/routine flag counts as a within-signal trial. **Cross-candidate**: Benjamini–Hochberg per review period on permutation percentiles, valid under the positive dependence pooling induces; nominal and effective counts both reported, clustered by shared pooled estimate. Explore and shadow candidates counted in full. **Specification search**: the trial count is the number of **specification versions, fourteen**; results attribute to **frozen designs, currently zero**.

**Design-segment search: the fourth family, new in v1.12, and the correction of a v1.11 error.** v1.11 counted pointers inside the specification-search family, which was the wrong ledger and created a perverse incentive: if raising an idea tightens the correction on everything else, the rational operator stops raising ideas, suppressing exactly the exploration the tier exists to make legible. The correct boundary follows §7.5's partition rule; **a multiplicity correction applies to the family sharing an evaluation sample**:

- **Counted here, in full, and dividing nothing**: every pointer raised including abandoned ones, every directive measurement, every manual-observation protocol, every displacement. A pointer **killed or left undetermined on the design segment never touches the evaluation sample**: its cost is design-segment power, tracked by §3.6.8's reuse ledger, not false-discovery budget.
- **Crossing into the cross-candidate family**: only a candidate that survives into an **evaluation-scored cohort**, at which point it enters the Benjamini–Hochberg step like any other, with its `self_generated` provenance displayed beside its percentile.

The family is disclosed with the other three on every published result: the reader sees how wide the design-segment search ran, and no statistic is divided by it.

### 6.5 Survivor risk profile

Maximum drawdown and recovery, Sortino, CVaR-95 on the pre-observation segment; advisory.

### 6.6 Breadth: the arithmetic, with its populations named

IR ≈ IC·√breadth. **Each figure below states the set it was measured on**, which is the correction §0.9 records.

| Book | Bets/year | IC for IR 0.5 |
|---|---|---|
| 16 positions, all h = 63 | 64 | 0.063 |
| 16 positions, all h = 21 | 192 | 0.036 |
| 16 positions, all h = 5 | 806 | 0.018 |
| Mixed (8 × h5, 6 × h21, 2 × h63) | ~483 | 0.023 |

**Position turnover is not the binding quantity.** The book can only turn over as fast as **qualifying** events arrive, and those are neither as numerous as the raw notification count nor uniformly distributed: they cluster when close periods lift after results and after price falls. Realised breadth is therefore lower than min(qualifying filings, position turnover), and §13 measures the **joint** rate: qualifying purchases in issuers above the tradability floor, with the arrival distribution and both marginals reported so the interaction is visible.

### 6.7 The allocation rule

**Base unit** 75 bps of current equity at risk. **Clip floor: DERIVED, per market, §13 row 30** *(§0.11, 27 August 2026; the fixed £50,000 is withdrawn, and £2,500 before it)*. **It is not a constant and there is no number here to quote.** The floor for a market is the smallest position at which §13 row 1's fixed round-trip cost falls at or below §13 row 29's tolerance. **Row 29 is OPEN and row 1 is PROVISIONAL, so the floor does not derive today for any market, position size is UNDETERMINED, and the book takes no positions.** The refusal carries `clip_floor_tolerance_unset` and names the parameter, which is the difference between an empty book that is legible and one that is not (§0.11, §0.6).

**The clip is a FLOOR and never a target.** Seven places in this manuscript read it so, audited on 27 August 2026 and listed in `docs/DECISION_sizing_collision.md` §1.1a. §5.1's explore arm is the one place that additionally *sizes at* the floor, which is a dual use rather than a contradiction, and it means **the explore arm has no size while the floor is undetermined**.

**Four coarse multipliers, product floored at 0.5, shrink-only:**
- **Decay**: 1.0 / 0.75 / 0.5.
- **Correlation** (max of worst pairwise and panel R²): 1.0 below 0.4 / 0.75 to 0.6 / 0.5 to the ceiling.
- **Regime**: 0.5 / 1.0.
- **Source lead**: reads the empirical-Bayes shrunk estimate from the creator ledger (§7.3) and nothing else. 1.0 for a first mention from a source whose shrunk lead profile is above the population median; 0.5 below it; 0.75 where measured and neither. **Unmeasured is a fourth branch, not a fallback into the third.** Below a minimum call count (§13 row 18) the input **refuses to score**, and the sizing record carries `source_lead_basis ∈ {measured, shrunk_to_prior, unmeasured}` so cohorts sized on evidence separate from cohorts sized on a prior. The unmeasured value is 0.75 under §0.8's laboratory calibration and 0.5 under a fund's, listed as a reversal switch.

**Caps, binding in fixed order, first-binder recorded:** position risk 37.5–75 bps; single name 10%; correlation cluster 3 units; ENB ≥ min(6, 0.75k); total risk-at-stop 12%; cross-section = min(risk budget, gross cap, 16) plus the explore sub-cap of 4; gross 100% ex-hedge; participation 2% of median daily notional per session over ≤ 3 sessions.

**Governor** (admissions only): at 10% trailing drawdown from the high-water mark (origin the first simulated position of the evaluation segment, continuous across folds), the cross-section falls 16→8 with ≤ 1 new position weekly; at 15%, none; restores at 5%.

**Shrink-only is a property test**: every post-Gate-6 stage non-increasing in absolute size and able to reach zero.

**Multiple survivors on one asset**: rank by permutation percentile, ties to the wider stop, size the top, **fall through on zero**.

**Partial fills**: below 60% of clip within the window → close, `liquidity_insufficient_realised`; at or above → keep, stop on achieved notional, shortfall logged. This code is a **primary rather than an edge-case outcome** for shadow-cohort candidates.

**Corporate actions.** Rights issues, spin-offs and splits recompute stop and size on the adjusted series. A suspended position is held at last traded price with its stop suspended. **A firm takeover offer closes positions whose entry catalyst is *not* the offer**, at the next open following announcement; positions anchored on the offer itself follow their own exit family. Without that condition the rule fires on its own entry event and annihilates the entire firm-offer catalyst class silently.

### 6.8 The beta measurement: a hedge demoted, with its costs priced

**The verification ran, and it failed on the account.** The instrument-side checks of v1.9 stood: the ICE Mini FTSE 100 future (£1 per index point, ≈ 0.09 beta units on £100k) and CME's Micro E-mini S&P (≈ 0.24 units) are small enough, and the prior recollection that no such instruments existed remains removed. **The operator does not qualify for futures dealing at the executing broker.** That closes the third recorded instance of the operator-assumption error class (the pattern of verifying the world and never the account), and the sequence is instructive: v1.9 verified the *contract*, v1.10 named the *account* as the untested half, and the account was the half that failed.

**The demotion, per the fallback v1.10 specified and declined to land without this fact.** No hedge leg is traded. Residual beta per listing market is **measured and reported**: realised book beta against the index total-return series §5.6 already names, computed with the abnormal-return machinery §4.2 and §7.1 already require, displayed on every book-level report beside the manual and explore shares. The tolerance band becomes a **reporting threshold, not a rebalancing trigger**: breaches are flagged, never traded against.

**Four consequences, priced rather than glossed:**

1. **§6.7's governor now binds on beta-inclusive drawdown.** A market fall can throttle admissions with no idiosyncratic loss whatever. Accepted deliberately: the governor protects the *evaluation*, not returns, and cutting intake into a falling market is the conservative direction at this capital. The alternative (running the governor on market-adjusted book returns) is **rejected**: it would let admissions continue at full rate through a crash, which converts the governor from a circuit-breaker into a beta-blind formality precisely when correlated losses make refusal most valuable.
2. **Gate 4 does more work.** With no hedge, book beta concentration is bounded only by Gate 4's ceiling, the ENB floor and the correlation multiplier. The gate's crisis-window delta was always the instrument for correlated-loss profiles; it is now the *only* instrument, and its refuse-below-250-sessions rule inherits that weight.
3. **§7.1's headline is unaffected**: forward returns were always market-adjusted. The **book-level** series is now reported twice, raw and market-adjusted, with the realised beta path between them, so a reader can see what the absent hedge cost in any window.
4. **The cost stack simplifies.** Hedge financing and rebalancing drop out at book level; §5.2.2's per-trade break-even table is **unchanged**, because it always priced the position leg only.

**What remains open, and where it binds.** The account type (cash-only or margin) is a §14 open decision. It is currently **non-binding**: the grammar is long-only by direction restriction and §0.7(e) notes borrowability is not currently load-bearing. It binds before any short-side family is admitted and before §5.9's margin simulation exists, and settling it by assumption would be the fourth instance of the error class this section just closed the third of.

### 6.9 Currency

Sterling accounting; the risk denominator stays the **local-currency** stop distance; currency is a measured sleeve exposure reported against a pre-registered budget (the one §0 decision pending in §13).

---

## 7. System-level validation

### 7.1 The headline: funnel depth orders forward returns

For every idea (accepted, rejected, zero-sized, explore-arm, shadow) the ledger records market-adjusted forward return over [`t_pub_observed`, +h], h ∈ {21, 63}, on delisting-inclusive data, survivorship-complete.

**Statistic:** Spearman ρ between death-gate index and forward return, standard errors clustered by asset and calendar week, effective count displayed beside n. **Series reported:** deployed (primary); automatic-only; override; **explore** (the below-floor region); **shadow** (the below-tradability region); filing-anchored carve-out; offer-period carve-out. Standing pair beside all: manual share of positions and of open risk: the unreplayable fraction §0.4 accepts by decision and refuses to hide. Secondary: accepted-versus-rejected cohort spread with its power curve, and at h = 63 additionally against size-and-book-to-market matched controls, winsorised at 1 and 99.

### 7.2 Per-gate attribution on a 10% audit stream

Batch mode stops at the first hard kill, so naive attribution compares "killed here" with "passed everything" and deletes late gates. A pre-registered 10% of intake runs the full panel regardless; attribution computes there exclusively.

### 7.3 The creator ledger

Per-source realised market-adjusted excess, backfilled; advisory always; empirical-Bayes shrunk, and the shrunk estimate is the only figure §6.7's fourth multiplier reads.

### 7.4 The unconstrained-model control arm

The same structured catalyst posed to an unconstrained model, model identifier and prompt pinned, versioned and cached. **Its test set is now populated**: every item where `direction_basis = inferred` and the extracted direction diverges from the source's stated conclusion routes here.

### 7.5 Retrospective deployment: three partitions, two oracles, one placebo

**Three named partitions**, boundaries per §0.7(a): **Design** (base-rate thresholds and review-point changes), **Calibration** (derived artefacts), **Evaluation** (scored). **Gate 0 asserts the separation**, and the assertion **extends to manually injected items**: injections carry an `injection_timestamp` distinct from all four anchors, are assigned to a partition by `t_pub_earliest` rather than by arrival, and are excluded from any partition already scored. Manual injection is the route every pre-freeze trace uses, so an unguarded hole there is a hole in the instrument being relied on.

Calibration campaigns use **contiguous runs, not scattered probes**. **Defined, frozen and evaluated are three claims**: the parameter hash exists from the freeze, the evaluation hash only once scoring runs, and every artefact names both.

**Positive oracle:** reproduce the textbook post-earnings-drift profile. **The oracle's population is stated in the parameter object and need not be the trading universe**: the cleanest unambiguous examples may sit on exchanges §0.7(f) excludes, and the paper previously left this unsaid.

**Negative control:** timestamp-randomisation placebo, **evaluated by equivalence** (Schuirmann, 1987; Lakens, 2017): two one-sided tests against ±Δ, passing only where both reject at α = 0.05, failing for want of power rather than passing by it. **Δ = one third of the un-randomised calibration-run association**, floored at the smallest association that changes a deployment decision; never taken from the randomised null, which would let a wide null pass the test it is meant to bound.

### 7.6 The shadow frontier

Candidates clearing every gate except the tradability floor run with full verdicts, forward tracking and zero capital. This is the instrument that tests §0.5's demoted premise **and** §0.10's microcap question, and its promotion predicate is pre-registered: realised net expectancy after measured spreads exceeding measured break-even by a stated margin over a stated minimum sample.

**One interpretation caveat, stated so a positive result is not over-read.** A persistent discount in smaller UK-listed companies is currently being harvested by acquirers who buy whole companies rather than shares. If that is the mechanism, a separating shadow cohort is evidence for the discount and **not** evidence that a public-market book could capture it at any size: control, leverage and a multi-year horizon are not position-sizing problems.

### 7.7 Review points

Design changes only at review points, on the design segment, excluded from headlines; quarterly by default but opening only once the audit stream reaches its §13 minimum; deferrals logged. Suspension reviews are calendar-exempt. §0.6 sits above this section.

---

## 8. The graveyard

Every kill writes the idea, deciding gate and flags, deciding statistic, threshold, **set size measured**, a machine-checkable **resurrection predicate**, and, from v1.12, a **rejection summary**.

**The rejection summary: two to three sentences of plain language on every refusal, everywhere.** The paper's product is legible rejection (§1), and a reason code is legible to the machine while remaining opaque to the person reading the ledger six months later. The rule:

- **Rendered, not judged.** For deterministic kills the summary is composed by a **fixed template over the record's own fields**: deciding gate, statistic against threshold, set size and population, and the resurrection predicate restated as a sentence. No model call: a model-written account of a deterministic decision would be a probabilistic gloss on an exact fact, and the clerk holds no authority here or anywhere.
- **Authored where the decision was.** Where the deciding step was human (an operator-mapping refusal, a pre-mortem refusal, a directive displacement, a manual-acceptance decline), **the operator writes the two to three sentences**, and the ledger records the author beside the text.
- **Display-only, structurally.** Nothing downstream reads the summary. It renders on §9.2's per-gate cards and in the graveyard; it feeds no gate, no statistic and no sizing input, so a badly written summary can mislead a reader and cannot mislead the system.
- **Scope: every refusal class in the paper.** Gate kills; advisory-haircut kills; screen refusals and blocks in §3.6.3; declined and deferred directives and displaced pointers in §3.6.5 and §3.6.8; `killed_negligible` and `undetermined_at_budget` verdicts; suspension of an extraction class; and manual-acceptance declines. Annex A.2's middle column (*why it will keep being proposed, and why it is wrong*) has carried this form since v1.5 and is the template's ancestor.

Predicates assert **transitions**, fire and log continuously, and are acted on only at the first review point after the §0.6 instruments report. Deferred and excluded registers are consolidated in **Annex A**.

---

## 9. Reference implementation

### 9.1 Derived artefacts carry two spans

Every archive-estimated artefact records an **estimation span** (changing it makes a new specification version) and an **application span** (deliberately different: applying a frozen estimate out of sample is the point of freezing it). Two *estimates* are never joined without rebuilding one.

### 9.2 The stack

One Python repository: SQLite decision ledger keyed on parameter hash and idea; parquet bar cache, pre-warmed, with no network at decision time; delisting-inclusive daily bars behind a `DataSource` interface; point-in-time ICB alongside; schema-enforced model calls at temperature zero, cached by content hash; **deterministic parsers for field-delimited regulatory forms**; primary-feed adapters for the regulatory news service and EDGAR. The interface renders the funnel, per-gate cards with the deciding number, the set size and the rejection summary, the design-segment reuse ledger, the survival surface, the reachability matrix, the §5.4.4 intersection, the binding-constraint distribution, the anchor map, and the manual, explore and shadow shares.

**Reproducibility:** the research record replays byte-for-byte; the book does not, and carries auditability and visibility instead. **The parameter-object refactor is first**: a hash over scattered constants is a hash over whatever the author remembered.

### 9.3 At the reference capital

£100,000. Participation makes any name above ≈ £42,000 median daily notional executable at the clip. **The economics, plainly:** even heroic net alpha here is a few thousand pounds a year. Per §0.5 there is no capital-derived edge; per §6.6 the breadth orientation makes skill *testable* rather than profitable. The book is the laboratory; the ledger is the product.

### 9.4 The trace harness

A specification test instrument, distinct from the production funnel: it runs **interactive always** (batch mode terminates at the first hard kill and therefore hides every downstream defect), it draws from the **whole feed rather than hand-picked items**, and its output is not verdicts but a **coverage report**.

Each gate returns one of four states: `pass`, `kill`, `unreachable_pending_calibration`, and **`undecidable`**: the rule exists, the data exists, and the rule does not determine an answer. `undecidable` is the harness's product; every instance is a candidate register entry.

The coverage report tracks gates reached against gates defined, rules exercised against rules defined, fields populated against fields defined, and one ratio above the rest: **reason codes emitted against reason codes defined.** A code defined but never emitted is an untested branch, and that single metric surfaces the failure class this paper's audits could not: a rule that is wrong because nothing ever reached it.

**The harness carries a pre-registered stopping rule.** It runs in blocks; after each, the marginal defect rate per hundred items is computed; when that falls below a stated threshold for two consecutive blocks, tracing stops, the register closes, and the parameter object is hashed. Without it, a productive remediation exercise becomes an indefinite improvement cycle wearing a test harness's clothes, which is the pattern §0.6 exists to prevent.

Sampling is stratified across source class and catalyst type, and includes **a mandatory minimum sample of the primary catalyst family's own live filing flow**. General items find machinery defects; only the family's own flow found the defect in §0.9's argument.

***Which pipeline this section is about, established 27 August 2026 (P115) by testing it rather than assuming it.*** **It is §3.5's ITEM pipeline.** Every load-bearing noun above is item-side: **gates**, which the discovery layer does not have; **items**; the **feed**; **source class** and **catalyst type**; the **filing flow**. **This section does not mention an intake point once**, and §0.5 states it in one line: *a trace harness (§9.4) that runs real items through the funnel*. **`src/fntn/scanner/trace.py` traces the DISCOVERY layer**, and says so of itself: *§9.4 applied to §3.7's two ingestion surfaces*, naming §13 rows 21 and 23 as what it can measure. **Both are §9.4 instruments and they are not the same exercise, so binding-path step 4 is not partly done: it has not been started.** **What the 200 items must CONTAIN is specified in `docs/PIPELINE_9_4_2026-08-27.md`**, stratum by stratum, and it is a stratification rather than a count: the count is §13 row 28's, two blocks of 100.


### 9.5 The review harness

*New in v1.10. Procedure, not apparatus. Where §9.4 tests the specification against a **world**, §9.5 tests the specification against **itself**, and the paper's own evidence is that the second is the weaker instrument, which is why it carries the tighter stopping rule.*

**Three layers, mirroring the architecture they review.**

| Layer | Instrument | Authority |
|---|---|---|
| **Deterministic** | A linter over the manuscript and its register documents | Emits defects by rule. Binding |
| **Clerk** | One schema-enforced call per pass, temperature zero, cached by content hash | Emits **observations** only: no severity, no verdict |
| **Adjudication** | A fixed table mapping observation → defect class → severity → landing | Pure lookup |

**Severity is computed, never proposed.** A reviewer who can set severity can flatter the denominator, which is the §0.3 problem in another costume.

**The deterministic checks.** Header–change-log agreement (the stated version, ordinal and counts must match §12's latest entry, a check added after v1.11 circulated under a v1.10 header because a drafting batch failed part-way and nothing tested the result); dangling section references; section-number collisions between a manuscript and a proposed drop-in; register-ID collisions, and the sharper case of **one register ID carrying two divergent specifications**; register entries missing their parameter-object or priority declaration; §13's membership rule (*nothing pends elsewhere*), tested by requiring every pending quantity to point at a row; Annex A.1 rows without predicates; numeric claims without a row-level provenance tag; and a **coverage report** in §9.4's idiom: sections cited against sections defined, identifiers consumed against identifiers defined, §13 rows pointed at against §13 rows defined.

**The judgement passes.** Two, and only two, need a model: **population declaration** (for every claim carried across, are `measured_on` and `tradable_on` both stated?) and **intersection risk** (does any fix interact with another fix landed on the same rule in the same version?). The second is the highest-yield pass, because two items on one gate is the v1.4 failure signature.

**The enhancement gate.** A proposed improvement is admissible into a version **only if** it removes a must-class defect, unblocks a named §13 row, closes a §14 precondition, or is a restriction or prior update under §3.6.4. Everything else is an extension and takes an Annex A.1 row. **The stated cost:** the gate declines improvements that are genuinely good. That is the intended direction of error: an improvement declined into A.1 is recoverable at a review point, while an improvement smuggled in pre-freeze is a fitted parameter wearing a restriction's clothes.

**The stopping rule, pre-registered.** The harness runs in passes. It stops when two consecutive passes yield zero must-class defects, or after three full cycles, whichever is sooner; it may not be re-run on a composition hash it has already cleared. The threshold is zero rather than §9.4's marginal rate because the population here is a document, and a document is finite.

**Two passes run, recorded because the yield is the point.**

| Pass | Object | Must-class | Findings |
|---|---|---|---|
| 1 | v1.9 composed with the v1.10 drop-ins | **4** | Two rules specified without reason codes (§3.5.1, §5.4.2); one extraction field named three ways across three artefacts (§3.5.2); one register document cited but absent (§14). Plus six sections with no inbound cross-reference, and an evidence table whose provenance sat in prose rather than on its rows (§0.5) |
| 2 | this document, composed | **0** | Residual advisories only: the linter cannot distinguish a system-*computed* figure (the break-even table) from an external claim, and flags both. That is a linter limitation, recorded rather than suppressed |

**The stopping rule is not yet satisfied**: it requires *two consecutive* passes at zero, and this composition resets the count to none achieved. §14 carries the open row. **The honest note beside that yield:** every finding is a legibility or bookkeeping defect. None of them is a defect in the *economics*, and none would have been found by more reading; but equally, none moves §7.1 one day closer. This is the pattern §0.6 exists to watch, and the stopping rule is why the harness has a last pass rather than a next one.

---

## 10. Limitations

**Capital.** §0.1's dilemma is unrepairable by design; only capital resolves it.

**The economics may be null.** The published anomaly cross-section fails this cost table. The insider family is the one live candidate and decays to marginal at the literature's harsher rungs. The expected earnings-drift outcome is an empty cohort.

**The §0.6 amendment is a risk taken, not a cost avoided.** If the run returns null, v1.8's additions were layers on nothing.

**Breadth and selection may be in tension** (§0.9). If the qualifying pool is only modestly larger than the book's capacity, a funnel whose product is refusal cannot refuse. §13's joint-rate row settles it.

**Laboratory calibration raises false positives by construction** (§0.8), deliberately, bounded, cohort-tagged and reversible by listed switches.

**The discretionary channel** is visible, not contained.

**Microcaps are measured, not traded** (§0.10), and live admission depends on a cost tier that does not yet exist and data quality that is the binding risk.

**Data.** Daily bars exclude intraday families and make short-reversal windows unreachable through a T+1 fill. UK daily factor series end 2017. ICB vintage is open. Borrow errs both ways. The commission assumption is unverified and is the most leveraged number in the paper. Survivorship-complete UK small-cap history is the binding data risk, and it binds hardest exactly where §0.10 wants to look.

**Power.** ~9–12 evaluation months; clustered effective samples far below nominal; pooling reduces independent tests further.

**The operator is inside the search, and two of the fences now have teeth.** §3.6.8 lets the operator's own hypotheses direct observation. The query fence closes the auditable route to archive-conditional contamination, and the equivalence verdicts move the pass condition from a sign the operator supplied to a magnitude the operator committed to blind. The rest (`registered_at`, counting, pre-mortem, literature-first, `self_generated` provenance) is legibility. **None of it makes the search unbiased**, because the system cannot observe the operator's priors; the same defect §1 attributes to the model, relocated to the person, where no data split reaches it. Accepted deliberately: the alternative is a system that can only investigate what someone else has already published: a constraint with its own bias and none of the visibility.

**Manual observation is slow, endogenous at the point of collection, and its backfill is the §0.10 trap in miniature.** The tier's protocol contains what it can, pre-registered cadence, gaps as gaps, survivorship caveats printed on every figure, and a hand-collected series remains what it is: thin, forward-only in any trustworthy form, and collected by the person who hoped it would be interesting.

**The book is unhedged.** Beta is measured and displayed, not removed (§6.8). The governor binds on beta-inclusive drawdown, market falls throttle admissions regardless of idiosyncratic performance, and Gate 4 is the only remaining instrument against correlated-loss profiles.

**The literature lane inherits the literature's selection.** §3.6 screens papers mechanically but cannot correct for the fact that published anomalies are the survivors of an unpublished search. The decay prior is applied *because* publication is a selection event, and that is a mitigation, not a fix.

**The first intake is single-source and vintage-limited.** §0.5's UK figures are measured on 1991–1998 LSE data. Three decades of disclosure-regime change sit between that sample and this archive, and the direction of the resulting bias is unknown: Brochet's mechanism argues prompt disclosure raises filing-window information content, which would make the old UK figures a *floor*, but that is an argument rather than a measurement.

**Model error** propagates; containment bounds without eliminating.

**Specification multiplicity.** Fourteen versions, each written with the archive in view. **Pointers are counted alongside them** (§3.6.8), so the denominator now grows when the operator has an idea, not only when the operator writes a rule.

**The discovery layer is the one place a model selects, and its containment is architectural rather than epistemic.** Selection cannot reach capital by any route, because a pointer's only output is a directive and a directive runs at zero capital; nevertheless the layer chooses what is investigated, and what is never investigated is invisible to every instrument in §7.

**The exclusivity guarantee covers data and not knowledge.** Partitions, markets and import fences are enforceable and are enforced; the weights are not partitionable. Mechanism-level emission lowers the resolution at which recalled price history can be exploited and does not remove it.

**A positive control-arm result means the agent beats a random draw, and means nothing stronger.** An agent whose recollection of price history is genuinely informative would also beat a random draw, and the instrument cannot separate that from skill. It is nevertheless the strongest available claim, and it is stronger than anything that can be said about the operator's own search.

**The default construction rests on an assumption that is only partly measurable.** `cross_market` holds that a mechanism observed under one market's disclosure regime holds under another's. §13 row 24 tests it wherever a class occurs in both, which is not everywhere; a class present only in the discovery market leaves the assumption untested, and the directive carries that on its face. Brochet's disclosure-speed mechanism argues the assumption is weakest precisely where regimes differ most, which is the same territory the row is least able to cover.

**The entity fence is only as complete as the security master behind it.** Its binding layer is a lookup, so an issuer absent from the master or from a discovery market's listing list is an episode the fence cannot see. §13 row 25 measures that coverage and §13 row 21 measures both error rates. Neither reaches a paraphrase that identifies an issuer without naming it, and nothing in this design does.

**Volume changes what the denominator means.** §6.4's fourth family now grows when a machine has an idea, at a rate no operator could match. It divides nothing, so it costs no statistical power; it does consume design-segment span, and a short segment is the binding constraint on the layer from its first day rather than eventually.

**Above all:** the system manufactures no edge; it prices refusal. An empty accepted cohort is a result, and a *positive* result carries the §0.8 caveat that the calibration was set to find one.

---

## 11. Conclusion

The design rests on one inversion (the model demoted to clerk, determinism promoted to epistemology) and nine lessons, compounding. **v1.4**: defects migrate to the intersections of independently correct rules. **v1.5**: a specification is complete only when every silence has an answer on the record. **v1.6**: every check here measures the machinery and none can fail for absent signal. **v1.7**: a rule about ordering is not exempt from the ordering problem, and a paper cannot audit itself by resolving to. **v1.8**: a system can be rigorous about the constraints it invents and negligent about the facts it could check.

**v1.9's lesson is about method, and it is the one that changes what happens next.** Six consistency audits and two external reviews read the rules against each other and found contradictions. Three days of tracing real items, filings, transcripts, media, a live corporate action, a full day of regulatory flow, read the rules against a world and found something the audits structurally could not: **rules that were wrong because nothing had ever reached them.** An exit rule that fired on its own entry event. A universe rule with no enforcing gate. A permissive default that became a fast lane when the horizons moved. A catalyst rule with a ceiling and no floor. And, from sampling the primary family's own filing flow, the one defect that was not machinery at all: an expected value computed across two different populations.

§2 has always held that a verdict never answers *did I measure what I said*. The corollary is that **a rule never answers *did anything ever reach me***, and no amount of re-reading supplies it. That is why §9.4 exists, why §14 now requires it, and why the harness carries a stopping rule: the exercise that measured the cost of the last amendment must not become the next one.

**v1.10's lesson is about evidence, and it is small but load-bearing.** The literature lane's first intake refused to score a number recalled from memory, and verification then found the recollection **wrong in two places**: a restriction that would have flagged all proximate news when only merger news matters, and a scalar where the truth is a sign structure with one counterintuitive term. Both would have entered the specification unchallenged. The lesson: **the discipline that refuses to consume unverified claims pays for itself on its first use, and it pays in the currency of errors that would otherwise have been invisible**, because a wrong restriction looks exactly like a right one until something reaches it.

The review harness carries the corollary and its own caution. It found four must-class defects in one pass, all of them real, and **none of them in the economics**. Rules specified without reason codes. A field named three ways. A register cited and absent. Legibility defects are worth fixing and are not worth mistaking for progress: the harness stops after two clean passes precisely because an instrument that always finds something will always be run.

**v1.11's lesson is about where a constraint should sit.** The request was to let good ideas direct observation. The naive form of that (let a promising idea open a feed) would have been apparatus admitted through the door marked *research*, and §0.6 would have been amended a second time without anyone writing the word amendment. The constraint moved instead to the **feed**: investigate anything, on anything already flowing, immediately and at zero capital; subscribe to nothing new until the instruments report. **The interesting consequence is that the rule declines exactly the directives that feel most promising**, and that asymmetry is the rule working rather than failing.

**v1.12's lesson comes in a pair, and both halves are about populations.** The hedge verification checked the contract meticulously and the account not at all, and the account was what failed. §2 has held from the start that a check measures a population and the population is a separate claim from the verdict; the corollary landed here is that **verification has a population too**, and *the world* and *this operator's access to it* are different sets. The second half is the constraint that was too coarse: `new_subscription` bundled a production adapter with a person reading a public register, and the repair was not to relax the rule but to **split the category**: the recurring shape of this paper's best fixes, from the anchor split of v1.3 to the population naming of v1.9. A constraint that binds on the wrong boundary is not evidence the constraint is wrong; it is evidence the boundary was drawn through the middle of two different things.

There is nothing further to specify. The remaining questions (whether the base rates leave Gate 2 anything to kill, whether the qualifying pool leaves Gate 6 anything to reject, whether the funnel orders ideas at all) are answered by running. The artefact promises no returns. It promises that every unit of capital withheld was withheld for a stated reason; that the accepted cohort, if empty, is visibly empty and, if not, is visibly tagged by the channel it arrived through; and that the denominator (configurations, thirteen specification versions, every raised pointer and every directive's design-segment consumption, zero frozen designs) is always on display.

---

## 12. Change log

### 12.1 v1.13 → v1.14

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P76 | **Bare tickers matched in a symbol's shape, not a word's.** v1.13's lookup fence took names and tickers as one set; 7,268 of the 10,388 US tickers are four characters or fewer and the loader filtered issuer names only, so `Note`, `Are`, `For`, `Law` and the single letters entered the fence as tradeable entities and ordinary English was refused, 257 hits across 41 tokens over the thirteen US pre-archive documents. Names keep the span lookup; a bare ticker matches **only in all capitals, three characters or more**, and the two sets are held apart because sixty-five US issuers have a one-word name identical to their own ticker. **The false negative is taken knowingly and named**: a bare ticker in lower or title case is now invisible, the cost falling on the exclusivity guarantee rather than on a re-raise, and taken over a common-word filter that would have hidden at least ninety-five real issuers in capitals as well. Five lexicon rows land with it, `CFR`, `LII`, `ACT`, `III` and `VII`, being legal-citation vocabulary that collides with real tickers | restriction | §3.7.3, §13 rows 21 and 25 | yes |
| P77 | **§13 row 21's two rates divided per arm, and v1.13's reading withdrawn.** Row 21 has always specified two rates "reported separately and each with its n"; the measuring harness divided both by the union of the arms, reporting one probe of six as 2%. A false positive can only be drawn from the class-level arm and a miss only from the probe arm, so the union is the population of neither, and the understatement is largest exactly where the arms are least balanced. Both arm sizes are now named in the rendered output, and an empty arm refuses to score rather than reading zero. **Separately, v1.13's "zero false positives and zero false negatives" is withdrawn**: it was measured against six plants defined inline in an uncommitted shell and is not reproducible from the repository. The labelled set is now in the tree at `docs/labelled_proposals.json` and the reading is locked by tests. Replacement on the drawn arm: **0 of 36** clean class-level mechanisms refused, against **3 of 36** on the fence as v1.13 left it. The second arm is corrected again by P79, which found the denominator repaired and the frame still wrong. Supersession banners stand above the stale wording in §3.7.3, §12.2 and §13, per §12.7 | restriction | §9.4, §3.7.3, §13 row 21 | no |
| P78 | **Row 21 stays PROVISIONAL, and its provenance is stated on the row.** The 42 labels carry provenance `model_clerk`: they are the clerk's classifications against the fixed taxonomy, not the operator's hand labels, and row 21 specifies 200 hand-labelled proposals. The row says so in those words rather than letting a reproducible figure imply a ratified one. **Operator ratification is the act that converts the reading into a calibration**, and it has not occurred | n/a | §13 row 21, §14 | no |
| P79 | **The probe arm reports coverage, and never a rate.** P77 repaired the denominator and left the frame: the six subjects in the second arm are **authored probes**, one per named route into the fence, so they are chosen rather than sampled and a proportion over them estimates nothing. "1 of 6 (17%)" reads as the fence's error rate on real episode-level material, which it is not; doubling the probe set to twelve routes halves the percentage whilst leaving the fence untouched, and a number with the right denominator and the wrong meaning still travels as a rate. The arm is renamed **authored probes** throughout, in the specification, in the harness and in the labelled set's own vocabulary, because *episode-level* implies a sample there is none of. It now reports **routes closed and routes left open by name**, prints no percentage, and refuses to score on an empty arm as the drawn arm already did. Reading: **5 of 6 routes closed, the open one a title-case bare ticker**. The drawn class-level arm is untouched and remains a rate | restriction | §3.7.3, §9.4, §13 row 21 | no |
| P80 | **The designator branch narrowed, and the fence's vocabulary registered.** A designator suffix alone was treated as sufficient, so the branch fired on Rule 16a-8's own heading, *Trust Holdings and Transactions*: `Holdings` is a legal-form suffix in a rulebook heading exactly as it is in a firm's name, and the pattern cannot separate them. The branch now fires only where the span's **leading token is proper-noun-shaped** and is **absent from a registered rulebook stopword set**, seeded from evidence at one token, `trust`, being the only designator span the 27 August corpus produced, and growing by operator mapping in §3.6.5's idiom. `Joint` joins the lexicon on the same trace: The Joint Corp is a listed US issuer whose one-word name is ordinary English, and the fence refused *Joint and group filings* in Rule 16a-3. **The stopword set enters the registration and therefore the hash**, because a value that changes what a fence refuses without reaching the hash makes that behaviour unattributable to any registration, and a row added quietly to a module constant would widen what a sweep lets through with nothing on the record. **The cost, stated:** a firm whose name *begins* with a stopword loses this branch and must be caught by the name lookup; the span matcher is greedy, so *Northern Trust Holdings* leads on `Northern` and is unaffected. Corpus false positives fall from 5 distinct to 3, and the three that remain are page furniture, which is §13 row 22's decision and not the fence's | restriction | §3.7.3, §13 rows 21 and 22 | **yes, `rulebook_stopwords`; re-stamped `b8dd61e7eea6898e`** |
| P81 | **The lexicon joins the stopword set in the parameter object.** P80 registered `rulebook_stopwords` on the argument that a value changing what a fence refuses must reach the hash, and recorded in the same paragraph that the lexicon did not, which left the defect stated and standing. It is now a registered field seeded from the module constant, and the constant is the seed rather than the authority. **The lexicon carries more weight than the stopword set, not less**: the fence passes over what is in it, and the security master's loader refuses to index it, so a lexicon row changes what the fence CAN SEE as well as what it ignores, and two runs under one hash could load two different masters and refuse two different token sets. Re-stamped `701adbd9d48015ed`. **This adds no capability and §0.6 is untouched**: no gate, no family, no grammar row, no cost tier, no feed, no sizing input and no field the funnel reads at decision time. The lexicon was already read at decision time and its content is unchanged to the token; what changes is that a reader can now say which list a run used. **The cost, stated:** adding a lexicon row is a re-stamp, so the operator mapping P75 specified is no longer free, and 181 tokens now sit in the registration where one line of prose sat before. Two further repairs land with it, both provenance: `Registration.save` refuses to overwrite a stamped registration unless the prior hash and path are recorded in `docs/REGISTRATION_HISTORY.md` first, rule 4 having exempted the registration from itself; and the registration records the hash it was stamped under, because a hash is taken over the dataclass as well as the values and a stored object stops recomputing to its own hash the moment a field is added | procedure | §3.7.3, §13 rows 21 and 25 | **yes, `lexicon`; re-stamped `701adbd9d48015ed`** |
| P82a | **Retrospective: the fetch-time chrome strip, recorded late.** The strip landed in the repository at commit `549836c` on 27 August 2026, removing `<nav>`, `<header>`, `<footer>` and elements whose class or id names furniture from every document of the US pre-archive corpus before it was written, and recording `raw_bytes` beside `bytes` in the manifest. **It took no change-log row at the time.** It is one here because it changed what material the agent is shown, which §3.6.4 counts as an input-source choice, and because 24% of the corpus by bytes is not a quantity that changes without a version. **The rule, stated so it is not settled case by case: a change to what a discovery corpus contains is a specification version, and there is no threshold of size or ambition below which it is not.** A chrome strip and a text extraction are the same kind of change and differ only in reach; P82 was treated as a version whilst its predecessor was not, and no rule separates them, which is why this row exists rather than a distinction. **The process fault is the point of recording it:** the rule moved in one commit and was written down in another, which is the one thing §12's discipline forbids outright, and it is annotated here rather than backdated. The letter marks a retrospective record and not a sub-change of P82 | restriction | §3.7.7, §13 row 22 | no |
| P82 | **The discovery corpus stores extracted text, not pages.** *P82a records the predecessor change, which took no row at the time; both are versions and no rule separates them.* §13 row 22's fetch wrote HTML with the page furniture stripped, and the fence refused `API`, `BlackBerry` and `Opera` once per document on thirteen documents that name no company: a search-endpoint comment in `<head>` and a user-agent sniffer in an inline `<script>`, neither of which `<nav>`, `<header>`, `<footer>` or a furniture-ish class or id can reach. **Naming those three constructs as three further things to remove would have closed three members of a class and left the fourth to be found by the fence again**, which is the same repair a fourth time; the fetch now drops `<script>` and `<style>` subtrees entire, drops comments, applies the furniture rules and writes the surviving text, because a construct that carries no text cannot put a name in the corpus. 542,878 of 638,883 bytes removed, 85% against 24%, and corpus fence hits fall from 3 distinct and 39 total to **nil**, which is a count over the thirteen documents and **not a rate and not a reading of either arm of row 21**, both of which are measured against the labelled set and neither of which moves. The document-present floor is re-derived for the new quantity at **500 bytes from 4,000**, the smallest genuine document being Rule 16a-13 at 763 bytes, one sentence and complete, against 54 and 377 for the two non-documents to hand; the gap is a factor of two and is stated rather than smoothed, and the byte floor is no longer the main guard, an unclosed dropped element now being refused directly rather than inferred from a ratio no longer expressible over text. **The cost, stated:** markup is gone and a table's structure and a link's target go with it, so a document whose meaning depended on either would now be read wrongly rather than incompletely; these thirteen are statutory prose and do not, a fetch list growing towards filings or data files would, and the files are `.txt` rather than `.htm` to say so. **No re-stamp**: the corpus is named by its retrieval route and its content reaches no hash, which is a limit of the registration rather than a comfort | restriction | §3.7.7, §13 rows 21 and 22 | no |
| P83 | **§0.5's provenance vocabulary gains `reconstructed_hash_verified`, and its classifications become total.** The tag names an artefact that **is not the original** and that **reproduces the original's hash under the dataclass of the commit the record names**; both halves bind, a reconstruction failing the hash being a guess and a hash reproduced under another schema being a different question answered. It is a positive verification and still not the artefact, so it **blocks the freeze signature** as `recollection` does whilst meaning something else, and it may never make an intake quantified. **The defect it exposed is the larger half of this row.** The freeze-blocking decision was the comparison `tag == "recollection"`, a blacklist of one, and the verified set was a literal restated at its point of use: a tag added to §0.5 would have been read as harmless by every consumer that had never heard of it, which is a vocabulary growing past its readers. Both classifications now hang off the enum, are **total over it**, and are tested to be, so an unclassified tag fails rather than passes. The §8 template for `claim_provenance_recollection` renders **the tag it found** instead of naming recollection unconditionally, per §8's rule that a summary is rendered from the record's own fields; the code keeps its name, which names its commonest case. An unknown tag now raises rather than passing. Occasioned by `890a80e3a8566837`, the discovery layer's first registration hash, whose object was overwritten before it was ever committed | restriction | §0.5, §3.6.2, §8 | no |
| P84 | **Two provenance repairs to the registration and the corpus, neither reaching the hash.** *First:* `Registration.load` verified nothing. A file whose recorded hash disagreed with its own contents loaded silently, and `save`'s overwrite guard reads that recorded hash as the identity of what it is about to destroy, so an edited hash would have released the guard against a history row for an object that was never on disk. The registration now records a **schema fingerprint** beside the hash, a digest of the field names the hash is taken over, and `load` returns one of three states: `unstamped`, `verified`, or **`unverifiable_schema_change`**. The third is the point. A recomputation can only check a stored hash whilst the dataclass is the one it was taken under, so raising on every older file and verifying nothing at all are both wrong; with the fingerprint the two cases are distinguishable and *cannot verify* becomes a value a reader sees rather than the silence that *verified* also produces. A comparable file that disagrees raises. **No re-stamp**: the fingerprint and the recorded hash are both outside the hashed payload, which the fingerprint describes, so adding either moves neither, and `701adbd9d48015ed` is unchanged. *Second:* the US corpus fetch **keeps the server's own bytes** at `corpora/us/_raw`, underscore-prefixed so both the corpus reader and the integrity check skip them. Extraction is destructive; until this the corpus could be re-derived from nothing, `raw_bytes` was a number with nothing behind it, and a change to the extractor could be tested only against itself. Neither repair changes what the agent is shown | procedure | §3.7.7, §13 rows 19, 20 and 22 | no |
| P85 | **§13 row 21 splits into 21a and 21b, and the drawn arm becomes BLOCKED.** One row carried two quantities of two kinds with two different blockers, and a single status could only be wrong about one of them. **21a, the false-positive rate on drawn proposals, is BLOCKED and not PROVISIONAL**, because its sample size is not a property of the fence: the tolerance is set by how much funnel depth §7.1 can lose before it loses power, and §7.1 has not run, so no n can be derived. **The n = 200 the row carried was chosen and not derived** and is withdrawn; a sample size with no power calculation behind it reads as a requirement and is a guess, and carrying it made the row look like it was waiting for labelling effort when it is waiting for a design segment. **The reading becomes an upper bound: 0 events in 36 trials, 95% upper bound approximately 8.3% by the rule of three.** *`0%` is withdrawn as a statement of the rate.* Zero events does not estimate zero, and a fence refusing one clean proposal in twenty would produce this same reading better than one time in six; the count, 0 of 36 refused, stands as a count. **21b, route coverage on the authored probes, stays PROVISIONAL and stays coverage**, never a rate, and it is unblocked by the operator reading the six probes rather than by any measurement, which is why the two could not share a status. **Splitting a calibration row is a rule change** under §3.6.4's counting rule, whatever the prose is doing, which is why this row exists. Landing with it, as procedure: a **ratification harness**, drawing twelve of the thirty-six by the registered seed with the clerk's label withheld, and revealing agreement as a count with its own denominator | restriction | §13 rows 21a and 21b, §3.7.3, §7.1 | no |
| P86 | **The run report.** `python -m fntn.scanner report` writes `docs/runs/<date>_funnel.md`, append-only, one file per run, rendered from the ledger, the registration and the code registry and **measuring nothing**: where a record does not exist the section says so rather than being omitted. Eight sections in a fixed order, of which three carry the weight. **The provenance header** carries the registration hash, the schema fingerprint **and its verification state**, a digest per corpus manifest and the code commit, and it says so where the ledger was written under a different registration than the tree holds, which it currently is; a measurement is never restated under parameters it was not taken under. **The fence report holds the entity fence's two arms apart**, in their own units, never summed and with no percentage on the probe arm. **The queue is ordered by how many operator inputs each draft is still missing, ascending, and by nothing else**, zero-outstanding drafts first under a heading saying they need a decision now. Ties break on the directive identifier, which ranks nothing. *Any other ordering is the model telling the operator which of their own decisions matters most, which is rule 1's clerk becoming an analyst*, and `test_the_queue_is_ordered_by_outstanding_count_and_nothing_else` builds drafts whose identifier, class and insertion orders each disagree with the count. **One finding the queue surfaced rather than smoothed:** `screen.register` refuses on `delta_min`, the pre-mortem and the literature search and **does not refuse a missing registered sign**, so the report reads the sign off the directive and states the gap between showing it and enforcing it. Procedure by §0.6's test: no gate, no family, no grammar row, no cost tier, no feed, no sizing input, and no field the funnel reads at decision time | procedure | §9.2, §9.4, §3.7, §13 rows 19 to 23 | no |
| P87 | **The intake budget, registered.** `intake_point_budget_s` = 20 s, `intake_subject_budget_s` = 120 s, `budget_retry_max` = 1, entering the parameter object and **re-stamping to `ce576a9fa04a7403`** with `intake_point_budget_s` as the causing field. Registered rather than hard-coded because it changes what a run refuses: two sweeps over one corpus under one hash could otherwise abandon different subjects, with the difference attributable to nothing on the record. A retry is allowed because the commonest cause of one slow point is a source briefly unavailable, and refusing an idea for that refuses the source's weather rather than the idea. **THE DECISION IS TAKEN ONCE, AT CAPTURE, AND THE LEDGER HOLDS IT.** The elapsed time, the budget in force and the verdict are recorded; `ReplayedBudget` reads them and **holds no clock to call**, the test handing it one that raises if touched and requiring the replayed refusal to match the captured one byte for byte, `attempted_at` included. *A wall clock in a replay path makes rule 1 false, quietly, on the one surface where the falsehood is hardest to see*: the same inputs would produce a different refusal set on a busier machine and every figure derived from the run would be a figure the parameter hash does not determine. `intake_budget_exhausted` is **non-positional** and the registry's ordering invariant is widened by an explicitly named set to admit it: a ceiling on time is an interruption that can fall at any point, not a thirteenth check, and giving it position 13 would say every abandonment happened after every other check passed, landing that in §13 row 23. Abandonments are reported **beside** row 23's distribution and never inside it, and the count is printed in every report including when it is zero. **§0.6 applied explicitly, and the answer recorded.** *Does it add a gate, a family, a grammar row, a cost tier, a sizing input, a feed, or a field the funnel reads at decision time?* **No.** It adds a refusal and three ceilings on the cost of reaching one; nothing here is read when deciding whether an idea passes, and the only effect on the funnel is that fewer subjects reach the end of it. A rule that refuses more than it did is a **restriction**, and a restriction may land under the armed rule. **The honest limit, stated: a ceiling that refuses, not a timeout that interrupts.** A check is run and then measured; nothing preempts a call, so a point that blocks forever blocks forever. Preemption needs a thread or a signal per check, which is apparatus of a different order and is not taken for this | restriction | §3.7, §9.2, §13 rows 23 and 27, §0.6 | **yes, three fields; re-stamped `ce576a9fa04a7403`** |
| P87a | **Retrospective: the fingerprint typed, and the loader made bilingual, recorded late.** *The change landed at commit `d95c816` on 27 August 2026 and took no row at the time, on the judgement that it moved no hash and no registered value. That judgement was reached in a commit message, which is the one place a rule is not on the record.* **What landed.** The schema fingerprint was stored as sixteen bare hex characters, indistinguishable in shape from a registration hash, so a mechanical sweep of `discovery_registration.json` found two values and needed a person to say which was a stamp; `Registration.schema_fingerprint` now returns `schema:<digest>`. The prefix is outside the hashed payload, so **nothing was re-stamped** and the registration hashes as it did. **The part that is a rule.** `Registration.schema_matches` accepts **two encodings**, the typed form and the superseded bare digest, so the loader now returns `verified` for a file it would have called `unverifiable_schema_change` the moment before. **That is an acceptance widening, and P80 is the standard it must answer to**: a value that changes what a fence lets through, added quietly, widens the sweep with nothing on the record. **The judgement, and it is a close one.** The widening admits exactly those files whose fingerprint equals a digest **the code recomputes from its own dataclass**, so it carries no free parameter, nothing an operator could have chosen otherwise, and nothing to attribute to a registration; and every file it newly admits is one whose shape genuinely matches, so it corrects a false negative the same commit would otherwise have created. *That argument would separate it from P80, whose stopword set was a chosen list governing real-world spans.* **It is recorded as a version all the same.** Rule 5 names *admissibility rule* without qualifying it as substantive, the bilingualism is a standing property of the loader that outlives the migration and must be findable by a reader of this document rather than of `git log`, and declining the row would have required inventing a meta-rule about which admissibility changes count, which is more judgement than the row costs. **The cost, stated:** until a registration is next saved it keeps the untyped encoding, so the sweep still reads its fingerprint as a bare hash; `save` writes the typed form unconditionally and `discovery_registration.json` was re-saved, so no file in this tree carries it, and any file written elsewhere does until it is stamped again. The sweep, `(?<![:0-9a-fA-F])[0-9a-f]{16}(?![0-9a-fA-F])`, is written down in `docs/REGISTRATION_HISTORY.md` beside the chain it is run against, and a test runs it against the real file and asserts that document still states it verbatim | procedure | §9.2, §13 rows 19, 20, 21a and 21b | no, and no re-stamp |
| P88 | **The run report gains a binding-path section, and it is placed first.** `## 1. Binding path` sits **above the provenance header**, and the order is the substance rather than the presentation: the provenance header answers *under what was this run taken* and the binding path answers *has the project moved*, and a reader opening the file for the second question should not have to find it under the first. Fourteen versions, a linter, a reference implementation, a literature lane and a discovery layer have been built and **the score does not move**, so a report whose first page is not the score is a report in which building reads as progress. It prints the register's own five steps, in the register's own order, with **every status read out of `docs/OPEN_ITEMS.md` and none stated in the code**. The one judgement is which register cells settle which step, and it is printed in the table's last column so a reader who disagrees can see it rather than infer it. **A qualified closure does not close a step:** `PART CLOSED` (row 22) and `CLOSED for US` (row 25) are closures over part of an object, and reading either as done would say the path had moved when the register says it has not. **A register that cannot be read produces `CANNOT READ THE REGISTER` and never `NOT CLOSED`**, a step reported outstanding when nothing was read being a refusal in a reading's clothes (rule 3). **The movement line is computed by diffing the previous file in `docs/runs/`, never asserted**, and its three outcomes are held apart: no previous report, a previous report carrying no binding path, and a real comparison. Only the third may say **`no binding-path movement since <file>`**, in those words and nothing softer; the second is every report written before this row and saying *no movement* of it would be the file asserting the thing it exists to compute. *Two findings the section surfaced rather than smoothed:* the register declares a four-word status vocabulary and its §13 table uses two more, `PART CLOSED` and `CLOSED for US`, which are admitted here and reported as qualified; and **0 of 5 steps are closed**, which is the first line of every report from now on. Supersedes P86's *eight sections in a fixed order*: there are nine, and the eight are renumbered 2 to 9. Procedure by §0.6's test: no gate, no family, no grammar row, no cost tier, no feed, no sizing input, and no field the funnel reads at decision time. **It takes a row all the same, because it changes what the report contains**, and a report whose contents move without a row is a register that cannot be reconciled against its own output | procedure | §9.2, §13, §14 | no |
| P89 | **The register's status vocabulary normalised, and the reader made strict.** `docs/OPEN_ITEMS.md` declared four statuses in its preamble and its §13 table used two more, `PART CLOSED` (row 22) and `CLOSED for US` (row 25). The second put a **scope inside a status**, so every reader of the file had to parse it out, and P88's first binding-path reader duly did: it admitted the loose cells and reported them as qualified. *That is the failure being corrected.* **A vocabulary kept in two places is widened in the second one**, and the second place was the code, which is the copy no operator reads. The register is normalised instead: **five statuses and no others** (`OPEN`, `BLOCKED`, `PROVISIONAL`, `PART CLOSED`, `CLOSED`), declared once in the preamble, and **`Scope` becomes a column of its own** across the §13 table and both §14 tables, reading `n/a` where the status is unqualified. Row 25 becomes `PART CLOSED` with scope `US`, as row 22 already was; §14's precondition on register completeness becomes `PART CLOSED` with scope `§12.7's terms`; the dates and notes that sat inside status cells move to the note column, where they were always due. **The reader refuses anything outside the five and repairs nothing.** `status_token` no longer splits a cell at the first colon, which was a silent salvage of a cell carrying a note where a status belongs, and `is_closed` is now `token == "CLOSED"` with no qualifier list, because a qualifier is a scope and scopes have a column. `CANNOT READ THE REGISTER` still covers an unreadable file, and now covers a status the register does not declare, so the two failures stay distinct. **No verdict moved:** all five binding-path steps read `NOT CLOSED` before and after, and what changed is that the evidence column prints `PART CLOSED (US)` where it printed `CLOSED for US`. It takes a row because the register's status vocabulary is a convention and the reader's admissible set is an admissibility rule, and rule 5 counts both, however small | procedure | §9.2, §13, §14 | no |
| P90 | **§0 operator decision, 27 August 2026: the clip moves from £2,500 to £50,000.** Reference equity unchanged at approximately £100,000, so the single-name position moves from **2.5% to 50%** of the book. **Not a parameter edit.** The clip was *defined as* the notional at which fixed round-trip cost falls below 25 bps, and a clip set by fiat no longer inherits that definition; the definition is what changes and the number follows it. **Recorded in the house style, cost and not benefit.** *One:* the fixed-cost saving is bounded and small, approximately 16 bp on US names, 0.5 bp on UK tiered and 14 bp on UK fixed, and **on UK tiered the total RISES, 61.4 to 61.5 bp**, because the PTM levy crosses its £10,000 threshold and becomes payable where the smaller clip sat below it. A levy with a threshold is not a rate. **The venue where this system's UK evidence lives is the venue where the change costs money.** *Two:* market impact scales with participation, has **no ceiling**, and rises hardest in the small and mid-caps where the documented effects live; it is unmeasured, has no §13 row and this decision creates none, so the one cost that can grow without limit is the one the system cannot refuse on. *Three:* single-name concentration rises **twentyfold** and two positions fill the book, which collides with §4.4's regime notional caps of 7.5% and 3.75%, exceeded by factors of roughly 6.7 and 13, and with §6.7's 75 bps base unit under the cap stack; **the collision is recorded and not resolved**, and the clip has not quietly repealed either. *Four:* **the analysis brought to the operator argued against the change and the operator took it**, recorded because a decision taken over a stated objection and one taken without are different records. **The §0.6 consequence, resolved rather than left to silence.** A £50,000 clip needs a participation constraint against daily traded value; a participation constraint is a gate, a gate is apparatus, and §0.6 is armed. The decision takes **(b)**: the clip runs with **no participation constraint**, a **known unbounded exposure with no refusing mechanism**, because the operator authorised the clip and did not authorise an exception to the armed rule, and an exception may not be inferred from what a decision did not say. **(a)**, the gate landing as a named §0.6 exception with its own row, remains available and is not taken. The gate is registered as deferred in Annex A.1 behind the standing predicate, which records that it is absent by decision and does not soften (b). **§13 row 1 is not closed by this and remains unverified**: the clip did not move because the commission resolved | **§0 decision** | §0.11, §0.7(c), §0.10, §4.4, §5.4.4, §6.7, §13 rows 1, 8, 9 and 14, Annex A.1 | yes, the clip; the parameter object's clip constant moves |
| P91 | **Every clip-dependent row invalidated and re-derived at £50,000, or invalidated and left blocked.** Consequent on §0.11 (P90). **No figure was edited in place**: each is marked as recomputed, the superseded value retained beside it, and where a value could not be derived that is stated rather than filled. **§13 row 1 moves BLOCKED to PROVISIONAL**, because a reading now exists and the calibration does not: **UK tiered 61.5 bp**, up from 61.4, and **US approximately 3 bp** at an illustrative **USD 64,000** trade value. **The PTM levy moves from `n/a` to APPLICABLE**, its threshold being **£10,000** of consideration, which the £2,500 clip sat below and the £50,000 clip does not; a levy that was *previously not applicable at all* is now payable on every UK trade, and that crossing is why the twentyfold notional makes the UK tiered round trip dearer. **The row is not closed**: the reading is the operator's arithmetic and not a cited schedule, and **the three gaps are unaffected by the clip** and still open, being the FX route absent from any published schedule, the tiered-or-fixed election unmade and the contracting entity unestablished. **Rows 8, 9 and 14 stay BLOCKED and say why.** Row 8's ceiling is set by the largest documented post-decay effect and not by the clip, so what moved is its fixed-cost input whilst the impact term still has no column; row 9 inherits row 8; row 14 additionally carries a new question, a single clip being **at least 6.4% of a whole day's traded value** in a sub-$1m name at the illustrative rate, before allowing that a round trip is two orders, and **(b) means nothing refuses on it**. **§4.4's boundary constants 12.0% / 5.45% / 3.16% are withdrawn and NOT replaced, and §5.4.4 with them.** The reason is not arithmetic difficulty: §6.7's risk-based sizing and §0.11's fixed notional disagree, §0.11 did not say which binds, and a bound computed under either reading would be *a fitted parameter wearing a restriction's clothes*, chosen for producing the more workable matrix. **Both are blocked on a §0 decision rather than on data.** §0.10's microcap table is invalidated as a live reading and not recomputed, because shrinking its break-even column whilst impact has no column would make microcaps look cheaper at a clip that makes them dearer to trade. §0.7(c)'s table is superseded **as a derivation**: the clip no longer follows from the commission. **One open §0 decision is now materially larger and its status has not moved:** the FX exposure budget decides half the book, a 50% position in a US name being 50% of the book in USD, where at the £2,500 clip it decided 2.5% | restriction | §0.7(c), §0.10, §0.11, §4.4, §5.4.4, §6.7, §13 rows 1, 8, 9 and 14 | yes, consequentially on P90 |
| P92 | **Two UK cost tiers deferred, not taken: the AIM stamp-duty exemption and the new-listing SDRT relief.** Both are **cost-tier changes that make a SUBSET of names cheaper**, and a cheaper subset **admits names the conservative single tier refuses**. That is capability by §0.6's test, so both take an Annex A.1 row with a predicate and wait; neither is applied to any figure in this paper. *The temptation each answers to is the same one: a cost saving that is real, checkable and immediately useful is exactly the shape of thing the armed rule exists to hold.* **The AIM tier.** s.99(4B) Finance Act 1986, effective 28 April 2014, AIM being on HMRC's recognised growth market list at STSM041330. **Two limbs, both binding:** admitted to trading on a recognised growth market **and** not listed on that or any other market, so a **dual-listed AIM company does not qualify** and a tier keyed on AIM membership alone would be wrong for precisely those names. Worth **61.4 bp to 11.4 bp at the £2,500 clip, a factor of 5.4**; the £50,000 equivalent is not published, the base being 61.5 bp on a **PROVISIONAL** row 1. Provenance **`verified_secondary`**: the statute and the manual page are named and unread in this tree. **At the £50,000 clip the tier may be largely unreachable**, most AIM names lacking the depth; a participation constraint would exclude them and **§0.11 took (b)**, so what follows is not an exclusion but an exposure. **The SDRT relief.** Autumn Budget 2025: relief from the **0.5% SDRT charge** for companies newly listed on a UK regulated market **on or after 27 November 2025**, for **three years from listing**; it **does not touch existing Main Market shares** and **does not apply to the 1.5% clearance-system charge**. **Provenance is CORROBORATION ONLY**, being law-firm commentary and not HMRC, with no legislation named, so **the predicate is doubled**: the instruments report *and* an upgrade to a primary source. **Both rows carry an expiry consideration and the second's is structural**: the relief is time-limited by construction, so a name qualifying today may not in two years, and a tier assigned once and cached would silently under-cost the trade after expiry | n/a, deferred | Annex A.1, §5.2.2, §0.5, §0.11 | no |
| P93 | **Two false claims in §0.11 corrected, and a prior question opened rather than answered.** *This row changes no rule. It takes a row because it changes what a §0 decision asserts, and a decision whose record is wrong is worse than one whose record is missing: the second invites a reader to check.* **What was false.** §0.11 recorded that the £50,000 clip runs with *"nothing in the funnel that refuses on participation"* and *"no reason code that fires when an order is large relative to the depth available to fill it"*, and called the result *"an unbounded exposure"* that is *"uninstrumented"*. **§6.7's cap stack has carried participation at 2% of median daily notional per session over ≤ 3 sessions throughout**, §0.10 quantifies it at about £42,000 of depth for the old clip, Annex A.1's market-impact row is predicated on the book outgrowing it, and a position capped below the clip is killed by `advisory_haircut_below_clip`. **What decision (b) declined is a participation GATE, and a cap and a gate are different instruments**: a gate refuses at Gate 1 and names depth; a cap shrinks the position and leaves the clip floor to kill it. **(b) stands as the operator took it.** Restated correctly, the cap requires **£833,333** of median daily notional at £50,000, computed as 50,000 ÷ (2% × 3) and reproducing §0.10's own figure at the old clip; the cost is **legibility, not instrumentation**. **The prior question, opened and NOT resolved.** §0.11's first sentence moves the **minimum clip** and its third moves the **position**, and the manuscript reads the clip as a **floor** in six places. Under the floor reading §6.7 sizes between **£1,875 and £15,000** across the stop range, **every one below a £50,000 floor**, so every candidate is killed for being too small and **the book takes no positions at all**, which is the reverse of what §0.11 records and is the state §0.6 names when it says *a funnel calibrated to reject everything returns a null indistinguishable from there is nothing here*. **Computed, not asserted: §4.4's two constants ARE §6.7's arithmetic at a 10% stop**, 750 ÷ 0.10 = 7,500 and 375 ÷ 0.10 = 3,750, so the two are one rule written twice and **§0.11 is the outlier by 6.67× and 13.33×**. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input and no field the funnel reads at decision time. It corrects prose and opens a question.** Prepared in `docs/DECISION_sizing_collision.md`; §4.4 and §5.4.4 stay withdrawn | n/a, correction | §0.11, §0.10, §4.4, §6.7, Annex A.1 | no |
| P94 | **The §9.4 trace corpus fenced, and a live containment defect closed.** `corpora/_trace_filings/` will hold SEC Form 4 filings for the trace harness. **A Form 4 names an issuer, a reporting owner and a transaction date, which is exactly the material the entity fence exists to keep out of a proposal**, so the fences were built and tested **before anything was fetched**: eleven tests were written to fail first against a deliberately mis-registered route, and all eleven did. **The rule that changed.** `Corpus.__post_init__` now **refuses** any `retrieval_route` with an underscore-prefixed component, at construction rather than in `missing()`, *because `missing()` returns advice and advice is not a fence*: a registration file naming the route will not load at all. Any component is checked, not merely the last, `_trace_filings/2026` reaching the same material one level down. **The defect this found, and it was live.** `cmd_sweep` skipped underscore-prefixed **files inside** a route and read everything else, so **a route pointed AT an underscore directory had its contents read in full**, and `corpora/us/_raw` was reachable that way by a one-line registration edit. The skip now covers the route itself and lives once, in `corpusio`. `fences.discovery_import_closure` is extracted so a second fence uses the same walk: **no module reachable from `discovery.py` may contain the string `_trace_filings`**, and the fetcher is outside the closure and does contain it, so the test tests something. **§0.6 APPLIED EXPLICITLY, and the answer recorded.** *Does it add a gate, a family, a grammar row, a cost tier, a sizing input, a feed, or a field the funnel reads at decision time?* **No, and the containment is what makes the answer no rather than a description of intent.** The corpus feeds `trace.py`, which is evidentially inert by construction and refuses to register or admit; everything produced carries `TRACE-NON-EVIDENTIARY`; and the funnel **cannot** read it, by a refusal at construction, a refusal in the loader and an import-closure assertion. ***The honest condition, stated rather than glossed: remove those three and the classification flips to apparatus.*** A fetcher whose output can become the funnel's feed by configuration is a production ingestion adapter, which §3.7.7 and P72 already class as apparatus. This one cannot be, and the tests are the reason. **A rule that refuses more than it did is a restriction, and a restriction may land under the armed rule** | restriction | §3.7.2, §9.4, §13 row 22 | no |
| P95 | **§13 row 23 re-based off a pooled population; rows 11 and 15 given their derivations and their gaps.** **The correction is the one P79 made on row 21, live one row along.** Row 23's published distribution, 5 at position 3 and 8 at position 9 over 42 subjects, **pooled a drawn arm with an authored one**. Split on the labelled set's own `origin` field: the **36 drawn** give **8 first failures, all at position 9**, an intake kill rate of **22.2%**, deepest **9 of 12**, and **position 3 never fires**; the **6 authored probes** give all five position-3 refusals. **A probe is authored to trip a named route, so its abort position is a property of the probe and not of the flow.** Pooling put a 12% position-3 rate into a funnel whose drawn material produced **none**, and *doubling the probe set to twelve routes would double it whilst the funnel stood still*, which is word for word P79's argument about row 21's denominator. **On drawn material ELEVEN of twelve intake points are unexercised, not nine**, and they are named rather than counted. `intake_budget_exhausted` is reported beside the distribution and never inside it: **0 abandonments**. **Row 11 stays BLOCKED and names its missing input.** The derivation is shown, `n = (z[1-α/2] + z[1-β])² · 2·p̄·(1-p̄) / δ²`, giving **n = 2.7132 / δ²** from `p̄ = 8/36` at α = 0.05 and power 0.80. **δ, *the smallest actionable per-gate difference*, appears in row 11's rule and nowhere else in this specification**, with no definition, no row and no stated basis, so **a sample size derived against it would be a number chosen and presented as derived**. A sensitivity table is published so the cost of choosing δ is visible **without this paper choosing it**, with two stated limits that both push n up. **Row 15 stays BLOCKED**: the lag has not been measured once at any n, and **no source class dominates the sample because the US class has ZERO drawn subjects**, the 36 being 12 ASX, 12 TSX/SEDI and 12 MAR, so a threshold generalised from them to Form 4 would generalise across exactly the classes the sample does not cover. **Row 21a is unchanged and nothing was pooled into it.** **Binding-path step 4 is NOT discharged and is not marked closed to make a movement line look better**, and the fourth of its five outstanding items is the one that matters: **§9.4 requires the marginal defect rate to fall below *"a stated threshold"* and the specification does not state it and it has no §13 row**, so the rule cannot be discharged by any amount of tracing. That is a defect in the rule and not a shortfall in the work. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input, no field the funnel reads at decision time.** It re-bases a reading over the population it was always about | restriction | §9.4, §13 rows 11, 15, 21a and 23, §14 | no |
| P96 | **The floor audit: SEVEN sites, not six, and they agree.** Performed as part of taking §0.11's decision, because a decision that rests on how the manuscript reads a word should not rest on a count made from memory. **The earlier count of six was wrong**; §0.1's *"no stop both preserves the thesis and clears the minimum clip"* was missed. The seven are §0.1, §4.4, §5.1, §5.2, §5.9, §0.10 and §6.7, quoted in `docs/DECISION_sizing_collision.md` §1.1a. **All seven read the clip as a FLOOR. None reads it as a target or a ceiling, so there is no disagreement defect and no row is taken for one.** §5.1's explore arm additionally *sizes at* the floor, which is a **dual use and not a contradiction**, the arm electing the smallest size the rules permit; its consequence is inherited by §0.11 and stated there, namely that **while the floor is undetermined the explore arm has no size** and the below-floor region the association otherwise never observes is unobserved too. **One defect WAS found and it is a legibility defect in a reason code.** `capital_exceeds_clip_floor` marks a **zero** cell, one where the position **fails to reach** the floor, and **the name asserts the opposite**: *capital exceeds the clip floor* is the passing case. Rule 4 makes a code's legibility first-class, so it is recorded. **It is NOT renamed here**, because renaming a reason code is a change to the registry and takes its own decision rather than riding in on another. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input, no field the funnel reads at decision time. It counts and quotes.** | n/a, audit | §0.1, §0.10, §4.4, §5.1, §5.2, §5.9, §6.7 | no |
| P97 | **§0 operator decision, 27 August 2026: the fixed clip is WITHDRAWN and replaced by a derived floor.** Supersedes P90's £50,000, which is withdrawn in full, and P90's £2,500 predecessor with it. Reference equity **confirmed at £100,000**. **What settled it.** The arithmetic prepared under P93 established that **§4.4's two regime constants ARE §6.7's sizing arithmetic evaluated at a 10% stop**, 750 ÷ 0.10 = 7,500 and 375 ÷ 0.10 = 3,750, so two of the three rules in the collision were **one rule written twice** and £50,000 was the outlier by between 3.3 and 13.3 times. The operator took **resolution (i)**, in a stronger form than it was prepared: not merely letting §4.4 bind, but **withdrawing the chosen number outright** so that the floor derives from a measurement and one governance parameter. **The rule: the clip floor for a market is the smallest position at which §13 row 1's fixed round-trip cost falls at or below §13 row 29's tolerance.** **The cost, and it is the whole of the near-term effect.** Row 29 is OPEN and row 1 is PROVISIONAL, so **the floor does not derive for any market, position size is UNDETERMINED, and the book takes no positions.** `sizing.py` returns `clip_floor_tolerance_unset`, a **refusal to score**, because *a size of zero would say the position was evaluated and came out small.* **That refusal is the point.** A £50,000 floor would have produced **the same empty book** — §6.7 sizes between £1,875 and £15,000 across the stop range, all below it — and **§0.6 names why that would have been worse**: *a funnel calibrated to reject everything returns a null indistinguishable from **there is nothing here***. **The two empty books are not the same artefact:** one is empty because a constant was set too high and says so nowhere; the other names the unset parameter and carries the predicate that would fill it. **A second cost, stated:** §5.1's explore arm sizes *at* the floor, so while the floor is undetermined the explore arm has no size. **What it does not do:** it does not close §13 row 1, whose three gaps the clip never touched; it does not resolve the participation question, §6.7's cap being in force and only the *gate* deferred (P93). **§0.6: it REMOVES a chosen sizing input and replaces it with a derived one, so the admissible set is narrower, not wider. A restriction, and a restriction may land under the armed rule** | **§0 decision, restriction** | §0.11, §0.1, §0.7(c), §0.10, §4.4, §5.1, §5.4.4, §6.7, §13 rows 1, 8, 9, 14, 29 and 30 | yes, the clip constant is removed |
| P98 | **§13 row 29: maximum tolerable fixed cost. OPEN, operator governance.** Basis points of position, round trip, **excluding spread and market impact**. **The one free parameter the clip-floor derivation cannot eliminate**, and it is named as such rather than buried. **Why it sits here and not in a per-market clip**, four properties of the quantity and not preferences: it is **dimensionless**, so one number governs a USD and a GBP trade without an FX rate entering a governance decision; it is **comparable across markets**, which is the substance rather than a convenience, row 30's entire output being which markets clear the same bar; it is **readable against the break-even table**, §5.2.2 and §0.5 already being in basis points so a tolerance can be set beside a documented effect and read off, which a clip in pounds cannot; and it is **set once instead of guessed per venue**, a per-market clip being one guess per market, each drifting separately and none recording what it was trying to achieve. **One tolerance is one decision and every floor beneath it is arithmetic.** **The exclusions are load-bearing:** spread and market impact are not fixed, scale with participation and have no row, and *a tolerance that silently included impact would be a tolerance nobody could check against a schedule*. **§0.6: it does not add a sizing input, it REPLACES one.** The chosen clip is removed in the same version; the count of free sizing parameters falls from one chosen number per market to one governance number in total. **Restriction** | restriction | §13 rows 1 and 30, §6.7, §0.11 | yes, as the clip's replacement |
| P99 | **§13 row 30: derived clip floor, per market. BLOCKED on row 29, inheriting row 1's PROVISIONAL.** **A function and never a number:** `floor(market) = absolute ÷ ((tolerance_bps − proportional_bps) ÷ 10,000)`. Implemented in `src/fntn/scanner/sizing.py`, which **refuses in three named ways rather than returning a number it cannot justify**: `clip_floor_tolerance_unset` and `clip_floor_cost_unset` are refusals to score, and **`clip_floor_unreachable_at_any_size` is not**, being the measured fact that the size-independent share alone meets the tolerance so **no size satisfies it**. *Keeping the third apart from the first two is the substance: an unreachable market and an unset parameter look identical from outside and mean opposite things.* **US, a floor exists**: two fixed minimums, USD 1.00 commission and USD 2.00 FX each applied twice, give USD 6.00 round trip with no proportional term, so a 10 bp tolerance implies **USD 6,000** and a 5 bp tolerance **USD 12,000**. **UK, no floor exists at any size**: stamp duty is a percentage and dominates, the cost is **flat at ~61.4 bp from £2,500 to £50,000** and moves by a tenth of a basis point across a twentyfold range, **upward**, because the PTM levy crosses its £10,000 threshold. **NO SIZE MAKES A UK MAIN MARKET POSITION CHEAPER IN BASIS POINTS, AND A CLIP FLOOR IS A US CONCEPT THAT DOES NOT TRANSFER.** **Two claims of different strength and the difference is the point:** any tolerance below **~61.4 bp** excludes UK Main Market *(PROVISIONAL: it inherits row 1's three open gaps)*; any tolerance below **50 bp** excludes it **WITH CERTAINTY**, stamp duty alone being 50 bp, statutory, a percentage, and independent of every one of row 1's gaps. **So any tolerance in the 2 to 20 bp range the US table makes sensible excludes UK Main Market with certainty.** **A disagreement with §13 row 1 recorded rather than smoothed:** the USD 6.00 model reproduces row 1's small-clip reading, 18.75 bp against ~19 bp at USD 3,200, and gives **0.94 bp at USD 64,000 where row 1 records ~3 bp**; the two recorded readings solve uniquely for **absolute ≈ USD 5.39 and proportional ≈ 2.16 bp**, and *the residual is the signature of a term that does not decay*. If it is real the **US has a hard floor near 2.16 bp and a 2 bp tolerance is unreachable there too.** This paper does not choose between the models; it records that they disagree by 2 bp on the most leveraged number in it, and that **row 1's citation is what settles it.** **Consequence for Annex A.1, recorded and NOT acted on:** at 11.4 bp the AIM growth-market tier now decides **whether the UK is reachable at all** under a tight tolerance rather than making a reachable market cheaper. **The predicate is unchanged and the row is not taken. A capability becoming more valuable is not a reason to take it early; it is the reason the armed rule exists.** **§0.6: no gate, no family, no grammar row, no cost tier, no feed. It replaces a chosen sizing input with a derived one and adds three refusals. Restriction** | restriction | §13 rows 1, 29, 8, 9 and 14, §6.7, §4.4, Annex A.1 | yes, as the clip's replacement |
| P100 | **§4.4 and §5.4.4 RESTORED as derivations, and the restoration removes a rule rather than reinstating one.** They were withdrawn under P91 because the blocker was a §0 decision; **P97 took it**, so they return. **§4.4's two regime constants are withdrawn as constants and not replaced by new constants**, because they were never independent: **7.5% and 3.75% ARE §6.7's arithmetic at a 10% stop**, once at 75.0 bps of risk and once at the 37.5 bps cap floor. *Carrying them here as separate numbers stated one rule twice and invited the two copies to drift.* §4.4 now states `notional_cap = risk_budget ÷ stop_distance` and §6.7 states the rule, **which is one rule and a derivation where there were two rules**. Feasibility is unchanged and was never clip-dependent. **What remains withdrawn, and now for a stated reason rather than an undecidable one:** the ATR bounds **12.0% / 5.45% / 3.16%** were computed against a £2,500 clip floor and an assumed commission, and **`capital_exceeds_clip_floor` has no threshold to test against until §13 row 30 derives**, so the matrix's zero cells cannot be located. **They return by arithmetic once row 29 is set and row 1 closes, with no further decision**, which is exactly what was not true before P97. **§5.4.4 has no independent content**: every cell is the intersection of an admissibility class with §4.4's bounds, so it is restored with §4.4 and needs no decision of its own. **The blocker on both is no longer a §0 decision; it is one governance number and one citation.** **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input. It deletes two constants and states the derivation that always produced them** | restriction | §4.4, §5.4.4, §6.7, §13 rows 1, 29 and 30 | no |
| P101 | **The 1e residual closed: it was a regime change, not a term, and the US hard floor is a function of share price.** P99 published two cost models side by side because a single (absolute, proportional) pair fitted to §13 row 1's two US readings gave **~USD 5.39 and ~2.16 bp**, and the proportional part did not decay and could not be named. **It is the per-share commission.** A per-share commission is proportional to trade value at a fixed share price and so never decays, **but it carries a per-order minimum**, and below the size at which the rate overtakes the minimum it behaves as a fixed charge and decays like one. **The two readings sit on opposite sides of that boundary**, and a linear model fitted across it splits the difference, which is exactly what produced the 2.16 bp. **The test, and it is a test rather than a fit.** The share price is solved from the **USD 64,000 reading alone**, so reproducing that reading is not evidence; **the model then predicts 18.84 bp at USD 3,200, against the ~19 bp row 1 records, having never been shown it.** One free parameter fitted to one point predicts a second point to within a fifth of a basis point. At USD 3,200 the commission is USD 0.37 a side and the **USD 1.00 minimum binds**; at USD 64,000 it is USD 7.31 a side and the **rate binds**. **What is confirmed and what is not.** The *mechanism* is confirmed. The *share price* is not: **row 1's working records no share price at all**, only two trade values and two readings, so `p ≈ 43.79` is derived from the readings under the schedule's structure and is not read from an assumption row 1 made. *That is a third outcome and it is recorded as itself rather than forced into either branch.* **THE CONSEQUENCE IS THE PROJECT'S FIRST DERIVED SCREENING RULE.** The US hard floor is `104/p` bp on fixed pricing and `74/p` on tiered, so **no position size gets a name below it and a tight tolerance excludes low-priced US stocks at ANY size, in the same way and for the same reason stamp duty excludes UK Main Market at any size.** At 2 bp the minimum share price is **USD 52.00 fixed / USD 37.00 tiered**; at 10 bp, USD 10.40 / USD 7.40. **Every one is a LOWER bound**: FINRA's activity fee and the SEC fee were not read from a published schedule and both push the floor up. **Second consequence, and it reclassifies an open gap.** Row 1's **tiered-or-fixed election moves the hard floor by about 29%** and therefore the admissible universe with it: at 5 bp it is the difference between names above USD 20.80 and names above USD 14.80. *It was a convenience question about which schedule costs less; it is now a question about which names exist*, and it is promoted in the decision pack. **`clip_floor_unreachable_at_any_size` fires for the US wherever the tolerance sits at or below the hard floor at that price**, and its distinction from a refusal to score survives, which is the requirement: **an unreachable name and an unset parameter look identical from outside and mean opposite things.** **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input. It replaces two published models with one and names the mechanism** | restriction | §13 rows 1, 29 and 30, §0.11, Annex A.1 | no |
| P103 | **§13 row 28 opened: §9.4's stopping threshold, which the rule requires and the document never states.** P95 recorded the gap and could not close it because there was no row to put it in; **this is the row**, and opening it converts *binding-path step 4 is undischargeable at any n* from an observation into a register entry with a status and an unblocker. **The threshold and the block size are one decision, by the rule of three row 21a already uses:** two consecutive blocks at zero must-class defects is `2n` items at zero, zero events does not estimate zero, and the 95% upper bound on the residual rate is `3/(2n)`. `n` = 100 supports 1.5 per hundred, `n` = 300 supports 0.5, `n` = 1,500 supports 0.1. **The row is BLOCKED in row 21a's shape**: the precision required is not a property of the harness but of what §14's freeze signature can carry, and §14 has never been approached. **Two counts of the §13 table corrected in the same row, and both were wrong by hand.** The heading read *twenty-five calibrations* and the summary read *twenty-seven numbered rows*; the table holds **twenty-nine numbers and thirty entries**, number 26 having never been issued. The summary's status tally omitted **row 1** and **row 29**, the two rows the cost derivation turns on. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input. It registers a parameter the specification already demands and states no value for it** | procedure | §9.4, §13, §14, binding-path step 4 | no |
| P104 | **§13 row 22 carries one observation about REPLAY, from the contamination check.** The twelve drafts on the queue were swept over ASX and ASIC documents **no commit in this repository has ever carried**: `query_log` records one sweep over 14 documents at 23:04 on 26 August, the registered corpus was `./corpora/us`, and `corpora/us` was not fetched until 23:19 by its own manifest. So the population behind rows 21a and 23 **cannot be replayed byte-for-byte from its parameter hash**, which is what rule 1 asks of anything on the trading path. Contained: the drafts are blocked on the operator, none registered, none carrying capital, and §3.7's fence keeps agent-selected material from capital by every route. *The contamination question it was raised to answer is separately answered and NEGATIVE, in `docs/CONTAMINATION_CHECK_2026-08-27.md`* | n/a, observation | §13 row 22 | no |
| P105 | **The third instance of one error, and the first found in CODE rather than in a published reading.** P77 and P79 found §13 row 21 pooling a drawn arm with an authored one; P95 found row 23 doing the same. **`RunReport._abort_positions` selected every intake refusal with no filter on `origin`**, so it pooled the **agent** arm, which is the thing under test, with the **random-mechanism control** arm, which §Σ.4 provides in order to be compared against it. **Pooling the control into the treatment destroys the comparison the control arm is for**, and this one was rendered from the ledger on **every run** rather than published once. **What it hid, on the live ledger:** agent **4/12 = 33.3%** at positions 3 and 9, control **8/12 = 66.7%** at position 7 **and nowhere else**, pooled *12/24 = 50%*, a figure describing neither arm. **Position 7's eight firings are an artefact of the control arm running second**, being duplicates of pointers the agent arm opened in the same run, so pooling imported a scheduling property of the control design into a figure claiming to describe the intake flow. **The report now splits by `origin`**, gives every arm that raised a subject a column whether it was refused or not, and retains the pooled figure **labelled as not a reading** so a reader holding a pre-P105 report can see what moved. *The cost, stated:* each arm's denominator is now half the pooled one and each reading is correspondingly weaker. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no sizing input. It is a denominator convention in a renderer, which is what P79 and P95 were** | restriction | §13 row 23, §9.2, §Σ.4 | no |
| P106 | **P96's rename prepared, and its stated premise refuted.** P96 declined to rename `capital_exceeds_clip_floor`, which marks a **zero** cell where the position **fails to reach** the floor whilst reading as the passing case, on the ground that *renaming a reason code is a change to the registry*. **It is not in the registry.** `ALL_CODES` holds forty codes and none is this one; the string appears in three documents and no Python file, as does `advisory_haircut_below_clip`. **A string the manuscript writes in code voice is not a code**, and by rule 4's own terms a code outside the registry cannot be counted or emitted. **The consequence is a window rather than a preference:** renaming today is a find and replace over prose; renaming once row 29 sets the floor and the code enters `codes.py` costs a registry entry, an emitting branch, a test, a §8 template, a resurrection predicate **and every ledger row already stamped with the old string, which rule 4 forbids overwriting**, leaving two names for one state for ever. `clip_floor_unreached` is rejected as a candidate because it collides in the eye with `clip_floor_unreachable_at_any_size`, a **market-level** fact against a **cell-level** one, which is how the original defect was made; `position_below_clip_floor` is recommended. **Prepared and NOT taken.** **Recorded in the same row: §5.1's explore arm has no size while the floor is undetermined**, so the below-floor region §7.1 would otherwise never observe goes unobserved too. *That is a COST of P97's derived floor, not a defect, and row 29 restores it by arithmetic with no further decision* | n/a, prepared | §4.4, §5.1, §13 rows 29 and 30, Annex A.1 | no |
| P107 | **`docs/CORRECTIONS.md` opened: one row per assertion this project has had to withdraw, whoever made it.** §12.1 records what the *specification* changed and not what was *said and was wrong*, and those are different: a corrected rule leaves a trace, a corrected claim leaves none. **Two sections deliberately**, errors made **to** this project by advice and errors made **by** it and refuted by its own instruments; *a register holding only the first is a grievance list*. **Seeded with thirteen rows**, each carrying a §0.5 provenance tag, `verified_primary` where the artefact is in this tree and `named_unverified` where the brief named an error nothing here establishes. **Section A:** the sec.gov 698-byte stub that looks like success; `tidy.sh` reporting *tests failed* when pytest was merely absent; the corpus integrity check walking manifest-to-disk and never disk-to-manifest; a directory's mtime read as a file's, demonstrated in this tree where every directory reads the checkout time; §0.10's false claim that nothing refuses on participation (P93); and the 1e model dropping the per-share commission (P101). **Section B:** the pattern-only entity fence that passed every unit test and refused 94% of real proposals; the designator branch; the contamination check recorded as run and NEGATIVE; the raw pages never retained, `raw_bytes` a number with nothing behind it; `_raw` reachable by a one-line registration edit; the abort-position distribution pooled three times, the third in code; and seven floor sites where six were counted. **The pattern the register exists to record:** in every Section B row the wrong belief passed the weaker instrument and was killed by the stronger, and the stronger was always the rules read against a **world** rather than against each other. **§0.6: it is a ledger, which is procedure by the rule's own list** | procedure | §12.1, §0.5, `docs/CORRECTIONS.md` | no |
| P108 | **The P96 rename TAKEN, on delegated authority, 27 August 2026, and the timing is the argument.** `capital_exceeds_clip_floor` marked a **zero** cell, one where the position **fails to reach** the floor, whilst reading as the passing case. It is renamed **`position_below_clip_floor`** throughout the operative rule text. **P96's stated ground for leaving it alone was false and that falsity is itself a corrections-register row**: it held that renaming a reason code is a change to the registry, and **the name was never in the registry**. **Taken now precisely because taking it after §13 row 29 lands would cost a migration.** Today it is prose: two operative sentences in §4.4 and four uses across the decision files. Once §4.4's matrix is implemented against a derived floor the same rename costs a registry entry, an emitting branch, a test, a §8 template, a resurrection predicate **and every ledger row already stamped with the old string, which rule 4 forbids overwriting**, leaving two names for one state for ever. **What is deliberately NOT renamed:** every place this register, `docs/DECISION_sizing_collision.md` or this change log **quotes** what §4.4 said, because renaming inside a quotation falsifies the quotation; and `from_narrative_to_null_v1_13.md` entire, which is a superseded manuscript and a record of what v1.13 stated. **It does not enter `codes.py`**: a code defined with no branch that emits it is the untested branch `test_every_defined_code_is_emitted` exists to refuse. `clip_floor_unreached` was rejected because it collides in the eye with `clip_floor_unreachable_at_any_size`, a **market-level** fact against a **cell-level** one. **§0.6 test, applied: does it add a gate, a family, a grammar row, a cost tier, a sizing input, a feed, or a field the funnel reads at decision time? NO to every one. It renames one label and changes no behaviour, so it is procedure** | procedure | §4.4, §5.4.4, §13 rows 29 and 30 | no |
| P109 | **§13 row 29 SET AT 10 BASIS POINTS, on delegated authority, 27 August 2026. CLOSED.** Registered as `max_tolerable_fixed_cost_bps` = 10.0; the object re-stamped to row 6 of `docs/REGISTRATION_HISTORY.md`, caused by that field and no other. **Both ends of the range were DERIVED and the value sits inside it rather than at an edge.** *Lower, 2.375 bp*: below `104/p` no position size of any kind reaches the tolerance. *Upper, 12.5 bp*: §5.2.2's cheapest break-even of 22.5 bp was computed at a **£6.25 round trip on £5,000**, a **12.5 bp** fixed-cost basis, so a tolerance above it permits a trade whose fixed cost alone exceeds the one Gate 1's ceiling was calibrated on. ***The withdrawn implicit rule set the clip where fixed costs fell below 25 bp, DOUBLE that basis, and was never coherent.*** **THE COST, BEFORE THE BENEFIT: 10 bp IS A US-ONLY DECISION.** UK Main Market is excluded **with certainty**, stamp duty alone being 50 bp. **AIM is excluded at about 10.3 bp and NOT because of stamp duty**: IBKR's UK commission is 0.05% a side, **10 bp round trip on its own**, and `sizing.py` refuses where the proportional share **meets or exceeds** the tolerance, so AIM is unreachable at 10 bp **with the exemption fully granted**. ***The deferred AIM growth-market tier therefore cannot rescue the UK: AIM fails on COMMISSION, not on TAX***, and its Annex A.1 row is marked **moot at this tolerance and expressly not withdrawn**, because it becomes live again at 12.5 bp. **US: reachable above about USD 10.40 a share** (`104/p` < 10), the clip floor rising steeply below about USD 12 and flat above about USD 30. ***THE REVISION AVAILABLE IN ONE WORD: 12.5 bp is the value at which AIM becomes reachable, so the choice between 10 and 12.5 is the choice of whether the UK exists in this strategy.*** 10 was taken because a parameter set at the exact edge of its own coherence bound has no margin for row 1's three open gaps, every one of which pushes cost UP. **One discrepancy recorded and not smoothed:** row 1's UK readings imply an AIM residual of 11.4 bp against a bottom-up 10.20 bp, a gap of 1.2 bp on a PROVISIONAL row; the conclusion is unaffected, both exceeding 10. **§0.6 test, applied: SETTING a declared governance parameter is the calibration sequence. ADDING one would be apparatus, and none was added: row 29 has existed since P98. No gate, no family, no grammar row, no cost tier, no feed. It is a sizing INPUT that the specification already declared and left unset** | restriction | §13 rows 29 and 30, §4.4, §5.4.4, §0.7(c), §0.10, Annex A.1 | no |
| P110 | **The row 29 cascade worked: ten releases, six close or return by arithmetic, three stay blocked on named MEASUREMENTS, one is discharged.** Worked in `docs/CASCADE_2026-08-27.md`. **§13 row 30 COMPUTES** and moves to PROVISIONAL, closing as the *function* it always said it was and never as a number: USD 6,055 at USD 43.79 a share, USD 30,000 at USD 12, **unreachable at or below USD 10.40**, and the independent `cost_at` inverse reads exactly **10.000 bp at every published floor**. **§4.4's ATR bounds return, and the derivation was RECOVERED rather than asserted**: `ATR_max = risk_budget / (multiplier x clip_floor)` reproduces the published 12.00 / 5.45 / 3.16 and 6.00 / 2.73 / 1.58 **six of six exactly** at the withdrawn £2,500 floor, with §6.7's £750 and £375 and multipliers 2.5 / 5.5 / 9.5. ***The cost: the reachable ATR range roughly HALVES***, 12.0% to about 6.4% at h = 5, the derived floor being nearly twice the withdrawn clip. ***A DEFECT EXPOSED AND NOT REPAIRED:*** §4.4's matrix is indexed (family x ATR decile x regime) and **a price-dependent bound does not fit that index**; publishing three constants again needs a chosen reference share price, which is a chosen parameter wearing a derivation's clothes, and adding a price dimension is **apparatus**. **§5.4.4 and §0.7(c)'s two columns return on the same terms**, correct at one named price. **Rows 8 and 9 stay BLOCKED**, row 8's blocker list shortened to row 1 and the design segment; a **derived minimum share price of USD 10.40 now exists beside row 9's floor and is a different mechanism**, commission against spread, the binding one being the higher. **Row 14's reachability question is ANSWERED**: at 6% of ADV the floor is reachable down to about **USD 101,000** of median daily notional, computed with **no FX at all**, and the row's earlier illustrative arithmetic is superseded. ***THE HEADLINE: THE BOOK IS NOT EMPTY.*** The floor of GBP 4,694 sits inside §6.7's GBP 1,875 to GBP 15,000 band, positions exist for stops up to **15.98%**, and the conclusion holds for **any USD/GBP rate between 0.404 and 3.229**, so no FX assumption is load-bearing. **§0.6: no gate, no family, no grammar row, no cost tier, no feed, no new sizing input. Every figure is arithmetic over §13 rows 1, 29 and 30 and §6.7, and where arithmetic could not reach it says so** | restriction | §4.4, §5.4.4, §0.7(c), §0.10, §5.1, §13 rows 8, 9, 14 and 30 | no |
| P111 | **§5.2.2 and §0.10 recomputed against a measured cost, and Erratum B discharged.** Both tables rested on assumed fixed costs, §5.2.2 on an assumed **£6.25 round trip on £5,000** (12.5 bp, *recovered backwards from the clip definition* by §0.7(c)'s own account) and §0.10 on **25 bp**, the cost at the withdrawn £2,500 clip. **The replacement is a BOUND and not another assumption**: row 29 registers 10 bp and row 30 defines the floor as the size at which cost equals it, so **every admissible position carries at most 10 bp of fixed cost by construction**, and the figures are upper bounds where they were estimates. §5.2.2 falls by exactly **2.5 bp** everywhere (cheapest 22.5/19.5 becomes **20.0/17.0**); §0.10 by **15 bp** (225/425/625 becomes **≤ 210/410/610**). **Published cells are retained beside the recomputed ones and none is edited in place.** ***NO CONCLUSION MOVED, and the check is recorded as RUN***: the midpoint reading stands, the bucket ordering is unchanged by a uniform shift, `delta_min_floor` = 25 bps stands on a ground that held at 22.5 and holds at 20.0, and §0.10's rows still fail by 95, 295 and 495 bps. **§5.2.2's UK column is STRUCK rather than recomputed**, UK Main Market being unreachable at any tolerance inside row 29's derived range, and **its heading changes from *AIM / US / short legs* to US**, AIM being excluded on commission and the short legs untraded. **Erratum B is discharged**: the two tables were incomparable because one was per-clip and the other per-notional, and a **dimensionless** bound is comparable where a per-notional assumption is not. **One stale number inside a surviving argument corrected**, the registration's `rationale` naming 22.5; `hash` pops `rationale` before hashing, so the correction costs **no re-stamp**, which is the design working. **The sweep found five sites and no others**: §5.2.2, §0.5's prose quotation of it, §0.10, §0.7(c)'s superseded clip table (deliberately not re-tabulated) and the registration rationale. **No gate threshold, sizing rule or admissibility rule was computed against the £6.25 assumption.** **§0.6: a grid's values move and no gate, family, grammar row, cost tier, feed or sizing input is added. Rule 5 counts a grid change as a version all the same, which is why this row exists although no conclusion moved** | restriction | §5.2.2, §0.10, §0.5, §0.7(c), §13 rows 1, 14, 29 and 30 | no |
| P112 | **Four prepared recommendations TAKEN on delegated authority, 27 August 2026, and one refused as undelegable.** Worked in `docs/PHASE5_decisions_2026-08-27.md`. **§13 row 28 CLOSED: zero MUST-CLASS defects per hundred items for two consecutive blocks, at n = 100.** Not zero defects of any class, which is what makes it satisfiable: §9.4 calls `undecidable` *the harness's product*, so a correctly working harness finds things indefinitely. **n is DERIVED on §13 row 21a's rule of three**: `2n` items at zero bounds the residual at `3/(2n)`, so n = 100 supports **1.5 per hundred** and `n = 150/b` inverts it. **Two blocks of 100 is 200 items, about three times all the tracing ever done here**, and doubling n buys 0.75 at the cost of 400 more items on an instrument that has never run to completion. ***The cost: the freeze is signed over a residual must-class rate that could be 1.5 per hundred.*** **Binding-path step 4 becomes dischargeable, which it was not at any n before.** **§13 row 1's tiered-or-fixed election: TIERED**, moving `104/p` to `74/p`, the hard floor down 28.8% and the minimum admissible share price from USD 10.40 to USD 7.40. ***The cost is larger than the benefit is certain:*** P101 fitted **both** schedules to the **same two readings** with the same USD 4.00 fixed component and the same USD 1.00 minimum, so **28.8% is `74/104` restated and not a measurement**. Every unmodelled tiered pass-through narrows the gap and none widens it, so **`74/p` and USD 7.40 are LOWER bounds**, and above about 0.0015 a share the election reverses by arithmetic. **§13 row 1's FX route: MANUAL SPOT**, on an asymmetry that survives the gap: automatic would need to price below 0.0031% to win at USD 64,000, a tenth of the reported 0.03%. **The rate stays uncited, the fetch having returned 403, so the FX term stays OPEN**: the decision does not depend on the number and the paper does. ***§13 row 1 STAYS PROVISIONAL on the contracting entity, which is NOT delegable: it is a fact about the operator's account and not a recommendation, and there is no conservative direction.*** **`audit_fraction` REGISTERED**, third instance of the class that caused three prior re-stamps; the value is unchanged at 0.10 and is now on the record, `ScanConfig` no longer defaults it, `cli.py` reads it from the registration, and `scan` refuses with a stated reason when it is unset. **§0.6 test, applied to each: SETTING declared parameters is the calibration sequence. Row 28 was declared by §9.4 and opened by P103; the two row 1 elections were declared gaps on an existing row; `audit_fraction` was declared pre-registered by §7.2 and merely was not. No gate, family, grammar row, cost tier or feed was added** | restriction | §9.4, §7.2, §13 rows 1 and 28, §14 | no |
| P113 | **The eight undefined referents resolved: none remains unnamed, and the largest is REFUSED rather than filled.** Worked in `docs/REFERENTS_RESOLVED_2026-08-27.md`. ***§13 row 31 opened for §0.10 and §7.6's PROMOTION-TO-LIVE-CAPITAL predicate, BLOCKED on an explicit §0 operator decision.*** Both sections call it *pre-registered* and it holds **two blanks**, *a stated margin* over *a stated minimum sample*, **and has done since the first version of this paper**. ***Until they are filled, nothing in this document authorises capital and the gate can neither pass nor fail.*** A predicate with an unstated margin is **not a strict gate that nothing clears; it is not a gate**, and a reader who assumed the first would be wrong in the direction that matters. It is **the only route by which a candidate that failed a hard floor later receives money**. *Contained, which is why this is a register entry and not an alarm: the shadow cohort needs a design segment and there is none.* **It heads the decision pack, above row 29.** **The other seven.** §9.4's threshold and §7.2's audit fraction were discharged at P112. **§14's *stated count of items* is DEFINED and DERIVES: 200**, being two blocks of 100 under row 28's stopping rule, so the precondition names the rule's own count rather than a second beside it; what remains is a **stratification** of those 200 and not a count, and it waits on which pipeline §9.4 addresses. **§13 row 32** opened BLOCKED for §3.4's roster coverage threshold, which today flags nothing. **§13 row 33** opened OPEN for §3.6.5's cadence, day and source pages, whose absence is what the 27 August replay finding is made of. **§5.4.2's fallback ladder is NON-BINDING with the reason**, the registration naming no surprise measure for it to fall back from, **and becomes required in the same commit that names one**. **§5.4.3's concert-party band is NON-BINDING by containment**, its family sitting in Annex A, **and must be set in the same commit that takes that row**. **§0.6: three §13 rows and no gate, family, grammar row, cost tier, feed or sizing input. Registering that a declared parameter is unset is the register doing its job** | procedure | §0.10, §7.6, §3.4, §3.6.5, §5.4.2, §5.4.3, §14, §13 rows 31, 32 and 33 | no |
| P114 | **The replay class closed at the class, not at a third instance, and the twelve drafts marked.** Worked in `docs/REPLAY_INVARIANT_2026-08-27.md`. **Three times this project depended on material it could not produce again**: the raw fetched pages were never retained, the registration chain's first object survives only as a reconstruction, and **the corpus the twelve queued drafts were swept from is in no commit at all**. ***Each was closed as an instance and the class stayed open, which is how it recurred twice more.*** The class is **material that decided something was not committed at the moment it decided it**, and retaining pages does not stop it, nor does recording a superseded hash: **only refusing to decide over uncommitted material does.** **Two reason codes on a new `provenance` surface.** `corpus_not_committed` refuses to CREATE an unreproducible record; `population_not_replayable` MARKS one that already is. **`cmd_sweep` now refuses over a corpus git cannot produce again**, before the master is loaded and before a document is opened, *a refusal that has already done the work it was refusing not being a refusal*. `--untracked-files=all` is load-bearing: **a corpus one document larger than its last commit is exactly the silent case**. The check is discriminating and not merely strict, the test asserting that `./corpora/us` passes. **Written to fail first and it did.** ***The cost: a corpus fetched and swept in one sitting must now be committed between the two.*** **The twelve are MARKED and nothing is deleted**: twelve `population_not_replayable` rows on the provenance surface, the records retained in full, **nothing about their content withdrawn and only the claim that they could be replayed**. *The code's resurrection predicate is a refusal to resurrect, because keeping the material now would not make those records reproducible, and a predicate offering a route where none exists would be worse than none.* **§0.6: two reason codes and a refusal, which the rule's own list calls procedure. No gate, family, grammar row, cost tier, feed or sizing input** | procedure | §3.6.5, §13 row 33, `codes.py`, `corpusio.py`, `cli.py`, `ledger.py` | no |
| P115 | **§9.4 is written about the ITEM pipeline, and the previous batch inventoried the wrong one. The import fence ran in one direction of a two-way prohibition, and now runs in both.** Worked in `docs/PIPELINE_9_4_2026-08-27.md`. ***Tested rather than assumed:*** every load-bearing noun in §9.4 is item-side, **gates** (which the discovery layer does not have), **items**, **feed**, **source class**, **catalyst type**, **filing flow**, and it does not mention an intake point once; §0.5 says *runs real items through the funnel*. **`trace.py` is not the error and does not claim to be the exercise**: it says *§9.4 applied to §3.7's two ingestion surfaces* and names §13 rows 21 and 23 as its product. **What was wrong is that P6 answered a correct question against the wrong set of twelve.** **Redone against the eleven `OBSERVATION_ORDER` points: a Form 4 block exercises FOUR directly** (`item_source_inaccessible`, `ingestion_lag_exceeds_window`, `extraction_schema_incomplete`, `issuer_unresolved`), a fifth for some filings, and **makes two others pass rather than fire**, a Form 4 being the regulator-stamped corroboration position 9 asks for. Against the discovery layer's twelve it exercised none. ***Position 5 is the one that matters: it is the only route to a §13 row 15 observation, and row 15 is BLOCKED for want of one.*** **Binding-path step 4's description corrected: it is not partly done, it has not been started.** ***THE IMPORT FENCE COVERED ONE DIRECTION.*** `assert_import_fence` stops `discovery.py` reaching prices, outcomes and gates; **nothing stopped a gate module importing the discovery layer**, which is the crossing `CLAUDE.md` forbids because it would re-base §7.1's headline on an agent-selected population, and the existing fence would have reported clean throughout. **`assert_reverse_import_fence` closes it with THREE states**, and today returns **`NOT_APPLICABLE`, deliberately not `CLEAN`**, no forbidden module existing yet: *a not-applicable check may never be read as a pass*. The breach path is tested **by building the breach**, a fence first exercised by the breach it exists against being a fence nobody has tested. **§8d's deliverable is the STRATA the 200 items must contain**, not their number: the live filing flow rather than a curated set, spanning transaction codes P, S, A, M and F because A, M and F are the ones that look like purchases and are not, **including amendments (4/A), which no point addresses at all**, late filings, unresolvable CIKs, at least one withdrawn document, and at least two calendar quarters; plus non-filing regulatory disclosure, §0.7(g) voluntary communications, running documents and single-session catalysts. **§0.6: one fence and one corrected description. A fence is a refusal, which the rule's own list calls procedure, and the trace corpus fence is NOT relaxed: what this row establishes is that the filings should have been pointed at the item pipeline, not that the discovery fence should admit them** | procedure | §9.4, §3.5, §14, binding-path step 4, `fences.py` | no |
| P116 | **Two more prepared recommendations TAKEN on delegated authority: §14's θ and the account type.** They were prepared with recommended values and were not named in this batch's phase list; the delegation is over prepared recommendations and does not stop at a work plan. **θ = 0.20**, registered, the object re-stamping to row 8 of the chain caused by `theta` alone. The prior 0.25 was **a recorded placeholder, non-binding until the archive exists**; 0.20 is a decision, at the **low end of the argued 0.2 to 0.5 band**. **The errors are not symmetric**: too low costs time and nothing else, the instrument still working later; **too high costs the instrument**, an association measured across overlapping segments being indistinguishable from an artefact of the overlap. ***The cost: fewer concurrent directives and slower accumulation, so §7.1's association arrives later.*** **Account type: CASH.** The book is a laboratory at zero expected capital-derived edge, the grammar is long-only for the one live family, and a margin facility adds a failure mode **no gate in the stack refuses on**. ***The cost: idle days between rotations***, a real drag on how many observations the design segment ever sees. Revisit if and only if a short-side family is admitted. ***It does NOT enter the parameter object***, on this project's own criterion that the registration carries values which change what a run refuses: **nothing in the code reads an account type**, and registering a value no code reads is how a parameter object stops meaning anything. ***And a correction to the batch's own expectation, recorded rather than quietly satisfied:*** the brief expected §13 row 29 closing to move **binding-path step 3**; **it cannot.** Step 3 is settled by §14's θ, δₘᵢₙ floor and account type, and **row 29 is a §13 row that appears in none of them.** Two of the three now read CLOSED; **step 3 stays NOT CLOSED because the δₘᵢₙ floor is deferred on purpose, waiting on row 1.** **§0.6: two declared §14 governance parameters set. Setting a declared parameter is the calibration sequence; adding one would be apparatus, and neither was added** | restriction | §14, §3.6.7, §6.9, §13 row 20 | no |
| P117 | **§13 row 1 CLOSED, and the entity gap was RETIRED BY BEING SHOWN IMMATERIAL rather than answered. The δₘᵢₙ floor DERIVES. BINDING-PATH STEPS 1 AND 3 CLOSE, the first steps to close in this project's history.** Read in `docs/IBKR_SCHEDULE_2026-08-27.md`. ***The entity gap.*** Both plausible entities' schedules were retrieved and compared **mechanically rather than by eye**: the United States commission block and the United Kingdom commission block are **byte-for-byte identical** on both pages, hashing to `053442ce710bbf1a` and `1ad21c16928f574b` respectively. **So the entity cannot change this row's answer, and no operator input was needed.** *Testing materiality before asking is what established that; the gap had stood on the register as a blocker for a fact the answer never depended on.* *The limit is stated: it retires the gap ON THIS ROW. Compensation limits, regulator and account terms still differ.* **Read from the publisher's own pages at 2026-08-27T19:00:05Z with URLs, byte counts and digests. Provenance `verified_primary`.** **US tiered USD 0.0035/share min USD 0.35, fixed USD 0.0050 min USD 1.00; UK tiered 0.05% min GBP 1.00; LSE exchange 0.000045 of value min GBP 0.11 and clearing GBP 0.06.** ***Two published figures contradict what this project assumed.*** The **tiered per-order minimum is USD 0.35**, not the USD 1.00 P101's model gave both schedules; and the **PTM levy is GBP 1.50**, not GBP 1.00, on buy and sell above GBP 10,000, so GBP 3.00 round trip. **The FX gap closed too:** the spot page that returned **403** to the previous batch answered **200** and was read: **0.20 basis points of trade value, minimum USD 2.00**. At USD 64,000 the minimum binds at **0.31 bp**, which is exactly the bounded downside P112's dominance argument used, **so that argument is confirmed by the schedule it was made without**. **CLOSED as a COMMISSION row, on option A's terms**: the SCOPE block names A, B and C with **no recommendation**, so the delegation does not reach it and the scope is unchanged. ***The δₘᵢₙ floor DERIVES at 17.0 bp*** and is registered, re-stamping to row 9 of the chain. **The floor IS the cheapest per-trade break-even**, an effect that cannot clear the cost of trading it being unactionable in every cell: `7.0 bp spread + 10.0 bp fixed`. **The fixed term is row 29's BOUND, not an estimate**, and needs neither a share price nor an FX rate. **Midpoint and not conservative, derived not preferred**, §5.2.2 saying the gates read the midpoint, so a conservative floor would refuse what the gates admit; **and §6.1's ladder does not apply**, Gate 1 applying it to the CLAIMED effect whilst δₘᵢₙ judges a MEASURED one, so applying it here would charge the decay twice. ***IT IS A LOOSENING: 25.0 to 17.0.*** The prior value carried **8.0 bp of margin that was never derived**, and directives between 17.0 and 25.0 bp are now admissible that were previously refused. **A necessary and not a sufficient condition**: no measurement bounds how far above break-even a directive must sit, so no margin is added. **Two report fixtures were found to have gone vacuous** by editing row 1 to CLOSED when row 1 had become CLOSED; `_register_copy` now **refuses a no-op edit** and the fixtures compute their flip from the register. **§0.6: a row closed on a read schedule and a declared governance parameter derived. Nothing added** | restriction | §13 rows 1 and 14, §14, §5.2.2, binding-path steps 1 and 3 | no |
| P118 | **THE TIERED ELECTION REVERSES TO FIXED, on measured components rather than a fit, and the measurement names the USD 4.00 nobody could name.** Worked in `docs/ELECTION_MEASURED_2026-08-27.md`. **The asymmetry is one published table row:** third-party fees under **tiered** are *Regulatory, Exchange, Clearing and Pass-Through*; under **fixed**, *Regulatory* only. **Fixed absorbs exchange fees, NSCC/DTC clearing and pass-through; P101's model gave BOTH schedules the clearing term.** **Crossover derived: tiered wins only where the two legs' exchange fees sum below USD 0.0025949, USD 0.0012974 a side.** ***§4.3 puts this strategy in a case the question did not name:*** entries and signal exits fill **at the open**, paying the **opening-auction** rate (NYSE 0.0010, NASDAQ and ARCA 0.0015), and **stop exits are marketable and remove at 0.0030**. **It never rests a limit order in the continuous book, so the add rebate is real and unreachable, and is reported rather than averaged into anything.** **Four grounds:** every stop exit favours fixed at every venue and no routing avoids it; two of three main venues' opening rates exceed the crossover and **SmartRouting picks the venue, not the strategy**; ***fixed's proportional term is a CONSTANT 102.01/p whilst tiered's spans 96.06/p to 116.06/p***, and §13 row 30 needs one number per market; and tiered wins only NYSE-open to NYSE-open by USD 0.0006 a share. *Tiered still wins below 200 shares, where fixed's USD 1.00 minimum binds and tiered's USD 0.35 does not; the region is real, bounded, and does not cover the stop legs.* ***THE MEASUREMENT NAMES ROW 1'S UNEXPLAINED USD 4.00: it is the two manual-spot conversions at their USD 2.00 minimum***, priced on the page that returned 403 to the previous batch, and USD 2.00 commission minimum plus USD 4.00 FX **is exactly the USD 6.00 row 1 has always stated.** **Measured: `60,000/V + 2.01/p + 0.206` below `V = 200p`, `40,000/V + 102.01/p + 0.206` above**, against the fitted `4/p` and `104/p`. *The fit was close for the wrong reason, putting the whole size-independent term on `4/p` where the measurement splits it into per-share regulatory fees and an SEC fee proportional to VALUE.* **§13 rows 29 and 30 recomputed**: floors USD 6,155 at USD 43.79, USD 8,522 at USD 20, USD 13,363 at USD 15, none at or below USD 10.42, every one checking at 10.000 bp. ***TWO SCREENS, AND THE BINDING ONE IS NOT THE COST: below USD 13.20 a share the floor exceeds §6.7's largest position of about USD 19,350, so between USD 10.42 and USD 13.20 a name is cost-reachable and size-unreachable.*** The book is still not empty. **§0.6: a declared election changed on a read schedule, and two derived tables recomputed. No gate, family, grammar row, cost tier, feed or new sizing input** | restriction | §13 rows 1, 29 and 30, §4.3, §5.2.2 | no |

**What v1.14 does not do.** It adds no gate, no family, no grammar row, no cost tier, no feed, no sizing input and no field the funnel reads at decision time. It closes no §13 row, ratifies no label, and moves nothing into the item pipeline. It does not make row 21 a calibration; it makes row 21's reading reproducible, and says which half of it is a rate and which half is coverage. Both are smaller claims than a calibration. §0.6 remains armed.

### 12.2 v1.12 → v1.13

*Superseded in part, v1.14 (P77). P75's row below ends "Repaired fence: 0% and 0% on 42 labelled proposals." That figure is withdrawn as unreproducible, having been measured against six plants defined inline in a shell that was never committed; the "0%" false-negative half of the pattern-only comparison rests on the same unrecorded plants and is withdrawn with it, whilst the 94% false-positive figure over the 36 agent-swept proposals stands. The reproducible replacement is **0 of 36** refused on the drawn class-level arm, with **3 of 36** on the fence as v1.13 left it, and **5 of 6 routes closed** on the authored probe arm, which P79 reports as coverage rather than as a rate. **The row itself is not rewritten**: it is the record of what v1.13 claimed, and carrying it verbatim under a banner is what makes the supersession auditable, per §12.7.*

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P66 | **Agent discovery layer specified.** Agents locate class-level mechanisms in permitted corpora and emit proposals; proposals run fail-fast through intake ingestion into the §3.6 evidence lane and never into the §3.5 item pipeline | procedure (see P72) | §3.7, §Σ.1 | yes, ordering and fences |
| P66a | **Erratum A, §0.5.** The conversion of a 7 bps per month gross median to a 63-session leg read **10.5 bps** and is corrected to **21 bps**: three months at 7 bps per month is 21 bps. The comparison against the 22.5 bps cheapest break-even stands, and the corrected figure still fails that break-even, by a narrower margin than the paper previously implied. Landed with a one-line supersession banner above the stale wording, per §12.7 | restriction | §0.5 | no |
| P66b | **Erratum B, §0.10 and §5.2.2.** The two break-even tables are computed on different notional bases: §0.10's on the £2,500 minimum clip, at which the fixed round-trip cost is 25 bps, and §5.2.2's on £5,000 notional. Each table now states its basis explicitly so that the two sets of figures are not read as comparable. **No number in either table is changed** | restriction | §0.10, §5.2.2 | no |
| P67 | **Fail-fast ingestion, with its obligation and its antidote.** Eleven ordered intake points and eleven ordered observation points, each with a named reason code; every abort writes a code, a set size and a rendered §8 summary; a pre-registered audit fraction runs the full panel so the reason-code distribution is not censored. Closes the `source_inaccessible` gap recorded on 17 August | restriction | §3.7.4, §3.6.3, §7.2 | yes |
| P68 | **The exclusivity construction.** `scoring_mode ∈ {cross_market, disjoint_partition, forward_only}` recorded per directive and printed beside every verdict; entity fence by schema; import fence over the discovery path; query fence extended to machine reads. Optional fourth archive partition, **Discovery**, with Gate 0 asserting separation as it does for injections | restriction | §3.7.3, §7.5, §0.7a | yes |
| P69 | **Random-mechanism control arm**, with a pre-registered seed, ratio and kill criterion in §3.6.8's three-verdict idiom. Joins §Σ.4's list of falsification instruments. *A layer that widens the search must be falsifiable on its own terms, and this is the only rule in P66 to P73 that measures rather than constrains* | restriction | §3.7.5, §Σ.4, §13 | yes |
| P70 | **Origin enum extended** to `{paper, operator, agent, random_control}`; machine-origin evidence carries `agent_generated` provenance and routes advisory-only under check 5 | restriction | §3.6.2, §3.6.3 | yes, enum |
| P71 | **Capacity discipline.** Admission by smallest registered span first, ties by registration time; machine-origin drafts queue and may not displace; §6.4's fourth family gains a three-tier counter (proposed, registered, promoted), all disclosed and none dividing anything | restriction | §3.6.8, §6.4, §9.2 | yes |
| P72 | **§0.6 applied and split.** The runner, screen, fences, ledger and summaries are procedure. A production ingestion adapter for a discovery corpus, and standing automation of the layer, are **apparatus** and take Annex A.1 rows. Hand-assembled corpora under the manual-observation protocol are not | n/a | §3.7.7, §0.6, Annex A.1 | no |
| P73 | **Agent-discovery endogeneity** added to §6.3's catalogue as the third sibling of §3.4, with six containment rules and the unreachable residual stated | n/a | §3.6.6, §6.3, §10 | no |
| P74 | **Default exclusivity construction settled as `cross_market`**, closing what P68 left as a §14 open decision. `disjoint_partition` is retained as a per-class override; a class must still be positively declared discoverable, so the default settles *which* construction applies and never *whether* one exists. The generalisability assumption the default buys is measured by §13 row 24 rather than merely disclosed, and a control-arm ratio of zero is refused rather than floored | restriction | §3.7.3, §3.7.5, §13, §14 | yes |
| P75 | **Entity fence rebuilt as a lookup, after a trace refuted its first design.** A specification trace over 36 proposals drawn by discovery agents from live ASX, SEDI and MAR primary sources refused 34, a 94% false-positive rate with no true positive among them: a pattern over an open vocabulary cannot separate a regulator's name from an issuer's. The binding layer becomes a lookup against the security master and the discovery markets' listing lists; patterns survive only for closed grammars (instrument identifiers, legal-form designators); a seeded regulatory lexicon grows by operator mapping and is ledgered; **dates become context and never a hit alone**; and a missing master emits `security_master_unavailable` rather than falling back to the weaker half. Repaired fence: 0% and 0% on 42 labelled proposals. *This is the trace doing the job §9.4 specifies, on a new surface, at the first attempt* | restriction | §3.7.3, §13 rows 21 and 25, §10 | yes |

**What v1.13 does not do.** It subscribes to nothing, admits no family, creates no grammar row, supplies no parameter, sizes no position, and lets nothing it raises act on capital. It moves no idea into the item pipeline. It does not permit an agent to register a directive, because registration requires two things only the operator may supply.

### 12.3 v1.11 → v1.12

Four solution sets, one legacy finding landed, and the residue of the harness's advisories. **No apparatus; §0.6 remains armed; the drafted second amendment is recorded and not taken.**

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P55 | **Manual-observation tier.** `stream_status` gains `manual_observation`: calendar-driven, pre-registered hand collection with gaps recorded as gaps, survivorship caveats printed on backfilled figures, and a structural bar on anything so tagged feeding a gate, anchor, base rate or peer set. Splits v1.11's over-coarse `new_subscription`, which conflated a production adapter with a person reading a public register. Promotion to an adapter still takes the A.1 predicate | restriction | §3.6.5 | yes, enum |
| P56 | **Declined-directive log.** Every declined, deferred or displaced directive logged with the feed it named; the distribution reported at freeze beside the §0.7 roster decision. Persistent mismatch between ideas and roster becomes evidence for changing the roster at the freeze, not for bypassing the rule | procedure | §3.6.5, §0.7 | no |
| P57 | **Pointer verdicts by equivalence.** Registration commits an abandonment threshold δₘᵢₙ; verdicts are `promoted` \| `killed_negligible` (two one-sided tests demonstrate the effect within ±δₘᵢₙ) \| `undetermined_at_budget`. Replaces sign-against-zero, under which the operator supplied both the hypothesis and its pass condition. §7.5's fails-for-want-of-power discipline, applied to pointers | restriction | §3.6.8 | yes |
| P58 | **Pre-mortem at registration.** The most plausible false-mechanism explanation written before data; **refusal with `confound_unmeasurable`** where that confound cannot be measured on available data | restriction | §3.6.8 | yes |
| P59 | **Query fence.** Class-level queries open pre-registration; conditional-return queries on the directive's own target population closed until `registered_at`. Enforced against the research stack's query log, which joins the ledger: a fence over auditable actions rather than over intentions | restriction | §3.6.6 | yes |
| P60 | **Literature first.** Search run and result recorded before registration: published → paper intake with decay prior; unpublished → *why not* recorded | procedure | §3.6.6 | no |
| P61 | **Fourth counting family and computed budget.** Design-segment search counted in full and dividing nothing; only evaluation-scored survivors enter the cross-candidate FDR, correcting v1.11, which put pointers in the specification-search family and thereby taxed exploration. The six-directive cap is superseded by arithmetic: per-directive span registration, a design-segment **reuse ledger** with pairwise overlap, calibrations holding first claim on the segment, concurrency bounded by the overlap tolerance θ. θ and a δₘᵢₙ floor survive as §14 governance decisions | restriction | §6.4, §3.6.8, §9.2, §14 | yes |
| P62 | **Rejection summaries.** Two to three sentences of plain language on every refusal in the system: template-rendered from the record's fields for deterministic kills, operator-authored where the decision was human, display-only by construction, rendered on §9.2's cards. Legible rejection acquires a mandatory form | restriction | §8, §9.2, §3.6 | yes, record schema |
| P63 | **Beta hedge demoted to a measurement**: the legacy finding v1.10 specified and declined to land without the fact. Operator eligibility for futures dealing checked and **failed**; third instance of the operator-assumption error class closed. No hedge leg trades; realised beta reported per market; governor binds on beta-inclusive drawdown with the market-adjusted alternative **rejected** for reasons stated in §6.8; Gate 4 inherits sole responsibility for correlated-loss profiles; book series reported raw and adjusted; §5.2.2 unchanged. Account type (cash or margin) is a §14 open decision, currently non-binding | restriction | §6.8, §6.7, §7.1, §10, §14 | yes |
| P64 | **Register of record.** The manuscript is declared the authoritative register: each entry's specification is its §12 row plus the governing section text, under the standalone supersession claim. Closes v1.10's P46: P27–P39's operative content survives in the sections §12.6 names; **their original defect narratives are not reproducible, and that loss is recorded as historical rather than operative** | procedure | title block, §12.8, §14 | no |
| P65 | **Residual advisories cleared.** (i) §6.7's source-lead minimum call count was a threshold pending outside §13, a membership breach; it becomes §13 row 18. (ii) The persons-closely-associated cohort's pending base rate becomes an Annex A.1 row with its predicate. (iii) §0.10's illustrative spread column marked as assumed-illustrative at the table | n/a | §13, Annex A.1, §0.10 | yes (row 18) |
| n/a | **v1.11 header defect recorded.** A drafting batch failed part-way; v1.11 circulated under a v1.10 header with its preamble absent. §9.5 gains a header–change-log agreement check. *The harness reviewed cross-references and never the title: a rule nothing had ever reached, in the reviewing instrument itself* | n/a | §9.5, §12.7 | no |
| n/a | Drafted second amendment (feed budget) recorded in §0.6 and **not taken** | n/a | §0.6 | no |

**What v1.12 does not do.** It subscribes to nothing, admits no family, and does not let any pointer act on capital. The manual tier buys observation, not automation; the equivalence rule makes killing ideas easier and passing them harder; and the one drafted route to early feeds is on the record precisely so that taking it cannot be quiet.

### 12.4 v1.10 → v1.11

One extension, at the operator's request, with its containment. **No apparatus; §0.6 remains armed.** Every embedded decision requiring ratification is marked.

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P49 | **Pointer tier.** Unquantified intakes (a suggestive paper, or the operator's own hypothesis) enter the evidence lane with `evidence_tier = pointer`. `evidence_tier` is **computed from field completeness, not asserted**. A pointer's only reachable output is an observation directive: it cannot amend a family, supply a parameter, create a grammar row, size a position, enter the item pipeline, or pool with a quantified family's peer set | procedure | §3.6.1–3.6.4, §3.6.8 | no |
| P50 | **Second origin.** `origin ∈ {paper, operator}`. Operator-origin intakes are hand-written into the same schema, and evidence produced by them carries `self_generated` provenance, routing advisory-only under check 5 | procedure | §3.6.1, §3.6.2 | no |
| P51 | **Unclassified event classes are mapped, not refused.** An event class outside §3.6.5's table routes to a binding manual observability screen (publisher, access route, machine-readability, per-item timestamps, corroborability) and the operator names the stream. Mappings are recorded with `stream_provenance = operator_mapped` and inherited by later intakes, so the table **grows by use rather than by anticipation**. *Refusal on novelty would have made the table's current contents a ceiling on what the system may ever investigate, hard-coding the very endogeneity §3.6.6 exists to contain* | restriction | §3.6.5 | **yes**, the table is in the parameter object |
| P52 | **When a directive may be followed: the `undecidable` v1.10 left open.** Settled by cost, not by promise: `subscribed` and `category_filter` proceed **immediately at zero capital** through §7.6's shadow instrument; `new_subscription` takes an Annex A.1 row, because a new feed is new ingestion code, a new parser and a new anchor-provenance question, and is therefore apparatus | restriction | §3.6.5, §0.6, Annex A.1 | yes |
| P53 | **Operator-hypothesis endogeneity** added to §6.3's catalogue as the stronger sibling of paper selection, with four containment rules: `registered_at` precedes observation, kill criteria written first, every raised pointer counted including abandoned ones, and `self_generated` provenance. **Recorded as containment, not as a solution** | n/a | §3.6.6, §6.3, §6.4, §10 | no |
| P54 | **Directive budget.** At most six concurrent open directives; a seventh must displace one, with the displacement recorded. Prevents the lane becoming an indefinite idea generator producing artefacts and no verdicts: the shape §0.6, §9.4's stopping rule and §9.5's enhancement gate all address elsewhere. ***Embedded decision requiring ratification: the number is governance, not measurement*** | n/a | §3.6.8, §14 | yes |

**What v1.11 does not do.** It admits no feed, no family, no gate, no grammar row and no parameter. It does not let a pointer act before the §0.6 instruments report: a surviving pointer re-enters as a *quantified intake* and takes the ordinary route through §3.6.4 and Annex A.1. **The extension buys the operator directed observation on feeds already flowing, and nothing else.**

### 12.5 v1.9 → v1.10

Three sources: the literature lane, its first verified intake, and the §9.5 review harness. **No apparatus added; §0.6 remains armed and there is no second amendment.** Supersession follows §12.7: superseded wording is annotated where it stands, never rewritten.

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P40 | **Literature lane specified**: intake schema, merit screen with refusal semantics, amendment fork by reachable-set diff, observation directive, ledger entry for every screened paper, paper-selection endogeneity added to §6.3's catalogue | procedure | §3.6, §6.3 | no, procedure |
| P41 | **News-adjacency restriction** on the insider family: two advisory flags with paper-sourced windows; **no general news flag**, its absence deliberate and evidenced; adoption of any magnitude threshold gated on a pre-registered design-segment test | restriction | §5.4.1, §13 | yes, at adoption |
| P42 | **§0.5 evidence block rebuilt**: UK-measured figures added with populations named and **row-level provenance tags**; pre-purchase run-up sign logged; Brochet's disclosure-speed mechanism stated; the carried citation row closed for all three names | prior update | §0.5, References | no |
| P43 | **Two reason codes named** where v1.9 specified the rule and omitted the code: `ingestion_lag_exceeds_window` (Gate 1) and `surprise_not_computable` (§5.4.2). A kill that cannot be counted cannot be shown to have been reached | restriction | §3.5.1, §5.4.2 | yes |
| P44 | **Extraction field naming settled.** `issuer` / `instrument_referenced` are canonical; `issuer_id`/`instrument_id` and `issuer`/`instrument` recorded as superseded; no alias in the parameter object; the primary-listing rule and Gate 1's `outside_universe` explicitly non-overlapping | restriction | §3.5.2 | yes |
| P45 | **Six orphaned sections given inbound references**: §5.9, §6.2, §6.5, §7.2, §7.3, §8 were cross-referenced by nothing. The prose analogue of a reason code defined and never emitted | n/a | §3.5.3, §4.3, §5.2, §6.7, §13 | no |
| P46 | **Register-artefact gap recorded.** Entries P27–P39 landed in v1.9 and are visible in §12.6, but the register document that specifies them is absent from the corpus. Recorded as a §14 provenance defect rather than glossed | n/a | §14 | no |
| P47 | **Trade-size threshold reclassified.** A materiality floor on the filing is what §5.4.1's economic-substance test already is; FGR supplies UK evidence for it plus a paper-sourced candidate parameterisation (0.1% of market capitalisation), recorded as a §13 prior. Only the *continuous* size-conditioning multiplier remains deferred | restriction | §5.4.1, §13, Annex A.1 | yes, at adoption |
| P48 | **Review harness specified** with three layers, a computed-severity adjudication table, an enhancement gate and a pre-registered stopping rule | procedure | §9.5, §14 | no |
| n/a | **§6.8 hedge downgraded from verified to specified.** Operator eligibility for futures dealing recorded as an open verification; the measurement-only fallback described and deliberately **not** landed | n/a | §6.8, §10, §14 | no |
| n/a | Two **recorded recollection errors** from the first intake: general news adjacency does not reduce the reaction; the ownership result is a sign structure, not a scalar | n/a | §3.6.7 | no |

**What this version does not do.** It adds no gate, no family, no grammar row, no cost tier and no sizing input. It does not adopt the 0.1% threshold, the news-adjacency magnitudes, or any ownership conditioning: each is a §13 row or an Annex A.1 predicate. **The version increments only because reason codes and a settled field name are rule changes**, and §0.3 counts rule changes however small.

### 12.6 v1.8 → v1.9

All items are remediation or population decisions. **No apparatus added.**

| # | Change | Sections |
|---|---|---|
| P8 | Source-lead multiplier: explicit unmeasured branch, provenance field, refuse-to-score below a call-count minimum | §6.7 |
| P9 | §0.9 states what the reorientation cost the founding substrate | §0.9 |
| P10 | §0.5 gains the extraction-cost and limits-of-arbitrage theory behind the filings pivot | §0.5 |
| P11 | `direction_basis`; divergence cases populate the control arm | §3.5.2, §7.4 |
| P12 | Transcript-quality check *(optional; deferred while the grammar reads filings)* | n/a |
| P13 | Novelty reports roster coverage; relay over-crediting flagged | §3.2 |
| P14 | Claim provenance tags; §14 unsignable on unverified load-bearing claims | §14 |
| P15 | Gate 2 offer-period carve-out | §5.3 |
| P16 | Firm-offer close rule conditioned on the position's own anchor | §6.7 |
| P17 | Dealing-restriction flag suppresses absence-of-signal readings | §5.4.1 |
| P18 | `mechanism_consistency` flag; divergent observations excluded from pooling | §5.4.2 |
| P19 | Universe membership asserted at Gate 1 with `outside_universe` | §0.7f, §5.2 |
| P20 | Anchor provenance recorded per value | §3.5.1 |
| P21 | Unclassified default inverted to the narrowest horizon set | §5.4 |
| P22 | `attributed_party`, `party_interest`, `genre`; excluded from the scorecard | §3.5.2, §3.2 |
| P23 | Issuer separated from instrument; primary-listing resolution | §3.5.2 |
| P24 | Surprise measure named, with fallback ladder and hard refusal | §5.4.2 |
| P25 | `source_generation`; machine sources advisory and off the scorecard | §3.5.2, §3.2 |
| P26 | Ingestion lag measured and gated against the tuple's horizon | §3.5.1, §5.2 |
| P27 | `document_type`; running documents take no anchor role | §3.5.1, §3.2 |
| P28 | Injected batches carry an injection timestamp and partition by anchor | §7.5, §5.2 |
| P29 | Catalyst duration floor; sub-session events inadmissible | §3.5.3 |
| P30 | Insider admissibility on net beneficial interest and open-market execution | §5.4.1 |
| P31 | Qualifying filer classes named; persons closely associated excluded | §5.4.1 |
| P32 | Concert-party accumulation routed to event-driven (other) | §5.4.3 |
| P33 | §0.9 and §6.6 state the population of every figure; joint rate to §13 | §0.9, §6.6, §13 |
| P34 | Source class by regulatory status, not delivery channel | §0.7g, §3.1 |
| P35 | `item_sponsorship`; wholly commissioned items off the scorecard | §3.5.2, §3.2 |
| P36 | Base rates measured on the primary feed; intermediary filter policy recorded | §3.3 |
| P37 | Headline-level screening impossible for the insider family; cost stated | §2, §5.4.1 |
| P38 | Joint qualifying-and-tradable rate as a §13 calibration | §13, §6.6 |
| P39 | Microcap shadow routing; live admission predicated | §0.10, §5.2.2, §7.6 |
| n/a | Positive oracle's population stated | §7.5 |
| n/a | Trace harness specified with a stopping rule | §9.4, §14 |

### 12.7 Supersession

Ratifications strand the artefacts that argued for them. Every memo, review record, drop-in file, register document and prior version superseded by this design carries a banner naming this document, its date and the governing section, **annotated above the stale text and never rewritten**: the superseded wording is the record of what was true when written, and carrying it verbatim is what makes supersession auditable rather than invisible. Two supersessions are recorded explicitly in this version: the field names in P44, and the recollection-tier claims corrected in §3.6.7.

**A scope note, honestly.** A change-log row saying *resolved* is only as resolved as the sub-clauses evidenced. P41 is specified and not adopted. P47 reclassifies a threshold whose value is a pending calibration. P46 recorded a gap that §12.8 now closes on stated terms. This paper made the opposite error once, in v1.4, and records the discipline here rather than repeating it.

### 12.8 The register of record

From v1.12, **the manuscript is the register**. The authoritative specification of any register entry P⟨n⟩ is its change-log row in §12 together with the section text that row names; separate register documents, where they survive, are archives and carry supersession banners per §12.7. This closes P46 on the following terms, stated so the closure cannot be mistaken for a gloss: **the operative content of P27–P39 is fully present** (each has a §12.6 row naming its sections, and those sections contain the rules), while **their original defect narratives (the *raised-by* items, the traced filings, the first diagnoses) are not reproducible from the surviving corpus.** What is lost is historical narrative; what is preserved is everything the funnel reads. The §14 precondition is satisfied because every cited entry is now producible as row-plus-section, and the loss is recorded here rather than discovered later.

---

## 13. Pending quantities: thirty-two numbered rows, thirty-three entries, and one §0 decision

**Membership rule:** §13 holds every quantity requiring measurement or lookup, each with sample, metric, rule and deadline; §14's open row holds pointers to §13 plus named pending §0 decisions; **nothing pends elsewhere**, and §9.5's linter tests that claim mechanically: row 18 exists because that test found a threshold pending outside this table. **Populating all twenty-five completes the freeze.**

**The ordering is not arbitrary.** Row 1 is first because every break-even denominator in the paper inherits it; rows 12 and 13 decide whether the one live family survives its own cost table; row 14 gates §0.10 entirely. Rows 16 and 17 are new in v1.10 and are the price of P41 and P47: both are thresholds the literature supplies as *priors* and this system must *measure*.

*Superseded, v1.14 (P77), row 21. The row's reading previously read: "**A provisional reading exists**: 42 labelled proposals, being 36 drawn by discovery agents from live ASX, SEDI and MAR sources plus 6 plants, returned 0% and 0% against the repaired fence and 94% and 0% against the pattern-only fence it replaced." Both rates there were divided by the union of the two arms rather than by their own; the probes they were measured against were never committed; and the second of the two was reported as a rate at all, which P79 corrects, a set of authored probes being chosen rather than sampled. The stale wording is annotated here rather than rewritten silently, per §12.7; the row below carries the reproducible replacement.*

| # | Quantity | Sample | Rule | Deadline |
|---|---|---|---|---|
| 1 | **Fixed round-trip commission** *(PROVISIONAL from 27 Aug 2026, P91)* | Named broker schedule, cited; incl. FX | The published figure; feasible band, reachability, §5.4.4 and break-even table **recomputed**. **The clip is no longer among them**: §0.11 fixed it at £50,000 by decision, so this row no longer determines it | **First** |
| 2 | Gate 2 kill percentile | Design segment, contiguous, primary feed | Percentile committed **before** scoring | Design segment |
| 3 | Gate 7 random-grid base rate and threshold | Design segment | Enrichment plus binomial p; threshold pre-committed | Design segment |
| 4 | Gate 6 percentile floor | Permutation percentiles across **all evaluated tuples** | Permissive: uncensored distribution to FDR | Calibration |
| 5 | Placebo Δ | **Un-randomised** calibration run | ⅓ of the measured association, floored at deployment relevance | Calibration |
| 6 | ATR-to-volatility ratio | Calibration, contiguous, §0.7(f) universe | Median; §4.1.1 multiples recomputed | Calibration |
| 7 | Per-family realised median | Calibration, per exit family | Median, minimum 100 trades | Calibration |
| 8 | Break-even ceiling | All cells | Reject above the class's largest documented post-decay effect | Before Gate 1 runs |
| 9 | Gate 1 price floor | Calibration | Floor where spread exceeds the ceiling | Before Gate 1 runs |
| 10 | Gate 5 minimum conditional sample | Calibration | Refuse below the count where conditional SE exceeds the effect | Calibration |
| 11 | Audit-stream minimum n (§7.2) | Observed intake and kill rates | Power for the smallest actionable per-gate difference | Before review point 1 |
| 12 | **Joint qualifying-and-tradable rate** | Design segment, **primary feed**, all filer classes | Share meeting §5.4.1's conjunctive tests **in issuers above the Gate 1 floor**; arrival distribution and both marginals reported; §6.6 rebuilt on it | Design segment |
| 13 | **Capture rate** | Backfill, insider family | Realised return from the next open after observation against the full announcement window | Calibration |
| 14 | **Sub-$1m cost tier** | Design segment, shadow-cohort names | Measured effective spreads by bucket; populates §5.2.2's empty row | Before any §0.10 promotion |
| 15 | Ingestion-lag threshold | Observed lag distribution per source class | Stated fraction of the tuple's admissible horizon | Before Gate 1 runs |
| 16 | **News-adjacency magnitude threshold** *(new, P41)* | Design segment, insider family | Conditional CAR difference by flag against the no-flag cohort; **sign taken from the paper, kill criterion written before the data is examined**; Gate 6's minimum count applies; the paper's estimate is the prior, never the answer | Design segment |
| 17 | **Filing materiality threshold** *(new, P47)* | Design segment, insider family | Trade size as a share of market capitalisation; the paper's 0.1% recorded as prior; adopted only if the conditional difference carries the paper's sign at Gate 6's minimum count | Design segment |
| 18 | **Source-lead minimum call count** *(new, P65, found pending outside this table)* | Calibration, per-source call counts | The count below which §6.7's source-lead input refuses to score: smallest n at which the shrunk lead estimate's standard error falls below the gap between adjacent multiplier branches | Calibration |
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | Design segment, both arms | The separation below which the discovery layer is refuted; committed **before the first sweep**, in the units the measurement reports | Before the first sweep |
| 20 | **Control-arm ratio *M/N* and seed** | n/a, governance | Fixed before the first sweep, strictly above zero, and recorded with every draw; a control redrawn after the treatment's result is known is not a control | Before the first sweep |
| 21a | **Fence false-positive rate, drawn proposals** *(revised, P75; corrected, P77 and P79; split from row 21, P85)* | **Not stated, and that is the row.** The sample size is a function of the tolerance, the tolerance is a function of how much funnel depth §7.1 can lose before it loses power, and §7.1 has not run | The share of clean **drawn** class-level mechanisms the fence refuses, divided by its own n and never by the union of the arms. **Reported with an interval, never as a point.** Zero events does not estimate zero, and a rate reported as `0%` on a sample that could not distinguish it from one in twenty is a precision claim the sample does not carry. Refuses to score on an empty arm. **The reading to date is an upper bound: 0 events in 36 trials, 95% upper bound 3/36 or approximately 8.3% by the rule of three.** On the fence as v1.13 left it the same 36 gave 3 refused, an upper bound near 22%, so the ticker rule moved the bound and not merely the count. **The n = 200 this row carried until the split was chosen and not derived**, a round number attached to a quantity whose tolerance nobody had computed; it is withdrawn rather than carried, because a sample size with no power calculation behind it reads as a requirement and is a guess. Labels carry provenance `model_clerk` and the operator has not ratified them | **Design segment** |
| 21b | **Fence false-negative route coverage** *(split from row 21, P85)* | 6 authored probes, one per named route into the fence | **Coverage, and never a rate.** Which named routes into the fence are closed and which are left open, with **no percentage**: probes are chosen rather than sampled, and a proportion over a chosen set estimates nothing, doubling the probe set to twelve routes halving the figure whilst leaving the fence untouched. The term *episode-level* is not used of this arm, implying as it would a sample there is none of. A drawn episode-level sample would yield a second rate; until one exists this arm is coverage. Refuses to score on an empty arm. **Reading: 5 of 6 routes closed, the open one a title-case bare ticker**, which is the residual P76's rule takes on knowingly. **Provisional rather than blocked, and the difference is real: nothing here waits on the design segment.** Coverage of six written routes is decidable by reading them, and the operator reading the six is what closes this | **Operator ratification** |
| 22 | **Discovery corpus roster, partition assignment and discoverable classes** | n/a, fixing | Named corpora, their markets, their partition and the retrieval route, together with the event classes positively declared discoverable and the construction each uses. A pre-calibration fixing in the sense of §13's existing list | Before the first sweep |
| 27 | **Intake budget** *(new, P87)* | n/a, governance | A ceiling on the cost of looking, not a judgement of the idea. `intake_point_budget_s` = 20 s per point, `intake_subject_budget_s` = 120 s cumulative per subject, `budget_retry_max` = 1 further attempt after an over-run. A subject exceeding either is abandoned with `intake_budget_exhausted`, which **refuses to score** and is neither an acceptance nor a rejection of the idea. **The decision is taken once, at capture.** The ledger records the elapsed time, the budget in force and the verdict; a replay reads that record and never re-times the work, because a clock in the replay path would make the same inputs produce a different refusal set on a different machine, which is §0.3's replayability and rule 1 made false on the surface where it is least visible. **Not counted in row 23's abort-position distribution**, and reported beside it: a subject that ran out of time did not fail the point it was standing on. **The honest limit: this is a ceiling that refuses, not a timeout that interrupts.** A check is run and then measured, so a point that blocks forever is never caught; what the budget catches is work that finished late | **Before the first sweep at scale** |
| 23 | **Intake abort-position distribution** | Audit stream, full panel | Distribution of first-failure position per surface. A surface whose failures cluster at position one is a surface whose later points have never been exercised, which is §9.4's failure class on a new surface | Design segment |
| 24 | **Cross-market generalisability** *(new, P74)* | Design segment, classes present in both the discovery market and §0.7(f)'s universe | Sign agreement and magnitude ratio of the same mechanism measured on each market, reported per class. **Coverage is partial by construction**: it is computable only where the class occurs in both, so a class absent from the home market leaves the assumption untested and the directive says so. Kill criterion written before the data is examined; sign disagreement at Gate 6's minimum count refuses `cross_market` for that class and routes it to `disjoint_partition` or `forward_only` | Design segment |
| 25 | **Security master and lexicon coverage** *(new, P75)* | Discovery-market listing lists | Share of listed entities in each discovery market present in the master, since the fence's binding layer is a lookup and an absent issuer is an undetectable episode. Below a stated floor the market is not readable for discovery | Before the first sweep |
| 28 | **§9.4 trace stopping threshold, and its block size** *(new, P103)* | §9.4's own coverage report | §9.4 stops when the marginal defect rate per hundred items falls below **a stated threshold** for two consecutive blocks, and **the threshold is not stated anywhere in this document**. **Two numbers joined by the rule of three:** two consecutive blocks at zero must-class defects is `2n` items at zero, whose 95% upper bound on the residual rate is `3/(2n)`, so **choosing the block size chooses the precision of the stop**. A threshold above zero is not a stopping rule at all but a budget | **Before §14's trace precondition can be discharged; it is undischargeable at any *n* until then** |
| 31 | ***Promotion-to-live-capital predicate*** *(new, P113)* | **n/a: a §0 operator decision** | §0.10 and §7.6 both call promotion of the shadow cohort to **live capital** *pre-registered*, requiring realised net expectancy after measured spreads to exceed measured break-even by **"a stated margin"** over **"a stated minimum sample"**, and **neither has ever been stated**. **Until they are, nothing in this document authorises capital and the gate can neither pass nor fail.** It is the only route by which a candidate that failed a hard floor later receives money | **Before any promotion from the shadow cohort. BLOCKED, and not delegable** |
| 32 | **Novelty roster coverage threshold** *(new, P113)* | An enumerated outlet population | §3.4 flags a first-mention claim from a roster below **a stated coverage threshold**, and none is stated, so the rule flags nothing. Novelty feeds the sizing multiplier and the error is **systematic**, over-crediting relay sources in proportion to how thin the roster is | Before novelty is read as evidence of anything |
| 33 | **§3.6.5 collection cadence: day, source pages, fields** *(new, P113)* | n/a, governance | Three values §3.6.5 requires to be pre-registered and none is stated. **A protocol with no stated source page cannot say which pages it read**, which is what the 27 August replay finding shows | Before the next hand collection |
| 29 | **Maximum tolerable fixed cost** *(new, P98)* | n/a, governance | Basis points of position, round trip, **excluding spread and market impact**. The one free parameter the clip-floor derivation cannot eliminate | **With row 30, before any position is sized** |
| 30 | **Derived clip floor, per market** *(new, P99)* | Row 1's fixed cost per market | **A function, not a number**: the smallest position at which row 1's fixed round-trip cost falls at or below row 29's tolerance. Refuses where either input is unset, and refuses separately where **no size** satisfies the tolerance | **BLOCKED on row 29; inherits row 1's PROVISIONAL** |
| n/a | **FX exposure budget** *(§0 decision, consumed by §6.9)* | n/a | Governance judgement in a stated range; recipe format deliberately withheld | Before any non-sterling position |

### Rows 29 and 30: the clip floor, derived

**Row 29, the maximum tolerable fixed cost. Why it sits here and not in a
per-market clip.** The alternative was a clip per venue, and it was rejected
for four reasons, each of which is a property of the quantity rather than a
preference:

- **Dimensionless.** Basis points of position carry no currency, so the same
  number governs a USD and a GBP trade without an FX rate entering the
  governance decision.
- **Comparable across markets.** A per-market clip in pounds and dollars
  cannot be compared without converting; a tolerance in basis points can, and
  **the comparison is the substance**: §13 row 30's whole output is which
  markets clear the same bar.
- **Readable against the break-even table.** §5.2.2 and §0.5 are already in
  basis points. A tolerance in the same unit can be set beside a documented
  effect and read off; a clip in pounds cannot.
- **Set once instead of guessed per venue.** A per-market clip is one guess per
  market, each of which drifts separately and none of which records what it was
  trying to achieve. **One tolerance is one decision, and every floor beneath it
  is arithmetic.**

**Scope, stated because the exclusions are load-bearing.** It covers **fixed**
round-trip cost only: commission, per-order minimums, levies, transfer taxes
and FX conversion. **It excludes spread and market impact**, which are not
fixed, scale with participation and have no row (§0.11). *A tolerance that
silently included impact would be a tolerance nobody could check against a
schedule.*

**Row 30, the derivation.** As a function and never a number:

```
absolute      = every per-order and per-conversion charge over the round trip,
                in the market's currency, which DECAYS as a share of position
proportional  = every charge that scales with the position, in basis points,
                which does NOT decay at any size

floor(market) = absolute / ((tolerance_bps - proportional_bps) / 10,000)
```

**Implemented in `src/fntn/scanner/sizing.py`, which refuses in three named
ways rather than returning a number it cannot justify:**
`clip_floor_tolerance_unset` (row 29 absent), `clip_floor_cost_unset` (row 1
absent for that market), and `clip_floor_unreachable_at_any_size`. **The third
is not a missing input**: where the proportional share alone meets the
tolerance, no size satisfies it and there is no floor to return.

#### What the derivation produces, and one figure this paper disagrees with

**US: the cost decays, so a floor exists.** Two fixed minimums, **USD 1.00
commission and USD 2.00 FX, each applied twice**, give a round trip of **USD
6.00** with no proportional term.

| Row 29 tolerance | Floor at USD 6.00, no proportional | Floor under the implied model below |
|---|---|---|
| 2 bp | USD 30,000 | **no size satisfies it** |
| 3 bp | USD 20,000 | USD 64,000 |
| 4 bp | USD 15,000 | USD 29,257 |
| 5 bp | USD 12,000 | USD 18,963 |
| 6 bp | USD 10,000 | USD 14,027 |
| 8 bp | USD 7,500 | USD 9,225 |
| 10 bp | USD 6,000 | USD 6,872 |
| 12 bp | USD 5,000 | USD 5,476 |
| 15 bp | USD 4,000 | USD 4,197 |
| 20 bp | USD 3,000 | USD 3,021 |

***The two models are now ONE. The residual was never a term; it was a regime
change (P101, 27 August 2026).***

**The hypothesis, and it was mechanical rather than a fit.** A **per-share
commission is proportional to trade value at a fixed share price**, so it never
decays. **But it carries a per-order minimum**, and below the size at which the
rate overtakes that minimum it behaves as a fixed charge and decays like one.
**The two recorded readings sit on opposite sides of that boundary**, and a
single linear model cannot straddle it: fitted across the boundary it splits
the difference, which is precisely the 2.16 bp nobody could name.

**Round-trip commission in basis points, at share price `p`:**

```
fixed   2 × 0.0050 / p  = 100/p bp        tiered  2 × 0.0035 / p  =  70/p bp
NSCC/DTC clearing       =   4/p bp        (0.0002 per share, both sides)
so the HARD FLOOR is    = 104/p bp  (fixed)   or   74/p bp  (tiered)
```

**Solved against the readings, and the test is the point.** The share price is
solved from the **USD 64,000 reading alone**, so reproducing that reading is
not evidence. **The evidence is the other point, which the model was never
shown:**

| Schedule | Implied share price | At USD 64,000 | At USD 3,200 | §13 row 1 records |
|---|---|---|---|---|
| **fixed** | **USD 43.79** | 3.00 bp *(fitted)* | **18.84 bp** *(predicted)* | ~19 bp |
| **tiered** | **USD 31.16** | 3.00 bp *(fitted)* | **18.88 bp** *(predicted)* | ~19 bp |

**One free parameter fitted to one reading predicts a second reading it was not
fitted to, to within a fifth of a basis point. The residual is explained.** At
USD 3,200 the per-share commission is **USD 0.37 a side** and the **USD 1.00
minimum binds**; at USD 64,000 it is **USD 7.31 a side** and the **rate binds**.

***What is confirmed and what is not, kept apart.*** The **mechanism** is
confirmed: the regime change accounts for the residual exactly. The **share
price is not**, because **§13 row 1's working records no share price at all**,
only the two trade values and the two readings. So `p ≈ 43.79` is **derived
from the readings under the schedule's structure**, not read from an assumption
row 1 made. *This is a third outcome, and it is recorded as itself rather than
forced into either "reconciled against row 1's assumption" or "unexplained".*

*Terms deliberately left out and their direction stated: FINRA's trading
activity fee on the sell leg and the SEC fee on sell value were not read from a
published schedule in this tree. Both are per-share or per-value and both push
the hard floor UP, so **every minimum share price below is a LOWER bound.***

#### The consequence, and it is the project's first DERIVED screening rule

**THE US HARD FLOOR IS NOT A CONSTANT. IT IS A FUNCTION OF SHARE PRICE.** No
position size gets a name below `104/p` bp (fixed) or `74/p` bp (tiered), so
**a tight tolerance excludes low-priced US stocks at any position size, in the
same way and for the same reason that stamp duty excludes UK Main Market at any
position size.**

| Row 29 tolerance | Minimum share price, fixed | Minimum share price, tiered |
|---|---|---|
| 2 bp | **USD 52.00** | USD 37.00 |
| 3 bp | USD 34.67 | USD 24.67 |
| 4 bp | USD 26.00 | USD 18.50 |
| 5 bp | USD 20.80 | USD 14.80 |
| 6 bp | USD 17.33 | USD 12.33 |
| 8 bp | USD 13.00 | USD 9.25 |
| 10 bp | USD 10.40 | USD 7.40 |
| 12 bp | USD 8.67 | USD 6.17 |
| 15 bp | USD 6.93 | USD 4.93 |
| 20 bp | USD 5.20 | USD 3.70 |

**This is a screening rule derived from the cost table rather than chosen, and
it is the first one the project has.** Every other threshold in §13 waits on a
measurement; this one falls out of arithmetic over a published schedule.

**The second consequence, and it reclassifies an open gap.** §13 row 1's
**tiered-or-fixed election moves the hard floor by 104 → 74, about 29%**, and
therefore moves the minimum admissible share price by the same proportion. **At
a 5 bp tolerance the election is the difference between a universe priced above
USD 20.80 and one priced above USD 14.80.** *It was a convenience question
about which schedule costs less. It is now a question about which names exist.*
It is promoted accordingly in `docs/DECISION_PACK.md`.

**UK: the cost is FLAT, so no size helps and there is no floor to find.**

| Position | UK Main Market, round-trip fixed cost |
|---|---|
| £2,500 | 61.4 bp |
| £10,000 | ~61.4 bp |
| £50,000 | 61.5 bp |
| £500,000 | ~61.4 bp |

**Stamp duty is a percentage and dominates**, so the UK figure does not fall as
the position grows; it moves by a tenth of a basis point across a twentyfold
range, and **upward**, because the PTM levy crosses its £10,000 threshold.
**NO SIZE MAKES A UK MAIN MARKET POSITION CHEAPER IN BASIS POINTS. A clip floor
is a US concept and it does not transfer.**

**The consequence, in two claims of different strength, and the difference is
the point.**

- ***PROVISIONAL:*** any row 29 tolerance below **~61.4 bp** excludes UK Main
  Market at every size. *This inherits row 1's three open gaps and moves if any
  of them resolves differently.*
- ***CERTAIN:*** any row 29 tolerance below **50 bp** excludes UK Main Market
  **with certainty**. **Stamp duty alone is 50 bp, it is statutory, it is a
  percentage, and it depends on none of row 1's open gaps.** No citation, FX
  route or contracting entity can move it.

**So a tolerance anywhere in the range the US table above makes sensible, 2 to
20 bp, excludes UK Main Market with certainty and not merely on present
figures.**

**Recomputed at the £50,000 clip, 27 August 2026 (§0.11, P91).** Each clip-dependent row was **invalidated and re-derived, or invalidated and left blocked.** No figure anywhere was edited in place, and where a value could not be derived that is said rather than filled.

| Row | Was | Now | What happened |
|---|---|---|---|
| **1** Fixed round-trip commission | **BLOCKED** | **PROVISIONAL** | A reading exists at the new clip and the calibration does not. **UK tiered: 61.5 bp**, up from 61.4 bp, because the **PTM levy crosses its £10,000 threshold**. **US: approximately 3 bp** at an illustrative **USD 64,000** trade value. The three gaps that blocked it are **unaffected by the clip** and still open: the FX route is not in a published schedule, the tiered-or-fixed election is not made, and the contracting entity is not established. *The reading is the operator's arithmetic and not a cited schedule, which is exactly what PROVISIONAL means here* |
| **8** Break-even ceiling | **BLOCKED** | **BLOCKED** | **Invalidated, not re-derived.** The ceiling is set by the class's largest documented post-decay effect and not by the clip, but its fixed-cost input moved and its impact term still has no row. It waits on the design segment as before, and now waits on it against a different cost base |
| **9** Gate 1 price floor | **BLOCKED** | **BLOCKED** | **Invalidated, not re-derived.** The floor is where the spread exceeds the ceiling, so it inherits row 8, which is blocked. Nothing about the clip makes it derivable |
| **14** Sub-$1m cost tier | **BLOCKED** | **BLOCKED** | **Invalidated, not re-derived, and its reachability is now in question.** At the illustrative USD 64,000 a single clip is **at least 6.4% of a full day's traded value** in a sub-$1m name, before any allowance for the fact that a round trip is two orders. §0.11 resolved to **(b)**, so **nothing in the funnel refuses on that**. The tier still waits on the design segment |
| §4.4 reachability matrix | published bounds | **withdrawn** | Boundary constants 12.0% / 5.45% / 3.16% withdrawn and **not replaced**. Blocked on a **§0 decision** and not on data: §6.7's risk-based sizing and §0.11's fixed notional disagree and §0.11 did not say which binds |
| §5.4.4 intersection | published cells | **withdrawn** | Every cell inherits §4.4's constants. Retained as the record of what was published under the £2,500 clip; no cell in it is now a reading |

**One consequence for a §0 decision that is still open.** The **FX exposure budget** row below is now materially larger than it was when it was written. **A 50% single-name position in a US name is 50% of the book in USD.** At the £2,500 clip the same position was 2.5%, so a governance judgement that could be deferred as second-order at 2.5% is a judgement about half the book at 50%. The row stays **OPEN**; what changed is what it decides, not its status, and this note exists so that the two are not confused.

**Pre-calibration fixings:** archive identity and span; partition boundaries with the negative-finding record if proportional; initial source roster; universe constituents; borrow snapshot date; intermediary filter policies.

---

## 14. Freeze record: a form, not a claim

| Field | Value |
|---|---|
| Specification version | **v1.14, fourteenth** |
| Frozen designs to date | **0** |
| Parameter hash | *does not exist until §13 rows 1–25 populate* |
| Manuscript hash | *computed on issue* |
| Evaluation hash | *does not exist until the evaluation segment is scored* |
| Open: calibrations | §13 rows 1–25 |
| Open: decisions | FX budget; UK factor series (§0.7b); ICB vintage vendor (§0.7d); **overlap tolerance θ and δₘᵢₙ floor (§3.6.8, superseding v1.11's six-directive cap)**; **account type, cash or margin (§6.8: currently non-binding, binds before any short-side family or margin simulation)**; the drafted feed-budget amendment (§0.6), **available, not taken** |
| Open, decisions | Control-arm ratio *M/N*, in a stated range and strictly above zero; manual-observation capacity per period, which the scanner will exhaust rather than approach |
| Open: ledger | **Open observation directives, listed individually** with `registered_at`, δₘᵢₙ, *n*ₘᵢₙ, segment span consumed and pairwise overlap. A directive open without its full registration is a freeze-blocking defect, not a to-do. **The design-segment reuse ledger publishes beside this row** |
| Open, ledger | Discovery corpora listed individually with market, partition and retrieval route; the three-tier family-4 counter published beside the reuse ledger |
| Open: verifications | Broker commission schedule (row 1, **first**); FGR published-version tables against the journal pagination, to upgrade §0.5's rows from working-paper to `verified_primary`. *Closed in v1.12: operator eligibility for futures dealing, checked, **failed**, hedge demoted (§6.8); the mini-contract access check is thereby moot* |
| **Closed in v1.13** | Default exclusivity construction: **`cross_market`**, on the arithmetic in §3.7.3, with `disjoint_partition` retained as a per-class override and §13 row 24 measuring the assumption the default buys |
| **Precondition: claim provenance** | Every load-bearing external factual claim tagged `verified_primary`, `verified_secondary` or `recollection`, **at row level where it sits in a table**. **This record cannot be signed while any `recollection` tag sits on a claim feeding a gate, a boundary or a published table.** |
| **Precondition: register completeness** | Every register entry cited by this document must be **producible as a specified entry**. **Closed in v1.12 on §12.8's terms**: the manuscript is the register of record, every entry is producible as change-log row plus governing section, and the unrecoverable loss (P27–P39's original defect narratives) is recorded as historical rather than operative. |
| **Precondition: review harness** | §9.5 run to its stopping rule: **two consecutive** passes at zero must-class defects, now including the header–change-log agreement check. **v1.14 is a new composition and resets the count: no clean pass recorded on this composition; two required.** |
| **Precondition: trace exercise** | §9.4's harness run to its pre-registered stopping rule, across a stated count of items spanning source classes and catalyst types, **including a minimum sample of the primary catalyst family's live filing flow**. Resulting defects are freeze-blocking. |
| Precondition, fences | The import fence must pass at process start, not merely in the test suite. A run whose fence check fails is a run whose output is inadmissible, not a run with a warning |
| Precondition, control arm | δ, *n*ₘᵢₙ, ratio and seed registered before the first sweep, the ratio strictly above zero. A layer whose kill criterion is written after its first result is not falsifiable, and a layer run without a control arm has no kill criterion at all |
| Scope when signed | Authorises the backfill and the two §0.6 instruments. **Not capital. Not evidence of edge.** |
| Re-review before | Any version adding apparatus: blocked until §7.1 and the placebo report. **Annex A.1 rows do not become admissible by accumulating**; the predicate is the only route |
| Signed / date | _____________ / _____________ |

---

## Annex A: Deferred and excluded

**A.1 Deferred, with predicates** (evaluated and logged continuously; acted on only after the §0.6 instruments report):

| Capability | Predicate |
|---|---|
| **UK growth-market cost tier: the AIM stamp-duty exemption** *(added 27 Aug 2026, P92)* | The §0.6 instruments report. **A cost tier, therefore apparatus, therefore blocked.** **Basis:** s.99(4B) Finance Act 1986, effective 28 April 2014; AIM appears on HMRC's recognised growth market list at STSM041330. **The condition has two limbs and both bind:** the security must be admitted to trading on a **recognised growth market** *and* **not be listed on that or any other market**, so a **dual-listed AIM company does not qualify** and a tier keyed on *AIM membership alone* would be wrong for exactly those names. **Worth, at the £2,500 clip:** 61.4 bp falls to **11.4 bp**, a factor of **5.4**. *The equivalent at the £50,000 clip is not published here: the base is now 61.5 bp and §13 row 1 is PROVISIONAL, so subtracting a component from a provisional base would mint a figure with a precision the base does not carry.* **Provenance `verified_secondary`.** The statute section and the manual reference are named and **have not been read against their sources in this tree**; `verified_primary` requires reading s.99(4B) and STSM041330 themselves. ***What this row governs CHANGED on 27 August 2026 (P99), and the change is not a refinement.*** The fixed £50,000 clip is withdrawn and the floor is derived against §13 row 29's tolerance. **At 11.4 bp, this tier now decides whether the UK is reachable AT ALL under a tight tolerance, rather than making a reachable market cheaper.** UK Main Market is **excluded with certainty at any tolerance below 50 bp**, stamp duty alone being statutory, a percentage, and independent of row 1's open gaps. **So for any tolerance between roughly 11.4 bp and 50 bp, AIM under this exemption is the ONLY reachable UK venue and without it the UK is not reachable at any size.** *The predicate is UNCHANGED and the row is not taken*: it remains a cost tier, therefore apparatus, therefore blocked on the §0.6 instruments report. **A capability becoming more valuable is not a reason to take it early; it is the reason the armed rule exists.** The earlier note that the tier might be unreachable at a £50,000 clip on depth is withdrawn with the clip; participation is a separate cap (§6.7) and is unaffected by this row. **Expiry:** the two-limb condition is a *status*, so a name's qualification can lapse on a later listing and a tier assignment fixed once would go stale |
| **UK new-listing SDRT relief** *(added 27 Aug 2026, P92)* | The §0.6 instruments report, **and** the provenance upgraded to a primary source. **A cost tier, therefore apparatus, therefore blocked**, and blocked twice over. **Basis:** Autumn Budget 2025. Relief from the **0.5% SDRT charge** for companies **newly listed on a UK regulated market on or after 27 November 2025**, running **three years from listing**. It **does not touch existing Main Market shares** and **does not apply to the 1.5% clearance-system charge**, so a tier that read it as "UK Main Market becomes cheap" would be wrong on both counts. **Provenance: CORROBORATION ONLY, and this is the row's main limitation.** The source is **law-firm commentary, not HMRC**, and no legislation is named; in §0.7(c)'s idiom, corroboration is not the citation. **Promoting it to a citation requires the HMRC guidance or the legislation itself**, and that promotion is part of the predicate rather than a tidying task afterwards. **Expiry, and here it is structural:** the relief is **time-limited by construction**, three years from listing, so **a name that qualifies today may not in two years** and a cost tier assigned once and cached would silently under-cost the trade after expiry. Any implementation carries the listing date, not a flag |
| **Participation GATE against daily traded value** *(added 27 Aug 2026, §0.11; corrected P93)* | The §0.6 instruments report. **A gate, therefore apparatus, therefore blocked.** §0.11 resolved to **(b)**: no participation *gate*. ***Corrected 27 August 2026: this row previously said the clip runs with "no participation constraint" and that "nothing in the funnel refuses on depth". Both were false.*** §6.7's cap stack carries **participation 2% of median daily notional per session over ≤ 3 sessions** and it is in force. **What is deferred is the gate and only the gate**, which would refuse a candidate at Gate 1 and name depth as the reason, where the cap instead shrinks the position and leaves `advisory_haircut_below_clip` to kill it. The difference is legibility, not instrumentation. Taking the gate early requires an explicit §0 exception to §0.6, its own §12.1 row, and a threshold as a §13 row with a sample and a rule |
| Short-term reversal family | Intraday data sufficient to estimate the T+1 fill shortfall against the reversal window |
| Activist and major-holdings event family | Event count sufficient for Gate 6 under peer pooling |
| **Concert-party accumulation family** | A measured base rate for holdings crossing the mandatory-offer band |
| **Spin-off and buyback families** | A measured base rate per catalyst type; both currently route to event-driven (other) |
| **Attribution-density counting** for novelty | A readable funnel-depth association; would detect relay directly rather than by roster-coverage proxy |
| Long-short relative value | Capital at which doubled costs do not consume the §0.5 margin |
| Meta-labelling and fitted sizing | 500 graveyard entries with elapsed windows **and** an explicit §0 reversal of §6.7's coarseness |
| Options and defined-risk convexity | Listed options with measurable spreads on ≥ 25% of the universe |
| Market-impact model | Book outgrows the participation cap |
| Cross-asset propagation | Point-in-time relationship data **and** a readable association |
| Multi-factor hedging beyond beta | Capital at which extra hedge legs do not consume the cross-section |
| Execution algorithms and passive posting | Intraday data sufficient to estimate spread capture **and** adverse selection |
| Live locate and borrow APIs | Execution layer live against a real account |
| **Literature-lane automation (Tier 2)**, papers as a live router source class with auto-generated shadow cohorts | The §0.6 instruments have reported, **and** the manual lane (§3.6) has produced at least one activated family or adopted restriction; automation follows demonstrated value, not the reverse |
| **Continuous insider trade-size conditioning**, a size multiplier rather than a threshold | The §0.6 instruments have reported. No new data dependency: trade size is already parsed from the notification (§3.5.2). *The threshold form is not deferred here: it collapsed into §5.4.1's economic-substance test as §13 row 17* |
| **Insider ownership-type conditioning** | The §0.6 instruments have reported, **and** a point-in-time ownership dataset is in the stack: a new dependency, named as such. The verified content is a **sign structure, not a scalar** (corporate blockholder −, individuals and families − weaker, **institutional +**, director blocks −) and **must be adopted whole or not at all**; a single concentration variable is underspecified |
| **New feed subscriptions arising from observation directives** (§3.6.5): index reconstitution, short-interest disclosure, and any `new_subscription` a future directive names | The §0.6 instruments have reported, **and** the directive that named the feed has a pre-registered measurement it cannot run on existing streams. *This row is the enforcement point for P52: a directive may name any feed; only this predicate admits one* |
| **Same-day multiple-director purchase clusters** | The §0.6 instruments have reported. Computable from filings already parsed; noted from the first literature intake and not pursued |
| **Persons-closely-associated cohort** (§5.4.1) | The §0.6 instruments have reported, **and** a measured PCA base rate exists on the design segment; the literature's null for large shareholders is the prior, so the burden runs against inclusion |
| **Discovery corpus ingestion adapters** for markets outside §0.7(f) | The §0.6 instruments have reported, **and** the manual-observation route has produced at least one registered directive that reached a verdict. Reading a foreign register by hand is not apparatus; a parser for it is |
| **Standing automation of the discovery layer** (scheduled sweeps, unattended) | The §0.6 instruments have reported, **and** the control arm (§3.7.5) has returned *agent selection carries information*. Automation follows demonstrated value and not the reverse, on the same terms as the literature lane's Tier 2 row |
| **Agent-proposed items entering the §3.5 item pipeline** | Refused rather than deferred, pending an explicit §0 decision. It would re-base §7.1's headline on an agent-selected population, and the association would then measure the agent's taste rather than the funnel's depth |

**A.2 Excluded, with reasons and enforcement:**

| Excluded | Why it will keep being proposed, and why it is wrong | Enforced by |
|---|---|---|
| Cross-sectional anomaly exploitation as a family | 4 bps/month average net, 10 best, 20 combined, below every cell of §5.2.2 | §0.5; break-even ceiling |
| Model-emitted numbers or dates in the fill path | Accuracy floors bound error rates, not authority | Gate 0 anchor assertion |
| Model similarity in peer construction | Drifting vendor dependency upstream of a hard gate | Import fence |
| Fitted sizing over the multipliers | Reverses, not extends, the coarseness decision | Parameter diff on multiplier cardinality |
| Passive posting and execution algorithms | Unestimable on daily bars; introduces adverse selection daily bars cannot see | Import fence |
| Continuous gate pruning between review points | Fits the design to its own evaluation window | Review only; no mechanical check exists, stated |
| Volatility and variance-risk premium | Requires options the universe lacks | §4.1 bucket restriction |
| Factor timing as signal | Weak evidence, high overfit risk | Gate 5 tier |
| Statistical arbitrage and pairs | Doubled costs, no cross-sectional breadth at 16 names | §0.5 arithmetic |
| Sentiment as signal | The substrate's alpha is *lead*, captured in §6.7's fourth multiplier | Control-arm design |
| **Insider sales as a short signal** | Sales are uninformative in every study cited; a symmetric rule would look principled and add noise | Grammar direction restriction |
| Free-form strategy structures | Reopens both defects §4 closed; the route to expressiveness is more pre-registered families | Grammar closure |

---

## References

Bailey, D. H. and López de Prado, M. (2014). The Deflated Sharpe Ratio. *Journal of Portfolio Management*, 40(5), 94–107.

Bailey, D. H., Borwein, J. M., López de Prado, M. and Zhu, Q. J. (2017). The Probability of Backtest Overfitting. *Journal of Computational Finance*, 20(4), 39–69.

Barber, B. M. and Lyon, J. D. (1997). Detecting Long-Run Abnormal Stock Returns. *Journal of Financial Economics*, 43, 341–372.

Benjamini, Y. and Hochberg, Y. (1995). Controlling the False Discovery Rate. *JRSS B*, 57(1), 289–300.

Bernard, V. L. and Thomas, J. K. (1989). Post-Earnings-Announcement Drift. *Journal of Accounting Research*, 27, 1–36.

Bloomfield, R. (2002). The Incomplete Revelation Hypothesis and Financial Reporting. *Accounting Horizons*, 16(3), 233–243. *(recollected; verify before circulation)*

Brochet, F. (2010). Information Content of Insider Trades before and after the Sarbanes–Oxley Act. *The Accounting Review*, 85(2), 419–446. *(figures verified; volume and pages recollected)*

Chen, A. Y. and Velikov, M. (2023). Zeroing In on the Expected Returns of Anomalies. *Journal of Financial and Quantitative Analysis*, 58(3), 968–1004.

Chen, A. Y. and Zimmermann, T. (2022). Open Source Cross-Sectional Asset Pricing. *Critical Finance Review*, 11(2), 207–264.

Chordia, T., Goyal, A., Sadka, G., Sadka, R. and Shivakumar, L. (2009). Liquidity and the Post-Earnings-Announcement Drift. *Financial Analysts Journal*, 65(4), 18–32.

Cohen, L., Malloy, C. and Pomorski, L. (2012). Decoding Inside Information. *Journal of Finance*, 67(3), 1009–1043. *(volume and pages recollected)*

Fidrmuc, J. P., Goergen, M. and Renneboog, L. (2006). Insider Trading, News Releases, and Ownership Concentration. *Journal of Finance*, 61(6), 2931–2973. *(volume and pages recollected)*

Fildes, R., Goodwin, P., Lawrence, M. and Nikolopoulos, K. (2009). Effective Forecasting and Judgmental Adjustments. *International Journal of Forecasting*, 25(1), 3–23.

Gregory, A., Tharyan, R. and Christidis, A. (2013). Constructing and Testing Alternative Versions of the Fama–French and Carhart Models in the UK. *Journal of Business Finance & Accounting*, 40(1–2), 172–214.

Grinold, R. C. (1989). The Fundamental Law of Active Management. *Journal of Portfolio Management*, 15(3), 30–37.

Grove, W. M. and Meehl, P. E. (1996). Comparative Efficiency of Informal and Formal Prediction Procedures. *Psychology, Public Policy, and Law*, 2, 293–323.

Jeng, L. A., Metrick, A. and Zeckhauser, R. (2003). Estimating the Returns to Insider Trading. *Review of Economics and Statistics*, 85(2), 453–471.

Lakens, D. (2017). Equivalence Tests: A Practical Primer. *Social Psychological and Personality Science*, 8(4), 355–362.

Lakonishok, J. and Lee, I. (2001). Are Insider Trades Informative? *Review of Financial Studies*, 14(1), 79–111.

Lyon, J. D., Barber, B. M. and Tsai, C.-L. (1999). Improved Methods for Tests of Long-Run Abnormal Stock Returns. *Journal of Finance*, 54(1), 165–201.

McLean, R. D. and Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? *Journal of Finance*, 71(1), 5–32.

Meehl, P. E. (1954). *Clinical versus Statistical Prediction*. University of Minnesota Press.

Mitchell, M. and Pulvino, T. (2001). Characteristics of Risk and Return in Risk Arbitrage. *Journal of Finance*, 56(6), 2135–2175. *(`recollection`; verify before circulation)*

Politis, D. N. and Romano, J. P. (1994). The Stationary Bootstrap. *JASA*, 89(428), 1303–1313.

Schuirmann, D. J. (1987). A Comparison of the Two One-Sided Tests Procedure and the Power Approach. *Journal of Pharmacokinetics and Biopharmaceutics*, 15(6), 657–680.

White, H. (2000). A Reality Check for Data Snooping. *Econometrica*, 68(5), 1097–1126.

**Citation confidence** *(the §14 precondition applies to every entry, at row level where a figure sits in a table)*.

| Tier | Entries |
|---|---|
| `verified_primary` | Fidrmuc, Goergen and Renneboog: all §0.5 figures read from the paper's own tables (ECGI WP N° 93/2005 full text, marked forthcoming at the *Journal of Finance*) |
| `verified_secondary` | Lakonishok and Lee; Jeng, Metrick and Zeckhauser; Chen and Zimmermann including licence; Chen and Velikov including the 4/10/20 bps and 50/72/93% figures; Chordia et al.; Gregory, Tharyan and Christidis including the December 2017 coverage end; the ICE mini-contract specification; **Brochet (2010), 85(2), 419–446**, closed in v1.10; **Cohen, Malloy and Pomorski (2012), 67(3), 1009–1043**, closed in v1.10; **Fidrmuc, Goergen and Renneboog (2006), 61(6), 2931–2973**, closed in v1.10 |
| `recollection`, **blocks the freeze signature** | Bloomfield's incomplete revelation hypothesis in full; Mitchell and Pulvino in full |

**One caveat, stated rather than glossed.** The FGR figures in §0.5 are read from the working-paper version explicitly marked forthcoming at the *Journal of Finance*. Published-version tables are **assumed congruent**, and any consumer requiring `verified_primary` against the journal's own pagination should check the published tables once library access is to hand. This is recorded as a §14 open verification rather than absorbed silently: the working paper is the source that was actually read, and saying otherwise would be the error class this paper spent v1.10 building a lane to prevent.
