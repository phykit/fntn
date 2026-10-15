# Reconciliation, 15 October 2026 (branch `futures-residual-2026-10-15`)

Session purpose: a non-evidentiary side test outside the FNTN funnel (the futures residual over spot
as a predictor of the spot price, US energy), on its own branch, after the pattern of
`credit-drift-2026-10-09`. `main` is not touched. The project is mothballed (27 September 2026); this
is one of the operator's one-off kill tests.

## Tree

- Branch created from `origin/main` at `4d104cc` (shallow clone, depth 1).
- Dirty state at start: none. New files only under `tools/futures_residual/`, `.github/workflows/`
  and `docs/`.
- Test suite: 288 passed, 3 failed, 1 deselected, in this workspace. Every failure is environmental
  and none is touched by this batch: `test_registration_history_recomputes` and
  `test_control_arm_values_unchanged_across_restamps` call `git archive` on commits a shallow clone
  does not hold; the two preflight tests import `anthropic`, which is not installed here. Not
  repaired: the batch does not enter `src/`.
- `docs/OPEN_ITEMS.md`: not read and not changed. No row is opened; P148 (no row from an instrument
  that has produced no reading) and the side-test convention both say so.

## Factual premises, each marked

| Premise | Status |
|---|---|
| FRED and Yahoo Finance are not reachable from this workspace (proxy 403) | CHECKED: `curl` to both returned `CONNECT tunnel failed, response 403` |
| GitHub is reachable and the repository can be pushed to | CHECKED: `add_repo` with push access returned the clone URL; clone succeeded |
| The credit-drift branch's workflow commits plain-text results back to its own branch as the return channel | CHECKED: read `.github/workflows/credit-drift.yml` on `credit-drift-2026-10-09` |
| Henry Hub NG futures expire on the 3rd business day prior to the contract month | CHECKED (`verified_secondary`): CME rulebook chapter 508, rule 508102.F, read 15 Oct 2026 |
| HO and RB futures expire on the last business day of the month preceding the contract month | CHECKED (`verified_secondary`) for HO: CME rulebook chapter 829, rule 829.06. RB assumed the same: UNCHECKED |
| FRED series DHHNGSP, DHOILNYH, DGASNYH and DTB3 exist with daily frequency | UNCHECKED here; `fetch.py` fails loudly if any is missing |
| The Yahoo chart endpoint returns daily closes for `NG=F`, `HO=F`, `RB=F` | UNCHECKED here; `fetch.py` falls back to `yfinance` and fails loudly otherwise |

## Dependency contracts

| Contract | Reference read |
|---|---|
| FRED CSV: first column date, second column value, "." for missing | FRED `fredgraph.csv` documentation, recalled; parser accepts any header and checks two columns |
| Yahoo chart JSON v8: `chart.result[0].timestamp[]`, `.indicators.quote[0].close[]`, `.meta.exchangeTimezoneName` | Recalled; `fetch.py` validates every path and falls back to `yfinance` |
| `yfinance.Ticker(sym).history(period="max", auto_adjust=False)` returns a DataFrame indexed by date with a `Close` column | `yfinance` README, recalled; pinned in `requirements.txt` |
| GitHub Actions: `permissions: contents: write` with `GITHUB_TOKEN` lets the job push to its own branch | Read from the working credit-drift workflow on this repository |
