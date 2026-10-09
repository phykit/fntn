# Credit drift pilot, hypothesis H1: pre-registration

**Status: FROZEN.** This file, the analysis code (`run.py`, `cdlib.py`) and the independent
implementation (`verify.py`) are committed together before the test is dispatched. The SHA-256 of
all four files is recorded in `docs/CREDIT_DRIFT_2026-10-09.md` in the same commit, and `run.py`
writes the hashes it finds into its result file, so that the two can be compared. No outcome had
been computed on the pinned inputs, by anyone, when this was frozen: probe runs 2 and 3 examined
structure only and placed no signal beside any stock return. Both implementations had been run on
synthetic inputs, with and without a planted effect.

**Standing.** A non-evidentiary side test outside the FNTN funnel. It has no apparatus, opens no
register row and authorises nothing. It is a kill test: its job is to bound an idea on free data.

**Rule of interpretation.** This specification governs. Where `run.py` disagrees with it, the code
is wrong and the disagreement is reported as a deviation. Anything computed that is not written
here is exploratory and carries no weight.

## 1. Hypothesis

H1. Among US-listed companies with non-investment-grade debt, the stocks of issuers whose bond
credit weakened most in month t underperform, in month t+1, the stocks of issuers whose credit
strengthened most.

The registered sign: the long-short return defined in section 6.1 (strengthened minus weakened) is
positive.

## 2. Inputs, pinned

A run that finds any other bytes refuses to score (section 7.4). Pins are from probe run 2
(`tools/credit_drift/results/2/probe.json`); probe run 3 found the same bytes.

### 2.1 Bond-month panel

| Item | Value |
|---|---|
| Source | Open Source Bond Asset Pricing, release `data-2026` of `Alexander-M-Dickerson/osbap-site` |
| Address | `https://github.com/Alexander-M-Dickerson/osbap-site/releases/download/data-2026/osbap_main_data_2026.zip` |
| Archive | 1,273,628,254 bytes, SHA-256 `bfcd509a923d34950318732171f571dbd202b05778048ce67121e5cf53c1e96f` (equal to the digest the release publishes) |
| Member | `main_panel_2026.parquet`, SHA-256 `64bf67fc6eeb5b89323576e024da436a7f80d07ce9cdb6ba9f9808576cfd035a` |
| Shape, for information (the hash decides) | 1,950,002 bond-months, 145 columns, month-end dates from 2002-08-31 to 2025-11-30, no duplicate (cusip, month) |
| Columns used | `cusip`, `date`, `permno`, `country`, `spc_rat`, `ret_vw`, `tret`, `mcap_s`, `cs`. `ret_type` is read and is not used in any calculation |
| Units | `ret_vw`, `tret` and `cs` are decimal fractions (median absolute `ret_vw` 0.0111; median `cs` 0.0141). The run classifies `ret_vw` and `tret` by the rule in section 2.3 and refuses unless both are decimal. The columns are stored as 32-bit floats |

`spc_rat` takes exactly two values in the published file: 1 (investment grade) and 11
(non-investment grade and default). `mcap_s` is the bond's market value at the end of month t-1.
`ret_vw` is the bond's total return from month-end t-1 to month-end t, measured on prices from the
last five business days of each month. `tret` is the return of a duration-matched Treasury
portfolio over the same month. `cs` is the annualised credit spread.

### 2.2 Stock signals

Open Source Asset Pricing (Chen and Zimmermann), release 2025.10, Google Drive folder
`1qQDuTsnyvWfEJR6nPBQZ8xxlq6bkLG_y`, individual predictor files, each a CSV with columns `permno`,
`yyyymm` and the signal, at `https://drive.google.com/uc?id=<file id>`.

| Signal | File id | Bytes | SHA-256 |
|---|---|---|---|
| `MomSeasonShort` | `1VWEjQvvSWXg1FAE60JWgeBmpvluPWmTP` | 117,061,858 | `09e494a3da4041e53c9efcb3f9c7b269fef0967cd8010804b5a6f04c44e39d6d` |
| `Mom6m` | `1IZC9q0e71UW7Yr55I4mEek7tGPFbP-hf` | 128,916,217 | `7b1ee9dc26a477719423780e9e016dceb6880b5eabcb23ab625447178a105911` |
| `Mom12m` | `1K2IDDXDQjKN9XHj3H4LvnjevOS3SIsgc` | 122,312,193 | `a5fef64b62bf64ae1babc66aa1d9483f6142dadac132f86ff0e53d081564d7ec` |

