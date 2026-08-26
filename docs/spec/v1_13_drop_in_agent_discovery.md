> **Superseded, 26 August 2026.** This drop-in was landed as **v1.13** of *From Narrative to Null*, not v1.14: v1.13's originally intended content, the commission-dependent recomputation, remains blocked on §13 row 1, and issuing this as v1.14 would have left a gap in a count §0.3 requires to be mechanical. The governing text is the composed manuscript. Every occurrence of "v1.14" below should be read as v1.13, and "v1.14" now names the future commission recomputation. Retained verbatim per §12.6: the superseded wording is the record of what was true when written.

# v1.14 Drop-in: The Agent Discovery Layer

**Proposed drop-in against spec v1.12, drafted 26 August 2026. Not landed; the version count does not move until it is.**

*Sequencing note. The week plan of 17 August reserves v1.13 for the errata, the recomputed commission and the £6,000 clip. This drop-in is drafted as **v1.14** and should land after that version, not folded into it; mixing an architectural change with an errata block makes the v1.13 diff unreadable, and §0.3 counts both regardless of which document carries them.*

*Drafting note. This drop-in contains no em-dashes, in prose or in table cells, per the operator's standing drafting convention; empty cells read `n/a` where §12 and §13 currently use an em-dash. The surrounding manuscript uses the glyph heavily. **The convention adopted here is the one to apply**: v1.14's composition should carry it through §12 and §13, so that one document does not run two conventions.*

---

## Σ.1 addendum: the one place a model selects

*Amends §Σ.1. The existing text stands; this is appended to it.*

**Every claim made for the clerk in §Σ.1 holds on the trading path and stops at the trading path's edge.** The discovery layer specified in §3.7 is the first place in this architecture where a model *selects* rather than classifies, and the paper should say so in the section that makes the opposite claim rather than leaving a reader to discover the exception in §3.7.

The containment is not that the agent is somehow prevented from selecting; it is that **selection cannot reach capital by any route**. A discovery agent's output is a proposal; a proposal that survives ingestion becomes a pointer-tier intake record; a pointer's only reachable output is an observation directive; a directive runs at zero capital; and a surviving directive re-enters as a quantified intake with machine provenance, taking the ordinary route through §3.6.4 and Annex A.1 behind §0.6. Five stages, each of which the manuscript already specifies, and none of which the discovery layer is permitted to shorten. What §3.7 adds is the volume; what it must not add is a shortcut.

---

## 3.7 The agent discovery layer

*New section. Procedure at the intake surface; apparatus in one respect, stated in §3.7.7. The §0.6 test is applied in §3.7.7 rather than asserted here.*

### 3.7.1 What it is, and what it inverts

§3.3 discovers by subscription: enumerable universes are subscribed, every item in them enters, and the funnel decides. That design has one property worth naming before it is changed, which is that **the intake population is not chosen by anything with a view about it**; therefore §7.1's headline association, measured across the entire intake, measures the funnel's depth and nothing else.

The discovery layer inverts the order for the *evidence* lane only. Agents read permitted material, locate candidate mechanisms, and emit them as proposals; each proposal is then run fail-fast through intake ingestion, screened, mapped to a stream and turned into an observation directive. Two things about that sentence are load-bearing. First, the layer feeds §3.6, not §3.5; nothing it produces enters the item pipeline, so the intake population §7.1 measures on is untouched. Second, the agents emit **mechanisms and never episodes** (§3.7.3), so what is selected is a class of event, which is the level at which the published literature also operates.

### 3.7.2 The problem the layer creates, stated before its solution

An agent that goes looking for promising ideas is doing selection conditioned on knowledge of what has already moved, and it is doing so at volume. This is the defect §1 attributes to the model and §3.6.6 relocates to the operator, relocated a third time and made cheap to repeat. It is worse than the operator's version in two respects and better in one.

Worse, because: i) the model's weights contain the price history the system will be evaluated on, and no data split reaches a leak inside the model; and ii) an operator raises perhaps a dozen hypotheses a year, whilst an agent raises that many in an afternoon, so the search widens by an order of magnitude and §6.4's fourth family must see the whole of it.

Better, because the agent's search is **auditable in a way the operator's is not**. Every document it read is a logged query; every proposal it made is a ledger row, including the ones that died at the first ingestion point; and its selection can be compared against a random draw from the same grid, which is an experiment that cannot be run on a person.

### 3.7.3 The exclusivity construction: keeping finding and evaluation disjoint

