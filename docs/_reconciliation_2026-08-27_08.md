# Reconciliation, 27 August 2026, session 08

**The batch: split auth, the re-pin, and the first sweep.** Written before any
work per `CLAUDE.md`'s session protocol, and carrying both extensions of it:
part 4 of the Class I invariant (the batch's factual premises, each marked
CHECKED or UNCHECKED) and the dependency-contract enumeration added after B12.

---

## 1. The tree against the register

| Reading | Value | How |
|---|---|---|
| Branch | `fence-and-corpus-repairs` | `git branch --show-current` |
| Dirty state | **clean** | `git status --porcelain`, empty |
| Local head | `91bd685` | `git log --oneline -1` |
| Remote head | `91bd685` | `git status -sb`, no ahead/behind marker |
| Unpushed commits | **none** | heads equal |
| Test count | **278 passed** | `python -m pytest tests/ -q` |
| `CLAUDE.md`'s stated count | 273 | **STALE by five.** The five landed with P137's preflight tests in `6a6d17d`; the summary line was not updated with them |
| Corpora | **22 documents**, three families: `buyback` 5, `earnings_event` 9, `major_holdings_change` 8 | `ls`, excluding the underscore-prefixed sidecars |
| Corpora committed | **yes**, `git status --porcelain corpora/` empty, so `corpus_not_committed` will not fire |

Register cells this batch reads, all matching the code: row 1 CLOSED, row 29
CLOSED at 8.7 bp, `delta_min_floor` 15.7, row 30 PROVISIONAL, row 31 BLOCKED
and empty, rows 21a BLOCKED and 21b PROVISIONAL, row 39 PART CLOSED.

---

## 2. THE BATCH'S FACTUAL PREMISES, each CHECKED or UNCHECKED

### The premises that HOLD

| # | Premise asserted by the batch | Status | Checked how |
|---|---|---|---|
| P1 | The key sits at `~/.fntn_key`, `chmod 600`, outside the work tree | **CHECKED, holds** | `stat -c '%a %s'` reports `600 108`; the path is `/home/codespace`, the tree is `/workspaces/fntn` |
| P2 | `ANTHROPIC_API_KEY` is not in this session's environment | **CHECKED, holds** | `env \| grep -c '^ANTHROPIC_API_KEY='` returns 0. **The stub that defeated three previous sittings is gone**, so the presence check and the usability check now agree |
| P3 | The models endpoint answers to the inline-key form | **CHECKED, holds** | `GET /v1/models?limit=100` with `x-api-key: $(cat ~/.fntn_key)` returned **HTTP 200** and ten model objects |
| P4 | `claude-sonnet-5` is present in the response | **CHECKED, holds** | id `claude-sonnet-5`, `display_name` `Claude Sonnet 5`, `created_at` `2026-06-29T00:00:00Z`. **Taken verbatim; nothing retyped from memory** |
| P5 | `cmd_sweep` refuses an uncommitted corpus with `corpus_not_committed` | **CHECKED, holds, and will not fire** | `src/fntn/scanner/cli.py:399`; `corpora/` is clean |
| P6 | `docs/CANDIDATE_MECHANISMS.md` carries a schema fixed before results, ten fields, ordering by criteria-met then alphabetical | **CHECKED, holds** | the file, the two sections under *THE SCHEMA* and *THE ORDERING* |
| P7 | The achievability lens has nine criteria, two of which are unscorable today | **CHECKED, holds** | `src/fntn/scanner/achievability.py:149`, docstring at line 21 |
| P8 | The control arm is drawn from the grid by a registered seed and makes **no model call** | **CHECKED, holds** | `discovery.draw_control_mechanisms` takes `grid, count, seed` and no client; `run.scan` calls it after the sweep loop |

### The premise that FAILS, and it governs Step A

| # | Premise asserted by the batch | Status | Checked how |
|---|---|---|---|
| **F1** | **"Re-stamp with the model as the causing field."** The premise is §13 row 39's own words: *"The pinned identifier is a registered field and re-pinning re-stamps."* | ***FAILS*** | **The model identifier is not a field of `Registration`.** `params.py`'s dataclass has no model field; `discovery_registration.json` has no key matching `model` or `pin`; the pin lives as a **default string in two places**, `clients.py:70` and `cli.py:610`. **So re-pinning today moves no hash, causes no re-stamp, and rows 19, 20, 21a and 21b would have nothing to record.** |

