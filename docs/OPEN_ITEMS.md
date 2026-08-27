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
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | **CLOSED 26 Aug 2026** | δ = 50 bps, *n*ₘᵢₙ = 30. **The commitment is the 26 August one and has not moved**: both values were stamped at 22:54 UTC on 26 August 2026, before any archive exists, so the criterion was written blind and remains so. The registration OBJECT carrying them has been re-stamped since, most recently to `b8dd61e7eea6898e` on 27 August 2026, **because a fence repair added `rulebook_stopwords` to the parameter object, not because δ or *n*ₘᵢₙ changed.** A re-stamp caused by a different field is a new hash on the same commitment; a re-stamp caused by this field would be a new commitment, and the two are distinguished here so that a reader cannot mistake one for the other. Earlier hashes on the same δ and *n*ₘᵢₙ: `890a80e3a8566837`, `a06400ef28ebb54c` |
| 20 | **Control-arm ratio *M/N* and seed** | **CLOSED 26 Aug 2026** | Ratio 1.0 (matched arms), seed 20260826. **The commitment is the 26 August one and has not moved**, fixed before the first sweep and before any archive exists, so the arm cannot be redrawn on a known result. Carried unchanged through the 27 August re-stamp to `b8dd61e7eea6898e`, which **was caused by a fence repair adding `rulebook_stopwords` to the parameter object and by nothing about the control arm.** Earlier hashes on the same ratio and seed: `890a80e3a8566837`, `a06400ef28ebb54c` |
| 21 | Entity-fence error rates | **PROVISIONAL, corrected 27 Aug 2026 (spec P77, P79 and P80)** | 200 hand-labelled proposals, under registration **`b8dd61e7eea6898e`** stamped 27 Aug 2026, which is the first registration whose hash covers the fence's own vocabulary. **The 0% / 0% previously recorded here was not reproducible** and is withdrawn: it was measured against six probes defined inline in a shell heredoc that was never committed. The labelled set is now in the tree at `docs/labelled_proposals.json` (36 class-level mechanisms drawn by agent sweep, 6 authored probes) and the reading is locked by tests. **The two arms are of two kinds and are not reported as one.** The drawn arm is a rate: **0 of 36 refused (0%)**. The probe arm is coverage and carries no percentage, the six being chosen rather than sampled, one per named route: **5 of 6 routes closed, the open one a title-case bare ticker**. Before the ticker rule the same 36 gave **3 refused (8%)**, on `Note`, `T` and `It`. **Measured against the corpus rather than the labelled set, the fence's two remaining genuine false positives are closed** (P80): `Joint`, a listed issuer whose one-word name is ordinary English, by a lexicon row; and `Trust Holdings`, Rule 16a-8's own heading, by narrowing the designator branch to a proper-noun-shaped lead absent from a registered rulebook stopword set. Corpus hits fall from 5 distinct / 41 to 3 / 39, the residue being `API`, `BlackBerry` and `Opera`, which are row 22's corpus-fetch decision and not fence defects. Labels are `model_clerk`, not hand labels, and operator ratification is outstanding |
| 22 | **Discovery corpus roster, partitions, discoverable classes** | **PART CLOSED** | US declared (`pre_archive`). UK, AU, EU and NZ profiled but not registered: each needs a listing file with a known total. **Fetch-time chrome strip landed 27 Aug 2026**: `scripts_fetch_us_corpus.sh` removes `<nav>`, `<header>`, `<footer>` and any element whose class or id contains nav, menu, sidebar, related, footer or breadcrumb before the file is written, and `_manifest.tsv` carries `raw_bytes` beside `bytes` so what was discarded is on the record. 154,132 of 638,883 bytes removed, 24%, integrity check passing with `MIN_BYTES` applied to the stripped size. **It did not clear `API`, `BlackBerry` or `Opera`**: those sit in an HTML comment and an inline `<script>` in `<head>`, which is neither `<header>` nor an element with a matching class or id, and the fence still refuses all three once per document. Widening the strip to `<script>`, `<style>` and comments would reach them and is an open operator decision on this row |
| 23 | Intake abort-position distribution | **PROVISIONAL, corrected 27 Aug 2026** | Audit stream at scale. The 26 August reading, every failure at position 3, was taken under a **wider exclusivity map than the registration declares**. Re-run under the registered four classes (`docs/trace_report_2026-08-27.txt`): 5 at position 3, **8 at position 9**, deepest failure **9 of 12**. Of the remaining ten points, every branch fires when a subject is built to trip it, so none is dead code, but **four cannot be reached by any configured path**: `agent_overreached_schema` (`raw_payloads()` is called from nowhere, so the authority fence has no input), `discovery_partition_violation` (`Corpus.__post_init__` refuses first), `registered_at_unstampable` (the query log is written and never read back, and each scan builds a fresh fence), and `source_inaccessible` (the resolver defaults to `bool(ref)`, so retrieval is never attempted). `provenance_tag_absent` can emit but can never be a first failure, being masked by position 10 on the same trigger. Those four are remediation candidates, not measurement gaps |
| 24 | Cross-market generalisability | BLOCKED | Design segment; classes present in both markets |
| 25 | **Security master and lexicon coverage** | **CLOSED for US** | 10,388 issuers from the SEC's own file, 100% by construction. Other markets outstanding |
| n/a | FX exposure budget (§0 decision) | OPEN | Governance judgement in a stated range |

**Rows 19, 20 and 25 closed on 26 August 2026**, and row 22 closed for US. Registration hash `890a80e3a8566837`.

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
