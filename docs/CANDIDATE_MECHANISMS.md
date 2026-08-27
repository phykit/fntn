# Candidate mechanisms

**27 August 2026.**

## WHAT THIS FILE IS, AND WHAT IT IS NOT

**It IS** a set of **class-level** mechanisms located by an agent reading
registered regulatory corpora, **passed through four fences**, and **screened
against registered constraints** by the achievability lens.

***It is NOT evidence that any of them works.***

- **No design segment exists.** Nothing here has been measured against price
  history of any kind.
- **Zero backtests. Zero frozen designs. Zero trades.**
- **Every entry is at ZERO CAPITAL**, and §13 row 31, the
  promotion-to-live-capital predicate, is **BLOCKED with its blanks empty by
  operator decision.**
- **The achievability lens reports; it refuses nothing.** A mechanism meeting
  nine criteria has been *screened*, not *tested*.

***A reader must not be able to mistake this list for results. It is a list of
things that have not been ruled out yet.***

---

## THE FINDING THAT GOES ABOVE THE LIST

***The control arm is not indistinguishable from the agent arm. It BEAT it,
three drafts to nought, and the comparison as constructed cannot be read as a
verdict on the agent.***

**On the run of record**, 27 August 2026:

| | Agent arm | Control arm |
|---|---|---|
| Raised | **6** mechanisms, plus one call that returned no array at all | **6** drawn |
| Reached the operator queue | **0** | **3** |
| Killed by | `scoring_mode_unsatisfiable`, all six | `duplicate_of_open_pointer`, three of six |
| Criteria met on the achievability lens | **0**, and all nine unscorable | **0**, and all nine unscorable |

***And the reason the agent arm lost is a STRUCTURAL ASYMMETRY IN THE
INSTRUMENT, not a fact about the agent.*** **All six agent proposals were
classified `unclassified` by the clerk**, which is what the system prompt
instructs where no row of the fixed table fits, and `unclassified` is absent
from §13 row 22's `discoverable_classes`, so intake refuses it with
`scoring_mode_unsatisfiable`. **The control arm draws its class FROM the
registered grid by construction**, so ***it can never emit `unclassified` and
therefore can never fail the check that killed the entire agent arm.***

> **The two arms are not running the same gauntlet.** One is scored against a
> class table it can miss; the other is drawn from that table. *A comparison in
> which only one arm can fail a given check is not the comparison §13 rows 19
> and 20 register, and reading three-nil off it as evidence about the discovery
> layer would be reading a rigged race.*

**This is recorded as a finding and NOT acted on.** Repairing it means either
admitting `unclassified` as a discoverable class, which is a §13 row 22 change,
or drawing the control arm from the same class distribution the agent produces,
which changes what the control arm IS. **Both are operator decisions and both
are `§12.1` versions.** Written as a pending block in `docs/OPEN_ITEMS.md`.

**§13 row 19's verdict is `undetermined_at_budget` and is not computed here.**
*n*ₘᵢₙ is 30 per arm and this run produced six and six. **Six is not thirty**,
and δ = 50 bps is a separation between *measured effects* that do not exist,
there being no design segment. *Nothing on this page is a reading against row
19's criterion, and the criterion has not been exercised.*

---

## HOW MANY MECHANISMS SURVIVED THE ACHIEVABILITY LENS

> ***None met a single criterion. None failed one either. The lens returned
> NINE UNSCORABLES on every mechanism in both arms, and `unscorable` may never
> be read as `met`.***

***And this is a structural finding about the wiring, not a property of what
was located.*** The lens reads nine declared fields: direction, venue, minimum
share price, liquidity floor, whether the edge survives to the next open,
claimed effect in basis points, holding period, input obtainability, and
backtestability.

**The discovery layer is FORBIDDEN from declaring the ones that matter.** The
system prompt's rule 3 is explicit: *do not state an expected effect size, a
horizon, or a threshold*, and the authority fence exists to discard a proposal
that does, with `agent_overreached_schema`. **So the lens's `claimed_effect_bps`
and `holding_period_sessions` criteria read fields that a conforming proposal
cannot carry**, and the remaining seven read fields the proposal schema has no
column for at all.