A file with any other column set is a refusal. Rows whose signal is null are then dropped, and a
file left with no rows, or with a duplicated (permno, yyyymm), is a refusal. Throughout this
document a signal *row* means a row whose signal is not null. The signals run from 1926 to 2024-12
and are decimal fractions.

### 2.3 Unit rule

Take the median absolute value m of the non-null values of the whole published column (every row,
every month). For a bond return: decimal if m < 0.05, per cent if m > 0.2, otherwise refuse. For a
stock return: decimal if m < 0.3, per cent if m > 1.0, otherwise refuse. The rule is applied to
three columns, `ret_vw` and `tret` (bond) and `MomSeasonShort` (stock), and the run refuses unless
all three are decimal. `Mom6m` and `Mom12m` are covered by the validation of section 3.3.

### 2.4 Months

Every month is indexed as mi = 12 x year + (month - 1), so consecutive calendar months differ by 1
and every lag below is a calendar lag. A bond row's month is the month of its `date`.

### 2.5 Arithmetic

All arithmetic is in 64-bit floating point. The panel's 32-bit columns are converted before any
subtraction, product or sum. Two correct implementations can still differ in the last digit of a
sum. Section 11 says what size of difference between the two implementations is a disagreement.

## 3. Stock returns

The release withholds raw monthly returns, so they are rebuilt from the three signals.

### 3.1 Definitions, as read in the publisher's source

With r the monthly return (delisting returns included, missing returns set to zero), a lag being
null where the stock has no row in the lagged month:

- MomSeasonShort(t) = r(t-11)
- Mom6m(t) = (1 + r(t-1)) x ... x (1 + r(t-5)) - 1
- Mom12m(t) = (1 + r(t-1)) x ... x (1 + r(t-11)) - 1

### 3.2 Reconstruction

For each permno:

1. Seeds. For every month t with a `MomSeasonShort` row, r(t-11) = MomSeasonShort(t).
2. Roll forward. For a month t whose return is not yet known, if r(t-5) is known and `Mom6m` has
   rows at both t and t+1, and 1 + Mom6m(t) >= 0.01, and 1 + r(t-5) >= 0.01, then
   r(t) = (1 + r(t-5)) x (1 + Mom6m(t+1)) / (1 + Mom6m(t)) - 1.
   A pass applies this to every qualifying month at once, using only returns known before the pass.
   Passes repeat until one adds nothing (two passes suffice on the pinned files).

`Mom12m` is not used in the reconstruction. A stock's final month can never be recovered, because
step 2 needs `Mom6m` one month later; that month carries any delisting return.

Terms used below, for a permno p:

- *listed at t*: p has a row in any of the three signals at t. A recovered return at t is not
  enough (section 5.1 says why).
- *last row* L(p): the last month at which p has a row in any of the three signals.
- *stock file end* E: the largest L(p) over all permnos (2024-12 on the pinned files).

### 3.3 Validation, and the refusal attached to it

Let H be the set of permnos with hy_share >= 0.5 (section 4) in at least one issuer-month of the
panel, in any month and whether or not the stock is listed. All comparisons are restricted to
permnos in H and to rows whose own month t is 2002-08 or later (the eleven returns behind a V1 row
may be earlier).

- V1. For every (p, t) with a published Mom12m(t): rebuild it as the product of (1 + r(t-k)) for
  k = 1 to 11, less 1, where all eleven returns are recovered (a *comparable* row). The error is the
  absolute difference from the published value. A comparable row is *rolled* if at least one of the
  eleven returns came from step 2 and not from a seed.
- V2. For every (p, t) whose return is a seed and for which step 2's inputs exist and its two
  guards hold, with r(t-5) itself a seed: the absolute difference between the seed and the value
  step 2 would give.

The run **refuses to score** unless all of the following hold:

| Check | Threshold |
|---|---|
| V1, all comparable rows: share with error <= 0.001 | >= 0.99, on at least 1,000 rows |
| V1, rolled rows only: share with error <= 0.001 | >= 0.99, on at least 1,000 rows |
| V2: share with error <= 0.001 | >= 0.99, on at least 1,000 rows |
| V1: comparable rows as a share of published Mom12m rows | >= 0.90 |

Probe run 2 found every one of these comparisons within 1e-13 and a comparable share of 0.99995,
so the thresholds are loose by many orders of magnitude; they exist to catch a changed file or a
broken definition, not to be approached. The tolerance of 0.001 was in the probe's code before its
output was read; the 0.99 and 0.90 shares were written afterwards, with those figures known.

