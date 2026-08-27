# Open items

The live register. §13 holds every quantity requiring measurement or lookup; §14 holds the decisions and the freeze preconditions; Annex A.1 holds deferred capability behind predicates. **Nothing pends elsewhere**, and the spec's own linter tests that claim mechanically.

**Status vocabulary, five values and no others**, in every table here that carries a Status column: `OPEN` not started; `BLOCKED` waiting on a named dependency; `PROVISIONAL` a reading exists but not the calibration; `PART CLOSED` closed over the scope in the Scope column and open elsewhere; `CLOSED` done, whole, and recorded in the spec.

**Scope is a column and never a status.** Row 25 once read `CLOSED for US`, which put the scope inside the status and left every reader of this file to parse it out. It is now `PART CLOSED` with `US` in the Scope column, as is row 22. `Scope` reads `n/a` wherever the status is unqualified. **The reader refuses on anything outside the five** rather than repairing it: a status the register writes loosely and the code silently understands is a vocabulary kept in two places, and the second copy is the one that gets widened.

**No registration hash is written in this file except inside a sentence that names `docs/REGISTRATION_HISTORY.md`.** Twice a line here has named a hash as the one the tree carries and been overtaken by a re-stamp, and both times the correction was written as though getting the number right were the repair. It is not: **a hash in prose records a moment and is read as a state.** The exception is deliberate and narrow. A hash naming what a reading was TAKEN UNDER is fixed for ever and may be written, beside the history row that holds it; a hash naming what is CURRENT may not, and is obtained from `python -m fntn.scanner check` or the run report's provenance header instead. `test_the_register_names_no_hash_outside_a_reference_to_the_history` is what holds this, using the same negative-lookaround sweep as the schema fingerprint.

---

## The binding path, in order

Progress is not gated on design quality. Fourteen versions, a linter, a reference implementation, a literature lane and a discovery layer have all been built; the score does not move because **nothing has been measured**. Five steps, and the order is not negotiable:

1. **Verify the commission** (§13 row 1). Every break-even denominator in the paper inherits it. Until it closes, the clip, the feasible band, the reachability matrix, §5.4.4 and the whole break-even table are bracketed.
2. **Fix the pre-calibration fixings**: archive identity and span, partition boundaries, universe constituents, source roster, borrow snapshot date.
3. **Settle the §14 governance decisions** that gate directive registration: θ, the δₘᵢₙ floor, account type.
4. **Run the trace harness** (§9.4) to its stopping rule, including a minimum sample of the primary catalyst family's live filing flow.
5. **Populate §13, hash the parameter object.** That act creates **frozen design 1**. Then the retrospective deployment, and §7.1 and §7.5 return a verdict.

Until step 5, no version may add capability (§0.6).

---

## Pending rule changes

A rule change is recorded in the same commit that lands it. Where the specification version is already composed, the record is its `§12.1` change-log row. Where it is not, the record is a row here, carried until the version is composed and then discharged into that row. **A rule moving in one commit and being written down in another is the failure this section exists against**: the recording is the version, and a rule change nobody wrote down is a version nobody counted.

| Rule changed | Sections it touches | Kind (§3.6.4) | Landed | Discharged into |
|---|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a |

*Empty is the correct state immediately after a version is composed. P76, P77 and P78 were carried here between 27 August 2026 and the composition of v1.14, and are discharged into §12.1.*

**One rule landed in this batch without a row, and the judgement is recorded here rather than left in a commit message.** Commit `d95c816` typed the schema fingerprint as `schema:<digest>` and, with it, made `Registration.schema_matches` accept **two encodings**: the typed form and the superseded bare digest. The loader therefore returns `verified` for a file it would have called `unverifiable_schema_change` the moment before, which is **an acceptance widening**, and P80 is the standard such a thing answers to: a value that changes what a fence lets through, added quietly, widens the sweep with nothing on the record.

