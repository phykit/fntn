# Open items

The live register. §13 holds every quantity requiring measurement or lookup; §14 holds the decisions and the freeze preconditions; Annex A.1 holds deferred capability behind predicates. **Nothing pends elsewhere**, and the spec's own linter tests that claim mechanically.

Status vocabulary: `OPEN` not started, `BLOCKED` waiting on a named dependency, `PROVISIONAL` a reading exists but not the calibration, `CLOSED` done and recorded in the spec.

---

## The binding path, in order

Progress is not gated on design quality. Thirteen versions, a linter, a reference implementation, a literature lane and a discovery layer have all been built; the score does not move because **nothing has been measured**. Five steps, and the order is not negotiable:

1. **Verify the commission** (§13 row 1). Every break-even denominator in the paper inherits it. Until it closes, the clip, the feasible band, the reachability matrix, §5.4.4 and the whole break-even table are bracketed.
2. **Fix the pre-calibration fixings**: archive identity and span, partition boundaries, universe constituents, source roster, borrow snapshot date.
3. **Settle the §14 governance decisions** that gate directive registration: θ, the δₘᵢₙ floor, account type.
4. **Run the trace harness** (§9.4) to its stopping rule, including a minimum sample of the primary catalyst family's live filing flow.
5. **Populate §13, hash the parameter object.** That act creates **frozen design 1**. Then the retrospective deployment, and §7.1 and §7.5 return a verdict.

Until step 5, no version may add capability (§0.6).

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
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | **CLOSED 26 Aug 2026** | δ = 50 bps, *n*ₘᵢₙ = 30. Registration `890a80e3a8566837`, stamped 22:54 UTC, before any archive exists |
| 20 | **Control-arm ratio *M/N* and seed** | **CLOSED 26 Aug 2026** | Ratio 1.0 (matched arms), seed 20260826 |
| 21 | Entity-fence error rates | **PROVISIONAL** | 200 hand-labelled proposals. A reading of 42 exists: 0% / 0% repaired, 94% / 0% on the pattern-only fence it replaced |
| 22 | **Discovery corpus roster, partitions, discoverable classes** | **PART CLOSED** | US declared (`pre_archive`). UK, AU, EU and NZ profiled but not registered: each needs a listing file with a known total |
| 23 | Intake abort-position distribution | **PROVISIONAL** | Audit stream at scale. A reading of 42 exists: every failure at position 3, so nine intake points remain unexercised on real material |
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
| Review harness run to its stopping rule | **OPEN**: v1.13 is a new composition; no clean pass recorded, two required |
| Trace exercise (§9.4) to its stopping rule | **OPEN**: the discovery-layer trace of 26 August is a first block, non-evidentiary, and does not discharge this |
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
