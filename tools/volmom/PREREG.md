# Pre-registration: volatility-managed momentum, out of sample 2016 to 2026

Written 29 October 2026, before any factor or price observation was retrieved for this test. A
replication of published work (Barroso and Santa-Clara, "Momentum has its moments", JFE 2015; Moreira
and Muir, "Volatility-Managed Portfolios", JF 2017; Daniel and Moskowitz, "Momentum crashes", JFE
2016) on the years after publication. It follows from study 2b of `docs/FOLLOWUP2_2026-10-29.md`
(momentum falls in de-gross weeks) only in motivation; it uses none of that data. Non-evidentiary
side test outside the FNTN funnel; not investment advice; authorises nothing.

## 1. Data

- Kenneth French daily momentum factor (`F-F_Momentum_Factor_daily_CSV.zip`, column `Mom`, per
  cent), fetched by the VIP test's frozen `tools/vip_premium/fetch_extra.py`.
- For the implementable version: Yahoo adjusted closes (yfinance) for MTUM (iShares MSCI USA
  Momentum, listed April 2013) and SPY, on SPY trading days.

## 2. Definitions (Barroso and Santa-Clara, applied monthly)

- Daily factor return r_d = Mom / 100. Monthly factor return R_m = product of (1 + r_d) over the
  month's trading days, minus 1.
- Realised monthly variance before month m: v_m = (21 / 126) x the sum of r_d^2 over the 126
  trading days preceding the first day of month m (undefined with fewer than 126).
- Target monthly volatility s_T = 0.12 / sqrt(12). Weight w_m = s_T / sqrt(v_m), uncapped.
- Managed return R*_m = w_m x R_m.
- A month is **complete** if the file holds a date in a later month, or its last date is the final
  weekday of that month.
- **In-sample:** the first month with v_m defined, to December 2015. **Out-of-sample (OOS):**
  January 2016 to the last complete month. INSUFFICIENT with fewer than 96 OOS months.

## 3. Tests (OOS; the in-sample figures are reported as the replication, no weight)

- **(a) Moreira-Muir alpha (primary):** in R*_m = a + b R_m + e_m over OOS months, a > 0 with
  Newey-West t (Bartlett, L = 3, no small-sample correction) >= 2.0.
- **(b) Sharpe ratio:** annualised OOS Sharpe (sqrt(12) x mean / sd, sd with ddof = 1) of R* at
  least 1.2 x that of R, and a circular block bootstrap p <= 0.05 that the difference is positive:
  `default_rng(20261029)`; 10,000 draws; each draw takes ceil(n / 12) block starts
  `rng.integers(0, n, size=ceil(n/12))`, each block the 12 consecutive months from its start,
  wrapping modulo n, concatenated and truncated to n; the same indices for R and R*;
  p = (1 + number of draws with Sharpe(R*) - Sharpe(R) <= 0) / (1 + 10,000).
- **Verdict:** PASS if (a) and (b); WEAK if exactly one; FAIL if neither.

## 4. Reported without weight

1. In-sample: Sharpe of R and R*, alpha and t, as the replication of the published result.
2. OOS maximum drawdown of R and R* (wealth from 1); the five worst raw months and R* in them;
   the distribution of w_m (minimum, median, maximum, share above 2).
3. **Implementable version:** long MTUM, short SPY. Daily spread d = r_MTUM - r_SPY; monthly spread
   S_m = product(1 + r_MTUM) - product(1 + r_SPY); v_m from the 126 prior days of d; the same
   scaling and tests (a) and (b), from the first month with v_m defined to the last complete month.
   Cost estimate: 20 bp x the sum of |w_m - w_(m-1)| per year (two legs at 10 bp), reported beside the
   managed annual return.

## 5. Disclosures

1. The analyst is a language model that knows the three papers and the post-2016 momentum
   history, including the crashes of 2020 and 2021; the OOS sample is not unseen.
2. The factor is long-short and costless by construction; the implementable version carries costs
   and a 2013 start. A PASS says the published effect persisted after publication; it is not a novel
   claim and it is not a position-sizing rule.
3. A second implementation is written from this file alone and compared on every headline figure.
