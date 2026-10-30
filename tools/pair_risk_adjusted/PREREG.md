# Pre-registration: is the covered-call excess over holding better per unit of risk when the two stocks are less correlated?

Written 30 October 2026 as a follow-up to `tools/single_name_vrp/` (run 3, run id 41055269824),
on the same inputs and months. A non-evidentiary side test outside the FNTN funnel. Not
investment advice.

## 1. Question and hypothesis

The operator asked whether lower correlation adds a risk-adjusted premium even though it adds no
premium. Arithmetic says the excess over holding becomes steadier as correlation falls, so its
ratio of mean to volatility (the information ratio, IR) should rise in magnitude whatever its
sign. Whether that ratio is better (more positive) at low correlation on real prices is the
question.

**H-RA.** Within each pair of names, the covered-call excess over holding has a higher IR in the
months when the pair's trailing correlation is below its median than in the months when it is at or
above it.

**Registered sign: positive** (low-correlation IR minus high-correlation IR). One-sided. It is the
direction the operator's thesis implies.

**What the analyst has already seen, stated before this test.** Run 3 of `tools/single_name_vrp`
reported, without weight, the pooled mean excess of pair-months below and at or above the pooled
median trailing correlation: -0.43% and -0.89% of spot a month. That is the numerator of a
closely related statistic, and it leans towards the registered sign. This test is therefore not
blind, and a SUPPORTED verdict is weaker evidence than it would otherwise be. It has not seen any
standard deviation, any IR, or any within-pair split.

**The analyst's prior.** The mean excess is negative for every name, so a steadier excess makes
the IR more negative, not less. Against that, the seen means favour low correlation by about
0.46% a month. The analyst does not predict the verdict.

## 2. Inputs and per-name quantities

Exactly those of `tools/single_name_vrp/PREREG.md` sections 2 and 3, fetched by the frozen
`tools/single_name_vrp/fetch.py` (unchanged; its hash is verified in the run), including the
section 2 amendment (CBOE source). From those definitions, for each used name-month (i, t0):

- `G_i = P_i(T1) / P_i(t0)`;
- the covered-call excess over holding `y_i = c_i - max(G_i - 1, 0)`, with `c_i` the at-the-money
  Black-Scholes premium of section 4.3 there (volatility `VX_i(t0) / 100`, rate 0, time
  `21 / 252`);
- for each pair (a, b), the trailing correlation `c_ab(t0)`: the Pearson correlation of the two
  names' daily log returns over the 252 trading days ending at and including `t0` (the beta
  window there).

## 3. Sample

`U` is the set of formation days on which all five names are used (section 3 there) **and which
fall on or before 2026-09-01**, the last month of run 3, so that the sample is run 3's. `n = |U|`.
Every pair uses every month in `U`. If `n < 120` the verdict is INSUFFICIENT.

## 4. Definitions per pair

For each of the 10 pairs p = (a, b) in the order AAPL-AMZN, AAPL-GOOG, AAPL-GS, AAPL-IBM,
AMZN-GOOG, AMZN-GS, AMZN-IBM, GOOG-GS, GOOG-IBM, GS-IBM, and each month in a set S of months:

- pair excess `y_p = (y_a + y_b) / 2`;
- held pair return `h_p = (G_a + G_b) / 2 - 1`; covered pair return `k_p = h_p + y_p`;
- `IR(S) = mean(y_p over S) / sd(y_p over S, ddof 1)`, monthly, not annualised;
- the median `med_p(S)` = `numpy.median` of `c_p` over S; the low half `L` is the months of S with
  `c_p < med_p(S)`, the high half `H` those with `c_p >= med_p(S)`;
- `delta_p(S) = IR(L) - IR(H)`;
- `D(S)` = the mean of `delta_p(S)` over the 10 pairs.

The statistic is `D = D(U)`.

## 5. Inference and verdict

