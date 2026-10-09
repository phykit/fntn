# Credit drift pilot: status, 9 October 2026

**Nothing has been measured.** This file is the record for the side test; it is updated in the
same commit as each thing it reports.

## What it is

A non-evidentiary pilot outside the FNTN funnel, requested by the operator on 9 October 2026 and
run on a GitHub-hosted runner because the session that wrote it cannot reach the data. The
repository is public, so run logs and committed result files are public; only derived results are
published, never a row of either input and never a reconstructed stock return.

**Everything a later session needs is on this branch**: this file, the reconciliation note
`docs/_reconciliation_2026-10-09.md`, the code under `tools/credit_drift/`, and each run's result
files under `tools/credit_drift/results/<run number>/`. No step depends on a note held elsewhere.

## The question

Among US-listed companies with non-investment-grade debt, do the stocks of issuers whose bond
credit weakened most in month t underperform, in month t+1, those whose credit strengthened most?

## Inputs

| Input | Source | Provenance |
|---|---|---|
| Bond-month panel, 2002 on, with credit spread, duration-matched Treasury return, grade flag and a dated bond-to-firm link | Open Source Bond Asset Pricing (Dickerson, Robotti and Rossetti): release `data-2026` of `Alexander-M-Dickerson/osbap-site`, asset `osbap_main_data_2026.zip` | `verified_secondary` for its documentation and for the release's asset list; the file itself unread until the probe |
| Monthly stock returns by `permno` | reconstructed from Open Source Asset Pricing signals (Chen and Zimmermann) | `verified_primary` for the signal definitions (source code read); reconstruction validated on the runner |

## Steps

| Step | What it does | Status |
|---|---|---|
| `probe`, run number 1 | the first probe, on `08b9ef8` | **void**: it concluded `success` behind a pipe with no `pipefail`, in a script that caught its own exceptions, and its output was never read. It proves nothing and nothing is taken from it |
| return channel | the workflow commits plain-text result files to this branch under `tools/credit_drift/results/<run number>/` | written; first exercised by run number 2 |
| `probe`, run number 2 | files with sizes and SHA-256; the panel's columns, dates and units; rating, return-type and country counts; high-yield issuers per month; the reconstruction validated against `Mom12m`; coverage of the bond-to-stock join with a reason for each miss. Examines no outcome | **complete**, on `9d326c9`; results in `tools/credit_drift/results/2/` and summarised below |
| `probe`, run number 3 | the same probe after "listed at t" was narrowed to a signal row (see below) | dispatched with this commit |
| freeze | `tools/credit_drift/PREREG.md` committed with the analysis code before `run` is dispatched | pending |
| `run` | the frozen test | pending |
| `verify` | an independent reimplementation of the headline numbers from the specification alone | pending |

## Probe run 2: what it shows (structure only; no signal was placed beside any outcome)

| Item | Reading |
|---|---|
| Return channel | works: the job committed `probe.log`, `probe.json`, `selftest.log` and `meta.txt` to this branch |
| Bond panel | `main_panel_2026.parquet` in `osbap_main_data_2026.zip`, release `data-2026`; archive 1,273,628,254 bytes, SHA-256 `bfcd509a...e96f`, equal to the release's published digest; member SHA-256 `64bf67fc...035a` |
| Shape | 1,950,002 bond-months, 145 columns, 2002-08-31 to 2025-11-30 (280 months), every date a calendar month-end, no duplicate (cusip, month) |
| Units | `ret_vw`, `tret`, `rfret`, `cs` are decimal fractions (median absolute `ret_vw` 0.0111; median `cs` 0.0141) |
| Counts | `spc_rat`: 1,512,297 at 1 and 437,705 at 11, none missing. `ret_type`: 1,942,897 `standard`, 5,575 `trad_in_def`, 1,530 `default_evnt`. `country`: 1,702,215 `USA`, then `CAN` 61,581 and `GBR` 40,936 |
| Bond-to-firm link | `permno` present on 88.8% of bond-months: 91.5% of investment-grade and 79.5% of non-investment-grade |
| High-yield issuers | 112,984 issuer-months, 1,765 distinct issuers; 203 to 518 a month, median 406 |
| Stock signals | release 2025.10; three CSV files of 117 to 129 MB, 3.7 to 3.9 million rows, 1926 to 2024-12, decimal; hashes in `results/2/probe.json` |
| Reconstruction | converged in two passes; 3,713,111 rebuilt `Mom12m` values all within 1e-13 of the published ones, including 267,393 that depend on the roll-forward; the roll-forward formula applied to 3,585,112 known seeds is within 3e-14 of every one |
| Coverage, as then defined | over formation months 2002-08 to 2024-10, of 107,731 high-yield issuer-months, 84.3% had a stock listed at t and 83.2% a recovered return at t+1 (175 to 436 a month) |
| Reasons for a miss, all high-yield issuer-months | permno never in the stock file 9,125; stock's last row before t 9,966, of which 3,995 are months after the stock file ends; not yet listed 2,276; stock's last row is t 492; **final month lost 499**; at or next to the stock file's end 702; other 298 |

Two consequences. The stock file ends eleven months before the bond panel, so the last outcome
month is 2024-11. And a fifth of non-investment-grade bond-months have no listed parent at all, so
this is a test on listed issuers only.

**A defect in the probe's own definition, found by an independent reading of the draft
specification before anything was frozen.** "Listed at t" was "a signal row at t, or a recovered
return at t". In a stock's first five listed months there is no signal row, and its return is known
only from `MomSeasonShort` eleven months later; so eligibility at t depended on the stock surviving
to t+11. "Listed at t" now means a signal row at t and nothing else (`cdlib.py`). Months after the
stock file's end are also counted under their own reason. Probe run 3 re-reads the coverage under
the corrected definition; no hash, unit or validation figure can change.

## How the stock returns are obtained, and what that costs

The open release of the stock signals withholds raw returns. Three of its published signals are
simple functions of the monthly return (`MomSeasonShort` is the return eleven months earlier;
`Mom6m` and `Mom12m` compound five and eleven lagged returns), so the monthly return can be rebuilt
from them: seeds from `MomSeasonShort`, then a roll-forward on ratios of `Mom6m`, validated against
`Mom12m`, which the rebuild does not use. `tools/credit_drift/selftest.py` shows on a synthetic
panel that this recovers every month except each firm's last.

**The cost, stated.** The rebuilt series is equivalent to data the publisher chose not to release.
It is therefore held in memory on the runner for the length of one job and is never cached,
uploaded, logged or committed; only statistics derived from it are published. Each firm's final
month, which carries any delisting return, cannot be rebuilt at all.

## What it will not license

A pass is not a calibration and authorises nothing: stock returns are reconstructed and lose each
delisted firm's final month; no equity market capitalisation or price filter is available; costs
are a flat assumption. A fail is informative: it bounds the idea on free data.