## 4. Bond side

### 4.1 Row filter

A bond-month enters only if: `country` is `USA`; `permno` is present; `ret_vw` and `tret` are
present; `mcap_s` is present and positive; `spc_rat` is 1 or 11. All three values of `ret_type`
(`standard`, `trad_in_def`, `default_evnt`) are kept: a return earned in or into default is a
return.

### 4.2 Issuer-month

For issuer (permno) i in month t, over its filtered bonds b with weights w_b = `mcap_s`:

- CR(i, t) = sum(w_b x (ret_vw_b - tret_b)) / sum(w_b). The issuer's credit return. Low CR means
  credit weakened.
- hy_share(i, t) = sum(w_b over bonds with spc_rat = 11) / sum(w_b).
- bond_value(i, t) = sum(w_b).
- DCS(i, t) = sum(w_b x (cs_b(t) - cs_b(t-1))) / sum(w_b), both sums over the same bonds: the
  filtered bonds at t whose `cs` is present at t and whose `cs` is present in the panel in the
  previous calendar month (same cusip; that earlier row need not pass the filter). Missing where no
  bond qualifies. Used only in section 8.

### 4.3 Universes

- **High-yield (the test's universe):** hy_share(i, t) >= 0.5.
- Investment-grade (secondary): hy_share(i, t) < 0.5.
- All issuers (secondary): every issuer-month.

## 5. Sample construction

### 5.1 Eligibility and outcome

An issuer-month (i, t) of the universe is **eligible** if the stock is listed at t (section 3.2).
Its **outcome** y(i, t) is the recovered return r(t+1), and is missing where r(t+1) is not
recovered.

Why "listed at t" is required, and why it means a signal row and nothing more. First, the
publisher sets a missing return to zero, and a stock's first listed month has a missing return;
without the requirement a zero would be scored as the outcome of a position that could not have
been opened. Secondly, eligibility must be knowable at t. A signal row at t depends only on months
up to t. A recovered return at t does not: in a stock's first five listed months there is no signal
row, and its return is known only from `MomSeasonShort` eleven months later, so admitting it would
make eligibility depend on the stock surviving to t+11. The cost: a stock's first five listed
months are never eligible.

An eligible issuer-month has a **lost final month** if its outcome is missing, t+1 = L(i) and
L(i) < E: the return existed, carried any delisting return, and cannot be rebuilt.

### 5.2 Fifths

Each month, sort the eligible issuers by the signal ascending, breaking ties by permno ascending,
and number them k = 1 to N. The fifth is floor(5 x (k - 1) / N) + 1. Fifth 5 (the **top fifth**)
holds the highest signal, fifth 1 (the **bottom fifth**) the lowest. Fifths are assigned over all
eligible issuers, before any outcome is consulted. The primary signal is CR.

### 5.3 Valid months and the sample floor

A formation month t is **valid** if N >= 100 and each of the top and bottom fifths has at least 10
members with an outcome. The test needs at least **120 valid months**; with fewer it is unscorable
(section 7.4). On the pinned files formation months run from 2002-08 to 2024-10 (outcomes 2002-09
to 2024-11), and probe run 3 counted between 174 and 432 eligible high-yield issuers with an
outcome in each of those 267 months.

## 6. Statistics

### 6.1 Long-short series (the primary statistic)

For each valid month, LS(t) = mean of y over top-fifth members with an outcome, minus the same for
the bottom fifth. Equal weights.

### 6.2 Mean and Newey-West t

For a series x_1..x_T in month order (months that are not valid are skipped and the remaining
observations treated as consecutive), with mean m and lag L = 3:

- gamma_j = (1/T) x sum over t = j+1..T of (x_t - m)(x_{t-j} - m)
- V = gamma_0 + 2 x sum over j = 1..L of (1 - j/(L+1)) x gamma_j
- se = sqrt(V / T), t = m / se

Bartlett weights, no small-sample correction, no pre-whitening. If T < L + 2 or V is not positive,
t is undefined and any criterion that needs it is not met.

### 6.3 Fama-MacBeth slope with controls

For each formation month, take the eligible issuers with an outcome, a recovered return at t
(own return) and a `Mom6m` row at t. If there are at least 50, regress y by ordinary least squares
on an intercept and three regressors: the ranks of CR, of the own return r(t), and of Mom6m(t).
Each rank is taken within that month's regression sample, ascending with ties broken by permno,
k = 1..n, and scaled as (k - 1) / (n - 1) - 0.5. The month's statistic is the coefficient on the
rank of CR: the return difference across the full range of the signal, holding the two controls
fixed. Every formation month with at least 50 such issuers has a regression, whether or not it is
valid under section 5.3. The slope's mean and t are from section 6.2 over those months.

### 6.4 Long-only form, net of costs

Weights at formation month t: w(t, i) = 1 / n5 for each of the n5 members of the top fifth (all
members, with or without an outcome), zero otherwise.

- cost(t) = 0.0025 x sum over i of |w(t, i) - w(t-1, i)|, where w(t-1, .) is the weight vector of
  the previous calendar month (its top fifth by section 5.2, whether or not that month is valid),
  and is zero if that month has no eligible issuers; the first month therefore bears a full
  purchase. That is 25 basis points on each unit of weight bought or sold.
- net(t) = [mean of y over top-fifth members with an outcome] - cost(t) - [mean of y over all
  eligible issuers with an outcome].

Costs are charged to the top fifth only; the universe is a paper benchmark, and it contains the
top fifth. Members without an outcome carry weight in the cost and none in the return, which is
the same as assuming they earned the mean of the rest. The series is taken over the valid months
of section 5.3; mean and t from section 6.2.

### 6.5 Halves

The valid months in order, split into the first ceil(T/2) and the rest. The mean of LS in each.

### 6.6 Imputation of lost final months

Two alternative outcome vectors, each replacing only missing outcomes of eligible issuer-months
with a lost final month, and each used to recompute section 6.1 in full (including which months
are valid):

- **e1, symmetric:** y = -0.30 for every lost final month, in every fifth.
- **e2, adversarial:** y = -0.30 for lost final months of top-fifth members only; every other lost
  final month stays missing.

An imputed series can have more valid months than the primary, so (a) and (e) can be means over
different months. The 120-month floor of section 5.3 applies to the primary series only.

## 7. Verdict

### 7.1 Criteria

| | Criterion | Met when |
|---|---|---|
| (a) | Long-short | mean of LS > 0 and t >= 3.0 |
| (b) | Fama-MacBeth with controls | mean slope > 0 and t >= 2.0 |
| (c) | Both halves | mean of LS > 0 in each half |
| (d) | Long-only, net | mean of net > 0 and t >= 2.0 |
| (e1) | Symmetric imputation | mean of LS under e1 > 0 |
| (e2) | Adversarial imputation | mean of LS under e2 > 0 |

### 7.2 Verdicts

- **PASS:** all six criteria are met.
- **WEAK:** not a PASS, and the mean of LS is positive with t >= 2.0. Not actionable.
- **FAIL:** anything else.

### 7.3 What each verdict means

A PASS says a long-only tilt survived a flat cost on its actual turnover in this sample, on
reconstructed returns. A WEAK says there is a relation that this test cannot show to be tradeable.
A FAIL bounds the idea on free data. None is a calibration and none authorises anything.

### 7.4 Unscorable

A fourth state, **UNSCORABLE**, is returned with a reason and no test statistics when: a pinned
file is absent or its hash differs from section 2; a signal file fails section 2.2; a column used
is absent or a key is duplicated; a unit is not decimal; the validation of section 3.3 fails; or
the primary has fewer than 120 valid months. Unscorable is never read as a pass or as a fail.

Because the inputs are pinned by hash, every refusal after the hash check guards against a file
that has changed, and none can fire on the pinned files. On those unreachable paths the two
implementations need not refuse in the same words.

## 8. Secondary analyses

Reported, labelled secondary, and given no weight in the verdict. Each long-short below uses
sections 5.2, 5.3, 6.1 and 6.2 unchanged except for what is named, with no floor on the number of
valid months. S1, S2, S9 and S11 are taken over the primary's valid months.

| | Analysis | What changes |
|---|---|---|
| S1 | Mean outcome of each fifth, and of the eligible universe | n/a |
| S2 | The two tails against the middle | top fifth minus the pooled mean of fifths 2 to 4; that mean minus the bottom fifth |
| S3 | Fama-MacBeth without controls | section 6.3 with the rank of CR as the only regressor, on the same regression sample rule applied without requiring the controls |
| S4 | Bond-value weighting | within each fifth, outcomes weighted by bond_value |
| S5 | Investment-grade universe | universe |
| S6 | All-issuer universe | universe |
| S7 | Spread-change signal | signal = -DCS. Eligible: high-yield, listed at t, DCS not missing; N and the fifths count only those |
| S8 | Three-month formation | signal = CR(t) + CR(t-1) + CR(t-2), an unweighted sum. Eligible: high-yield and listed at t, with an issuer-month (section 4.2) at t-1 and at t-2 in any universe, listed or not |
| S9 | Mean LS by calendar year of the outcome month | n/a |
| S10 | Attrition by fifth | members, share with an outcome, lost final months, stocks whose last row is t, other missing outcomes |
| S11 | Widest imputation at -30% | y = -0.30 for every top-fifth member whose outcome is missing, whatever the reason; LS over the primary's valid months |
| S12 | Long-only form under e2 | section 6.4 with the e2 outcome vector in both of its means (the universe contains the top fifth), over e2's valid months |
| S13 | S11 at -100% | as S11 with y = -1.00. Minus 30% is a convention carried from the draft, not a floor: a delisting for cause can lose everything |

## 9. What a result will not license

1. **Listed issuers only.** Over the formation months 2002-08 to 2024-10, 107,731 high-yield
   issuer-months carry a permno; 83.5% of them have a listed stock at t and 82.4% a recovered
   outcome (probe run 3, under the definition of section 3.2). The largest gaps are a permno that
   never appears in the stock file, and bonds that still trade after the stock's last row (taken
   private, or reorganised). Bonds with no permno at all (a fifth of non-investment-grade
   bond-months) are outside the test altogether, and those are disproportionately private issuers.
