# Reconciliation, 27 August 2026, session 07

**The seven-phase batch.** Written before any work, per `CLAUDE.md`'s session
protocol, and including part 4 of the Class I invariant: the batch's factual
premises about this tree are enumerated and each is marked CHECKED or
UNCHECKED.

---

## 1. The tree against the register

| Reading | Value | How |
|---|---|---|
| Branch | `fence-and-corpus-repairs` | `git branch --show-current` |
| Dirty state | **clean** | `git status --porcelain`, empty |
| Local head | `7994411` | `git log --oneline -1` |
| Remote head | `7994411` | `git log --oneline -1 origin/fence-and-corpus-repairs` |
| Unpushed commits | **none** | heads equal |
| Test count | **273 passed** | `python -m pytest tests/ -q` |
| `CLAUDE.md`'s stated count | 273 | matches |
| Corpora | 22 documents over three families | `buyback` 7, `earnings_event` 11, `major_holdings_change` 10, minus the three `_sources` sidecars counted at the root, plus `us` 16 and the fenced `_trace_filings` |

**The register matches what the code does** on every cell this batch reads:
§13 row 1 CLOSED, row 29 CLOSED at 10.0 bp, row 30 PROVISIONAL, row 31 BLOCKED
and empty, rows 32 to 35 open, binding-path steps 1 and 3 CLOSED, step 4 not
begun, `delta_min_floor` 17.0.

---

## 2. THE BATCH'S FACTUAL PREMISES, each CHECKED or UNCHECKED

*Part 4 of the Class I invariant: where an instruction asserts what a file
contains, what a variable gates or what a step needs, that is a claim about
this repository and it is checked before work proceeds on it.*

### The premises that HOLD

| # | Premise asserted by the batch | Status | Checked how |
|---|---|---|---|
| P1 | Reference equity was stated by the operator and §0.11 confirmed it at GBP 100,000 | **CHECKED, holds** | `docs/USD_COST_MODEL_2026-08-27.md:151`, `docs/OPEN_ITEMS.md` row 29 |
| P2 | The previous batch recorded the USD denomination without the amount, which is why the re-derivation stopped between 8.5 and 10.9 | **CHECKED, holds** | `docs/USD_COST_MODEL_2026-08-27.md` §1c, the two-row table at line 143 |
| P3 | The claim that removing per-trade FX would move row 29's LOWER bound is false | **CHECKED, holds** | the FX term was USD 4.00 absolute, `104/p` is proportional; `docs/USD_COST_MODEL_2026-08-27.md` §1c already records the refutation |
| P4 | P111 recomputed §5.2.2 against row 29's own 10 bp bound, making the 12.5 bp upper bound circular | **CHECKED, holds** | `§12.1` P111, spec line 1250; §5.2.2's recomputed column, spec lines 819 to 830 |
| P5 | δₘᵢₙ is 7.0 bp spread plus row 29's bound | **CHECKED, holds** | `docs/IBKR_SCHEDULE_2026-08-27.md:160-166` |
| P6 | The 7.0 bp spread was *recovered*, not measured | **CHECKED, holds, and it is worse than the batch states** | `19.5 − 12.5 = 7.0` from §5.2.2's PUBLISHED column, whose own basis §0.7(c) records as *recovered backwards from the clip definition*. See §3 below |
| P7 | Fixed cost no longer constrains position size; the binding constraints are spread, market impact and the edge | **CHECKED, holds** | `docs/USD_COST_MODEL_2026-08-27.md` §1b, block quotation |
| P8 | `cmd_sweep` refuses with `corpus_not_committed` | **CHECKED, holds** | `src/fntn/scanner/cli.py:399,419` |
| P9 | `docs/CANDIDATE_MECHANISMS.md` carries a schema fixed before results, with nine achievability criteria and an ordering by criteria-met | **CHECKED, holds** | the file, lines 70 to 106 |
| P10 | The `queue_from_ledger` repair exists and has consumer-path tests | **CHECKED, holds** | `src/fntn/scanner/report.py:501,531,1031`; `tests/test_scanner.py:1215,3077` |
| P11 | 8-K Item 2.02 is the only step-4 candidate that exercises `extraction_schema_incomplete` against prose | **CHECKED, holds** | binding-path step 4 in `docs/OPEN_ITEMS.md`; `§12.1` P126 |
| P12 | Forms 25, 25-NSE and 15 are on EDGAR and free | **CHECKED, holds as a claim; provenance `named, unread`** | `docs/ARCHIVE_OPTIONS_2026-08-27.md:104-123`, which states the forms were NOT retrieved |
| P13 | Stooq returned a JavaScript notice and the Norgate URL 404'd, so neither coverage claim is established | **CHECKED, holds** | `docs/ARCHIVE_OPTIONS_2026-08-27.md:89,97` |
| P14 | The Class I invariant stands at four clauses with six instances | **CHECKED, holds** | `docs/CORRECTIONS.md:41,48-142` |
| P15 | §6.7's smallest position is GBP 1,875 and its largest GBP 15,000 | **CHECKED, holds** | `docs/DECISION_sizing_collision.md:159-169`; spec line 753 |

