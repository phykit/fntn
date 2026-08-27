# CLAUDE.md: From Narrative to Null

Project memory for Claude Code. Read this before changing anything.

**What this is.** A falsification-first architecture for trading ideas extracted from financial media, at ~£100,000 reference equity, long-only UK Main Market / AIM and US equities through IBKR. The governing document is `docs/spec/from_narrative_to_null_v1_14.md`. **The specification governs; this file is a summary of it and where the two disagree, the specification wins.**

**What the product is.** Not returns. The ledger: every unit of capital withheld was withheld for a stated reason, and the reason is machine-checkable. If the stream contains nothing exploitable, the correct output is an empty accepted book, visibly empty.

**Where it stands.** Fourteen specification versions. **Zero frozen designs. Zero backtests. Zero trades.** No gate has been exercised against calibrated thresholds, so the absence of signals to date is structural, not evidential.

---

## The five rules that bind everything

### 1. The model is a clerk, never an analyst

The model extracts structure and classifies against a fixed taxonomy. **Every number, date, threshold and verdict on the trading path is deterministic arithmetic over logged data, replayable byte-for-byte from the parameter hash.** A model-mediated value upstream of a hard gate is a probabilistic dependency in a deterministic coat.

*The model classifies; the table decides.* Where a regulatory form is field-delimited, even the clerk is replaced by a parser.

The one exception is `src/fntn/scanner/discovery.py`, where an agent *selects*. Its containment is architectural: selection cannot reach capital by any route (§3.7). Do not widen that exception.

### 2. §0.6 is ARMED: no version may add capability

Until §7.1's funnel-depth association and §7.5's placebo return a verdict, **no specification version may add apparatus.** Remediation, governance and the calibration sequence proceed normally.

Before adding anything, apply the test explicitly:
- Does it add a gate, a family, a grammar row, a cost tier, a sizing input, a feed, or a field the funnel reads at decision time? **That is apparatus.** It takes an Annex A.1 row with a predicate and waits.
- Is it a checklist, a harness, a linter, a ledger, a refusal? **That is procedure.** It may land.

The rule has been amended exactly once, on the record, and re-armed. If you find yourself arguing that something is *really* procedure, that argument is the failure mode the rule exists against.

### 3. Refuse to score; never fall back to a default

Wherever an input is missing, below a sample floor, or carries unverified provenance, the consuming check **refuses to score**. A refusal is a state with a reason code, not an absence.

Concretely, in this codebase:
- No `or default`, no `except: return 0`, no silently substituting a working value for a broken one.
- A missing security master emits `security_master_unavailable`; it does not run the weaker half of the fence.
- A control-arm ratio of zero raises; it is not floored to one.
- A not-applicable check is recorded as not-applicable and **may never be read as a pass**.

### 4. Every refusal is counted, coded and legible

- Reason codes live in `src/fntn/scanner/codes.py` and **nowhere else**. A code emitted from outside the registry cannot be counted, and a kill that cannot be counted cannot be shown to have been reached.
- Every code carries a §8 rejection summary template and a machine-checkable resurrection predicate.
- Summaries are **rendered from the record's own fields**, never model-written, and are display-only: nothing downstream reads one back.
- Where the deciding step was human, the operator authors the summary and the ledger records the author.
- **Nothing is deleted from the ledger and nothing is overwritten.**

### 5. Counting is mechanical, because intent flatters the denominator

- Any change to a grid, threshold, convention, gate membership, anchor assignment, cost tier, sizing rule, admissibility rule, input-source choice, extraction schema field, or estimation span **is a specification version**, however small. `docs/spec/` is currently the **fourteenth**.
- A correction to a *justification* is not a version. A correction to a *rule* is.
- Frozen designs are counted separately and stand at **zero**. Results attribute to frozen designs, never to versions.
- **A rule change must be recorded in the same commit as the rule change.** Where the version is already composed, that record is a `§12.1` change-log row. Where it is not, that record is a **pending block** in `docs/OPEN_ITEMS.md` naming the rule, the sections it touches and its kind, carried until the version is composed and then discharged into the row. What may not happen is a rule moving in one commit and being written down in another. *The earlier wording of this bullet demanded a `§12.1` row in the same commit, which is a stricter thing: it makes composing a whole specification version the price of landing one rule, and the predictable effect is that the rule lands unrecorded instead.*

---

## Hard prohibitions