2. **Reconstructed returns, and outcomes that are missing for a reason.** Each firm's final month
   is lost: 499 eligible high-yield issuer-months, against 88,801 with an outcome. Criteria (e1)
   and (e2) impute those months at a conventional -30% and do not recover them. They reach nothing
   else. Other eligible issuer-months have no outcome and are not imputed in any criterion:
   a stock whose last row is t (492; there is no later return to recover, and the data cannot say
   whether the position could have been opened); and 171 others, which are stocks listed for fewer
   than sixteen months, some or all of whose returns cannot be rebuilt, the months before a long
   gap in a listing, and months blocked by the guard of section 3.2, which bites after a loss of
   more than 99% over five months and can then block the months five and ten later. All lean
   towards bad outcomes. **The outcome is therefore still conditional on survival for a new
   listing**: one that fails within sixteen months contributes missing outcomes, not bad ones.
   S10 counts every class by fifth; S11 and S13 impute them in the top fifth, with no weight.
   Criterion (d) is not recomputed under imputation; S12 does that, with no weight.
3. **Zeros that are not returns.** A missing return in the middle of a listing is published as
   zero, becomes a seed, and is scored as an outcome of 0%. About 5% of all rebuilt returns since
   1926 are exactly zero; some are genuine.
4. **Validation is self-consistency.** Section 3.3 compares three signals built from one return
   series. It shows the algebra and the files agree. It cannot detect a property of the publisher's
   return itself, such as its treatment of delisting returns, and it is silent on the months that
   cannot be rebuilt. The run validates the stocks of high-yield issuers only; the probe validated
   every stock in the file, to the same precision, which is what S5 and S6 rest on.
