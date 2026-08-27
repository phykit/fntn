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

***Neither arm exists. The question 7d asks cannot be answered, and it is not
evaded.***

**The comparison this file exists to make is whether the agent arm is
distinguishable from the random-mechanism control arm on the achievability
lens.** *If a random draw over the grid meets as many criteria as an agent
reading corpora, the agent has located nothing and the whole discovery layer is an
expensive way to sample a grid.*

**That comparison is NOT made here, because neither arm was produced:**

```
$ python -m fntn.scanner sweep
no API key: set ANTHROPIC_API_KEY or pass api_key. Refusing rather than falling
back to an unauthenticated call that would fail later with a less useful message.
```

**`ANTHROPIC_API_KEY` is unset.** The control arm is sized relative to the agent
arm at the registered ratio, so **with zero agent proposals the correct control
arm is zero as well.**

***The question stands open and unanswered. It is not "no difference found";
nothing was looked at.*** *Those are different claims and this project has
corrected the confusion of them three times.*

---

## THE LIST

**0 mechanisms.**

| # | Mechanism | Family | Origin | Criteria met | Failing criteria |
|---|---|---|---|---|---|
| — | *(none)* | — | — | — | — |

**0 agent-origin. 0 control-arm-origin.**

***The zero has one cause and it is not the corpora.*** Twenty-two documents are
built, committed, integrity-checked, registered and readable across three
families. **The apparatus is complete up to the model call and stops there.**

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
