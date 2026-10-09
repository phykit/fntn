# Reconciliation, 9 October 2026 (credit-drift side test)

Written before any work on this branch, per the session protocol in `CLAUDE.md`.

## Tree

| Item | Reading |
|---|---|
| Branch | `credit-drift-2026-10-09`, cut from `main` at `4d104cc` (shallow clone, depth 1) |
| Dirty state | clean at cut |
| Tests on the untouched tree, this environment | 288 passed, 4 failed (292 collected; `CLAUDE.md` says 285, so the count there is stale) |
| The 4 failures | `test_registration_history_recomputes`, `test_control_arm_values_unchanged_across_restamps`, `test_a_SET_ANTHROPIC_API_KEY_can_still_be_unusable`, `test_the_preflight_refuses_a_pinned_model_the_key_cannot_see` |
| Their cause | NOT ESTABLISHED. Two fetch objects from history, which a depth-1 clone does not hold; two read an `ANTHROPIC_*` environment this sandbox sets. Both are inferences from the test names, not readings. This branch touches no file any of them reads |
| `docs/OPEN_ITEMS.md` against the code | not reconciled beyond its head. This branch changes nothing under `src/`, `docs/spec/`, `docs/OPEN_ITEMS.md` or any registration object |
| Project state | mothballed 27 September 2026; `killtest-2026-10-07` unmerged and unrun |

## What this branch is, and the §0.6 test applied

A side measurement requested by the operator on 9 October 2026: does last month's move in an
indebted issuer's bond credit predict next month's return on its stock. It adds no gate, family,
grammar row, cost tier, sizing input, feed or decision-time field to the funnel. It is not
apparatus and it is not part of the FNTN design. It is **non-evidentiary** in the sense of the
measurement ladder's first rung: a crude bound on an answer, never a calibration, and it opens no
§13 row.

## Factual premises about this tree and its dependencies

| Premise | Status | Read where |
|---|---|---|
| The repository is public and Actions is enabled | CHECKED | GitHub API, today |
| A workflow file that exists only on a non-default branch runs on a push to that branch | UNCHECKED | recollection of GitHub's documented behaviour; the first push tests it |
| The existing runbook commits nothing back (`contents: read`) | CHECKED | `.github/workflows/runbook.yml` |
| OSBAP publishes a monthly bond panel carrying `permno`, `cs`, `ret_vw`, `tret`, `mcap_s` and a rating collapsed to 1 (investment grade) or 11 (non-investment grade and default) | CHECKED for the documentation, UNCHECKED for the file | `stage2/DATA_DICTIONARY.md` of `Alexander-M-Dickerson/trace-data-pipeline`, read today; the probe reads the file |
| The published panel's download address | UNCHECKED | the probe lists the site's links |
| OSAP `MomSeasonShort` is the 11-month lag of the monthly return; `Mom6m` compounds lags 1 to 5; `Mom12m` compounds lags 1 to 11; missing returns are set to zero first | CHECKED | `Signals/pyCode/Predictors/*.py` of `OpenSourceAP/CrossSection`, read today |
| Individual OSAP signals download without WRDS credentials | CHECKED in source, UNCHECKED on a runner | `openassetpricing` 0.0.2, `dl_signal`, read today |
| A GitHub-hosted runner can reach `openbondassetpricing.com` and Google Drive | UNCHECKED | the probe |

## Dependency contracts this branch writes or runs against

| Contract | Reference read |
|---|---|
| `openassetpricing.OpenAP().dl_signal(backend, [name])` returns `permno, yyyymm, <name>` | package source, wheel 0.0.2 |
| `actions/checkout@v4`, `setup-python@v5`, `cache@v4`, `upload-artifact@v4` | as already used in `runbook.yml` |
| `pyarrow.parquet.ParquetFile` column projection | standard library documentation, recollection |