5. **Timing of bond-side attributes, unverified.** The documentation does not say as of when the
   rating and the bond-to-permno link are known. If either is assigned with hindsight, universe
   membership at t uses later information.
6. **No price or size.** The release withholds both, so there is no penny-stock filter and no
   value weighting by equity. Equal-weighted returns of distressed stocks carry bid-ask bounce,
   which raises the measured return of the weakest names and works against H1.
7. **Costs are an assumption.** 25 basis points one way is flat across names that differ enormously
   in liquidity, and the short side of (a) ignores borrow cost and availability altogether. Weights
   are not allowed to drift with returns, a name that delists is "sold" at 25 basis points, and no
   closing cost is charged.
8. **One sample.** 267 months, 2002 to 2024. The published effect this follows was documented on
   samples ending between 2013 and 2019.
9. **Timing of the signal.** Bond prices come from the last five business days of the month, so
   the signal is on average a few days stale at the month-end at which the stock position is
   opened. That works against H1, not for it.

## 10. Changes from the draft design, and why

The draft is in the operator's handover of 9 October 2026. Nothing below was changed after any
outcome was seen; none had been computed.

| No. | Change | Why |
|---|---|---|
| 1 | Criterion (e) split into (e1) symmetric and (e2) adversarial, both required | Imputing -30% to every lost final month most plausibly helps H1, since defaults concentrate among issuers whose credit weakened. (e2) imputes the loss only where it hurts |
| 2 | Newey-West, cost and Fama-MacBeth formulas written out (6.2, 6.3, 6.4) | The draft named them without defining them, so two honest implementations could differ. Controls enter as ranks so that a few extreme stock returns cannot set the slope |
| 3 | Inputs pinned by SHA-256, with a refusal on mismatch (2) | The bond data is under revision by its authors and may change |
| 4 | Validation thresholds, minimum cross-section and sample floor declared (3.3, 5.3); a fourth state, UNSCORABLE, added (7.4) | A check that cannot be applied must not be readable as a pass or a fail |
| 5 | "Listed at t" required for eligibility, and defined as a signal row at t (5.1) | A first listing month's missing return is published as zero and would otherwise be scored. A recovered return at t was first admitted as evidence of listing and then removed, because in a stock's first five months it depends on survival to t+11 |
| 6 | Fifths, ties and month validity defined exactly (5.2, 5.3) | Reimplementability |
| 7 | WEAK defined as "not a PASS, and LS positive with t >= 2.0" (7.2) | The draft's two descriptions of WEAK ("t between 2 and 3" and "(a) without the rest") are both covered by this one rule |
| 8 | Halves split by count of valid months (6.5) | The draft said "both halves" without saying of what |
| 9 | Row filter fixed; all three return types kept; US domicile is `country = USA` (4.1) | "Valid bond return" needed a definition; the probe supplied the values |
| 10 | Reconstruction passes repeat until one adds nothing, where the handover said two (3.2) | Identical on the pinned files (the probe converged in two); the rule is now stated instead of the count |
| 11 | Five secondary items added (S1, S3, S11, S12, S13); the draft's list is otherwise kept | S1 and S3 are reading aids for (a) and (b). S11 and S13 impute the outcomes that (e1) and (e2) do not reach; S12 stresses (d) for delisting losses. None carries weight |