The design requirement is that the material an agent selects *from* and the material a directive is scored *on* share no observations. The leak does not run through documents; it runs through the underlying price path, so a split by source or by document type is weaker than it appears. Two items describing the same issuer over the same weeks are not independent however different their text.

Four mechanisms, composable, and each of a different kind.

**i) Structural blinding, enforced by schema and by lookup.** The proposal type carries no field for an issuer, an instrument, a ticker or a dated episode, and the intake runner refuses any proposal whose text contains one, discarding the whole proposal rather than stripping the names from it. A proposal may say *clusters of open-market purchases by two or more directors of one issuer settled within five sessions*; it may not say what happened to a named company in a named month.

**The detector's first design was wrong, and the trace is what found it.** It flagged any two-to-five-letter capitalised token and any bare four-digit year, on the stated theory that bluntness was the safe direction: a false positive costs one re-raise, whilst a false negative costs the exclusivity guarantee. Run over thirty-six proposals drawn by discovery agents from live ASX, SEDI and MAR primary sources, it refused **thirty-four of thirty-six, a 94% false-positive rate, with no true positive among the refusals.** It tripped on `ASX`, `TSX`, `MAR`, `SEDI`, `ESMA`, `AFM`, `CIRO`, `UMIR`, `DAX` and on the years inside regulatory citations, for a reason no amount of tuning removes: **a regulator's name and an issuer's name are both proper nouns, and a pattern over an open vocabulary cannot separate them.** A filter refusing 94% of clean input is not a conservative filter; it is a filter that would have silently shaped the search to whatever survived it, which is the endogeneity §3.6.6 exists to contain, arriving through the containment.

**The repair is the architecture's own principle rather than a better pattern.** *The model classifies; the table decides.* A tradeable entity is a member of an enumerable set, namely the security master and the discovery markets' listing lists, so the binding layer is a **lookup against a closed list**. Patterns are retained only where the grammar genuinely is closed: instrument identifiers (ISIN, exchange-prefixed ticker) and legal-form designators, which attach to firms and never to regulators. A seeded regulatory lexicon carries the vocabulary that is not an issuer, and it grows by operator mapping in the same idiom as §3.6.5's stream table, by use rather than by anticipation, each addition recorded.

**Dates are demoted from hits to context.** An episode is an entity bound to a time; a mechanism referring to a review month, a statutory deadline or a regulatory calendar is doing its job. Dates are therefore reported beside an entity hit and never constitute one alone, and removing that single rule removed the largest share of the false-positive rate.

**Without a master the check refuses to score.** Patterns alone are not a fence, so a run with no security master loaded does not fall back to the weaker half; it emits `security_master_unavailable` on every machine-origin proposal. §0.8's asymmetry is still reversed here, but it now buys something: on the same corpus plus six labelled plants, the repaired fence recorded **zero false positives and zero false negatives**, catching every planted issuer name, ticker and identifier whilst passing every regulatory citation.

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

### 3.7.4 Fail-fast ingestion, and the obligation attached to it

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

### 3.7.5 The random-mechanism control arm

*This is the instrument that makes the discovery layer falsifiable, and it belongs in §Σ.4's list beside the placebo and the unconstrained-model control arm.*

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

### 3.7.6 Capacity, queueing and the counting family

A machine raises registrable pointers faster than a short design segment can absorb them, so §3.6.8's admission arithmetic binds immediately rather than eventually. Two rules follow.

**Admission is by smallest registered span first**, ties broken by registration time. This maximises directives per unit of segment; more importantly, neither the agent nor the operator scores merit at admission, since a proposed priority would return ranking to the party that raised the idea.

**Machine-origin drafts queue and may not displace.** Only operator-origin pointers retain the displacement right v1.11 gave them. Without this rule the scanner evicts the operator's own directives simply by out-producing them, which converts a capacity rule into a takeover; (n.b., the displacement summary remains operator-authored under §8, and the implementation refuses a template-rendered one).

**§6.4's fourth family gains a three-tier counter.** A scanner makes the proposal count and the registration count differ by orders of magnitude, so reporting one number would mislead in whichever direction the author preferred. All three are disclosed on every published result: i) **proposals raised**, including every one abandoned at the first ingestion point; ii) **pointers registered**, which is the subset consuming design-segment span and entering the reuse ledger; and iii) **promoted**, which is the subset crossing into an evaluation-scored cohort. None divides anything. Only the third enters the Benjamini-Hochberg step, with its provenance displayed beside its percentile.

### 3.7.7 The §0.6 test, applied

The rule is tested rather than asserted past, and the answer splits in the way P55's answer split.

