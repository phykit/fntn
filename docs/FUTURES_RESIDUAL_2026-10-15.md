# Futures residual over spot, US energy: a non-evidentiary side test (15 October 2026)

**Status: outside the FNTN funnel.** No apparatus, no row in `docs/OPEN_ITEMS.md`, no
authorisation, no reading for any §13 row. The project is mothballed (27 September 2026); this is
one of the operator's one-off kill tests, run on its own branch after the pattern of
`credit-drift-2026-10-09`. `main` is not touched.

## What it tests

Whether the front-month futures premium over the physical spot price, net of bill financing
(the "financing only" residual, M), predicts the subsequent change in the spot price over 1, 5 and
20 trading days, beyond spot momentum. Primary asset Henry Hub natural gas; heating oil and
gasoline replicated without weight. Two hypotheses (the level M and its daily change dM), two-sided
by the operator's choice, each judged at 1.25% with six criteria. The full specification is
`tools/futures_residual/PREREG.md`, frozen by `tools/futures_residual/FROZEN.sha256` before any
observation was retrieved.

## Why this version

The same proposal applied to Nasdaq-100 futures and to LME copper against COPX was tested on
12 October 2026 and failed on every hypothesis (project files
`claude/ndx_futures_premium_record_2026-10-12.md`, `claude/copper_premium_copx_record_2026-10-12.md`).
A physical commodity whose spot is a different instrument from the front future is the remaining
version with a mechanism (storage, convenience yield, term structure) rather than basis noise, and
US energy is the only such family with free daily spot data (EIA via FRED).

## How it runs

The workspace cannot reach FRED or Yahoo (proxy 403). The GitHub Actions runner can. Pushing a
change to `tools/futures_residual/DISPATCH` on this branch runs `.github/workflows/futures-residual.yml`:
freeze check, self-test, fetch, frozen run, independent reimplementation (`verify.py`, written from
`PREREG.md` alone by a separate agent that did not see `run.py`), and a figure-by-figure comparison.
Derived statistics only are committed back under `tools/futures_residual/results/<run>/`. No
observation of any input is stored, printed or committed.

## What a result licenses

A PASS authorises nothing: it would justify one separate frozen test of a tradable expression
(front futures, roll-aware, with costs and the operator's futures permissions, which are
unverified). A FAIL is no support at the detectable size. The spot price itself is not traded.
