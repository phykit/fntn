# Pre-registration: do single-stock options carry a premium on company-specific volatility?

Written 30 October 2026, before any input to this test was fetched or seen. A non-evidentiary side
test outside the FNTN funnel. Not investment advice.

## 1. Question and hypothesis

The operator's thesis: a two-stock portfolio that sells a call on each stock every month earns more
than holding the two stocks, and the excess is larger when the two stocks are less correlated. The
Monte Carlo theory check of the same day (`tools/covered_call_pair_mc/`, verdict NOT SUPPORTED)
showed that the excess over holding equals the premium the calls are sold at above their fair
value, and that correlation cannot raise that excess unless the premium attaches to the
company-specific (idiosyncratic) part of each stock's variance. If the market charges a premium
only on the market-driven (systematic) part, low correlation lowers the excess. This test asks the
empirical question the simulation could not.

**H-IV.** Single-stock implied variance exceeds subsequently realised variance on the idiosyncratic
component, after the systematic component (beta squared times the market's implied and realised
variance) is removed.

**Registered sign: positive.** One-sided. The sign is the one the operator's thesis requires.

**The analyst's prior, stated before any data.** Driessen, Maenhout and Vilkov (2009, Journal of
Finance) report a large negative market variance risk premium and a small, usually insignificant
one in individual stock options (`recollection`). The analyst expects the total single-name premium
to be positive in this sample, the systematic part to be positive, and the idiosyncratic part to be
near zero. Predicted verdict: NOT SUPPORTED, held with low confidence; this sample is five large,
heavily traded names, not the cross-section in that paper.

## 2. Inputs

- **Implied volatility.** FRED daily closes, in volatility points: `VXAPLCLS` (Apple), `VXAZNCLS`
  (Amazon), `VXGOGCLS` (Google), `VXGSCLS` (Goldman Sachs), `VXIBMCLS` (IBM), and `VIXCLS` (the
  market). Fetched as CSV from `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<series>`. A
  value recorded by FRED as missing stays missing.
- **Prices.** Daily adjusted closes (`auto_adjust=True`) from Yahoo Finance via `yfinance`, from
  2009-01-01 to the fetch date, for AAPL, AMZN, GOOG, GS, IBM and SPY. GOOG is the listing matched
  to `VXGOGCLS`.
- `fetch.py` writes `data/vx.csv` (columns `date, AAPL, AMZN, GOOG, GS, IBM, MKT`, the last being
  `VIXCLS`) and `data/prices.csv` (columns `date, AAPL, AMZN, GOOG, GS, IBM, SPY`), empty cells for
  missing values, and prints only structure (first and last date and non-missing count per column),
  never a value.

## 3. Definitions

- **Trading days** are SPY's dates in `prices.csv`. Daily log return of series k on day d:
  `r_k(d) = ln(P_k(d) / P_k(d-1))`, d-1 the previous SPY trading day; undefined if either price is
  missing.
- **Formation days.** For each calendar month, `t0` is its first trading day. A formation day is
  used only if at least 21 trading days follow it in `prices.csv`.
- **Holding window** of `t0`: the 21 trading days following `t0`, so the 21 returns from the close
  of `t0` to the close of the 21st trading day after it. `T1` is that 21st day.
- **Realised variance** (annualised): `RV2_k = (252 / 21) * sum of r_k(d)^2` over the 21 window
  days. Not demeaned.
- **Implied variance** (annualised): `IV2_i = (VX_i(t0) / 100)^2` for name i; `IVM2 = (VIX(t0) /
  100)^2`. Values are read at `t0` exactly; no carrying forward.
- **Beta.** `b_i` is the ordinary least-squares slope, with intercept, of `r_i(d)` on `r_SPY(d)` over
  the 252 trading days ending at and including `t0`. All 252 pairs must be present.
- **Name-month.** (i, t0) is used only if `VX_i(t0)` and `VIX(t0)` are present, `b_i` is defined,
  and all 21 window returns of i and of SPY are present.
- For a used name-month:
  - total premium `VRP = IV2_i - RV2_i`;
  - systematic premium `SVRP = b_i^2 * (IVM2 - RV2_SPY)`;
  - idiosyncratic premium `IVRP = VRP - SVRP`
    (that is, implied idiosyncratic variance `IV2_i - b_i^2 * IVM2` less realised idiosyncratic
    variance `RV2_i - b_i^2 * RV2_SPY`).
- **Monthly series.** For each formation day with at least 3 used name-months, `x_t` is the equal
  mean across the used names of a quantity. Formation days with fewer than 3 are dropped.

## 4. Test

