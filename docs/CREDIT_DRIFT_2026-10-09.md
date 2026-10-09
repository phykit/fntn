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
| `probe`, run number 2 | files with sizes and SHA-256; the panel's columns, dates and units; rating, return-type and country counts; high-yield issuers per month; the reconstruction validated against `Mom12m`; coverage of the bond-to-stock join with a reason for each miss. Examines no outcome | dispatched with this commit |
| freeze | `tools/credit_drift/PREREG.md` committed with the analysis code before `run` is dispatched | pending |
| `run` | the frozen test | pending |
| `verify` | an independent reimplementation of the headline numbers from the specification alone | pending |

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