Unchanged from the draft: the hypothesis; the universe (at least half of rated bond value
non-investment grade); the signal and its weights; fifths; Newey-West lag 3; the thresholds 3.0,
2.0 and 2.0; 25 basis points; -30%.

**How this text was checked before it was frozen.** A separate agent implemented this
specification blind as `verify.py`. It was given the specification, a note of the retrieval
functions it could call, a harness serving synthetic inputs, and the layout of its output file; it
did not see `run.py`, `cdlib.py` or any number produced by them. It listed every sentence it found
ambiguous, twice. Its lists produced the clarifications in sections 2.2, 2.3, 2.5, 3.3, 4.2, 6.2,
6.3, 6.4, 6.6, 7.4 and 8, the narrowing in row 5 above, limits 2 to 5 of section 9, S11 to S13 and
section 11. On the text as revised, the two implementations were then run on the same synthetic
inputs, once with no effect and once with a planted one: every headline number, the validation
counts and S5 to S8, S11 and S12 agreed to within 4e-15. All of that happened before any outcome
existed on the pinned inputs.

**Stated before the fact, so that it cannot be discovered afterwards:** criterion (d) is hard to
meet by construction. A monthly sort on a bond return that does not persist turns over most of the
top fifth every month, and at 25 basis points on each unit traded that is of the order of 40 basis
points a month of cost. A real effect that is smaller than that will return WEAK, not PASS. That
is the intended behaviour of a kill test and it is not to be relaxed after the result.

## 11. Deviations, and disagreement between the two implementations

Any departure from this file, including a defect found in `run.py` after dispatch, is listed in
`docs/CREDIT_DRIFT_2026-10-09.md` with its effect on every headline number. A defect is corrected
towards this specification and the test is re-run; the first result is kept beside the second.

`verify.py` covers sections 2 to 7 and S5 to S8, S11 and S12. The headline numbers are the verdict,
the number of valid months, and the mean and t (or slope and t) of each criterion. After both have
run on the pinned inputs:

- a difference of at most 1e-9 in every headline number is agreement;
- any larger difference is a **disagreement**. Both numbers are then reported, **no verdict is
  reported as final**, and the difference is traced to a sentence of this file before anything
  else is done. Which implementation is right is decided by that sentence, not by which answer is
  preferred; if the sentence does not decide it, that is a defect of this specification, the test
  is unscorable on that criterion, and it is said so.