> **The achievability lens was written for §3.5 ITEMS, which declare claims.
> The discovery layer emits class-level POINTERS, which by construction do
> not.** *Pointing it at the discovery layer's output produces nine unscorables
> every time, for every mechanism, for ever, and no run of any size changes
> that.*

**What follows, stated plainly:** *the lens screened nothing.* B4's instruction
to record the lens criterion by criterion is carried out below in full, and
what it records is nine unscorables per row. **The ninth is separately
unscorable for a second reason** — `backtestable` needs an archive and §13 row
35's coverage fraction, and neither exists — **so even a mechanism that
declared all eight of the others could not reach nine today.**

*This is written as a finding and the lens is NOT changed. A lens rewritten
once its output is known is a lens chosen to flatter its output, which is 3f's
rule applied to the instrument instead of the schema.*

---

## WHAT WAS SWEPT, WHAT IT COST, AND EVERY RUN THAT HAPPENED

**Five sweeps were attempted on 27 August 2026 and all five are recorded**,
because reporting the last one alone would be selection over runs.

| Run | Calls | What happened | Is it the record? |
|---|---|---|---|
| 0 | 2 | **Crashed.** The loader called `.get` on a payload element that was a bare string: `AttributeError` part-way through the second family. The first family's cost was measured and the rest was lost | no |
| 1 | 3 | Ran. **One family conformed** and returned 4 proposals; two returned `proposals` as a *string*, which the repaired loader walked **character by character**: 8,476 refusals, a funnel reporting **8,484 proposals raised**, and a denominator inflated four orders of magnitude | no |
| 2 | 3 | Ran. **All three families returned a string.** 3 proposals raised, 3 refused, 0 mechanisms | no |
| 3 | 3 | Ran under the corrected counting. All three conformed: **17 agent, 17 control, 7 agent drafts** | no |
| **4** | **3** | Ran under the per-family instrumentation. **6 agent, 6 control, one non-array payload, 3 control drafts and 0 agent drafts** | ***YES*** |

***Why run 4 and not run 3, decided BEFORE run 4's content was known.*** The
run of record was fixed as **the first run under the per-family instrumentation**,
because a book that cannot be attributed to a family cannot answer B3. *Run 3
was the richer result and it is not the record, which is the point of fixing
the rule first: a rule chosen after the results are known is a rule chosen to
select among them.* **Run 3 is reported in full above and its numbers are not
merged with run 4's.**

### The variance, which is itself a finding

**Agent proposals across the four runs that completed: 4, 3, 17, 6.**
**Agent drafts reaching the queue: 0, 0, 7, 0.** *Same corpora, same prompt,
same pin, same registration hash.*

**Temperature zero is no longer available** — `messages.create` removed the
parameter and the current models reject sampling parameters — and the client's
docstring already records that two sweeps over identical material may return
different proposals. ***What it did not record is the magnitude.*** A layer
whose located population varies between four and seventeen between consecutive
runs cannot support a funnel-depth statement, and **§7.1's headline is a
funnel-depth association.**

### The cost, measured where it was measured and estimated where it was not

| | |
|---|---|
| Model | `claude-sonnet-5`, §13 row 39, registration `bbfc50c781de67b5` |
| Calls, all runs | **14** |
| Input tokens, all runs | **303,093**, exact. Input is deterministic here: 31,389 + 16,408 + 16,027 per full run over the three corpora |
| Output tokens, measured | **13,380** over 9 calls |
| Output tokens, NOT measured | **5 calls**, in runs 0 to 2, which had no end-of-run accounting. *That instrumentation is the reason run 4 exists* |
| **Measured floor** | **USD 0.7400** |
| Estimate for the five unmeasured outputs | ~6,900 tokens at the measured mean of 1,371 per call, **~USD 0.07**, ***marked an estimate and not added to the floor*** |
| **What ONE FULL SWEEP costs** | ***USD 0.1611 measured on run 4; USD 0.1764 on run 3*** |
| Balance | **NOT ESTABLISHED.** The models endpoint does not consult it, and no message call has returned a 400 |

