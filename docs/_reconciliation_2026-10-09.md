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

---

## Extension, later sessions of 9 October 2026 (appended; nothing above is rewritten)

Written before any further work on this branch. The second session of the day was read-only and
its findings (items 1 to 7 below) were saved only in the operator's handover; they are entered
here so that the record is in the repository. The third session (this one) re-read what it could
and marks each item with who checked it.

### Tree, as re-read by the third session

| Item | Reading |
|---|---|
| Branch | `credit-drift-2026-10-09` at `08b9ef8` on the remote (`git ls-remote`), cut from `main` at `4d104cc`; `main` untouched |
| Dirty state | clean at the start of the session |
| Tests on the untouched tree | **292 passed, 0 failed**, after `git fetch --depth=1000 origin main` and `pip install anthropic`. The four failures recorded above are explained by item 3 and were environmental. `CLAUDE.md` says 285, which is stale; this branch does not edit `CLAUDE.md` |
| `docs/OPEN_ITEMS.md` against the code | not reconciled beyond its head, as above. This branch still changes nothing under `src/`, `docs/spec/`, `docs/OPEN_ITEMS.md` or any registration object |
| Workflow runs on this branch | one: run 37936127772, run number 1, `probe`, on `08b9ef8`, concluded `success` (Actions API, read today) |

### Items 1 to 7 (established by the second session)

| No. | Finding | Status |
|---|---|---|
| 1 | The branch is on GitHub at `08b9ef8`. The earlier warning that it was unpushed was a false alarm | CHECKED by both sessions (`git ls-remote`) |
| 2 | Run 37936127772 (job 113838517299) ran on `08b9ef8`. Its `success` proves nothing: the probe step pipes into `tee` with no `pipefail`, and `probe.py` catches its own exceptions and exits 0. The remedy is `shell: bash` on those steps | CHECKED for the workflow text and the five `except Exception` handlers in `probe.py` (read today). The job id is as reported by the second session, not re-read. That an explicit `shell: bash` adds `-eo pipefail` is a recollection of GitHub's documentation, UNCHECKED; the rewritten workflow therefore also writes `set -euo pipefail` in each script, which does not depend on it |
| 3 | The four failing tests: two call `git archive 3d3a09a`, which a depth-1 clone does not hold; two import `anthropic`, which `pyproject.toml` does not declare. After `git fetch --depth=1000 origin main` and `pip install anthropic`, 292 pass | CHECKED for the outcome (292 passed, this session). The two causes are as read by the second session |
| 4 | `openassetpricing` 0.0.2: `dl_signal(backend, [names], signed=False)` returns unsigned values. A bare `except` inside `_dl_individual_signal` prints a message and can return an empty or partial frame without raising, so the caller must check columns and row counts and refuse otherwise. Pin the release with `OpenAP(202510)` | CHECKED (wheel 0.0.2 downloaded from PyPI and read, this session). Further reading: the module imports `wrds` at import time, so that package must be installed although no connection is opened; an individual signal is one CSV at `https://drive.google.com/uc?id=<id>`, with a fallback through `_get_readable_link` when Google Drive serves its confirmation page instead of the file |
| 5 | `OpenSourceAP/CrossSection` at `8db8924`: `MomSeasonShort` is the 11-month lag of the monthly return; `Mom6m` compounds lags 1 to 5; `Mom12m` compounds lags 1 to 11; missing returns are set to zero first; lags are calendar-aware and null where the lagged row is absent; null rows are dropped. The return includes delisting returns (defaults of -35% and -55%). Universe: share codes 10 to 12, exchanges 1 to 3. `Price`, `Size` and `STreversal` are stripped from the public release as CRSP data, so no price filter or value weighting is possible, **and the reconstruction recovers returns the publisher withheld** | CHECKED by the second session (source read); not re-read by the third. The wheel confirms that `Price`, `Size` and `STreversal` are served only through a WRDS connection |
| 6 | Reconstruction: seeds r(s) = MomSeasonShort(s+11); roll-forward passes with `Mom6m` ratios reach every month except the firm's last, which is the delisting month. A firm needs 12 listed months. Divisions are guarded where 1 + Mom6m or 1 + r is near zero. The panel's final month is unrecoverable for every firm. A firm's last row is its last month with any of the three signals | DERIVED, not yet exercised. The algebra: (1 + Mom6m(t+1)) / (1 + Mom6m(t)) = (1 + r(t)) / (1 + r(t-5)). `tools/credit_drift/selftest.py` exercises it on a synthetic panel built from the definitions in item 5, and the probe validates it on the published files against `Mom12m`, which the reconstruction does not use |
| 7 | `Alexander-M-Dickerson/trace-data-pipeline` at `7edcb67`, `stage2/DATA_DICTIONARY.md`: the panel is `main_panel_2026.parquet`, 145 columns, true month-end dates, from 2002-08. `permno` is kept; ratings are collapsed to 1 or 11 and unrated bonds stay missing; `ret_type` is `standard`, `trad_in_def` or `default_evnt`; `mcap_s` is bond value at the end of t-1; `ret_vw` uses prices from the last five business days of each month. Units of returns and spreads are not stated | CHECKED for the dictionary (re-read today at `main`): date, `permno`, the rating collapse, `ret_type`, `mcap_s` and the five-day window are as stated; `permco` and `gvkey` are null in the published file; `tret` is "rounded to 2 decimals", which suggests per cent and is to be settled by the probe. The file name and the 145 columns are stated in the pipeline's README as `main_panel_<mode>.parquet`, not in the dictionary. UNCHECKED for the file itself |