### The premises that FAIL, and they govern three of the seven phases

| # | Premise asserted by the batch | Status | Checked how |
|---|---|---|---|
| **F1** | **Phase 3's gate: *if `ANTHROPIC_API_KEY` is unset, refuse*. The implied premise is that a SET key is a USABLE key.** | ***FAILS*** | The variable is set to a **10-character stub** beginning `sk-ant-`. A live probe of `https://api.anthropic.com/v1/models` with it returns **HTTP 401 Unauthorized**; the same probe reaches the host, so this is not a network failure. **The key is present and not usable.** |
| **F2** | **Phase 4's gate: *if `SEC_CONTACT` is unset, refuse at the fetch*. Same implied premise.** | ***FAILS, and worse*** | `SEC_CONTACT` is set to the literal string **`<name> <email>`**. `trace_filings.user_agent()` tests `if not contact` only, so **the placeholder passes**, and the module whose own docstring says it *"refuses to substitute a placeholder: a placeholder is a false statement made to a regulator's server to obtain data"* would send exactly that placeholder to `sec.gov`. |
| **F3** | Implied by F1 and F2: the guards protect against a missing credential | ***FAILS as a class*** | **Both credential guards test PRESENCE, not USABILITY.** An environment variable set to a placeholder defeats both. This is the same defect twice, in two modules, written by two different rules. |

**EDGAR reachability, checked because F2 makes it load-bearing:** `sec.gov`,
`data.sec.gov` and `efts.sec.gov` all answered **200** at probe time. *So
phases 4 and 5 are blocked by the identity string and by nothing else. The
network is not the obstacle and must not be reported as one.*

---

## 3. One premise that holds but understates the problem

**P6.** The batch asks where the 7.0 bp spread came from and offers three
answers: measured, assumed, or inherited. **It is inherited, and the chain has
two links rather than one.**

`7.0 = 19.5 − 12.5`, where 19.5 is §5.2.2's published most-liquid midpoint
break-even and 12.5 is the fixed-cost basis that table was computed on. **But
§0.7(c) records that the 12.5 bp basis was itself *recovered backwards from the
clip definition*** (`§12.1` P111). So the spread term is the residue of
subtracting a back-derived assumption from a published figure whose own spread
column has never been measured on this system's data. ***Two assumptions deep,
and the number gates every mechanism this project will ever consider.***

---

## 4. What this reconciliation changes about the batch

- **Phase 3 refuses**, and not for the reason the batch anticipated. The key is
  set, so the batch's own stop condition does not fire; the key is unusable, so
  the sweep cannot run. **The refusal must be recorded against the true cause.**
- **Phase 4 refuses at the fetch**, and the guard that should have produced that
  refusal does not, so the guard is repaired first.
- **Phase 5's fetch is blocked by the same string**, and its non-fetching parts
  (5b's specification of the bound, 5c's withdrawal of the unverified coverage
  figures) proceed in full.
- **Phases 0, 1, 2 and 6 are unaffected** and carry the batch's substance.

*Nothing here is a reason to widen a guard. Both failures are reasons to
narrow one.*