Do not, without an explicit §0 decision from the operator recorded in the spec:

- Put a model-emitted number or date in the fill path.
- Let anything machine-raised supply `delta_min`, `n_min`, a registered sign, or a ratified pre-mortem. The scanner's steady state is a queue of drafts **blocked on the operator**, and that is the design working.
- Let agent-origin material enter the §3.5 item pipeline. It would re-base §7.1's headline on an agent-selected population.
- Fit a parameter on the archive and present it as a restriction. A restriction parameter fitted on the archive is a fitted parameter wearing a restriction's clothes.
- Assume a value for any pending §13 row. **§13 row 1, the broker commission, is unverified and is the most leveraged number in the paper.** The clip stays £2,500 and the reachability figures stay as they are until it verifies.
- Weaken the import fence, the query fence, the entity fence or the authority fence.

---

## Layout

```
src/fntn/scanner/  the agent discovery layer (spec §3.7)
  codes.py        reason-code registry; the ONLY place a code is introduced
  records.py      Proposal / IntakeRecord / Directive / Item; the entity fence
  fences.py       query fence, authority fence, import fence
  ingest.py       fail-fast runner, both surfaces, audit-stream sampler
  screen.py       §3.6.3 screen, §3.6.5 stream table, §3.6.8 registration
  segment.py      design-segment reuse ledger, theta arithmetic, the queue
  discovery.py    agent protocol, schema, prompt, cache, control arm
                  ** UNDER THE IMPORT FENCE: no prices, no outcomes **
  budget.py       §13 row 27 intake ceiling. THE DECISION IS TAKEN ONCE, AT
                  CAPTURE. ReplayedBudget holds no clock; a replay that
                  re-races one makes rule 1 false
  ledger.py       SQLite; nothing deleted, nothing overwritten
  summaries.py    §8 rejection summaries: rendered, never judged
  trace.py        §9.4 trace harness; evidentially inert by construction
  ratify.py       §13 row 21a/21b ratification: twelve drawn by the
                  registered seed, clerk labels withheld
  run.py          one scan cycle and its report
  report.py       the §9.2 run report; renders the ledger, measures nothing.
                  The queue is ordered by outstanding-blocker count ONLY
docs/spec/         the governing manuscript
docs/OPEN_ITEMS.md   §13 calibrations, §14 decisions, Annex A.1 predicates
docs/REGISTRATION_HISTORY.md  one row per registration hash ever stamped, the
                     object each was taken over, its §0.5 provenance tag and
                     the field that caused it. Registration.save() will not
                     overwrite a stamped registration until the prior row is
                     here; Registration.load() verifies the recorded hash, or
                     says it cannot
corpora/us/_raw/   the pages the server sent, kept because extraction is
                     destructive. Underscore-prefixed, so every corpus reader
                     skips them
docs/CONVENTIONS.md  coding conventions derived from the spec
tests/
```

## Working here

```bash
pip install -e ".[dev]"      # once: puts src/ on the path
python -m pytest tests/ -q   # 218 tests
```

Without the editable install the package sits at `src/fntn` and is invisible to
`python -m`, which reports `No module named 'fntn'`. If you would rather not
install, prefix every command with `PYTHONPATH=src`.

**The headline test is `test_every_defined_code_is_emitted`.** A code defined but never emitted is an untested branch, which is the defect class no amount of re-reading finds. If you add a reason code, add the branch that emits it *and* the test that reaches it, in the same commit.

**Before claiming a fence works, trace it.** `src/fntn/scanner/trace.py` runs real material through the real machinery and reports coverage, not verdicts. The pattern-only entity fence passed every unit test and refused 94% of real agent proposals; the trace is what found that. Rules read against each other are the weaker instrument. Rules read against a world are the stronger one.

## Style

- Formal British English. **No em-dashes**, in prose or in table cells; empty cells read `n/a`.
- Docstrings carry the *reason* a rule exists, not just its behaviour. A rule whose justification is not written down gets relaxed by whoever meets it next.
- When a design decision has a cost, state the cost rather than the benefit.

## Two things that look like bugs and are not

1. **The scanner admits nothing on a first run.** Every draft blocks on `delta_min_absent`, `premortem_unratified` and `literature_search_absent`. Widening the search must not shorten the fence.
2. **The coverage report is far below 100% on any single live run.** One sweep exercises a handful of branches; the suite exercises all of them deliberately.