**Rate provenance, stated because a cost figure without one is a guess wearing a
decimal point:** USD 2.00 in and 10.00 out per million, list price, read from a
reference table stamped `cached: 2026-06-24`. **`named, unread` under §0.5.**

### The cost guard, which fired correctly and was never binding

```
COST GUARD, after the first family and before the rest.
measured: 1 model call(s) at claude-sonnet-5
  input tokens          : 31389
  output tokens         : 2256
  cost at list price    : USD 0.0853
  families                 : 3
  PROJECTED for all 3      : USD 0.2560
  control arm              : USD 0.0000, and this is measured, not assumed:
                             the draw takes the grid and the registered seed
                             and makes no model call.
  ceiling                  : USD 4.00
  within the ceiling; continuing.
```

**The projection was 0.2560 and the outturn 0.1611**, so the guard
over-projected by 59%. *It projects the remaining families at the first
family's cost and they are smaller, which is stated in its docstring as an
order-of-magnitude guard. It over-projects, which is the direction a guard
should err in.*

---

## THE LIST

**3 mechanisms.** ***0 AGENT-ORIGIN. 3 CONTROL-ARM-ORIGIN.***

*Read the finding above the list before reading the list. Three control draws
reaching the queue whilst no agent proposal does is not a result about the
discovery layer; it is a comparison in which only one arm could fail the check
that decided it.*

| # | Mechanism | Family | Origin | Criteria met | Failing criteria |
|---|---|---|---|---|---|
| 1 | a mechanism drawn from the buyback cell | buyback | **CONTROL-ARM-ORIGIN** | **0 of 9** | *none failed; all nine UNSCORABLE* |
| 2 | a mechanism drawn from the earnings_event cell | earnings_event | **CONTROL-ARM-ORIGIN** | **0 of 9** | *none failed; all nine UNSCORABLE* |
| 3 | a mechanism drawn from the major_holdings_change cell | major_holdings_change | **CONTROL-ARM-ORIGIN** | **0 of 9** | *none failed; all nine UNSCORABLE* |

**Ordered by criteria met, descending, then alphabetically by mechanism. All
three tie at nought, so the order here is entirely the alphabetical tie-break
and it ranks nothing.**

### Entry 1, against the published schema

| Field | Value |
|---|---|
| **Mechanism, class-level, naming no issuer** | *a mechanism drawn from the buyback cell.* ***A placeholder, and it is reported as one.*** The control arm draws a grid CELL, not a described mechanism; §3.7.5 makes it a random draw over the registered grid precisely so that it carries no content the agent could have supplied |
| **Family and corpus** | family `buyback`; **corpus `major_holdings_change`**, and the mismatch is structural: a control draw is filed against the first registered corpus because it was read from no corpus at all. *`origin` is what separates the arms, never `corpus_id`* |
| **Fences passed** | import **clean** (`assert_import_fence` on `fntn.scanner.discovery`); query **0 refusals**, 3 mechanism-level queries logged; entity **0 refusals**, US master at 100.0% coverage over 10,388 rows; authority **0 refusals** |
| **Reason codes NOT triggered** | `proposal_names_entity`, `discovery_partition_violation`, `agent_overreached_schema`, `security_master_unavailable`, `event_definition_absent`, `measured_on_absent`, `registered_at_unstampable`, `source_inaccessible`, `provenance_tag_absent`, `claim_provenance_recollection`, `population_not_replayable`, `intake_budget_exhausted` |
| **Achievability, criterion by criterion** | `long_only` **unscorable**, no direction declared. `us_listed` **unscorable**, no venue. `min_share_price` **unscorable**, none declared; the threshold it would be read against is USD 12.09. `min_liquidity` **unscorable**; the floor is USD 4,031,250 of median daily notional. `actionable_at_next_open` **unscorable**; §13 row 13 would measure it and is BLOCKED. `effect_exceeds_delta_min` **unscorable**, no effect declared. `holding_period_admissible` **unscorable**, none declared. `obtainable_without_purchase` **unscorable**, inputs not declared. `backtestable` **unscorable**, *and separately so: the archive does not exist and §13 row 35's coverage fraction is unset*. ***0 met, 0 failed, 9 unscorable*** |
| **Fixed cost at §13 row 1** | **NOT EVALUABLE**, and this is a refusal rather than a blank. The schedule is `20,000/V + 2.01/p + 0.206` below `V = 200p` and `102.01/p + 0.206` above; **both are functions of share price `p` and notional `V`, and the mechanism declares neither** |
| **Clears δₘᵢₙ at 15.7 bp?** | ***CANNOT BE ASKED.*** No effect is claimed, and the system prompt forbids claiming one |
| **Origin** | ***CONTROL-ARM-ORIGIN***, drawn at ratio 1.0 from seed 20260826, both registered 26 August 2026 before any archive existed |
| **What would falsify it, stated BEFORE any measurement** | *The control arm is refuted as a whole and not entry by entry.* **§13 row 19's criterion, registered blind on 26 August 2026: if the agent arm and the control arm separate by less than 50 bps on a measured effect, over at least 30 observations per arm, the discovery layer is refuted.** Below 30 the verdict is `undetermined_at_budget` and never a quiet pass. ***This run produced six per arm, so the criterion is not met and not missed; it is not yet exercised.*** |