**Procedure.** The intake runner, the screen, the fences, the reuse ledger and the rejection summaries are of the same class as §9.4's trace harness and §9.5's review harness: they add no gate, no family, no grammar row, no cost tier and no field the funnel reads at decision time. Directives over streams already flowing were settled as procedure by P52 and remain so; a machine raising the pointer changes the counting, not the cost.

**Apparatus, in one respect, and it is the respect that matters.** Cross-market discovery requires *reading* material from markets outside §0.7(f). Hand collection of that material under §3.6.5's manual-observation protocol is not apparatus, being of the same class as §9.4's tracing. **A production ingestion adapter for a discovery corpus is apparatus**, however modestly it is described, and takes an Annex A.1 row with its dependency named. The discovery agent itself, being new code that makes model calls at volume, likewise takes an Annex A.1 row for its **automation**, on the same terms as the literature lane's Tier 2 row: automation follows demonstrated value and not the reverse.

**What this permits before the instruments report.** An operator running sweeps over hand-assembled corpora, at zero capital, producing directives that measure on streams already subscribed. **What it does not permit**: subscribing to a discovery corpus feed, and running the layer as a standing automated process. The asymmetry will be irritating in precisely the cases that feel most promising, which is the rule working rather than failing.

---

## 3.6.2 amendment: the origin enum

*Amends P50's enum.*

`origin ∈ {paper, operator, agent, random_control}`. The two machine origins are siblings by construction, the control arm being identical to the agent arm in every respect except the thing under test. Evidence produced by either carries `agent_generated` provenance, routing advisory-only under §3.6.3 check 5 exactly as `self_generated` and `single_study` do.

## 3.6.6 amendment: agent-discovery endogeneity

*Joins §6.3's catalogue as the third sibling of §3.4, after paper selection and operator hypothesis.*

The containment is six rules and, as with the operator's, none of them is a solution: i) structural blinding by schema, refusing episodes; ii) partition or market disjointness, recorded per directive in `scoring_mode`; iii) the query fence extended to machine reads; iv) the import fence, checked at process start; v) every proposal counted, including those abandoned at the first ingestion point; and vi) the random-mechanism control arm, which is the only one of the six that *measures* rather than *constrains*.

**What is unreachable, stated plainly.** The weights are not partitionable, so the agent's recollection of price history cannot be fenced, only diluted by requiring mechanism-level emission. This is the same defect §1 attributes to the model and §3.6.6 relocates to the operator, and it is unsolved in all three locations.

## 3.6.8 amendment: registration inputs the machine may not supply

*Amends step 4. The four parts are unchanged; what changes is who may supply them.*

Neither an agent nor any automated process may supply δₘᵢₙ, *n*ₘᵢₙ, the registered sign, or a ratified pre-mortem. An agent may **draft** a pre-mortem, which is recorded with `author = agent, ratified = false` and blocks registration until the operator ratifies or rewrites it; the ledger records the author beside the text, per §8.

**The consequence, and it is the design working rather than a defect.** The scanner's steady-state output is a queue of registration-ready drafts blocked on exactly the two things only the operator may supply. **Widening the search does not shorten the fence**, and a layer that produced registered directives without the operator would have moved the pass condition to the party that raised the idea.

Registration is deliberately **not** fail-fast, and reports every missing part at once. Fail-fast exists to stop spending compute on an idea that has already died; registration spends no compute and its output is a worklist for a person, and handing someone one blocker at a time when four are known is a worse deliverable rather than a purer one.

---

## 12.1 (proposed) v1.13 → v1.14

