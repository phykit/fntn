# Reconciliation, 29 October 2026 (degross-proxy side test)

Written before any work on this branch, per the session protocol in `CLAUDE.md`.

## Tree

| Item | State |
|---|---|
| Base | `main` at `4d104cc` (shallow clone, depth 1) |
| Branch | `degross-proxy-2026-10-29`, created from `main` |
| Dirty state | clean at branch creation |
| Test suite | 292 collected: 288 passed, 4 failed |
| `docs/OPEN_ITEMS.md` | 544 lines; not read against the code in this session, because this batch touches neither the scanner nor the register |

The four failures are environmental and pre-date this branch:

- `test_registration_history_recomputes` and `test_control_arm_values_unchanged_across_restamps` fetch objects and code from historical commits; the clone is shallow (depth 1), so those commits are absent.
- `test_a_SET_ANTHROPIC_API_KEY_can_still_be_unusable` and `test_the_preflight_refuses_a_pinned_model_the_key_cannot_see` depend on the API-key environment of the host; this workspace sets an `ANTHROPIC_*` variable that the tests do not expect.

None is reached by this batch, which adds files under `tools/degross_proxy/`, one workflow and one dated document only.

## Scope of the batch

A non-evidentiary side test outside the FNTN funnel, on the pattern of `futures-residual-2026-10-15`: no apparatus, no row in `docs/OPEN_ITEMS.md`, no authorisation. Question: does a price-implied hedge-fund de-grossing proxy, built from the Kenneth French momentum deciles, warn of Nasdaq 100 drawdowns, after first passing a gate against weeks Goldman Sachs Prime Brokerage itself reported as de-grossing.

## Factual premises

| Premise | Status |
|---|---|
| The workspace shell cannot reach the French Data Library or FRED; the GitHub Actions runner can | CHECKED for the runner by precedent (`futures-residual-2026-10-15` fetched FRED on the runner); the French library is UNCHECKED until the fetch step runs |
| The return channel is a commit of derived result files by the workflow to this branch | CHECKED: `.github/workflows/futures-residual.yml` on `futures-residual-2026-10-15` |
| French daily momentum deciles are published as `10_Portfolios_Prior_12_2_Daily_CSV.zip`, value-weighted section first, values in per cent, missing as -99.99 | UNCHECKED: recollection; `fetch.py` prints the file structure and refuses if it differs |
| FRED `NASDAQ100` starts in 1986 | UNCHECKED: recollection; `fetch.py` prints the first and last dates |
| The three reference weeks (late January 2021, late April to early May 2026, mid-October 2026) were reported by Goldman as de-grossing | CHECKED in conversation against press reports (Bloomberg 2 February 2021; Investing.com via Tradingpedia 4 May 2026; Briefs and Gadget Review, week to 15 October 2026); T2 for 2021, T3 for 2026 |

## Dependency contracts

| Dependency | Reference read |
|---|---|
| numpy 2.x API used (`lstsq`, `percentile`, `random.default_rng`) | read: installed numpy 2.5.3 in this workspace; the runner pins 2.2.6 as on the precedent branch, and only stable functions are used |
| GitHub Actions `actions/checkout@v4`, `actions/setup-python@v5` | read: the precedent workflow, which ran successfully on 15 October 2026 |