### Entries 2 and 3

**Identical in every field to entry 1** except the family, the drawn cell, and
the directive's mapped stream: entry 2 is `earnings_event`, stream *RNS results
categories; earnings calendars*, status `subscribed`; entry 3 is
`major_holdings_change`, stream *RNS TR-1; EDGAR 13D/G full text*, status
`category_filter`. **Written out rather than tabulated three times, because
three identical tables would suggest three findings where there is one.**

---

## WHAT THE AGENT ARM ACTUALLY EMITTED, since none of it reached the list

***Recorded because a book of nought agent-origin entries is uninformative and
the six proposals behind it are not.*** All six were refused at intake point
`scoring_mode_unsatisfiable`, all six from the `buyback` and `earnings_event`
corpora, and **all six were classified `unclassified` by the clerk.**

| Corpus | What the clerk emitted | Source it cited |
|---|---|---|
| `buyback` | monthly issuer disclosure of aggregate open-market repurchases, including shares bought outside an announced programme and residual authorised capacity | 17 CFR 229.703 (Item 703) |
| `buyback` | restrictions on a distribution participant bidding for a covered security during a pre-offering restricted period | 17 CFR 242.101 |
| `buyback` | the same restriction applied to issuers and selling security holders during a distribution | 17 CFR 242.102 |
| `buyback` | regulated stabilisation bidding during a distribution, with price ceilings tied to independent bids | 17 CFR 242.104 |
| `buyback` | clusters of issuer repurchases satisfying the safe harbour's broker, timing, price-ceiling and volume conditions | 17 CFR 240.10b-18 |
| `earnings_event` | *`unclassified`, with no definition offered* | 17 CFR 249.308, 229.10, 243.100-103, 244.100-101, 240.13a-11 |

***THE OBSERVATION, and it is about the corpus rather than the clerk.*** **Five
of the six describe a REGULATION rather than a MECHANISM.** *They are accurate
descriptions of what the documents say*, and the documents are regulatory text:
Item 703, Regulation M and Rule 10b-18. **A clerk told to read a rulebook and
emit mechanisms returns the rules**, and it classified them `unclassified`
because the fixed table has no row for *a safe harbour exists*.

**Whether that is a corpus-selection defect is not decided here.** §13 row 22
registers these three corpora and the registration was stamped before the
sweep. *Changing what the layer is shown because of what it returned is fitting
the input to the output, and it takes an operator decision and a `§12.1` row.*
Written as a pending block in `docs/OPEN_ITEMS.md`.

**The sixth is different and worse: it emitted the literal string
`unclassified` as its own event definition.** *That is a conforming reply
carrying nothing, and the intake point that refused it refused it for the right
reason by accident: it was refused on its CLASS, and its DEFINITION is empty in
a way `event_definition_absent` did not catch because the string is not empty.*
**Recorded, not repaired.**

---

## THE PAYLOAD DEFECT, which is the largest single finding of the batch

> ***A forced tool call is not a validated tool call. In 8 of 14 calls the
> model returned `proposals` as a JSON STRING rather than an array.***