| # | Change | Kind (§3.6.4) | Sections | Parameter object |
|---|---|---|---|---|
| P66 | **Agent discovery layer specified.** Agents locate class-level mechanisms in permitted corpora and emit proposals; proposals run fail-fast through intake ingestion into the §3.6 evidence lane and never into the §3.5 item pipeline | procedure (see P72) | §3.7, §Σ.1 | yes, ordering and fences |
| P67 | **Fail-fast ingestion, with its obligation and its antidote.** Eleven ordered intake points and eleven ordered observation points, each with a named reason code; every abort writes a code, a set size and a rendered §8 summary; a pre-registered audit fraction runs the full panel so the reason-code distribution is not censored. Closes the `source_inaccessible` gap recorded on 17 August | restriction | §3.7.4, §3.6.3, §7.2 | yes |
| P68 | **The exclusivity construction.** `scoring_mode ∈ {cross_market, disjoint_partition, forward_only}` recorded per directive and printed beside every verdict; entity fence by schema; import fence over the discovery path; query fence extended to machine reads. Optional fourth archive partition, **Discovery**, with Gate 0 asserting separation as it does for injections | restriction | §3.7.3, §7.5, §0.7a | yes |
| P69 | **Random-mechanism control arm**, with a pre-registered seed, ratio and kill criterion in §3.6.8's three-verdict idiom. Joins §Σ.4's list of falsification instruments. *A layer that widens the search must be falsifiable on its own terms, and this is the only rule in P66 to P73 that measures rather than constrains* | restriction | §3.7.5, §Σ.4, §13 | yes |
| P70 | **Origin enum extended** to `{paper, operator, agent, random_control}`; machine-origin evidence carries `agent_generated` provenance and routes advisory-only under check 5 | restriction | §3.6.2, §3.6.3 | yes, enum |
| P71 | **Capacity discipline.** Admission by smallest registered span first, ties by registration time; machine-origin drafts queue and may not displace; §6.4's fourth family gains a three-tier counter (proposed, registered, promoted), all disclosed and none dividing anything | restriction | §3.6.8, §6.4, §9.2 | yes |
| P72 | **§0.6 applied and split.** The runner, screen, fences, ledger and summaries are procedure. A production ingestion adapter for a discovery corpus, and standing automation of the layer, are **apparatus** and take Annex A.1 rows. Hand-assembled corpora under the manual-observation protocol are not | n/a | §3.7.7, §0.6, Annex A.1 | no |
| P73 | **Agent-discovery endogeneity** added to §6.3's catalogue as the third sibling of §3.4, with six containment rules and the unreachable residual stated | n/a | §3.6.6, §6.3, §10 | no |
| P75 | **Entity fence rebuilt as a lookup, after a trace refuted its first design.** A specification trace over 36 proposals drawn by discovery agents from live ASX, SEDI and MAR primary sources refused 34, a 94% false-positive rate with no true positive among them: a pattern over an open vocabulary cannot separate a regulator's name from an issuer's. The binding layer becomes a lookup against the security master and the discovery markets' listing lists; patterns survive only for closed grammars (instrument identifiers, legal-form designators); a seeded regulatory lexicon grows by operator mapping and is ledgered; **dates become context and never a hit alone**; and a missing master emits `security_master_unavailable` rather than falling back to the weaker half. Repaired fence: 0% and 0% on 42 labelled proposals. *This is the trace doing the job §9.4 specifies, on a new surface, at the first attempt* | restriction | §3.7.3, §13 rows 21 and 25, §10 | yes |
| P74 | **Default exclusivity construction settled as `cross_market`**, closing what P68 left as a §14 open decision. `disjoint_partition` is retained as a per-class override; a class must still be positively declared discoverable, so the default settles *which* construction applies and never *whether* one exists. The generalisability assumption the default buys is measured by §13 row 24 rather than merely disclosed, and a control-arm ratio of zero is refused rather than floored | restriction | §3.7.3, §3.7.5, §13, §14 | yes |

**What v1.14 does not do.** It subscribes to nothing, admits no family, creates no grammar row, supplies no parameter, sizes no position, and lets nothing it raises act on capital. It moves no idea into the item pipeline. It does not permit an agent to register a directive, because registration requires two things only the operator may supply.

---

## 13 (proposed) additional rows

| # | Quantity | Sample | Rule | Deadline |
|---|---|---|---|---|
| 19 | **Control-arm separation δ and *n*ₘᵢₙ** | Design segment, both arms | The separation below which the discovery layer is refuted; committed **before the first sweep**, in the units the measurement reports | Before the first sweep |
| 20 | **Control-arm ratio *M/N* and seed** | n/a, governance | Fixed before the first sweep, strictly above zero, and recorded with every draw; a control redrawn after the treatment's result is known is not a control | Before the first sweep |
| 21 | **Entity-fence error rates** *(revised, P75)* | 200 hand-labelled proposals | Share of clean class-level mechanisms refused, and share of episode-level proposals passed, reported separately and each with its n. **A provisional reading exists**: 42 labelled proposals, being 36 drawn by discovery agents from live ASX, SEDI and MAR sources plus 6 plants, returned 0% and 0% against the repaired fence and 94% and 0% against the pattern-only fence it replaced. Recorded as a reading, not as the calibration | Design segment |
| 25 | **Security master and lexicon coverage** *(new, P75)* | Discovery-market listing lists | Share of listed entities in each discovery market present in the master, since the fence's binding layer is a lookup and an absent issuer is an undetectable episode. Below a stated floor the market is not readable for discovery | Before the first sweep |
| 22 | **Discovery corpus roster, partition assignment and discoverable classes** | n/a, fixing | Named corpora, their markets, their partition and the retrieval route, together with the event classes positively declared discoverable and the construction each uses. A pre-calibration fixing in the sense of §13's existing list | Before the first sweep |
| 23 | **Intake abort-position distribution** | Audit stream, full panel | Distribution of first-failure position per surface. A surface whose failures cluster at position one is a surface whose later points have never been exercised, which is §9.4's failure class on a new surface | Design segment |
| 24 | **Cross-market generalisability** *(new, P74)* | Design segment, classes present in both the discovery market and §0.7(f)'s universe | Sign agreement and magnitude ratio of the same mechanism measured on each market, reported per class. **Coverage is partial by construction**: it is computable only where the class occurs in both, so a class absent from the home market leaves the assumption untested and the directive says so. Kill criterion written before the data is examined; sign disagreement at Gate 6's minimum count refuses `cross_market` for that class and routes it to `disjoint_partition` or `forward_only` | Design segment |