**The row asserting it is mine**, written last sitting in `6a6d17d`, and it is
recorded as a correction rather than quietly repaired. *This is the eighth time
the Class I invariant has caught a claim about this tree that was written
flatly instead of checked, and the second in two sittings on the same row.*

**What follows from F1, and it is a decision rather than a tidy-up.** The
instruction's intent is that the pin be a registered value whose movement is on
the record. **The repair that satisfies the instruction is to MAKE it one**:
add `agent_model` to `Registration`, set it verbatim from the response, and let
`save` produce the re-stamp the instruction asks to be recorded. **The repair
that would defeat the instruction is to edit two default strings**, which moves
the behaviour of every future sweep with nothing on the record — *exactly the
defect row 39's open half is about, arriving through the front door.*

**§0.6 applied explicitly.** Is `agent_model` apparatus? **No.** It adds no
gate, family, grammar row, cost tier, sizing input or feed, and the funnel does
not read it at decision time. It records which clerk read the corpus, a value
that **already exists and already varies unrecorded**. *Making an existing
value legible is procedure; the capability was already there and is not
widened.* **It is still a rule-5 change** — an input-source choice — and it
takes a `§12.1` row in the same commit.

---

## 3. THE DEPENDENCY CONTRACTS this batch writes code against

*Named with the reference that was READ rather than recalled, per the protocol
added after B12.*

| Contract | What is assumed | Reference READ |
|---|---|---|
| `client.models.list()` returns objects with `.id` | the preflight enumerates ids | **the live 200 response** above, and `shared`/models section of the bundled `claude-api` skill: *"Each model object has `id`, `display_name`, `created_at`"* |
| `messages.create` rejects `temperature` | already repaired in `6a6d17d` | bundled skill: sampling parameters *"Removed — 400"* on Sonnet 5 |
| `response.usage` carries `input_tokens` and `output_tokens` | **the cost guard reads them** | bundled skill, Prompt Caching section: `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens` |
| `claude-sonnet-5` price | **USD 2.00 / 1M input, USD 10.00 / 1M output** | bundled `claude-api` skill's model table. ***PROVENANCE, stated because it matters: that table is stamped `cached: 2026-06-24`. It is `named, unread` against a live pricing page, and the cost figures in this batch inherit that tag.*** A cost computed from a cached table is an estimate whose basis is dated, and it is labelled as one wherever it appears |
| `claude-opus-4-6` price, for the comparison | USD 5.00 / 25.00 | same table, same provenance |
| Sonnet 5 thinking | adaptive is the only on-mode; omitting the parameter runs adaptive | bundled skill's thinking table. **The client passes no `thinking`, so the sweep runs adaptive at default effort `high`.** *Not changed in this batch: effort is a knob on how the clerk reads, and moving it is a rule-5 change that has not been decided* |

---

## 4. What this reconciliation changes about the batch

- **Step A proceeds, but through a registration field that does not yet exist.**
  The re-stamp the instruction asks to be recorded can only be produced by
  first making the pin registrable. F1 is recorded in `docs/CORRECTIONS.md`.
- **Step A's row 39 half-closure gains a second observation**: the models
  response **does** expose `created_at`, which row 39 names as the route that
  would settle the stability half **affirmatively** and is checkable on any two
  dates. **The half stays OPEN** — one reading is not two — but today's value
  is written down as the baseline a second reading is taken against.
- **Step B's cost guard is procedure and lands**: a run-scoping flag and a
  usage accumulator measure what a sweep costs. They add no gate the funnel
  reads.
- **Step B's split must not split the control draw.** `run.scan` sizes the
  control arm as `round(len(all_proposals) * ratio)` and draws once. Three
  separate `scan()` calls would draw three arms from the same seed on three
  smaller populations, which is not the registered construction. **The guard is
  therefore placed INSIDE one scan**, between corpora, and not around three.