- **Moving-block bootstrap over months**, resampling the same months for every pair so that the
  dependence between pairs is kept. Block length 12. `rng = numpy.random.default_rng(20261031)`.
  For each of `B = 2000` replications, in order: draw `nb = ceil(n / 12)` block starts with
  `rng.integers(0, n - 11, size=nb)`; the replication's month list is the concatenation, in draw
  order, of positions `s, s+1, ..., s+11` of `U` (ordered by date) for each start `s`, truncated to
  its first `n` entries; compute `D*` on that list exactly as section 4 (a month drawn twice
  counts twice). If any `IR` in a replication has a zero standard deviation, that replication is
  discarded and counted.
- `lower = numpy.percentile(D*, 5)` over the kept replications (default linear interpolation).
- **Verdict.** INSUFFICIENT if `n < 120`. REFUSED if more than 20 replications are discarded.
  SUPPORTED if `D > 0` and `lower > 0`. NOT SUPPORTED otherwise.

## 6. Reported without weight

- Per pair: mean `c_p` over U; mean, sd and `IR` of `y_p` over U, over L and over H;
  `delta_p(U)`; and the diversification ratio `sd(y_p) / ((sd(y_a) + sd(y_b)) / 2)` over U.
- Per name: mean, sd and IR of `y_i` over U.
- Across the 10 pairs: the Spearman rank correlation (average ranks for ties) between mean `c_p`
  and full-sample `IR(U)`, and between mean `c_p` and the diversification ratio.
- The decomposition of D: the mean over pairs of `mean(y_p over L) - mean(y_p over H)` and of
  `sd(y_p over L) - sd(y_p over H)`.
- Per pair Sharpe ratios over U at rate 0 (`mean / sd`, monthly): held pair `h_p`, covered pair
  `k_p`, and covered minus held; and their means over pairs.
- The bootstrap's mean of `D*`, its 5th and 95th percentiles, and the count discarded.
- **Reconciliation with run 3.** Pooled over pairs and months of U, the mean `y_p` (in per cent)
  of pair-months below and at or above the pooled median `c_p`. Run 3 reported -0.4320 and
  -0.8870 on its month set, which U is built to equal; a difference beyond 1e-6 is reported, not
  acted on, since a re-fetch of adjusted prices can move the last digits.

## 7. Self-test, independent check

1. `selftest.py`, on the implementation's own functions, with synthetic per-name `y`, `G` and
   per-pair `c` arrays over 187 months: a world in which every pair's `y_p` has the same mean and
   standard deviation in both halves (null) gives SUPPORTED in no more than 4 of 40 worlds (with
   `B = 500` to keep the self-test short); a world in which `y_p` has mean +0.5% in L and -0.5% in
   H at the same standard deviation of 3% gives SUPPORTED in 8 of 8; the IR of `[1, 2, 3]` is
   `2 / 1`; the median rule puts a value equal to the median in H; and two calls with the same seed
   give identical `D*`.
2. `verify.py` is a second implementation written by a separate agent from this document and
   `tools/single_name_vrp/PREREG.md` alone. `compare.py` requires `n`, the verdict, `D` (to 1e-9),
   `lower` (to 1e-9), the discard count, and every per-pair `IR(U)`, `delta_p(U)` and Sharpe figure
   (to 1e-9) to agree.

## 8. Disclosures

1. Not blind, as section 1 states.
2. Splitting each pair's months by its trailing correlation also splits by market regime: high
   correlation follows market-wide stress. A difference between halves may reflect the regime and
   not the correlation. The test cannot separate the two.
3. Five surviving large caps, 2011 to 2026; ten pairs drawn from them share names and are not
   independent; the bootstrap keeps that dependence but cannot add breadth.
4. The excess is the proxy of `tools/single_name_vrp/PREREG.md` section 4.3: priced at the CBOE
   index level, which includes the skew, so it overstates the at-the-money premium. That bias is a
   level shift common to both halves and largely cancels in `D`, but not exactly.
5. The analyst is a language model with general knowledge of market history to mid-2026.
