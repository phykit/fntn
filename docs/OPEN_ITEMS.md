# Open items

The live register. §13 holds every quantity requiring measurement or lookup; §14 holds the decisions and the freeze preconditions; Annex A.1 holds deferred capability behind predicates. **Nothing pends elsewhere**, and the spec's own linter tests that claim mechanically.

Status vocabulary: `OPEN` not started, `BLOCKED` waiting on a named dependency, `PROVISIONAL` a reading exists but not the calibration, `CLOSED` done and recorded in the spec.

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

---

## §13: twenty-five calibrations

| # | Quantity | Status | What unblocks it |
|---|---|---|---|
| 1 | **Fixed round-trip commission** | **BLOCKED** | A cited, published IBKR schedule at the required granularity. A phone answer is corroboration, not the citation. **Runs first; decide in advance what you will accept as a substitute, before you know whether you need one** |
| 2 | Gate 2 kill percentile | BLOCKED | Design segment exists |
| 3 | Gate 7 random-grid base rate and threshold | BLOCKED | Design segment exists |
| 4 | Gate 6 percentile floor | BLOCKED | Calibration segment exists |
| 5 | Placebo Δ | BLOCKED | An un-randomised calibration run |
| 6 | ATR-to-volatility ratio | BLOCKED | Calibration segment; archive |
| 7 | Per-family realised median | BLOCKED | Calibration segment; minimum 100 trades |
| 8 | Break-even ceiling | BLOCKED | Row 1 |
| 9 | Gate 1 price floor | BLOCKED | Row 1; calibration segment |
| 10 | Gate 5 minimum conditional sample | BLOCKED | Calibration segment |
| 11 | Audit-stream minimum n (§7.2) | BLOCKED | Observed intake and kill rates |
| 12 | **Joint qualifying-and-tradable rate** | BLOCKED | Design segment on the primary feed. **Decides whether the one live family survives its own cost table** |
| 13 | **Capture rate** | BLOCKED | The backfill. FGR documents a same-session jump reversing ~11% over ten days against a next-open fill convention |
| 14 | Sub-$1m cost tier | BLOCKED | Design segment, shadow-cohort names. Gates §0.10 entirely |
| 15 | Ingestion-lag threshold | BLOCKED | Observed lag distribution per source class |
| 16 | News-adjacency magnitude threshold | BLOCKED | Design segment; sign taken from the paper, kill criterion written first |
| 17 | Filing materiality threshold | BLOCKED | Design segment; 0.1% of market capitalisation as the paper-sourced prior |
| 18 | Source-lead minimum call count | BLOCKED | Calibration, per-source call counts |
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | **CLOSED 26 Aug 2026** | δ = 50 bps, *n*ₘᵢₙ = 30. **The commitment is the 26 August one and has not moved**: both values were stamped at 22:54 UTC on 26 August 2026, before any archive exists, so the criterion was written blind and remains so. The registration OBJECT carrying them has been re-stamped since, most recently to `701adbd9d48015ed` on 27 August 2026, **because the fence's vocabulary moved into the parameter object, not because δ or *n*ₘᵢₙ changed.** A re-stamp caused by a different field is a new hash on the same commitment; a re-stamp caused by this field would be a new commitment, and the two are distinguished here so that a reader cannot mistake one for the other. **The whole chain, with the causing field named on every row and each hash recomputed from the object it was taken over, is `docs/REGISTRATION_HISTORY.md`**; the earlier hashes on this same δ and *n*ₘᵢₙ are `890a80e3a8566837`, `a06400ef28ebb54c` and `b8dd61e7eea6898e` |
| 20 | **Control-arm ratio *M/N* and seed** | **CLOSED 26 Aug 2026** | Ratio 1.0 (matched arms), seed 20260826. **The commitment is the 26 August one and has not moved**, fixed before the first sweep and before any archive exists, so the arm cannot be redrawn on a known result. Carried unchanged through two 27 August re-stamps to `701adbd9d48015ed`, which **were caused by the fence's vocabulary entering the parameter object, `rulebook_stopwords` and then `lexicon`, and by nothing about the control arm.** Earlier hashes on the same ratio and seed: `890a80e3a8566837`, `a06400ef28ebb54c`, `b8dd61e7eea6898e`, and the chain is `docs/REGISTRATION_HISTORY.md` |
| 21a | **Fence false-positive rate, DRAWN proposals** *(split from row 21, 27 Aug 2026)* | **BLOCKED** | **Blocked on the design segment**, and this is the substance of the split rather than its bookkeeping. **The required precision is not a property of the fence; it is set by how much funnel depth §7.1 can afford to lose before it loses power**, and §7.1 has not run. Until it does, nobody can say whether this rate needs to be known to a percentage point or to five, so no sample size can be derived and none is proposed here. **The n = 200 the superseded row specified was chosen and not derived.** It was a round number attached to a quantity whose tolerance nobody had computed. Deriving it is what is blocked; the number is withdrawn rather than carried, because a sample size with no power calculation behind it reads as a requirement and is a guess. **The current reading is an UPPER BOUND and is not a rate.** 0 events in 36 trials. By the rule of three the 95% upper bound is 3/36, approximately **8.3%**. ***It is not 0%.*** Zero events does not estimate zero: a fence refusing one clean proposal in twenty would produce this same reading better than one time in six, and the sample cannot separate the two. The **8.3%** is what 36 trials can support and the **0%** previously carried on this row is withdrawn as a statement of the rate, whilst standing as the count it is: **0 of 36 refused**. Reading taken under registration `701adbd9d48015ed` against `docs/labelled_proposals.json`, locked by tests. On the fence as v1.13 left it the same 36 gave **3 refused**, an upper bound of roughly 22% by the exact binomial, so the ticker rule moved the bound and not merely the count. Labels carry provenance `model_clerk`, not hand labels; `python -m fntn.scanner ratify-draw` puts twelve of the thirty-six in front of the operator with the clerk's label withheld |
| 21b | **Fence false-negative ROUTE COVERAGE** *(split from row 21, 27 Aug 2026)* | **PROVISIONAL** | **5 of 6 routes closed; the open one is a title-case bare ticker**, which is the residual P76's rule takes on knowingly. **Coverage, and never a rate.** The six are authored probes, one per named route into the fence, so they are chosen rather than sampled and a proportion over them estimates nothing: change the probe set from six routes to twelve and the percentage halves whilst the fence is untouched. This row therefore names routes and prints no denominator-bearing figure. The term *episode-level* is not used of it, because that implies a sample of episode-level material and there is none. **It is PROVISIONAL and not BLOCKED, and the difference is real:** nothing here waits on the design segment. Coverage of six written routes is decidable by reading them. **The operator reading the six authored probes is what unblocks it**, and `python -m fntn.scanner ratify-draw` writes all six into the ratification file unwithheld for exactly that. What ratification settles is whether each probe exercises the route it claims and whether six routes are the routes that matter; it does not turn coverage into a rate, and only a drawn episode-level sample could. Labels carry provenance `model_clerk` |
| 22 | **Discovery corpus roster, partitions, discoverable classes** | **PART CLOSED** | US declared (`pre_archive`). UK, AU, EU and NZ profiled but not registered: each needs a listing file with a known total. **The corpus stores extracted text, from 27 Aug 2026**: `scripts_fetch_us_corpus.sh` drops `<script>` and `<style>` subtrees entire and drops comments, applies the furniture rules (`<nav>`, `<header>`, `<footer>`, and any element whose class or id contains nav, menu, sidebar, related, footer or breadcrumb), and writes the text that survives. `_manifest.tsv` carries `raw_bytes` beside `bytes`, so what was discarded is on the record. **542,878 of 638,883 bytes removed, 85%**, against 24% under the chrome strip this replaces, which reached none of the three names it was aimed at: `API` sat in an HTML comment in `<head>` and `BlackBerry` and `Opera` in a user-agent sniffer in an inline `<script>`, and `<head>` is not `<header>` whilst a comment and a `<script>` carry no class or id. Naming those three constructs as three more things to remove would have closed three members of a class; text closes the class, a construct that carries no text being unable to put a name in the corpus. **Fence hits on the corpus fall from 3 distinct / 39 total to 0 / 0** (`docs/trace_report_2026-08-27.txt`), which is a **count** over thirteen documents and not a rate, and is not a reading of rows 21a or 21b, which are measured against the labelled set. `MIN_BYTES` re-derived for the extracted size at **500 bytes**, from 4,000: the smallest genuine document is Rule 16a-13 at 763 bytes, one sentence and complete, whilst the two non-documents to hand extract to 54 (LII's 404) and 377 (the sec.gov stub); the gap is a factor of two and is stated rather than smoothed, and the byte floor is no longer the main guard, the extractor refusing an unclosed dropped element directly. **The cost, stated:** markup is gone, so a table's structure and a link's target are gone, and files are `.txt` rather than `.htm` to say so. **The raw pages are retained** at `corpora/us/_raw`, underscore-prefixed so the corpus reader and the integrity check both skip them, digests in `_raw/_fetch.tsv`, and `test_raw_html_reextracts_to_the_stored_corpus` re-derives all thirteen through the fetch script's own extractor byte-for-byte. Extraction is destructive and until this the corpus could not be re-derived from anything. The corpus text was produced by extracting over the chrome-stripped HTML already in the tree; the network was hit separately, thirteen GETs on 27 Aug 2026, to check that argument and to keep the pages, and every raw size matched the 26 Aug manifest with every extracted document byte-identical. **What is kept is the 27 Aug fetch, not the 26 Aug one**: the 26 Aug raw pages were overwritten by the chrome strip at fetch time and are gone. UK, AU, EU and NZ remain unregistered: each needs a listing file with a known total |
| 23 | Intake abort-position distribution | **PROVISIONAL, corrected 27 Aug 2026** | Audit stream at scale. The 26 August reading, every failure at position 3, was taken under a **wider exclusivity map than the registration declares**. Re-run under the registered four classes (`docs/trace_report_2026-08-27.txt`): 5 at position 3, **8 at position 9**, deepest failure **9 of 12**. Of the remaining ten points, every branch fires when a subject is built to trip it, so none is dead code, but **four cannot be reached by any configured path**: `agent_overreached_schema` (`raw_payloads()` is called from nowhere, so the authority fence has no input), `discovery_partition_violation` (`Corpus.__post_init__` refuses first), `registered_at_unstampable` (the query log is written and never read back, and each scan builds a fresh fence), and `source_inaccessible` (the resolver defaults to `bool(ref)`, so retrieval is never attempted). `provenance_tag_absent` can emit but can never be a first failure, being masked by position 10 on the same trigger. Those four are remediation candidates, not measurement gaps |
| 24 | Cross-market generalisability | BLOCKED | Design segment; classes present in both markets |
| 25 | **Security master and lexicon coverage** | **CLOSED for US** | 10,388 issuers from the SEC's own file, 100% by construction. Other markets outstanding |
| 27 | **Intake budget** | **CLOSED 27 Aug 2026** | `intake_point_budget_s` = 20 s, `intake_subject_budget_s` = 120 s, `budget_retry_max` = 1, registered under `ce576a9fa04a7403`. A ceiling on the cost of looking, not a judgement of the idea: a subject exceeding either is abandoned with `intake_budget_exhausted`, which refuses to score. **The decision is taken once, at capture**, and the ledger records the elapsed time, the budget in force and the verdict; a replay reads that record and never re-times the work, `ReplayedBudget` holding no clock at all. **Abandonments are reported beside row 23's abort-position distribution and never inside it**, a subject that ran out of time not having failed the point it was standing on, and the count is printed in every report including when it is zero. **The honest limit: a ceiling that refuses, not a timeout that interrupts.** A check is run and then measured, so a point that blocks forever is never caught. The three values are governance and were set before any sweep at scale; they are not calibrated against an observed distribution of intake times, because none exists yet, and the first run at scale is what would justify moving them |
| n/a | FX exposure budget (§0 decision) | OPEN | Governance judgement in a stated range |

**Rows 19, 20 and 25 closed on 26 August 2026**, and row 22 closed for US. The registration in the tree now hashes to `701adbd9d48015ed`. *This line previously named `890a80e3a8566837`, which was the hash at the moment those rows closed and stopped being the current hash three re-stamps ago, so it contradicted rows 19 and 20 four lines above whilst reading as the live figure.* The commitments have not moved; the object carrying them has, three times, and **`docs/REGISTRATION_HISTORY.md` is the chain**: one row per hash, the causing field named, each recomputed from the object it was taken over.

**What now stands between the layer and a first sweep** is the archive's opening boundary. `pre_archive` is defined as *material predating* it, so with no boundary declared the mode names nothing. Fixing the archive span is a §13 pre-calibration decision (week-plan task 3.3) and **needs no purchase**: it is a decision about which span the archive will cover, not an acquisition of it. Set `archive_opens` in the registration and the US corpus becomes sweepable.

**One limit, stated rather than implied.** Nothing checks the date of each document in a `pre_archive` corpus folder. The guarantee rests on the operator putting only pre-boundary material there. That is a curation control, not a mechanical one.

---

## §14: open decisions

| Decision | Status | Note |
|---|---|---|
| Default exclusivity construction | **CLOSED v1.13** | `cross_market`, with `disjoint_partition` as a per-class override |
| Overlap tolerance θ | OPEN | Governance in a stated range. Gates directive admission |
| δₘᵢₙ floor | OPEN | Governance. Below it a directive is not worth a session of the segment |
| Account type, cash or margin | OPEN | Currently non-binding; binds before any short-side family or margin simulation. **Note the settlement-bridge cost line arguably binds it already** |
| Control-arm ratio *M/N* | OPEN | Also §13 row 20 |
| Manual-observation capacity per period | OPEN | The scanner will exhaust it rather than approach it |
| UK daily factor series (§0.7b) | OPEN | Standard library ends December 2017, five years before the archive opens |
| ICB point-in-time vintage vendor (§0.7d) | OPEN | Until procured, peer sets are not point-in-time and every pooled estimate carries that qualification |
| The drafted feed-budget amendment (§0.6) | **Available, not taken** | Its shape is fixed in the spec so that taking it cannot be quiet |

## §14: preconditions to signing the freeze

| Precondition | Status |
|---|---|
| Claim provenance: no `recollection` tag on anything feeding a gate, boundary or published table | **OPEN**: Bloomfield and Mitchell & Pulvino remain `recollection` and block the signature |
| Register completeness | CLOSED on §12.7's terms |
| Review harness run to its stopping rule | **OPEN**: v1.14 is a new composition and resets the count; no clean pass recorded, two required |
| Trace exercise (§9.4) to its stopping rule | **OPEN**: the discovery-layer traces of 26 and 27 August are two blocks, both non-evidentiary. Neither includes the primary catalyst family's live filing flow, and no US corpus sweep has run for want of a client |
| Broker commission schedule verified | **OPEN**: §13 row 1 |
| FGR published-version tables against journal pagination | OPEN: upgrades §0.5 rows to `verified_primary` |

---

## Annex A.1: deferred, with predicates

Evaluated and logged continuously; acted on only after the §0.6 instruments report. The full table is in the spec. The rows added in v1.13:

| Capability | Predicate |
|---|---|
| Discovery corpus ingestion adapters for markets outside §0.7(f) | Instruments reported, **and** the manual-observation route has produced at least one registered directive that reached a verdict. Reading a foreign register by hand is not apparatus; a parser for it is |
| Standing automation of the discovery layer | Instruments reported, **and** the control arm has returned *agent selection carries information*. Automation follows demonstrated value, not the reverse |
| Agent-proposed items entering the §3.5 item pipeline | **Refused rather than deferred**, pending an explicit §0 decision |

---

## What is explicitly not next

| Item | Why |
|---|---|
| A fourteenth design round | The learning of the last four versions is that further design rounds do not move the score |
| Running any directive measurement | The query fence closes conditional-return queries on a target population until `registered_at`, and the archive does not exist |
| Any new apparatus | §0.6 armed. The drafted feed-budget amendment stays available and not taken |
| Live capital of any kind | Nothing signed authorises capital. The freeze record's scope, when signed, is the backfill and the two instruments |
