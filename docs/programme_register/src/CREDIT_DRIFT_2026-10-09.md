# Credit drift pilot: status, 9 October 2026

**Verdict: WEAK, against the rules frozen at `5444df2`.** There is a relation in this sample; the
test cannot show it to be tradeable, and the frozen rules call that not actionable. The independent
implementation returns the same verdict and the same numbers. Non-evidentiary: this is not a
calibration and it authorises nothing. The results are in the section "Result" below.
This file is the record for the side test; it is updated in the same commit as each thing it
reports.

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
| `probe`, run number 3 | the same probe after "listed at t" was narrowed to a signal row (see below) | **complete**, on `711dba7`; results in `tools/credit_drift/results/3/` and summarised below |
| freeze | `tools/credit_drift/PREREG.md` committed with the analysis code before `run` is dispatched | **done in this commit**; hashes below |
| `run`, run number 4 | the frozen test, on the files frozen at `5444df2` | **complete**, on `f7ccf6b`; results in `tools/credit_drift/results/4/` |
| `verify`, run number 5 | the independent implementation (`verify.py`, frozen at `5444df2`) on the same pinned inputs | **complete**, on `6844ba5`, dispatched before the result of run number 4 was read; results in `tools/credit_drift/results/5/` |

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

## Probe run 3: coverage under the corrected definition

Every hash, unit and validation figure is identical to run 2. Coverage, with "listed at t" meaning
a signal row at t:

| Item | Reading |
|---|---|
| High-yield issuer-months, formation months 2002-08 to 2024-10 (267 months) | 107,731 |
| of which the stock is listed at t (eligible) | 89,961 (83.5%) |
| of which a return at t+1 is recovered | 88,801 (82.4%); 174 to 432 a month, median 325 |
| Reasons for a miss, all 112,984 high-yield issuer-months | permno never in the stock file 9,125; stock's last row before t 5,971; months after the stock file ends 3,995; not yet listed 3,078; gap in the listing 150; stock's last row is t 492; **final month lost 499**; at or next to the stock file's end 702; other 171 |
| Eligible, with an outcome, and both Fama-MacBeth controls present | 99.99% |

## The freeze

`tools/credit_drift/PREREG.md` is frozen in this commit together with the code. Its section 10
lists every change from the draft design and the reason for each. The test has not been dispatched:
`DISPATCH` still names the probe, and the next commit changes it.

| File | SHA-256 |
|---|---|
| `tools/credit_drift/PREREG.md` | `43e5062459343c90528b5b77feee28a06b7494af1390b377152adf3c92579bd8` |
| `tools/credit_drift/run.py` | `1867129330048a11497b84a2a8672b45d5295f39bd6943611486528129e1085c` |
| `tools/credit_drift/cdlib.py` | `775b9699fedcafe7620aa9f3b7bd6cc265e6c6cd6e6025415c738cf57b2a055b` |
| `tools/credit_drift/verify.py` | `e500badef9c67b61a5165a00d9242ba4f59a953e730ffd96051915e80d36f06e` |

**How the specification was checked before the freeze.** A separate agent, which saw neither
`run.py` nor `cdlib.py` nor any number from them, implemented the specification as `verify.py` and
listed every sentence it found ambiguous. Its lists changed the text in eleven sections and one
rule (the definition of "listed at t", above). On the revised text the two implementations were run
on the same synthetic inputs, with no effect and with a planted one, and agreed on every headline
number to within 4e-15. `run.py` was also checked against a third, loop-based computation of each
criterion. All of this used synthetic data; no outcome existed on the real inputs.

**What the verdict can be**, from `PREREG.md` section 7: PASS (all six criteria), WEAK (not a PASS,
and the long-short return positive with t at or above 2.0; not actionable), FAIL (anything else),
or UNSCORABLE (a refusal, never read as a pass or a fail). Criterion (d), the long-only form net of
25 basis points on actual turnover, is hard to meet by construction and the specification says so
in advance.

## Result (runs 4 and 5)

Both runs found the pinned bytes, decimal units and a reconstruction that validates (217,185
rebuilt `Mom12m` values for the stocks of high-yield issuers, every one within 2e-14). Both hashed
the four frozen files to the values in the table above. Sample: 90,665 eligible high-yield
issuer-months, 88,801 with an outcome, 267 valid months, outcome months 2002-09 to 2024-11, on
average 337 issuers a month and 66 in each extreme fifth.

### Criteria