## 14 (proposed) additions

| Field | Addition |
|---|---|
| **Closed in v1.14** | Default exclusivity construction: **`cross_market`**, on the arithmetic in §3.7.3, with `disjoint_partition` retained as a per-class override and §13 row 24 measuring the assumption the default buys |
| Open, decisions | Control-arm ratio *M/N*, in a stated range and strictly above zero; manual-observation capacity per period, which the scanner will exhaust rather than approach |
| Open, ledger | Discovery corpora listed individually with market, partition and retrieval route; the three-tier family-4 counter published beside the reuse ledger |
| Precondition, fences | The import fence must pass at process start, not merely in the test suite. A run whose fence check fails is a run whose output is inadmissible, not a run with a warning |
| Precondition, control arm | δ, *n*ₘᵢₙ, ratio and seed registered before the first sweep, the ratio strictly above zero. A layer whose kill criterion is written after its first result is not falsifiable, and a layer run without a control arm has no kill criterion at all |

## 10 (proposed) additional limitations

**The discovery layer is the one place a model selects, and its containment is architectural rather than epistemic.** Selection cannot reach capital by any route, because a pointer's only output is a directive and a directive runs at zero capital; nevertheless the layer chooses what is investigated, and what is never investigated is invisible to every instrument in §7.

**The exclusivity guarantee covers data and not knowledge.** Partitions, markets and import fences are enforceable and are enforced; the weights are not partitionable. Mechanism-level emission lowers the resolution at which recalled price history can be exploited and does not remove it.

**A positive control-arm result means the agent beats a random draw, and means nothing stronger.** An agent whose recollection of price history is genuinely informative would also beat a random draw, and the instrument cannot separate that from skill. It is nevertheless the strongest available claim, and it is stronger than anything that can be said about the operator's own search.

**The default construction rests on an assumption that is only partly measurable.** `cross_market` holds that a mechanism observed under one market's disclosure regime holds under another's. §13 row 24 tests it wherever a class occurs in both, which is not everywhere; a class present only in the discovery market leaves the assumption untested, and the directive carries that on its face. Brochet's disclosure-speed mechanism argues the assumption is weakest precisely where regimes differ most, which is the same territory the row is least able to cover.

**The entity fence is only as complete as the security master behind it.** Its binding layer is a lookup, so an issuer absent from the master or from a discovery market's listing list is an episode the fence cannot see. §13 row 25 measures that coverage and §13 row 21 measures both error rates. Neither reaches a paraphrase that identifies an issuer without naming it, and nothing in this design does.

**Volume changes what the denominator means.** §6.4's fourth family now grows when a machine has an idea, at a rate no operator could match. It divides nothing, so it costs no statistical power; it does consume design-segment span, and a short segment is the binding constraint on the layer from its first day rather than eventually.

## Annex A.1 (proposed) additional rows

| Capability | Predicate |
|---|---|
| **Discovery corpus ingestion adapters** for markets outside §0.7(f) | The §0.6 instruments have reported, **and** the manual-observation route has produced at least one registered directive that reached a verdict. Reading a foreign register by hand is not apparatus; a parser for it is |
| **Standing automation of the discovery layer** (scheduled sweeps, unattended) | The §0.6 instruments have reported, **and** the control arm (§3.7.5) has returned *agent selection carries information*. Automation follows demonstrated value and not the reverse, on the same terms as the literature lane's Tier 2 row |
| **Agent-proposed items entering the §3.5 item pipeline** | Refused rather than deferred, pending an explicit §0 decision. It would re-base §7.1's headline on an agent-selected population, and the association would then measure the agent's taste rather than the funnel's depth |
