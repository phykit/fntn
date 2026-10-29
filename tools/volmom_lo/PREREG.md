# Pre-registration: volatility-managed momentum as a long-only strategy (MTUM against SPY)

Written 29 October 2026, after `docs/ADJACENT_TESTS_2026-10-29.md` section 1 (PASS) and before any
figure below was computed. This is the translation of that result into a form a long-only account
can hold; it is **not** an independent confirmation, because it uses the same MTUM and SPY sample
on which the long-short spread passed (disclosed). Non-evidentiary side test outside the FNTN
funnel; not investment advice; nothing here authorises a position.

## 1. The strategy (fixed)

- Universe: SPY and MTUM (iShares MSCI USA Momentum), daily adjusted closes on SPY trading days.
- Signal at each month-end m (the last trading day of the month): realised monthly variance of the
  daily spread d = r_MTUM - r_SPY over the 126 trading days to and including that close,
  v_m = (21 / 126) x sum of d^2; sigma_m = sqrt(v_m). Target s_T = 0.12 / sqrt(12) (the published
  target). **Weight w_m = min(1, s_T / sigma_m)**: the long-short weight of the passed test, capped at
  one because the account cannot borrow or short.
- Holding: a fraction w_m of the equity sleeve in MTUM and 1 - w_m in SPY. The weight decided at the
  month-end close is executed at the close of the first trading day of the next month, so that
  day's return is earned at the old weight; the new weight applies from the second trading day.
  Weights change only at month ends; between rebalances the holding drifts with prices.
- Costs: 10 bp per leg on each rebalance, charged on the traded fraction: 20 bp x |w_m - w_(m-1)|
  on the execution day (the first month's establishment is charged against a prior SPY holding,
  20 bp x w). Nothing else (no borrow, no management of the ETFs' own fees, which are inside their
  prices).
- Sample: the first month-end with 126 spread days available, to the last complete month (complete
  as in `tools/volmom/PREREG.md`). INSUFFICIENT with fewer than 96 months.
- Comparators, same costs where they trade: SPY held; MTUM held (static, no trading); a static
  50/50 MTUM/SPY rebalanced monthly.

## 2. Tests (all on monthly returns, net of costs)

Active return A_m = strategy return minus SPY return; static active return S_m = MTUM minus SPY.

- **(a) Moreira-Muir alpha of the long-only tilt:** A_m = a + b S_m + e_m; a > 0 with Newey-West t
  (Bartlett, L = 3, no small-sample correction) >= 2.0.
- **(b) Sharpe of the active return:** sqrt(12) x mean / sd (ddof = 1) of A_m at least 1.2 x that of
  S_m (as a gain of 0.2 x |Sharpe(S)| when Sharpe(S) <= 0), with the circular block bootstrap p
  <= 0.05 exactly as specified in `tools/volmom/PREREG.md` section 3(b) (`default_rng(20261029)`,
  10,000 draws, blocks of 12, same indices for A and S).
- **(c) Worth holding at all:** the strategy's total-return Sharpe (over the French one-month RF,
  compounded monthly from `ff5_daily.csv`) >= SPY's over the same months.
- **PASS:** (a), (b) and (c). **WEAK:** (a) or (b) but not all three. **FAIL:** neither (a) nor (b).

## 3. Reported without weight

Annualised return (geometric), volatility, Sharpe and maximum drawdown for SPY, MTUM, 50/50 and the
strategy; the weight series (minimum, median, maximum, share of months at the cap of 1, share below
0.5); annual turnover (sum of |w_m - w_(m-1)| per year) and annual cost; year-by-year strategy and
SPY returns; the strategy minus MTUM-held active return and its Sharpe; **the live weight**, as at
the last complete month-end and as at the latest close in the data, as the signal the strategy
would act on now.

## 4. Disclosures

1. Same sample as the passed spread test (November 2013 to September 2026); the cap, the delay and
   the costs are the only differences. A PASS here says the long-only form keeps the published
   effect net of costs; it cannot add to the evidence that the effect exists.
2. The 12% target binds as a cap whenever the spread's realised volatility is below 12% a year;
   how often is reported. No alternative target is tested.
3. Operational points outside the test: whether the account can hold US-domiciled ETFs; tax
   treatment of monthly switches; the ETFs' expense ratios are inside the prices.
4. A second implementation is written from this file alone and compared on the headline figures.
