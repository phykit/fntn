# Pre-registration: does writing the index call only when the volatility term structure slopes upward improve the index overwrite?

Written 30 October 2026, before any three-month VIX figure was fetched or seen. The fifth test in
this thread (after `tools/covered_call_pair_mc`, `tools/single_name_vrp`,
`tools/pair_risk_adjusted` and `tools/index_vs_single_overwrite`). A non-evidentiary side test
outside the FNTN funnel. Not investment advice.

## 1. Question and hypothesis

The operator asked whether a calendar element could make the index covered call more profitable,
and chose a term-structure filter: write the month's call only when the one-month VIX is below the
three-month VIX (contango), and otherwise hold SPY without a call.

**H-TS.** The filtered overwrite has a higher Sharpe ratio than the overwrite written every month.

**Registered sign: positive** (filtered minus always). One-sided.

**The analyst's prior: the sign is uncertain.** Johnson (2017, Journal of Financial Economics,
`recollection`) finds the slope of the VIX term structure predicts returns on variance assets, and
backwardation coincides with stress. But a covered call is not a variance asset. In a month that
starts in backwardation the premium is unusually large and a crash leaves the call worthless, which
helps the overwrite; a sharp rebound gives the upside away, which hurts it. The analyst does not
predict the verdict, and expects few backwardation months (perhaps 10% to 15%), so power is low.

**Multiple testing.** This is the fifth pre-registered test in the thread. The hurdle is therefore
set at one-sided 1% (the bootstrap 1st percentile), roughly a Bonferroni correction of 5% over five
tests, not the 5% used in the earlier tests.

**What the analyst has already seen.** The index overwrite's figures over February 2011 to
September 2026 (`tools/index_vs_single_overwrite`, run 1): mean excess over holding -0.22% a
month, Sharpe held 0.30 and covered 0.44 a month. Nothing has been split by the term structure.

## 2. Inputs

- CBOE published histories, column `CLOSE`, dates `MM/DD/YYYY`, from
  `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/<INDEX>_History.csv` for `VIX`
  and `VIX3M`. A blank or non-numeric close stays missing.
- SPY daily adjusted closes (`auto_adjust=True`) from Yahoo Finance via `yfinance`, from
  2009-01-01.
- `fetch.py` writes `data/vx.csv` (columns `date, MKT, M3`) and `data/prices.csv` (columns
  `date, SPY`), and prints only structure.

## 3. Definitions

- Trading days are the dates with a SPY price. `t0` is the first trading day of each calendar
  month with at least 21 trading days after it; `T1` is the 21st trading day after `t0`.
- A month is **used** when `VIX(t0)` and `VIX3M(t0)` are both present (read at `t0` exactly) and
  `t0` falls on or before 2026-09-01. `U` is the set of used months; `n = |U|`; INSUFFICIENT if
  `n < 120`.
- `G = P_SPY(T1) / P_SPY(t0)`; held `h = G - 1`; excess `y = c(VIX(t0) / 100) - max(G - 1, 0)`,
  where `c(s) = N(d1) - N(-d1)`, `d1 = s * sqrt(21 / 252) / 2`, `N(x) = 0.5 * erfc(-x / sqrt(2))`
  (the at-the-money call per unit of spot, rate 0); always-written covered `k_A = h + y`.
- Contango indicator `W = 1` if `VIX(t0) < VIX3M(t0)`, else `0`. Filtered covered
  `k_F = h + W * y`.
- `Sh(x) = mean(x) / sd(x, ddof 1)`, monthly, rate 0.

## 4. Statistic, inference, verdict

`Delta = Sh(k_F) - Sh(k_A)`.

Moving-block bootstrap over months: `rng = numpy.random.default_rng(20261102)`, `B = 2000`,
block length 12; each replication draws `ceil(n / 12)` starts with `rng.integers(0, n - 11,
size=...)`, concatenates `range(s, s + 12)` for each start in draw order, truncates to `n`, and
recomputes `Delta*` on those months (duplicates count). A replication in which `k_F` or `k_A` has
zero standard deviation is discarded and counted. `lower = numpy.percentile(Delta*, 1)` over the
kept replications.

Verdict: INSUFFICIENT if `n < 120`; REFUSED if more than 20 replications are discarded; SUPPORTED
if `Delta > 0` and `lower > 0`; NOT SUPPORTED otherwise. Figures are reported whenever `n >= 12`.

## 5. Reported without weight

- `n`, the number of backwardation months `n_back = n - sum(W)`, and their dates.
- Mean and sd of `y` (per cent) in contango months and in backwardation months.
- `Sh` of `h`, `k_A` and `k_F`, monthly and annualised (`* sqrt(12)`); `Sh(k_F) - Sh(h)`.
- Mean of `k_F - k_A` (per cent a month; equal to minus the mean of `(1 - W) * y`) with a
  Newey-West t (3 lags, Bartlett `1 - l / 4`, no small-sample correction, constant-only).
- Annualised mean return of `h`, `k_A` and `k_F` (`12 * mean`).
- The bootstrap mean of `Delta*`, its 5th and 95th percentiles, and the count discarded.
- **Sensitivity rows.** `Delta` with the threshold moved to `VIX(t0) / VIX3M(t0) < 0.95` (write
  only in steeper contango); and `Delta` with every call priced at `0.9 * VIX(t0) / 100` (the skew
  correction used in the previous test, `recollection`, fitted to nothing).

## 6. Self-test, independent check

1. `selftest.py`: on synthetic monthly arrays (n = 204), a null world in which `y` has the same
   distribution whatever `W` is gives SUPPORTED in no more than 2 of 40 worlds (`B = 500`); a world
   in which `y` has mean +0.3% in contango and -3% in backwardation (about 15% of months) gives
   SUPPORTED in 8 of 8; `Sh([1, 2, 3]) = 2`; the at-the-money premium at `s * sqrt(21/252) = 0.2`
   equals `N(0.1) - N(-0.1)`; same seed gives identical `Delta*`.
2. `verify.py` is a second implementation by a separate agent from this document alone.
   `compare.py` requires `n`, `n_back`, first and last month, the verdict, `Delta` and `lower`
   (1e-9), the discard count, and the three Sharpe ratios (1e-9) to agree.

## 7. Disclosures

1. Few backwardation months: the test can find only a large effect.
2. The excess is priced from the VIX, which includes the skew and overstates the at-the-money
   premium; the bias is roughly proportional in both regimes and is checked by a sensitivity row.
3. One index, one sample path from late 2009, no transaction costs. Writing in only some months
   saves the cost of the calls not written; that small saving is ignored.
4. Not blind (section 1). The analyst is a language model with general knowledge of market
   history to mid-2026, including the dates of the major volatility spikes in this sample.
