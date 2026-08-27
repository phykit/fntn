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

***Neither arm exists. The question 3g asks cannot be answered, and it is not
evaded.***

**The comparison this file exists to make is whether the agent arm is
distinguishable from the random-mechanism control arm on the achievability
lens.** *If a random draw over the grid meets as many criteria as an agent
reading corpora, the agent has located nothing and the whole discovery layer is an
expensive way to sample a grid.*

**That comparison is NOT made here, because neither arm was produced.** The
control arm is sized relative to the agent arm at the registered ratio, so with
zero agent proposals the correct control arm is zero as well.

***The question stands open and unanswered. It is not "no difference found";
nothing was looked at.*** *Those are different claims and this project has
corrected the confusion of them three times.*

---

## WHY NOTHING WAS SWEPT, 27 August 2026. TWO CAUSES, AND NEITHER IS THE ONE THE INSTRUCTION ANTICIPATED

**The instruction's stop condition was `ANTHROPIC_API_KEY` unset.** ***It is
set.*** It is set to a ten-character stub beginning `sk-ant-`, and the API
answers **401 Unauthorized**. **A variable that is SET is not thereby USABLE**,
and the guard tested only that something was there.

```
$ python -m fntn.scanner sweep
ANTHROPIC_API_KEY is set and the API refused it: Error code: 401 -
{'type': 'error', 'error': {'type': 'authentication_error',
'message': 'API key is invalid.'}, 'request_id': None}.

SET IS NOT USABLE. A placeholder, a revoked key and a truncated paste all
satisfy a presence check and none of them authenticates, so this is checked
here rather than discovered part-way through a sweep.

Nothing has been swept and no proposal has been authored.
```

***And the first attempt did not even reach the 401.*** It raised

```
TypeError: Messages.create() got an unexpected keyword argument 'temperature'
```

**`temperature` has been removed from `messages.create` in `anthropic` 1.x and
the current models reject sampling parameters outright.** The client carried
`temperature=0`, so **the sweep could not have run even with a working key**,
and the class's own name-line claimed a determinism the API no longer offers.

**Both are repaired, both are refusals rather than fallbacks, and both are
tested** (`test_a_SET_ANTHROPIC_API_KEY_can_still_be_unusable`,
`test_the_client_no_longer_claims_temperature_zero`). *The key check is now a
preflight `models.retrieve` at construction: no tokens, and it settles the key
and the model identifier together, before a single document is opened.*

### Re-attempted 27 August 2026 after the operator reported the endpoint answering

***It did not answer to THIS session, and the difference is recorded rather
than reconciled away.*** The operator read the models endpoint and reports key,
credit and connectivity good, and `claude-opus-4-6` present — **which refuted a
claim of mine and is recorded as `docs/CORRECTIONS.md` B14.**

**What this session can see is unchanged**, checked three ways: the process
environment, a login shell, and `models.list` itself.

| Check | Reading |
|---|---|
| `ANTHROPIC_API_KEY` in-process | **10 characters**, prefix `sk-ant-` |
| the same in a login shell | **10 characters**, identical |
| `~/.config/anthropic`, `ant` CLI, `.env` | **absent, absent, absent** |
| `client.models.list()` | **401 `authentication_error`** |
| `python -m fntn.scanner sweep` | **exit 4**, refused at construction |

***So the re-pin to a cheaper model is PREPARED AND NOT TAKEN.*** The
instruction is that the identifier be taken **verbatim from the models
response**, and **this session has no models response.** *Retyping an
identifier from memory is precisely what the instruction forbids, and inventing
a response would be the authored-as-drawn defect wearing a different coat.*
**The pin stays at `claude-opus-4-6`, which is the pin that was already
registered, so no hash moves and nothing becomes non-comparable.**

**The justification for the re-pin is recorded now so it survives this
session** and can be taken the moment a response exists: **cost**, a full sweep
at Opus pricing possibly exceeding the available credit; and **timing**, *no
proposals having ever been drawn, so there is no arm this makes
non-comparable.* ***And the sticky rule, recorded before the first sweep rather
than after it: once one sweep has run, the pin becomes STICKY and does not move
without a stated reason on the record.*** *A pin that moves between sweeps
makes them incomparable, and the cheapest moment to move it is the only moment
at which moving it costs nothing.*

### The three temptations, named and refused

*Each is already in this project's record as the authored-as-drawn defect.*

| Temptation | Refused because |
|---|---|
| **Author the proposals** | an authored proposal presented as a drawn one is the defect §13 row 23 was re-based to remove, and it would enter §7.1's population as though a model had located it |
| **Write a transcript and replay it** | `TranscriptClient` replays what a model returned. A transcript written by hand is authorship with a file in front of it |
| **Fall back to a weaker call** | rule 3. A missing input produces a refusal with a reason code; it does not run the weaker half of the machinery |

### Cost, reported because the operator is choosing to spend it

| | |
|---|---|
| Model calls made | **0** |
| Input tokens | **0** |
| Output tokens | **0** |
| Credits | **0** |

***Zero is the honest figure and it is reported rather than omitted.*** *The
refusal happened at client construction, before the first corpus document was
read, which is where a refusal belongs.* **What a real sweep will cost is not
estimated here**, because an estimate written beside a zero reads as a result.

---

## THE LIST

**0 mechanisms.**

| # | Mechanism | Family | Origin | Criteria met | Failing criteria |
|---|---|---|---|---|---|
| — | *(none)* | — | — | — | — |

**0 agent-origin. 0 control-arm-origin.**

***The zero has one cause and it is not the corpora.*** Twenty-two documents are
built, committed, integrity-checked, registered and readable across three
families, and the sweep cleared the registration, the corpus-commit fence and
the security master before it stopped. **The apparatus is complete up to the
model call and stops there.**

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
