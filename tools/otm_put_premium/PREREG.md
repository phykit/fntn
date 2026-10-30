# Pre-registration: is there a collectable premium in selling 5% out-of-the-money S&P 500 puts?

Written 30 October 2026, before any PPUT, PUT or matched SPY figure was fetched. The seventh test in
this thread. A non-evidentiary side test outside the FNTN funnel. Not investment advice.

## 1. Question and hypothesis

At traded prices the at-the-money index call overwrite (BXM) lagged holding and lowered the Sharpe
ratio (`tools/bxm_real_overwrite`, run 1). The literature places most of the index volatility
premium in out-of-the-money puts, where the skew sits. The operator asked for a test.

The Cboe S&P 500 5% Put Protection Index (PPUT) holds the S&P 500 with dividends reinvested and
buys, at each monthly expiry (third Friday), the first SPX put strike below 95% of the index,
priced at the 11:30 to 12:00 ET volume-weighted average of traded prices (Cboe PPUT methodology,
`verified_primary`, read 30 October 2026). Its return less the S&P 500's is the return of the long
put leg; the seller of those puts earns the reverse.

**Put seller's monthly net**, as a fraction of index notional: `y = r_SPY - r_PPUT`, where `r_SPY`
is SPY's dividend-adjusted return (the S&P 500 total-return proxy).

**H-OTM.** `y` has a positive mean.

**Registered sign: positive.** One-sided. Seventh test in the thread: hurdle one-sided 1%.

**What the analyst has seen.** A practitioner summary (CXO Advisory, read 30 October 2026) reports
PPUT trailing the S&P 500 total return by about 3.3% a year over July 1986 to mid-May 2016, with
beta 0.74. Most of this test's sample before mid-2016 is therefore not blind. The months from
2016-06 onward are reported separately as the part the analyst has not seen summarised; the
analyst has general knowledge of market history to mid-2026 (including the 2020 and 2022 falls).
The analyst predicts SUPPORTED on the full sample and does not predict the unseen sub-period.

## 2. Inputs

- PPUT, PUT (the Cboe S&P 500 at-the-money PutWrite Index, cash-secured) and BXM daily values from
  `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/<INDEX>_History.csv`, columns
  `DATE` (`MM/DD/YYYY`) and the index name. A blank or non-numeric value stays missing.
- SPY daily adjusted close (`auto_adjust=True`) from Yahoo Finance via `yfinance`, from 1993-01-01.
- `fetch.py` writes `data/series.csv` (columns `date, PPUT, SPY, PUT, BXM`); structure only printed.

## 3. Definitions

- A month's value of a series is the last date in the calendar month on which **PPUT and SPY are
  both present**; the same date is used for PUT and BXM (missing there means that series has no
  value that month). Monthly return = that value over the previous calendar month's value, minus
  1; a month whose previous calendar month has no value has no return. Months run to 2026-09.
  `n` is the number of months with both PPUT and SPY returns; INSUFFICIENT if `n < 120`.
- `y = r_SPY - r_PPUT` per month.

## 4. Test and verdict

Mean of `y` with a Newey-West standard error (3 lags, Bartlett `1 - l / 4`, no small-sample
correction, constant-only regression); `t = mean / se`.

INSUFFICIENT if `n < 120`; SUPPORTED if `mean(y) > 0` and `t >= t_crit`; NOT SUPPORTED otherwise.

**Critical value `t_crit` (block-bootstrap t).** `rng = numpy.random.default_rng(20261106)`;
`B = 1999` replications drawn together as `starts = rng.integers(0, n - 11, size=(1999,
ceil(n / 12)))`; replication `b`'s month list is the concatenation of `range(s, s + 12)` over row `b`
of `starts`, in order, truncated to `n`; `t*_b = (mean(y*_b) - mean(y)) / se_NW(y*_b)` with the same
Newey-West estimator; `t_crit = numpy.percentile(t*, 99)`.

*Amendment, 30 October 2026, before any input was fetched.* As first committed (`ff4991c`) the
critical value was the normal 2.326. The self-test showed that on synthetic data shaped like a
short put's returns (small gains, 8% of months a large loss) with a true mean of zero, `t >= 2.326`
occurred in 3.75% of 2,000 worlds, nearly four times the nominal 1%; the null `t`'s 99th percentile
was 3.36. Negative skew inflates the upper tail of the t statistic, so the normal critical value is
biased towards SUPPORTED on exactly this kind of data. On the same worlds the block-bootstrap t held
0.75% (400 worlds). Its cost, stated: power against a true premium of +0.3% a month fell to 43%
(200 worlds), so a premium of that size can be missed. The normal-critical-value verdict is reported
without weight.

## 5. Reported without weight

- `t_crit`, and the verdict under the normal critical value 2.326 (`verdict_normal`).
- `mean(y)` and `t` in two sub-periods: months to 2016-05 (summarised before; not blind) and from
  2016-06 (the unseen sub-period).
- `y`: annualised mean (`12 * mean`), sd, ratio `mean / sd`, skewness (`mean(e^3) / sd_pop^3`),
  worst month, share of months with `y < 0`, and the sum of `y` over the 5 worst months as a share
  of the sum of all positive months.
- **Overlay on held stock.** `k = r_SPY + y` (hold the S&P 500 and sell one 5% out-of-the-money put
  per unit, so equity exposure rises in a fall). Annualised mean, volatility, Sharpe (rate 0),
  maximum drawdown and downside ratio `mean / sqrt(mean(min(x, 0)^2))` for `k` and `r_SPY`;
  `Delta_k = Sh(k) - Sh(r_SPY)` monthly, with a moving-block bootstrap (`rng =
  numpy.random.default_rng(20261105)`, `B = 2000`, block 12, starts `rng.integers(0, n - 11,
  size=ceil(n / 12))`, concatenated in draw order and truncated to `n`), reporting its 5th and 95th
  percentiles.
- **At-the-money comparators at traded prices.** Over months where PUT, BXM and SPY all have
  returns: annualised mean, volatility, Sharpe and maximum drawdown of PUT (cash-secured
  at-the-money put writing) and BXM, beside SPY.

## 6. Self-test, independent check

1. `selftest.py`: with synthetic monthly `y` (n = 400) shaped as above with population mean 0,
   SUPPORTED in no more than 2 of 40 worlds; with population mean +0.8% a month and the same shape,
   SUPPORTED in 8 of 8; the Newey-West standard error at 0 lags equals `sqrt(sum e^2) / n`; maximum
   drawdown of `[+0.10, -0.20, +0.05, -0.10]` is `-0.244`; same seed gives identical bootstrap
   draws.
2. `verify.py` is a second implementation by a separate agent from this document alone.
   `compare.py` requires `n`, the first and last month, the verdict, `mean(y)` (1e-12), `t` and
   `t_crit` (1e-9), and both sub-period means (1e-12) to agree.

## 7. Disclosures

1. Not blind before mid-2016 (section 1).
2. SPY carries a fee of about 0.09% a year (`recollection`) that PPUT's index does not; it lowers
   `y` by under 0.01% a month, against the hypothesis.
3. PPUT's put is bought at a traded VWAP, so the seller's `y` is before the seller's own spread;
   a real seller nets slightly less. No margin or financing costs.
4. A short put is a crash-exposed position. A positive mean is compensation for that exposure, not
   free money; the skewness, worst month and drawdown rows exist to show its size.
5. The calendar months used here are not the options' expiry cycle; this affects the timing of
   each month's figure, not the sum over the sample.
