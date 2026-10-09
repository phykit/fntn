# Credit drift pilot: status, 9 October 2026

**Nothing has been measured.** This file is the record for the side test; it is updated in the
same commit as each thing it reports.

## What it is

A non-evidentiary pilot outside the FNTN funnel, requested by the operator on 9 October 2026 and
run on a GitHub-hosted runner because the session that wrote it cannot reach the data. The
repository is public, so run logs and artifacts are public; only derived results are uploaded,
never the source panels.

## The question

Among US-listed companies with non-investment-grade debt, do the stocks of issuers whose bond
credit weakened most in month t underperform, in month t+1, those whose credit strengthened most?

## Inputs

| Input | Source | Provenance |
|---|---|---|
| Bond-month panel, 2002 on, with credit spread, duration-matched Treasury return, grade flag and a dated bond-to-firm link | Open Source Bond Asset Pricing (Dickerson, Robotti and Rossetti) | `verified_secondary` for its documentation; the file itself unread until the probe |
| Monthly stock returns by `permno` | reconstructed from Open Source Asset Pricing signals (Chen and Zimmermann) | `verified_primary` for the signal definitions (source code read); reconstruction validated on the runner |

## Steps

| Step | What it does | Status |
|---|---|---|
| `probe` | lists files, schemas, date ranges and join-key coverage; examines no outcome | pending |
| freeze | `tools/credit_drift/PREREG.md` committed with the analysis code before `run` is dispatched | pending |
| `run` | the frozen test | pending |

## What it will not license

A pass is not a calibration and authorises nothing: stock returns are reconstructed and lose each
delisted firm's final month; no equity market capitalisation or price filter is available; costs
are a flat assumption. A fail is informative: it bounds the idea on free data.