| | Criterion | Value | Threshold | Met |
|---|---|---|---|---|
| (a) | Long-short, top fifth minus bottom fifth | +1.02% a month, t 3.10 | positive, t >= 3.0 | yes |
| (b) | Fama-MacBeth slope with controls | +1.56% across the range of the signal, t 4.79 | positive, t >= 2.0 | yes |
| (c) | Both halves | +1.11% and +0.93% a month | both positive | yes |
| (d) | Long-only, top fifth minus universe, net of costs | +0.22% a month, t 0.99 (gross +0.61%, cost 0.39%, one-way turnover 78% a month) | positive, t >= 2.0 | **no** |
| (e1) | Lost final months at -30%, every fifth | +1.04% a month | positive | yes |
| (e2) | Lost final months at -30%, top fifth only | +0.79% a month | positive | yes |

**Verdict: WEAK** (not a PASS; long-short positive with t at or above 2.0). Not actionable.

### The two implementations

`run.py` and `verify.py` agree on the verdict, on 267 valid months, on both sample counts and on
every criterion's mean and t to within 4e-15, and on the six secondary items `verify.py` covers.
Under `PREREG.md` section 11 that is agreement.

### Secondary (no weight in the verdict)

| | Item | Value |
|---|---|---|
| S1 | Mean outcome by fifth, bottom to top | 0.92%, 1.18%, 1.14%, 1.45%, 1.93% a month; universe 1.32% |
| S2 | Tails against the middle | top minus middle +0.68% (t 2.20); middle minus bottom +0.34% (t 1.03) |
| S3 | Fama-MacBeth without controls | +1.21%, t 3.26 |
| S4 | Weighted by bond value | +0.58%, t 1.15 |
| S5 | Investment-grade universe | +0.05%, t 0.37 |
| S6 | All issuers | +0.71%, t 3.40 |
| S7 | Spread-change signal | +0.75%, t 1.95 |
| S8 | Three-month formation | +1.20%, t 2.38 |
| S9 | By outcome year | positive in 20 of 23 calendar years; the largest are 2003, 2008, 2014 and 2016 (3.2% to 4.0% a month); 2020 is -3.5% a month |
| S10 | Attrition by fifth, bottom to top | lost final months 148, 77, 75, 71, 128; stock's last row is t 153, 65, 67, 78, 129 |
| S11 | Every missing top-fifth outcome at -30% | +0.39%, t 1.24 |
| S12 | Long-only net, under e2 | +0.04% a month, t 0.16 |
| S13 | Every missing top-fifth outcome at -100% | **-0.94%, t -2.82** |

### Reading it as a kill test

1. **It is not tradeable on this evidence.** The long-only tilt earns 61 basis points a month over
   the universe before costs and gives back 39 to turnover, leaving 22 with a t of 1.0. With the
   top fifth's lost final months at -30% it leaves 4 (S12). The cost assumption is generous for
   this population: there is no price filter, and many of these are distressed small stocks.
2. **Criterion (a) clears its bar by a hair.** t is 3.10 against 3.0. Any of the stresses below
   takes it under.
3. **The outcomes that are missing are not missing at random, and the result does not survive the
   worst case for them.** 322 top-fifth outcomes are missing in the valid months, 257 of them for a
   delisting-related reason. With every one at -30% the long-short falls to 0.39% (t 1.24); at
   -100% the sign reverses. The truth is between the primary and S13 and this data cannot say
   where.
4. **It is a small-issuer effect.** Weighted by bond value it is 0.58% with a t of 1.15, and in
   the investment-grade universe there is nothing.
5. **It comes from the long side.** The top fifth beats the middle by 0.68%; the bottom fifth
   trails the middle by 0.34% with a t of 1.0. The hypothesis as worded (weakened credit
   underperforms) is the weaker half of what was found.
6. **It is concentrated in credit crises.** Four years supply most of it.

### Exploratory (computed after the result from the published monthly series; not in the frozen specification; no weight)

| Item | Value |
|---|---|
| Outcome months to 2019-12, the span of the published samples | +1.38% a month, t 3.77, 208 months |
| Outcome months 2020-01 to 2024-11, the only span later than those samples | **-0.25% a month, t -0.38, 59 months** |
| April 2020 alone | -41.8%: the stocks whose credit had weakened most in March rebounded |
| Excluding 2020 | +1.23% a month, t 3.97 |
| Excluding the five best months of 267 | +0.69% a month |
| Monthly standard deviation of the long-short | 5.6% |

The sub-period split is the most important thing here and it was not pre-registered, so it is a
question and not a finding: on the 59 months that no published study could have seen, the sign is
wrong.

### Deviations

1. None from the frozen specification is known in either implementation.
2. S13 is computed by `run.py` only; `verify.py` covers S5 to S8, S11 and S12, as the specification
   says.
3. S10's "other missing" in the result file includes the two formation months at the stock file's
   end (2024-11 and 2024-12), in which every outcome is missing; those months are not valid and
   enter no statistic. The delisting-related counts in the table above exclude them.
4. The definition of "listed at t" changed between probe run 2 and the freeze, before any outcome
   existed; see above.

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
