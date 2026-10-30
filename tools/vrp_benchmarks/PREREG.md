# Pre-registration: do Cboe's option-selling benchmarks earn a return beyond their equity exposure?

Written 30 October 2026, before any WPUT or CNDR figure was fetched or seen. The eighth test in this
thread. A non-evidentiary side test outside the FNTN funnel. Not investment advice.

## 1. Question and hypotheses

The thread so far: the index volatility premium is real (5% out-of-the-money puts, about +3% a year,
`tools/otm_put_premium`), but no covered call or short put added to a held index improved its Sharpe
ratio, because the premium is payment for the same crash risk the shares already carry. The
operator asked whether a strategy can harvest the premium, and chose a comparison of Cboe's traded-
price benchmarks. Three cash-secured strategies, each holding one-month Treasury bills
(`verified_secondary`: Cboe descriptions read 30 October 2026):

- **PUT**: sells a one-month at-the-money SPX put each month.
- **WPUT**: sells a one-week at-the-money SPX put each week (shorter maturity).
- **CNDR**: monthly iron condor: sells puts and calls of about 0.20 delta, buys puts and calls of
  about 0.05 delta (defined risk, both tails).

The question is whether each earns more than its exposure to the S&P 500 explains.

**H-PUT, H-WPUT, H-CNDR.** In a regression of the strategy's monthly excess return (over the bill
rate) on SPY's monthly excess return, the intercept (alpha) is positive.

**Registered sign: positive** for each. One-sided.

**Multiple testing.** Three hypotheses, eighth test in the thread. Family-wise one-sided 1% across
the three: each is judged at one-sided 1/3% (critical value at the 99.667th percentile).

**What the analyst knows.** In general terms (`recollection`): Bondarenko's Cboe-commissioned study
(2016) reports PUT with returns close to the S&P 500's at lower volatility over 1986 to 2015, and
WPUT with lower returns than PUT. The analyst read the PUT/BXM/SPY figures over 2007 to 2026 from
`tools/otm_put_premium` run 1 (PUT Sharpe 0.70 at rate 0, SPY 0.75). Nothing about CNDR and no alpha
has been computed or seen. The analyst predicts PUT alpha positive but not significant at this
hurdle, WPUT below PUT, and does not predict CNDR.

## 2. Inputs

- PUT, WPUT and CNDR daily values from
  `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/<INDEX>_History.csv`, columns `DATE`
  (`MM/DD/YYYY`) and the index name; a blank or non-numeric value stays missing.
- SPY daily adjusted close (`auto_adjust=True`) from Yahoo Finance via `yfinance`, from 2005-01-01.
- The 13-week Treasury bill yield, `^IRX` close (per cent a year, discount basis) from Yahoo Finance
  via `yfinance`, from 2005-01-01.
- `fetch.py` writes `data/series.csv` (columns `date, SPY, IRX, PUT, WPUT, CNDR`); structure only.

## 3. Definitions

- A month's value of a series is its value on the last date in the calendar month on which **SPY,
  IRX, PUT, WPUT and CNDR are all present**. Monthly return = value over the previous calendar
  month's value, minus 1; a month whose previous calendar month has no such date has no return.
  Months run to 2026-09. `n` = number of months with a return; INSUFFICIENT if `n < 120`.
- Monthly bill rate for month m: `rf_m = IRX_(m-1) / 100 / 12`, the previous month-end's yield.
- Excess return: `x = r - rf` for each of SPY, PUT, WPUT and CNDR.
- For strategy S: OLS of `x_S` on `x_SPY` with intercept; alpha `a_S` is the intercept, `b_S` the
  slope. Standard error of `a_S`: Newey-West, 3 lags, Bartlett `1 - l / 4`, no small-sample
  correction, sandwich `(X'X)^-1 S (X'X)^-1`; `t_S = a_S / se(a_S)`.

## 4. Inference and verdict

**Critical value (block-bootstrap t), per strategy.** `rng = numpy.random.default_rng(20261107)`;
one draw `starts = rng.integers(0, n - 11, size=(1999, ceil(n / 12)))` shared by all three
strategies; replication `b`'s months = concatenation of `range(s, s + 12)` over row `b` in order,
truncated to `n`; on those months (pairs of `x_S`, `x_SPY` kept together) refit and compute
`t*_b = (a*_b - a_S) / se(a*_b)`; `c_S = numpy.percentile(t*, 100 - 100/3)` (the 99.667th
percentile). The bootstrap-t is used because option-selling returns are strongly negatively skewed,
under which the normal critical value over-rejects (`tools/otm_put_premium`, PREREG section 4).

Verdict per strategy: INSUFFICIENT if `n < 120`; SUPPORTED if `a_S > 0` and `t_S >= c_S`; NOT
SUPPORTED otherwise. There is no combined verdict; each is reported.

## 5. Reported without weight

- Per strategy and SPY: annualised mean excess return (`12 * mean`), annualised volatility, excess
  Sharpe (`sqrt(12) * mean(x) / sd(x)`), maximum drawdown of the compounded total-return series,
  skewness (`mean(e^3) / sd_pop^3`), worst month (total return).
- Per strategy: `b_S`, annualised alpha (`12 * a_S`), `t_S`, `c_S`, correlation with SPY.
- Differences in monthly excess Sharpe, WPUT minus PUT and CNDR minus PUT, with moving-block
  bootstrap 5th and 95th percentiles from the same index draws.
- Each strategy's alpha t against the normal critical value at one-sided 1/3% (2.713), as
  `verdict_normal`.

## 6. Self-test, independent check

1. `selftest.py`, on synthetic monthly data (n = 248): SPY excess with mean 0.6% and sd 4.3%; a
   strategy `x_S = 0.5 * x_SPY + e` with `e` short-put-shaped (8% of months a large loss) and
   population mean 0: SUPPORTED in no more than 2 of 40 worlds; the same with `e` shifted by +1.0% a
   month: SUPPORTED in 8 of 8; the OLS slope of `[1, 2, 3, 4]` on `[0, 1, 2, 3]` is 1 and intercept
   1; Newey-West at 0 lags equals White's estimator; same seed gives identical `c_S`.
2. `verify.py` is a second implementation by a separate agent from this document alone.
   `compare.py` requires `n`, first and last month, each strategy's verdict, `a_S`, `b_S` (1e-12),
   `t_S` and `c_S` (1e-9) to agree.

## 7. Disclosures

1. Three strategies on one index and one 20-year path; they are correlated, so the bootstrap shares
   its draws.
2. The indices carry no bid-ask spread on the options; a real seller nets less, and WPUT, trading 52
   times a year, would lose most to costs.
3. `^IRX` is a discount yield, not the bills the indices actually hold; small mismatch.
4. SPY's fee (about 0.09% a year, `recollection`) slightly favours the strategies' alphas.
5. Not blind for PUT (section 1). The analyst is a language model with general knowledge of market
   history to mid-2026.