**The judgement, stated, and it is a close one.** There is a real argument that it is notation and not a rule: the widening admits exactly those files whose fingerprint equals a digest **the code recomputes from its own dataclass**, so it carries no free parameter, nothing an operator could have chosen otherwise and nothing to attribute to a registration, and every file it newly admits is one whose shape genuinely matches. That would separate it from P80, whose stopword set was a chosen list governing real-world spans. **It is recorded as a version all the same.** Rule 5 names *admissibility rule* without qualifying it as substantive; the bilingualism is a standing property of the loader that outlives the migration and must be findable by a reader of the specification rather than of `git log`; and declining the row would have meant inventing a meta-rule about which admissibility changes count, which is more judgement than the row costs. **Discharged into `§12.1` row P87a**, written retrospectively as P82a was, in the same commit as this paragraph. The table above stays `n/a` because the version is already composed and the row is in it.

---

## §13: twenty-five calibrations

| # | Quantity | Status | Scope | What unblocks it |
|---|---|---|---|---|
| 1 | **Fixed round-trip commission** | **PROVISIONAL** | n/a | **Moved from BLOCKED on 27 August 2026 (§0.11, `§12.1` P91), because a reading now exists and the calibration does not.** *Recomputed at the £50,000 clip, not edited in place.* **UK, tiered schedule: 61.5 bp**, up from **61.4 bp** at the £2,500 clip. **The PTM levy moves from `n/a` to APPLICABLE**: its threshold is **£10,000** of consideration, the £2,500 clip sat below it and the £50,000 clip does not, so a levy that was *previously not applicable at all* is now payable on every UK trade. That crossing is why a twentyfold notional makes the UK tiered round trip **dearer and not cheaper**. **US: approximately 3 bp** at an illustrative trade value of **USD 64,000**. **The reading is the operator's arithmetic and not a cited schedule**, which is what PROVISIONAL means here and why the row is not CLOSED. **The three gaps are unaffected by the clip and remain open:** the FX route is not in a published schedule; the tiered-or-fixed election is not made; the contracting entity is not established. What unblocks it is unchanged: a cited, published IBKR schedule at the required granularity. A phone answer is corroboration, not the citation. **Runs first; decide in advance what you will accept as a substitute, before you know whether you need one** |
| 2 | Gate 2 kill percentile | BLOCKED | n/a | Design segment exists |
| 3 | Gate 7 random-grid base rate and threshold | BLOCKED | n/a | Design segment exists |
| 4 | Gate 6 percentile floor | BLOCKED | n/a | Calibration segment exists |
| 5 | Placebo Δ | BLOCKED | n/a | An un-randomised calibration run |
| 6 | ATR-to-volatility ratio | BLOCKED | n/a | Calibration segment; archive |
| 7 | Per-family realised median | BLOCKED | n/a | Calibration segment; minimum 100 trades |
| 8 | Break-even ceiling | BLOCKED | n/a | **Invalidated at the £50,000 clip on 27 August 2026 and NOT re-derived (§0.11, P91).** The ceiling is set by the class's largest documented post-decay effect and not by the clip, so the clip did not move it; what moved is its fixed-cost input, and the impact term it has never had a column for is the one now growing. Row 1, and the design segment |
| 9 | Gate 1 price floor | BLOCKED | n/a | **Invalidated at the £50,000 clip on 27 August 2026 and NOT re-derived (§0.11, P91).** The floor is where the spread exceeds the ceiling, so it inherits row 8 and row 8 is blocked. Nothing about the clip makes it derivable. Row 1; calibration segment |
| 10 | Gate 5 minimum conditional sample | BLOCKED | n/a | Calibration segment |
| 11 | Audit-stream minimum n (§7.2) | BLOCKED | n/a | Observed intake and kill rates |
| 12 | **Joint qualifying-and-tradable rate** | BLOCKED | n/a | Design segment on the primary feed. **Decides whether the one live family survives its own cost table** |
| 13 | **Capture rate** | BLOCKED | n/a | The backfill. FGR documents a same-session jump reversing ~11% over ten days against a next-open fill convention |
| 14 | Sub-$1m cost tier | BLOCKED | n/a | **Invalidated at the £50,000 clip on 27 August 2026 and NOT re-derived (§0.11, P91), and its reachability is now in question.** At the illustrative **USD 64,000** a single clip is **at least 6.4% of a whole day's traded value** in a sub-$1m name, before allowing that a round trip is two orders. **§0.11 resolved §0.6's consequence to (b), so nothing in the funnel refuses on that.** Whether this tier can be reached at all at the new clip is a question the row now carries and does not answer. Design segment, shadow-cohort names. Gates §0.10 entirely |
| 15 | Ingestion-lag threshold | BLOCKED | n/a | Observed lag distribution per source class |
| 16 | News-adjacency magnitude threshold | BLOCKED | n/a | Design segment; sign taken from the paper, kill criterion written first |
| 17 | Filing materiality threshold | BLOCKED | n/a | Design segment; 0.1% of market capitalisation as the paper-sourced prior |
| 18 | Source-lead minimum call count | BLOCKED | n/a | Calibration, per-source call counts |
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | **CLOSED** | n/a | **Closed 26 August 2026.** δ = 50 bps, *n*ₘᵢₙ = 30. **The commitment is the 26 August one and has not moved**: both values were stamped at 22:54 UTC on 26 August 2026, before any archive exists, so the criterion was written blind and remains so. The registration OBJECT carrying them has been re-stamped since, most recently on 27 August 2026, **because the intake budget entered the parameter object, not because δ or *n*ₘᵢₙ changed.** The causing field is `intake_point_budget_s`: a ceiling on how long a run may spend reaching a refusal, which is a statement about the cost of looking and says nothing whatever about how far apart the arms must be before the difference counts. A re-stamp caused by a different field is a new hash on the same commitment; a re-stamp caused by this field would be a new commitment, and the two are distinguished here so that a reader cannot mistake one for the other. **The whole chain, with the causing field named on every row and each hash recomputed from the object it was taken over, is `docs/REGISTRATION_HISTORY.md`, and no hash is written on this row.** Five stamps stand there and four are re-stamps; not one of the four was caused by either value on this row, and the causing-field column is what says so |
| 20 | **Control-arm ratio *M/N* and seed** | **CLOSED** | n/a | **Closed 26 August 2026.** Ratio 1.0 (matched arms), seed 20260826. **The commitment is the 26 August one and has not moved**, fixed before the first sweep and before any archive exists, so the arm cannot be redrawn on a known result. Carried unchanged through three 27 August re-stamps, which **were caused by the fence's vocabulary entering the parameter object, `rulebook_stopwords` and then `lexicon`, and then by the intake budget entering it, `intake_point_budget_s`, and by nothing about the control arm.** The budget is a ceiling on the time a run may spend on one subject; it cannot reach the seed, and a seed it cannot reach is a seed no re-stamp of its object has redrawn. Every stamp this ratio and seed have stood under is in `docs/REGISTRATION_HISTORY.md`, with the causing field named on each, and none is written on this row |
| 21a | **Fence false-positive rate, DRAWN proposals** *(split from row 21, 27 Aug 2026)* | **BLOCKED** | n/a | **Blocked on the design segment**, and this is the substance of the split rather than its bookkeeping. **The required precision is not a property of the fence; it is set by how much funnel depth §7.1 can afford to lose before it loses power**, and §7.1 has not run. Until it does, nobody can say whether this rate needs to be known to a percentage point or to five, so no sample size can be derived and none is proposed here. **The n = 200 the superseded row specified was chosen and not derived.** It was a round number attached to a quantity whose tolerance nobody had computed. Deriving it is what is blocked; the number is withdrawn rather than carried, because a sample size with no power calculation behind it reads as a requirement and is a guess. **The current reading is an UPPER BOUND and is not a rate.** 0 events in 36 trials. By the rule of three the 95% upper bound is 3/36, approximately **8.3%**. ***It is not 0%.*** Zero events does not estimate zero: a fence refusing one clean proposal in twenty would produce this same reading better than one time in six, and the sample cannot separate the two. The **8.3%** is what 36 trials can support and the **0%** previously carried on this row is withdrawn as a statement of the rate, whilst standing as the count it is: **0 of 36 refused**. Reading taken against `docs/labelled_proposals.json`, locked by tests, under the registration at row 4 of `docs/REGISTRATION_HISTORY.md`, `701adbd9d48015ed`, which is written here because a hash naming what a reading was TAKEN UNDER is fixed for ever whilst a hash naming what is CURRENT goes stale at the next re-stamp. **The object has since been re-stamped**, caused by `intake_point_budget_s`, and **the reading is not restated under it.** The budget is a ceiling on how long intake may spend before it abandons a subject; it reaches nothing the entity fence reads, so the fence that produced 0 of 36 is the fence that stands today and the count needs no re-taking. What it does not license is printing this figure under the current hash: a reading carries the hash it was taken under, and moving it forward each time some unrelated field re-stamps the object would hand it a provenance no measurement ever gave it. The chain between the two is `docs/REGISTRATION_HISTORY.md`. On the fence as v1.13 left it the same 36 gave **3 refused**, an upper bound of roughly 22% by the exact binomial, so the ticker rule moved the bound and not merely the count. Labels carry provenance `model_clerk`, not hand labels; `python -m fntn.scanner ratify-draw` puts twelve of the thirty-six in front of the operator with the clerk's label withheld |
| 21b | **Fence false-negative ROUTE COVERAGE** *(split from row 21, 27 Aug 2026)* | **PROVISIONAL** | n/a | **5 of 6 routes closed; the open one is a title-case bare ticker**, which is the residual P76's rule takes on knowingly. **Coverage, and never a rate.** The six are authored probes, one per named route into the fence, so they are chosen rather than sampled and a proportion over them estimates nothing: change the probe set from six routes to twelve and the percentage halves whilst the fence is untouched. This row therefore names routes and prints no denominator-bearing figure. The term *episode-level* is not used of it, because that implies a sample of episode-level material and there is none. **It is PROVISIONAL and not BLOCKED, and the difference is real:** nothing here waits on the design segment. Coverage of six written routes is decidable by reading them. **The operator reading the six authored probes is what unblocks it**, and `python -m fntn.scanner ratify-draw` writes all six into the ratification file unwithheld for exactly that. What ratification settles is whether each probe exercises the route it claims and whether six routes are the routes that matter; it does not turn coverage into a rate, and only a drawn episode-level sample could. Labels carry provenance `model_clerk`. **The six probes were read under the registration at row 4 of `docs/REGISTRATION_HISTORY.md`, `701adbd9d48015ed`, and the object has since been re-stamped**, caused by `intake_point_budget_s`. Coverage of six authored routes is decided by reading the fence's rules, and the budget changed none of them, so the five closed routes stay closed and the title-case bare ticker stays open. As on row 21a, the coverage is not restated under the current hash |
| 22 | **Discovery corpus roster, partitions, discoverable classes** | **PART CLOSED** | US | US declared (`pre_archive`). UK, AU, EU and NZ profiled but not registered: each needs a listing file with a known total. **The corpus stores extracted text, from 27 Aug 2026**: `scripts_fetch_us_corpus.sh` drops `<script>` and `<style>` subtrees entire and drops comments, applies the furniture rules (`<nav>`, `<header>`, `<footer>`, and any element whose class or id contains nav, menu, sidebar, related, footer or breadcrumb), and writes the text that survives. `_manifest.tsv` carries `raw_bytes` beside `bytes`, so what was discarded is on the record. **542,878 of 638,883 bytes removed, 85%**, against 24% under the chrome strip this replaces, which reached none of the three names it was aimed at: `API` sat in an HTML comment in `<head>` and `BlackBerry` and `Opera` in a user-agent sniffer in an inline `<script>`, and `<head>` is not `<header>` whilst a comment and a `<script>` carry no class or id. Naming those three constructs as three more things to remove would have closed three members of a class; text closes the class, a construct that carries no text being unable to put a name in the corpus. **Fence hits on the corpus fall from 3 distinct / 39 total to 0 / 0** (`docs/trace_report_2026-08-27.txt`), which is a **count** over thirteen documents and not a rate, and is not a reading of rows 21a or 21b, which are measured against the labelled set. `MIN_BYTES` re-derived for the extracted size at **500 bytes**, from 4,000: the smallest genuine document is Rule 16a-13 at 763 bytes, one sentence and complete, whilst the two non-documents to hand extract to 54 (LII's 404) and 377 (the sec.gov stub); the gap is a factor of two and is stated rather than smoothed, and the byte floor is no longer the main guard, the extractor refusing an unclosed dropped element directly. **The cost, stated:** markup is gone, so a table's structure and a link's target are gone, and files are `.txt` rather than `.htm` to say so. **The raw pages are retained** at `corpora/us/_raw`, underscore-prefixed so the corpus reader and the integrity check both skip them, digests in `_raw/_fetch.tsv`, and `test_raw_html_reextracts_to_the_stored_corpus` re-derives all thirteen through the fetch script's own extractor byte-for-byte. Extraction is destructive and until this the corpus could not be re-derived from anything. The corpus text was produced by extracting over the chrome-stripped HTML already in the tree; the network was hit separately, thirteen GETs on 27 Aug 2026, to check that argument and to keep the pages, and every raw size matched the 26 Aug manifest with every extracted document byte-identical. **What is kept is the 27 Aug fetch, not the 26 Aug one**: the 26 Aug raw pages were overwritten by the chrome strip at fetch time and are gone. UK, AU, EU and NZ remain unregistered: each needs a listing file with a known total |
| 23 | Intake abort-position distribution | **PROVISIONAL** | n/a | **Corrected 27 August 2026.** Audit stream at scale. The 26 August reading, every failure at position 3, was taken under a **wider exclusivity map than the registration declares**. Re-run under the registered four classes (`docs/trace_report_2026-08-27.txt`): 5 at position 3, **8 at position 9**, deepest failure **9 of 12**. Of the remaining ten points, every branch fires when a subject is built to trip it, so none is dead code, but **four cannot be reached by any configured path**: `agent_overreached_schema` (`raw_payloads()` is called from nowhere, so the authority fence has no input), `discovery_partition_violation` (`Corpus.__post_init__` refuses first), `registered_at_unstampable` (the query log is written and never read back, and each scan builds a fresh fence), and `source_inaccessible` (the resolver defaults to `bool(ref)`, so retrieval is never attempted). `provenance_tag_absent` can emit but can never be a first failure, being masked by position 10 on the same trigger. Those four are remediation candidates, not measurement gaps |
| 24 | Cross-market generalisability | BLOCKED | n/a | Design segment; classes present in both markets |
| 25 | **Security master and lexicon coverage** | **PART CLOSED** | US | 10,388 issuers from the SEC's own file, 100% by construction. Other markets outstanding |
| 27 | **Intake budget** | **CLOSED** | n/a | **Closed 27 August 2026.** `intake_point_budget_s` = 20 s, `intake_subject_budget_s` = 120 s, `budget_retry_max` = 1, registered under the stamp `docs/REGISTRATION_HISTORY.md` records them as causing. A ceiling on the cost of looking, not a judgement of the idea: a subject exceeding either is abandoned with `intake_budget_exhausted`, which refuses to score. **The decision is taken once, at capture**, and the ledger records the elapsed time, the budget in force and the verdict; a replay reads that record and never re-times the work, `ReplayedBudget` holding no clock at all. **Abandonments are reported beside row 23's abort-position distribution and never inside it**, a subject that ran out of time not having failed the point it was standing on, and the count is printed in every report including when it is zero. **The honest limit: a ceiling that refuses, not a timeout that interrupts.** A check is run and then measured, so a point that blocks forever is never caught. The three values are governance and were set before any sweep at scale; they are not calibrated against an observed distribution of intake times, because none exists yet, and the first run at scale is what would justify moving them |
| n/a | FX exposure budget (§0 decision) | OPEN | n/a | Governance judgement in a stated range. **Materially larger from 27 August 2026 (§0.11): a 50% single-name position in a US name is 50% of the book in USD.** At the £2,500 clip the same position was 2.5%, so a judgement that could be deferred as second-order is now a judgement about half the book. **The status has not moved and what it decides has**, and the two are not the same thing |

### PENDING, and addressed to the operator: the SCOPE of row 1 is under review

**The row is not changed by this block and stays BLOCKED. No figure is looked
up here and no value is assumed.** What is recorded is a question about what
row 1 is a row about, raised because the answer changes what closing it would
even mean.

**The question.** Row 1 reads **fixed round-trip commission**. Should it read
**fixed round-trip transaction cost**, and take in:

- **transfer taxes, per venue**;
- **exchange and regulatory levies, with their thresholds**, a levy with a
  threshold not being a rate and not behaving like one at a £2,500 clip;
- **FX conversion, in both directions**, the outward leg and the return leg
  being two conversions and not one.

**Why it is not bookkeeping.** Row 1 runs first and **every break-even
denominator in the paper inherits it**: the clip, the feasible band, the
reachability matrix, §5.4.4 and the whole break-even table. A row whose scope
is too narrow closes to a verified figure that is nonetheless the wrong
quantity, and the arithmetic downstream is then exact over the wrong number.
**That is a failure no later precision on row 1 repairs**, because the defect
is not in the measurement.

**AIM and the Main Market may be separate tiers.** Stamp duty exempts AIM and
does not exempt the Main Market, so the two venues do not share a transfer-tax
treatment. If they do not, **a single UK denominator is wrong for both**: too
high for AIM and too low for the Main Market, and wrong in opposite directions,
so no single figure is conservative for the pair and no average over them is a
figure about anything. Whether the split is by venue, and whether the US then
needs its own tier for the same reason, is part of the question and is not
answered here.

**The options, named.**

| Option | What it would mean |
|---|---|
| A. Leave the scope as commission | Row 1 stays a commission row and closes on a commission schedule. The other components are then somebody's row and nobody has said whose, which is the state that produced this block |
| B. Widen to transaction cost, one UK denominator | Row 1 becomes the whole round-trip cost. Simplest to state and, if stamp duty does exempt AIM, wrong for both UK venues at once |
| C. Widen to transaction cost, tiered by venue | Row 1 becomes the whole round-trip cost and splits: AIM, UK Main Market, and US considered separately. Most rows to close, and the only option that can be right for both UK venues |

**What is deliberately left open.** Whether taking B or C is a correction to a
pending row's definition or a **cost-tier change**, which under §0.6 is
apparatus and takes an Annex A.1 row with a predicate, is itself part of the
decision and is not settled here. Answering it in this block would be the
scanner choosing the rule that governs its own scope.

**Raised 27 August 2026.** Carried until the operator answers. Nothing acts on
it in the meantime, and row 1 remains **BLOCKED** on a cited, published IBKR
schedule at whatever granularity the answer turns out to require.


**Rows 19, 20 and 25 closed on 26 August 2026**, and row 22 closed for US. **The hash the registration currently carries is not written in this file, and this line is why.** It has named a superseded hash twice: first the stamp those rows closed under, which stopped being current three re-stamps later, and then its replacement, which stopped being current one re-stamp after that. Each time the line contradicted the rows above it whilst reading as the live figure, and each time the correction was itself overtaken. **A hash written into prose records a moment and is read as a state**, which is a defect that recurs on every re-stamp and cannot be fixed by getting the number right once more. The chain is `docs/REGISTRATION_HISTORY.md`, one row per hash with the causing field named and each recomputed from the object it was taken over; the current hash is what `python -m fntn.scanner check` prints and what the run report's provenance header carries. The commitments have not moved; the object carrying them has, four times.

**What actually stands between the programme and a measurement.** *This paragraph previously named the archive's opening boundary and told the reader to set `archive_opens`. It has been set to 2023-01-01 since 26 August 2026, and `docs/REGISTRATION_HISTORY.md` names `archive_opens` as the field that caused the second stamp in the chain. The paragraph named as pending a thing this register elsewhere recorded as done, and it is replaced rather than amended.* The statuses below are read from the two tables above and not from recollection.

**First, the four operator inputs, on every draft there is.** The ledger holds **twelve drafts and none registered**: `delta_min`, the registered sign, the ratified pre-mortem and the literature search are outstanding on all twelve, four of four apiece. Nothing machine-raised may supply any of them, so the scanner cannot shorten this queue by running longer, and running it again produces more drafts blocked on the same four. **That is the design working and it is also the binding constraint.**

**Second, the three §14 governance decisions that gate directive admission.** Overlap tolerance θ, the δₘᵢₙ floor and account type are each **OPEN** in the §14 table. θ bounds concurrency against the design-segment reuse ledger and the δₘᵢₙ floor decides what is worth a session of the segment, so a directive cannot be admitted on the operator's four inputs alone whilst these stand open.

**Those seven are the whole of it at this stage**, and neither group waits on data, a purchase, a client or a corpus. Both wait on a person, which is why no amount of further building moves them.

**What lies behind them, so the seven are not mistaken for the end.** Of the twenty-seven numbered §13 rows, **twenty are BLOCKED, three are CLOSED whole (19, 20 and 27), one is PART CLOSED (22), one is a closure over the US only (25) and two are PROVISIONAL (21b and 23)**. The commonest unblocker named in the blocked rows is a design segment that does not exist, and **§13 row 1 runs first** because every break-even denominator inherits it. Of the six §14 freeze preconditions, five are **OPEN**. So the seven decisions above unblock registration; they do not on their own produce a measurement, and nothing in this register claims they do.

**One limit, stated rather than implied.** Nothing checks the date of each document in a `pre_archive` corpus folder. The guarantee rests on the operator putting only pre-boundary material there. That is a curation control, not a mechanical one.

---

## §14: open decisions

| Decision | Status | Scope | Note |
|---|---|---|---|
| Default exclusivity construction | **CLOSED** | n/a | **Closed v1.13.** `cross_market`, with `disjoint_partition` as a per-class override |
| Overlap tolerance θ | OPEN | n/a | Governance in a stated range. Gates directive admission |
| δₘᵢₙ floor | OPEN | n/a | Governance. Below it a directive is not worth a session of the segment |
| Account type, cash or margin | OPEN | n/a | Currently non-binding; binds before any short-side family or margin simulation. **Note the settlement-bridge cost line arguably binds it already** |
| **Minimum clip (§0 decision)** | **CLOSED** | n/a | **Closed 27 August 2026, over a stated objection.** £2,500 to £50,000 against unchanged reference equity of approximately £100,000, taking the single-name position from 2.5% to 50%. The costs are on the record in §0.11 and `§12.1` P90 and are not restated here: a bounded fixed-cost saving that is **negative on the UK tiered schedule**, 61.4 to 61.5 bp, because the PTM levy crosses its £10,000 threshold; market impact that scales with participation, has no ceiling and has no row; concentration up twentyfold; and an analysis that argued against the change. **The §0.6 consequence resolved to (b)**: no participation constraint, a known unbounded exposure with no refusing mechanism. The gate is deferred in Annex A.1 |
| Control-arm ratio *M/N* | OPEN | n/a | Also §13 row 20 |
| Manual-observation capacity per period | OPEN | n/a | The scanner will exhaust it rather than approach it |
| UK daily factor series (§0.7b) | OPEN | n/a | Standard library ends December 2017, five years before the archive opens |
| ICB point-in-time vintage vendor (§0.7d) | OPEN | n/a | Until procured, peer sets are not point-in-time and every pooled estimate carries that qualification |
| The drafted feed-budget amendment (§0.6) | OPEN | n/a | **Available, not taken.** Its shape is fixed in the spec so that taking it cannot be quiet |

## §14: preconditions to signing the freeze

| Precondition | Status | Scope | Note |
|---|---|---|---|
| Claim provenance: no `recollection` tag on anything feeding a gate, boundary or published table | **OPEN** | n/a | Bloomfield and Mitchell & Pulvino remain `recollection` and block the signature |
| Register completeness | **PART CLOSED** | §12.7's terms |  |
| Review harness run to its stopping rule | **OPEN** | n/a | v1.14 is a new composition and resets the count; no clean pass recorded, two required |
| Trace exercise (§9.4) to its stopping rule | **OPEN** | n/a | the discovery-layer traces of 26 and 27 August are two blocks, both non-evidentiary. Neither includes the primary catalyst family's live filing flow, and no US corpus sweep has run for want of a client |
| Broker commission schedule verified | **OPEN** | n/a | §13 row 1 |
| FGR published-version tables against journal pagination | OPEN | n/a | upgrades §0.5 rows to `verified_primary` |

---

## Annex A.1: deferred, with predicates

Evaluated and logged continuously; acted on only after the §0.6 instruments report. The full table is in the spec. The rows added in v1.13:

| Capability | Predicate |
|---|---|
| Discovery corpus ingestion adapters for markets outside §0.7(f) | Instruments reported, **and** the manual-observation route has produced at least one registered directive that reached a verdict. Reading a foreign register by hand is not apparatus; a parser for it is |
| Standing automation of the discovery layer | Instruments reported, **and** the control arm has returned *agent selection carries information*. Automation follows demonstrated value, not the reverse |
| Agent-proposed items entering the §3.5 item pipeline | **Refused rather than deferred**, pending an explicit §0 decision |

The rows added on 27 August 2026, by §0.11 and by `§12.1` P92. **The two cost tiers are deferred and not taken.** Both make a **subset** of names cheaper, and a cheaper subset **admits names the conservative single tier refuses**, which is capability under §0.6:

| Capability | Predicate |
|---|---|
| **UK growth-market cost tier: the AIM stamp-duty exemption** | The §0.6 instruments report. **Basis:** s.99(4B) Finance Act 1986, effective 28 April 2014; AIM is on HMRC's recognised growth market list at STSM041330. **Two limbs, both binding:** admitted to trading on a recognised growth market **and** not listed on that or any other market, so a **dual-listed AIM company does not qualify** and a tier keyed on AIM membership alone is wrong for exactly those names. **Worth 61.4 bp to 11.4 bp at the £2,500 clip, a factor of 5.4**; the £50,000 equivalent is not published, the base being 61.5 bp on a PROVISIONAL row 1. **Provenance `verified_secondary`:** statute and manual page named, **unread in this tree**; `verified_primary` needs s.99(4B) and STSM041330 read. **At the £50,000 clip the tier may be largely unreachable**, most AIM names lacking the depth; a participation constraint would exclude them and §0.11 took **(b)**, so the consequence is an exposure and not an exclusion. **Expiry:** qualification is a status and can lapse on a later listing |
| **UK new-listing SDRT relief** | The §0.6 instruments report, **and** the provenance upgraded to a primary source. **Basis:** Autumn Budget 2025. Relief from the **0.5% SDRT charge** for companies newly listed on a UK regulated market **on or after 27 November 2025**, for **three years from listing**. **Does not touch existing Main Market shares. Does not apply to the 1.5% clearance-system charge.** **Provenance: CORROBORATION ONLY**, law-firm commentary and not HMRC, no legislation named; corroboration is not the citation, and promoting it needs the HMRC guidance or the legislation itself, which is why the predicate is doubled. **Expiry, structural:** time-limited by construction, so a name qualifying today may not in two years, and a tier assigned once and cached would silently under-cost the trade after expiry |
| **Participation constraint against daily traded value** | The §0.6 instruments report. A gate, therefore apparatus, therefore blocked. §0.11 resolved to **(b)**, so the £50,000 clip runs with no participation constraint; this row records that the refusing mechanism is **absent by decision and not by oversight**, and does not soften the exposure. Taking it early needs an explicit §0 exception to §0.6, a `§12.1` row, and a threshold as a §13 row with a sample and a rule |

---

## What is explicitly not next

| Item | Why |
|---|---|
| A fourteenth design round | The learning of the last four versions is that further design rounds do not move the score |
| Running any directive measurement | The query fence closes conditional-return queries on a target population until `registered_at`, and the archive does not exist |
| Any new apparatus | §0.6 armed. The drafted feed-budget amendment stays available and not taken |
| Live capital of any kind | Nothing signed authorises capital. The freeze record's scope, when signed, is the backfill and the two instruments |