1. **Primary.** The mean of the monthly `IVRP` series `x_t`, with a Newey-West standard error, 3
   lags, Bartlett weights `1 - l / (L + 1)`, no small-sample correction, on a constant-only
   regression; `t = mean / se`.
2. **Verdict.**
   - INSUFFICIENT when fewer than 120 monthly observations are used.
   - SUPPORTED when the mean is positive and `t >= 2.0`.
   - NOT SUPPORTED otherwise.
3. **Reported without weight.**
   - The same mean and t for `VRP` and `SVRP`; the share `mean IVRP / mean VRP`.
   - Per-name means and t of `VRP`, `SVRP`, `IVRP` on each name's own monthly series (no
     minimum-name rule), with the name's month count.
   - Primary mean and t in each half of the used months (split at floor(n / 2), first half taking
     the first floor(n / 2)).
   - Mean implied idiosyncratic variance `IV2_i - b_i^2 * IVM2` on the monthly series, and the
     ratio of mean `IVRP` to it.
   - **Robustness, ex-post beta.** The primary statistic with `b_i` replaced by the slope of the 21
     window returns of i on SPY's (an in-window estimate, which is not available at `t0` and is
     reported only to bound the effect of beta error).
   - **Covered-call proxy.** Per name-month, the excess over holding of a one-month at-the-money
     call sold at `t0`: `y = c - max(G - 1, 0)`, with `G = P_i(T1) / P_i(t0)` and `c` the
     Black-Scholes call premium per unit of spot at strike 1, volatility `VX_i(t0) / 100`, rate 0,
     time `21 / 252`: `c = N(d1) - N(d2)`, `d1 = sigma * sqrt(tau) / 2`, `d2 = -d1`,
     `N(x) = 0.5 * erfc(-x / sqrt(2))`. Monthly mean across used names (same 3-name rule), mean and
     Newey-West t as above, in per cent of spot per month.
   - **Pair proxy.** For each of the 10 pairs of names and each formation day on which both names
     are used, the pair's `y` is the mean of the two names' `y`, and its trailing correlation is the
     Pearson correlation of the two names' daily log returns over the same 252 days used for beta.
     Pooled across pairs and formation days: the mean pair `y` in the half with trailing correlation
     below the pooled median and in the half at or above it, and their difference. Without a
     standard error; descriptive only.

## 5. Self-test, independent check

1. `selftest.py` generates synthetic inputs in the formats of section 2: 5 names and a market over
   about 4,000 trading days, daily returns `r_i = b_i * r_M + e_i` with known `b_i`, market and
   idiosyncratic volatilities constant within a world, and implied volatilities set so that
   `IV2_i = b_i^2 * IVM2 + s_e^2 * (1 + k)` with `IVM2 = s_M^2 * 1.3` (a planted systematic premium).
   With `k = 0.3` the verdict must be SUPPORTED in 8 of 8 worlds; with `k = 0` it must be SUPPORTED
   in no more than 4 of 40. It also checks the Newey-West code against White's estimator at 0 lags,
   the Black-Scholes premium against `N(0.1) - N(-0.1)` at `sigma * sqrt(tau) = 0.2`, and that a
   month with 2 used names is dropped.
2. `verify.py` is a second implementation written by a separate agent from this document alone,
   reading the same `data/` files. `compare.py` requires the months used, the primary mean and t
   (to 1e-9 and 1e-6), the verdict, and the no-weight means and t of `VRP`, `SVRP`, the ex-post
   robustness and the covered-call proxy (to 1e-9 and 1e-6) to agree.

## 6. Disclosures

1. **Selection.** The five names are those CBOE chose in 2011: large, liquid, surviving firms. They
   are not a sample of stocks a covered-call writer would otherwise pick.
2. **What the index measures.** Each CBOE volatility index applies the VIX method to the stock's
   listed options, so its square is approximately a 30-day variance swap rate, which includes the
   skew. It is higher than at-the-money implied variance, so the covered-call proxy is biased
   upward and a negative proxy result is robust while a positive one is not. The index horizon is
   30 calendar days, close to but not equal to the 21-trading-day window.
3. **Beta error biases the primary statistic downward.** Estimation noise in `b_i` raises the
   expectation of `b_i^2`, which raises `SVRP` and lowers `IVRP` when the market premium is
   positive. The ex-post robustness row reports the size of this.
4. **Rate zero.** The proxy ignores interest, which understates call premiums by a few basis points
   a month at the rates of this sample; it is reported without weight.
5. The analyst is a language model with general knowledge of market history to mid-2026; the sample
   is not unseen.
