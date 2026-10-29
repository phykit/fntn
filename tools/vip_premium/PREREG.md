# Pre-registration: does the hedge-fund favourites (VIP) basket earn a premium beyond factor exposure?

Written 29 October 2026, before any return of the basket used below was computed. The basket is
Version B's long basket (`tools/degross_proxy_b/PREREG.md` section 3, built by the frozen
`tools/degross_proxy_b/build.py`), whose construction was frozen and run for the gate test earlier
the same day; only derived counts and the three gate-week figures were seen from it. A
non-evidentiary side test outside the FNTN funnel; not investment advice.

## 1. Question and hypothesis

Goldman Sachs reports that its Hedge Fund VIP basket (the 50 stocks most often in hedge funds' top
10 holdings) beat the S&P 500 in about 60% of quarters since 2001, by an average of about 52 bp a
quarter (`verified_secondary`: Goldman Sachs Research, Hedge Fund Trend Monitor, 20 February 2025,
read 29 October 2026). The operator's question: is there a potentially profitable strategy in it?
An ETF tracking a version of the basket already exists (GVIP), so any premium is buyable; the
question that matters is whether a premium survives standard factor exposures.

**H-VIP.** The equal-weighted long basket earns a positive monthly alpha against the Fama-French
five factors plus momentum.

**Registered sign: positive.** One-sided.

## 2. Inputs

- Long basket: `data/baskets.csv` rows with `leg = long`, produced on the runner by the frozen
  Version B scripts (`fetch_raw.py`, `build.py`, `fetch_prices.py`), unchanged.
- Basket daily returns: Version B `PREREG.md` section 4 exactly (entered at the close of the
  effective date, equal-weighted mean of entered constituents' daily returns, earning
  E_q < d <= E_next), computed by `tools/degross_proxy_b/run.py`'s `daily_legs`, imported, not
  copied.
- Factors: Kenneth French Data Library, daily: `F-F_Research_Data_5_Factors_2x3_daily_CSV.zip`
  (`Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, `RF`) and `F-F_Momentum_Factor_daily_CSV.zip` (`Mom`), in
  per cent.
- Benchmarks: SPY, QQQ and RSP (equal-weight S&P 500) daily adjusted closes from Yahoo via
  `yfinance`, on SPY's trading days.

## 3. Definitions

- Monthly return of a daily series: the product of (1 + r_d) over the calendar month's days, minus
  1. The basket's first month is the first full calendar month after its first earning day; the
  last month is the last full calendar month for which the factors exist.
- A month is used only if the basket, all factors and all benchmarks have a return for every
  trading day in it (days on which the basket has no return break the month).
- Basket excess return x_m = basket return minus RF (monthly, compounded the same way).

## 4. Test

1. **Primary.** OLS of x_m on monthly Mkt-RF, SMB, HML, RMW, CMA and Mom, with intercept. Alpha is
   the intercept. Newey-West standard error with 3 lags (Bartlett kernel). One-sided t = alpha /
   se.
2. **Verdict.**
   - PASS when t >= 2.0 **and** annualised alpha (12 x monthly alpha) >= 2.0% **and** at least 120
     months are used.
   - INSUFFICIENT when fewer than 120 months are used.
   - FAIL otherwise.
   The 2.0% floor exists because GVIP's expense ratio (about 0.45% a year, `recollection`) and
   quarterly turnover of a 50-name basket would consume a smaller alpha.
3. **Reported without weight.** Annualised mean and volatility of the basket, SPY, QQQ and RSP;
   annualised excess return of the basket over each benchmark, with Newey-West t; the basket's
   factor loadings; the share of months in which the basket beat SPY; the basket's maximum
   drawdown against each benchmark's; alpha in a CAPM regression and in a regression on QQQ's
   excess return; and the six-factor alpha in each half of the sample.

4. **Conventions.**
   - Factor and RF monthly values: each daily value divided by 100 and compounded as in section 3.
   - Month coverage: every SPY trading day of the month must have a basket return, a value for all
     six factors and RF (French dates), and a return for SPY, QQQ and RSP.
   - Newey-West: plain HAC sandwich (X'X)^-1 S (X'X)^-1 with Bartlett weights 1 - l/(L+1), L = 3,
     no small-sample correction.
   - Annualised mean = 12 x monthly mean; annualised volatility = sqrt(12) x monthly sd (ddof 1).
   - Excess over a benchmark: 12 x mean of monthly (basket - benchmark), t from a constant-only
     regression with the same Newey-West estimator.
   - Maximum drawdown on the compounded monthly series.
   - Halves: the used months split at floor(n / 2), the first half taking the first floor(n / 2).

## 5. Self-test, independent check, disclosures

1. `selftest.py`: the regression and Newey-West code on synthetic data with a planted alpha (must
   PASS 8 of 8) and with none (no more than 4 of 40 PASS).
2. `verify.py` is a second implementation by a separate agent from this document and the input
   formats alone, reading the same `data/` files; `compare.py` requires the months used, alpha, t
   and verdict to agree (alpha and t to 1e-6).
3. **Survivorship biases this test towards PASS.** Version B priced 451 of 701 symbols; delisted
   names never entered the basket, and delisting is disproportionately failure. A FAIL is therefore
   robust; a PASS would overstate the premium.
4. Equal weighting with daily rebalancing has no trading costs here; it is an idealised basket.
5. The analyst is a language model with general knowledge of market history to mid-2026, including
   Goldman's published VIP performance figures; the sample is not unseen.
