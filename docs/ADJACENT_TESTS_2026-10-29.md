# Adjacent tests: volatility-managed momentum, GVIP concentration, aggregate short interest

Run 29 October 2026, GitHub Actions run ids 40959765194 (run 1, commit `b6117e0`) and 40960035674
(run 2, `749ff56`; a refetch after run 1's short-interest comparison failed on an interface mismatch
in the data header, not in either implementation; every figure of the two completed tests is
identical across the runs except MTUM's alpha t in the sixth decimal, from one further day of Yahoo
prices). Pre-registrations committed at `939c563` before any data: `tools/volmom/PREREG.md`,
`tools/gvip_concentration/PREREG.md`, `tools/short_interest/PREREG.md`. Each test has an
independent second implementation written from its PREREG alone; all three agree on every mandated
figure. Non-evidentiary side tests outside the FNTN funnel; not investment advice; nothing here
authorises a position.

These three tests were run at the operator's request after the de-gross programme
(`docs/FOLLOWUP2_2026-10-29.md`) closed without a tradeable result. They are the adjacent
published ideas, not reframings of the de-gross data.

## 1. Volatility-managed momentum, out of sample 2016 to 2026: PASS

Barroso and Santa-Clara (2015) scaling of the French momentum factor by inverse realised volatility
(126-day window, 12% target), judged after both papers' publication.

| | In-sample 1927 to 2015 (replication) | **Out of sample 2016-01 to 2026-09 (129 months)** |
|---|---|---|
| Sharpe, raw factor | 0.49 | 0.15 |
| Sharpe, managed | 0.88 | **0.39** (ratio 2.6; bootstrap p 0.004) |
| Moreira-Muir alpha of managed on raw | 0.71% a month, t 6.5 | **0.24% a month, t 2.6** |
| Maximum drawdown, raw / managed | n/a | -35% / **-21%** |
| Weights (OOS) | n/a | 0.30 to 1.54, median 0.83; never above 2 |

Both criteria met: **PASS**. The five worst raw months (January 2023 -13.7%, April 2020 -12.2%,
November 2020 -12.0%, July 2026 -10.9%, March 2021 -8.7%) were cut to -6.5%, -10.7%, -4.1%, -6.2%
and -3.3% by the scaling, which is the mechanism the papers describe: momentum crashes arrive in
high-volatility states, when the weight is already low.

**Implementable version, long MTUM short SPY, November 2013 to September 2026 (155 months): PASS.**
Sharpe 0.20 to 0.40 (p 0.018), alpha 0.24% a month (t 2.0), managed spread return 4.4% a year
(geometric; 5.1% arithmetic in the second implementation, the one definitional difference between
them), estimated switching cost 0.28% a year. **Its maximum drawdown was deeper managed than raw**
(-31.7% against -28.7%): the scaling improves the average, not every path.

**What this does and does not license.** The published effect persisted for a decade after
publication, at the factor level and in a tradeable ETF spread. It is a modest edge: a Sharpe ratio
of about 0.4 on a long-short spread, about 4% a year at 11% volatility, before borrow on the SPY leg.
In a long-only book of about GBP 100,000 the natural form is an overweight of MTUM against the
index with the overweight scaled by realised volatility, which has not been tested here. It is not
a Nasdaq 100 signal, and it is not novel: the contribution is the out-of-sample check.

## 2. GVIP's shortfall against QQQ is concentration exposure: CONCENTRATION EXPLAINS

December 2016 to September 2026, 118 months. GVIP minus QQQ regressed on QQQE minus QQQ (equal-weight
Nasdaq 100 less cap-weight):

| | Coefficient | t |
|---|---|---|
| Loading on the equal-weight spread | **0.71** | 7.3 |
| Residual (alpha) | -0.05% a month | -0.3 |
| R-squared | 0.35 | |
| GVIP minus QQQE, annual excess | +1.1% | 0.5 |

Both halves agree (loadings 0.81 and 0.65, alphas t -0.7 and +0.2). The same regression on
RSP minus SPY gives a loading of 0.79 (t 6.8) and alpha t -1.2. GVIP's 4.9% a year shortfall against
QQQ is the cap-weighted index's concentration premium over the decade; against the equal-weight
Nasdaq 100 the fund is level. **"Long QQQ, short GVIP" is a bet that the largest names keep
outrunning the next fifty; it is not an anomaly, and it is closed.**

## 3. Aggregate short interest (Rapach, Ringgenberg and Zhou) and the Nasdaq 100: FAIL

The authors' updated index (1973 to 2021, from Rapach's data page; the probe is in the PREREG's
terms) recursively detrended, against the next month's Nasdaq 100 excess return, January 1986 to
December 2021, 432 months.

| Criterion | Requirement | Result |
|---|---|---|
| Primary: slope negative, shift p <= 0.025 | | slope -0.0065 per sd of the signal; **p 0.032**; Newey-West t -2.22 |
| Secondary: out-of-sample R-squared > 0, Clark-West t >= 1.65 | | R-squared 0.35%, t 2.04: met |

**FAIL (right sign, just outside the registered bar).** The in-sample R-squared is 0.9%, about half
the published figure for the S&P 500 and below the 1.4% that 432 months can detect at 80% power.
Both halves have a negative slope; in the 84 months after the paper's sample (2015 to 2021) the
slope is negative with t -0.5. The honest reading is that the published relationship is weakly
present for the Nasdaq 100 and too small to be a usable predictor: 0.35% of next-month variance
explained out of sample is not a signal a reader could act on, and the series ends in 2021.

## Disclosures

1. The analyst is a language model that knows all three papers and the market history of every
   sample; none of the samples is unseen.
2. Momentum: the French factor is costless and long-short; the ETF version carries costs and a 2013
   start. Concentration: expense ratios inside all returns. Short interest: the published index was
   detrended on its full sample by the authors; the recursive residual is invariant to that, as both
   implementations verified on synthetic data.
3. No test here used the de-gross episode data; the multiplicity of today's programme (three
   further tests) is noted, and the one PASS is a replication of a published result, not a
   discovery.
