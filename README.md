# From Narrative to Null

A falsification-first architecture for trading ideas extracted from financial media.

A language model reading financial media can be used as an **analyst** or as a **clerk**. As an analyst it hallucinates numbers, leaks hindsight through memorised price history, and cannot be audited. As a clerk it does one thing: it turns unstructured text into structured fields against a fixed schema, and classifies those fields against a fixed taxonomy.

**This system uses the model only as a clerk.** Every number, date, threshold and verdict on the trading path is deterministic arithmetic over logged data, replayable byte-for-byte from the parameter hash.

## What it claims, and what it does not

It does not claim returns. At £100,000, even excellent alpha is a few thousand pounds a year, less than the engineering time. **The product is the ledger**: every unit of capital withheld was withheld for a stated reason, and the reason is machine-checkable. If the stream contains nothing exploitable, the correct output is an empty accepted book, visibly empty.

## Where it stands

| | |
|---|---|
| Specification version | **v1.13, thirteenth** |
| Frozen designs | **0** |
| Backtests run | **0** |
| Trades | **0** |
| §0.6, no new apparatus | **Armed.** Second amendment drafted, available, not taken |

No gate has been exercised against calibrated thresholds, so the absence of signals to date is structural, not evidential.

## Contents

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project memory. The five rules that bind everything. Read first |
| `docs/spec/from_narrative_to_null_v1_13.md` | The governing manuscript. Standalone; supersedes all prior versions |
| `docs/OPEN_ITEMS.md` | The live register: §13 calibrations, §14 decisions, Annex A.1 predicates, and the binding path in order |
| `docs/CONVENTIONS.md` | Coding conventions, each a spec rule with its implementation consequence |
| `docs/trace_report_2026-08-26.txt` | First specification trace of the discovery layer. Non-evidentiary |
| `docs/trace_corpus.json` | Its input: 36 proposals from live ASX, TSX/SEDI and EU MAR sources |
|  `src/fntn/scanner/` | The agent discovery layer (§3.7). See `src/fntn/scanner/README.md` |
| `tests/` | 94 tests. The headline is `test_every_defined_code_is_emitted` |

## Running

```bash
pip install -e ".[dev]"      # once: puts src/ on the path
python -m pytest tests/ -q   # 128 tests
```

Without the editable install the package sits at `src/fntn` and is invisible to
`python -m`, which reports `No module named 'fntn'`. If you would rather not
install, prefix every command with `PYTHONPATH=src`.

The scanner needs one thing wired in from your side: an `AgentClient` with `complete(system, user, schema) -> dict`, calling the model at temperature zero. Everything else is deterministic and offline.

## The next five steps, in order

1. Verify the broker commission (§13 row 1). Every break-even denominator inherits it.
2. Fix the pre-calibration fixings: archive identity and span, partitions, universe, roster.
3. Settle θ, the δₘᵢₙ floor and account type (§14).
4. Run the trace harness to its stopping rule.
5. Populate §13 and hash the parameter object. That act creates frozen design 1.

Until step 5, no version may add capability.