### Factual premises for this batch

| Premise | Status | Read where |
|---|---|---|
| A workflow file that exists only on a non-default branch runs on a push to that branch | CHECKED | run number 1 ran on `08b9ef8` (Actions API) |
| The published monthly panel's download address | PARTLY CHECKED | `openbondassetpricing.com/data/` (read today) links only the stage 1 daily file and reports. The release `Alexander-M-Dickerson/osbap-site`, tag `data-2026` (release page read today), lists 18 assets, among them `osbap_main_data_2026.zip`, 1.19 GB. That this archive holds the monthly panel is UNCHECKED until the probe opens it |
| A workflow with `permissions: contents: write` can push to this branch with the job token | UNCHECKED | recollection of GitHub's documented behaviour; branch protection and the repository's token default could not be read through this session's proxy. The first probe run tests it. If the push fails, results remain in the job summary on the run page |
| A push made with the job token does not start another workflow run | UNCHECKED, and not relied upon | the results path is outside the workflow's `paths` filter |
| A GitHub-hosted runner can reach Google Drive and the release assets | UNCHECKED | the probe |
| Returns in the panel and in the signals are decimal fractions | UNCHECKED | the probe reports quantiles; the specification states the rule that decides |

### Dependency contracts this batch writes or runs against

| Contract | Reference read |
|---|---|
| `openassetpricing.OpenAP(202510)`; `._get_individual_signal_url(name)` returns `https://drive.google.com/uc?id=<id>`; `gdrive_parse._get_readable_link(url)` resolves the confirmation page | wheel 0.0.2, `openap_download.py` and `gdrive_parse.py`, read today. Both are private names; the version is pinned for that reason |
| `GET /repos/{owner}/{repo}/releases/tags/{tag}` returns `assets[]` with `name`, `size`, `browser_download_url` | recollection. The `digest` field on an asset is also a recollection; the probe tolerates its absence and computes SHA-256 itself for every file it downloads |
| `actions/checkout@v4` leaves the job token configured for `git push` | recollection; the first probe run tests it |
| `pyarrow.parquet.ParquetFile(path).read(columns=[...])`; `zipfile.ZipFile.extract` | standard library and pyarrow documentation, recollection; exercised locally by `selftest.py` |
| The path first run by this batch: `cdlib.py` (download, hashing, reconstruction, universe), `probe.py`, the workflow's commit step | written in this batch; `selftest.py` runs every function in `cdlib.py` that does not need the network |

### The return channel, and why it changed

Run logs and artifacts are served from a host this session cannot reach. The first design (workflow
notices carrying an encoded payload) was never executed. The design adopted here, approved by the
operator on 9 October 2026: the workflow holds `contents: write` and commits **plain-text** result
files (a log and JSON, no encoding) to this branch under `tools/credit_drift/results/<run number>/`,
which a session reads with `git fetch`. **The cost, stated:** a workflow on a public repository that
can write to its own branch; it is limited to this branch by its trigger, it has no pull-request
trigger, and its commit step copies only `.log`, `.json` and `.txt` files under a size ceiling, so a
data file written by mistake cannot be committed. The artifact upload and the download cache are
removed: one channel, and nothing derived from the stock signals is kept on GitHub's side between
runs. The cost of removing the cache is that every run downloads its inputs again.