| Run | Families whose payload conformed | Families that returned a string |
|---|---|---|
| 0 | 1 of 2 reached | — (crashed before it could be told) |
| 1 | 1 of 3 | **2 of 3** |
| 2 | 0 of 3 | **3 of 3** |
| 3 | 3 of 3 | 0 |
| 4 | 2 of 3 | **1 of 3** |

`tool_choice={"type": "tool", "name": "emit_proposals"}` compels the model to
call the tool. **It does not compel the arguments to validate**, and `strict`
is not set on the tool definition. *`docs/DECISION_structured_outputs_2026-08-27.md`
prepared that decision on 27 August 2026 and recommended waiting for exactly
one thing: **a sweep, so the cost of taking it would be a known quantity rather
than an unknown one.*** **The sweep has run. The evidence is above.**

***It is still not taken here***, being an admissibility rule and therefore a
rule-5 specification version and the operator's. **Written as a pending block
in `docs/OPEN_ITEMS.md` with both options and their costs named.**

**What DID land, because it is a refusal and refusals are procedure:** two
reason codes, `agent_payload_not_a_list` and `agent_payload_off_schema`, both
non-positional so §13 row 23's abort-position panel does not move; both counted
and both legible; **and neither repairs anything.** *A JSON string could be
handed to `json.loads` and the array recovered. It is not, and the reason is
rule 3: a consuming check that repairs a broken input has substituted a working
value for a broken one, and the count of how often the producer breaks is the
measurement the pending block needs.*

---
### The schema is NOT revised, and one note on how it fits

**3f forbids revising the schema now that the results are known, and the
results are zero, which is exactly when a schema looks wrong.** *It is left
alone.*

**One observation recorded as a finding rather than acted on:** the schema's
**Clears δₘᵢₙ?** row names *"the derived 17.0 bp"*, and δₘᵢₙ was re-derived to
**15.7 bp** in phase 1 of this same batch. **The figure in the schema is stale
and the FIELD is not.** *A field that names the derived floor is correct; the
number beside it is a copy of a register cell, and the register is the record.*
**The row is left as written**, and a reader takes δₘᵢₙ from §14 and not from
here.

---

## THE SCHEMA, fixed now so the first real sweep cannot choose its own

**Every entry carries these fields, in this order.** *Fixing the format before
there is anything to put in it is deliberate: a schema chosen after the results
are known is a schema chosen to flatter them.*

| Field | Rule |
|---|---|
| **Mechanism** | **class-level, naming NO issuer.** The entity fence refuses a proposal that names one, so an entry naming an issuer is a fence failure and not a list entry |
| **Family** | one of the registered `discoverable_classes` |
| **Corpus of origin** | the `corpus_id` the proposal was read from |
| **Fences passed** | import, query, entity, authority: all four, named |
| **Reason codes NOT triggered** | the intake points it cleared, named rather than counted |
| **Achievability, CRITERION BY CRITERION** | all nine, each `met` / `failed` / `unscorable`, **with any failing criterion NAMED**. *`unscorable` is never counted as `met`* |
| **Fixed cost** | at §13 row 1 as recomputed under §0 decision 0b: `20,000/V + 2.01/p + 0.206` below `V = 200p`, `102.01/p + 0.206` above |
| **Clears δₘᵢₙ?** | the claimed effect against the derived **17.0 bp** |
| **Origin** | ***`AGENT-ORIGIN` or `CONTROL-ARM-ORIGIN`, marked on every row without exception*** |
| **What would falsify it** | **stated BEFORE any measurement.** A falsifier written after a result is a description of the result |

## THE ORDERING

**By number of achievability criteria MET, descending. Then
alphabetically by mechanism.**

***And by nothing else.*** No merit, no severity, no score, no plausibility, no
recency, no confidence. **The alphabetical tie-break ranks nothing**; it exists
so the order is total and the file is diffable between runs.

***Plausibility is named explicitly because it is the one a model would reach
for.*** A model-derived plausibility ranking is the clerk becoming an analyst,
and the criteria-met count is a count of registered constraints satisfied,
which is arithmetic over the parameter object and not a judgement.

`test_the_candidate_list_carries_no_ranking_key_but_the_criteria_count` holds
this.
