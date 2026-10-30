# Pre-registration: does the index overwrite improve risk-adjusted return at real option prices?

Written 30 October 2026, before any BXM figure was fetched or seen. The sixth test in this thread.
A non-evidentiary side test outside the FNTN funnel. Not investment advice.

## 1. Question and hypothesis

`tools/index_vs_single_overwrite` (run 1) found the index overwrite raised the monthly Sharpe
ratio from 0.30 to 0.44 over 2011 to 2026, with calls priced from the VIX, which includes the skew
and overstates the at-the-money premium. This test replaces the proxy with real prices: the Cboe
S&P 500 BuyWrite Index (BXM), which holds the S&P 500 with dividends and sells a one-month
at-the-money S&P 500 call each month at traded prices, against SPY held with dividends.

**H-BXM.** BXM's monthly Sharpe ratio exceeds SPY's.

**Registered sign: positive.** One-sided.

**Multiple testing.** Sixth test in the thread: one-sided 1% hurdle, as the fifth.

**What the analyst knows already.** In general terms (`recollection`), BXM is documented as giving
return close to the S&P 500 with markedly lower volatility over 1988 to 2001 (Whaley 2002), and as
lagging the S&P 500 in return through the long rally after 2009. No BXM figure for this sample has
been computed or seen in this project. The VIX-proxy result above is known. The analyst predicts a
smaller Sharpe improvement than the proxy showed, and does not predict the verdict.

## 2. Inputs

- BXM daily close: `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/BXM_History.csv`,
  columns `DATE` (`MM/DD/YYYY`) and `BXM`. A blank or non-numeric value stays missing.
- SPY daily adjusted close (`auto_adjust=True`, dividends reinvested) from Yahoo Finance via
  `yfinance`, from 2002-01-01.
- VIX daily close from CBOE, as `tools/ts_filter_overwrite`, for the proxy reconciliation only.
- `fetch.py` writes `data/series.csv` (columns `date, BXM, SPY, VIX`) and prints structure only.

## 3. Definitions

- **Monthly return** of a series: last value in the calendar month on which both BXM and SPY are
  present, divided by the same for the previous calendar month, minus 1. Months run from the first
  calendar month after the first month with both series present to September 2026. `n` = number
  of months; INSUFFICIENT if `n < 120`.
- `Sh(x) = mean(x) / sd(x, ddof 1)`, monthly, rate 0.

## 4. Statistic, inference, verdict

`Delta = Sh(BXM) - Sh(SPY)`.

Moving-block bootstrap over months: `rng = numpy.random.default_rng(20261104)`, `B = 2000`, block
length 12, drawing `ceil(n / 12)` starts with `rng.integers(0, n - 11, size=...)`, concatenating
`range(s, s + 12)` in draw order, truncating to `n`, recomputing `Delta*`; a replication with a
zero standard deviation is discarded and counted. `lower = numpy.percentile(Delta*, 1)`.

Verdict: INSUFFICIENT if `n < 120`; REFUSED if more than 20 replications are discarded; SUPPORTED
if `Delta > 0` and `lower > 0`; NOT SUPPORTED otherwise.

## 5. Reported without weight

- For BXM and SPY: annualised mean (`12 * mean`), annualised volatility (`sqrt(12) * sd`),
  annualised Sharpe (`sqrt(12) * Sh`), maximum drawdown of the compounded monthly series, and the
  downside ratio `mean / sqrt(mean(min(x, 0)^2))` (monthly), which does not count upside swings as
  risk.
- `Delta` in each of two sub-periods: months up to and including 2010-12, and months from 2011-01.
- Monthly difference `BXM - SPY`: mean (per cent) and Newey-West t (3 lags, Bartlett `1 - l / 4`,
  no small-sample correction, constant-only), over the whole sample and from 2011-01.
- **Proxy reconciliation.** Over months from 2011-02 to 2026-09, the mean of `BXM - SPY` in per
  cent a month, set beside the VIX-proxy index excess of `tools/index_vs_single_overwrite` run 1
  (-0.2214% a month over formation months 2011-02 to 2026-09). The two are on different monthly
  cycles (calendar month against the first-trading-day cycle; BXM rolls at the monthly expiry), so
  the comparison is of levels only.
- Bootstrap mean, 5th and 95th percentiles of `Delta*`; the count discarded.

## 6. Self-test, independent check

1. `selftest.py`: with synthetic monthly series (n = 290), when the two series have equal Sharpe
   ratios (null) SUPPORTED occurs in no more than 2 of 40 worlds (`B = 500`); when one has a
   Sharpe ratio 0.15 a month higher, SUPPORTED in 8 of 8; `Sh([1, 2, 3]) = 2`; maximum drawdown of
   `[+0.10, -0.20, +0.05, -0.10]` is `-0.244`; same seed gives identical `Delta*`.
2. `verify.py` is a second implementation by a separate agent from this document alone.
   `compare.py` requires `n`, first and last month, the verdict, `Delta` and `lower` (1e-9), the
   discard count, and both Sharpe ratios (1e-9) to agree.

## 7. Disclosures

1. BXM is the S&P 500 index; SPY is a fund tracking it with a fee of about 0.09% a year
   (`recollection`), which lowers SPY's return slightly against BXM.
2. BXM has no trading costs or bid-ask spread on the calls; a real overwriter pays them, which
   lowers its return relative to BXM.
3. Sharpe counts upside volatility as risk, which a call sells; the downside ratio is reported for
   that reason.
4. One index, one path, 2002 to 2026. Not blind (section 1). The analyst is a language model with
   general knowledge of market history to mid-2026.
