# Pre-registration: the dividend month premium, long-only, after publication

Written 29 October 2026, before any price or dividend observation was retrieved. Idea: Hartzmark and
Solomon, "The dividend month premium", JFE 2013: firms earn abnormally high returns in months when
they are predicted to pay a dividend (1927 to 2009; 0.3% to 0.5% a month long-short, with the long
leg positive). No published post-2009 replication was found in the prior-art check, so 2010 to 2026
is a genuine out-of-sample test. Non-evidentiary side test outside the FNTN funnel; not investment
advice; authorises nothing.

## 1. Universe and data

- Universe: the S&P 500 constituents as listed on the English Wikipedia constituents page at run
  time (count printed). **Survivorship: this is today's list applied backwards.** Dividend payers
  that survived to 2026 are over-represented; the bias favours the long leg, so a FAIL is
  conservative and a PASS would need a survivorship-free rerun before any use.
- Yahoo via yfinance: monthly total returns from adjusted closes, and ex-dividend dates, from
  January 2000 to the last complete month.

## 2. Definitions (Hartzmark and Solomon)

- Stock i is a **predicted payer** in month m if it had an ex-dividend date in month m-3, m-6, m-9
  or m-12.
- Portfolios, equal-weighted over stocks with a return in month m: P_m (predicted payers), N_m
  (the rest), U_m (all). Long-leg spread D_m = P_m - U_m; the paper's spread S_m = P_m - N_m.

## 3. Test

- **Primary (OOS, January 2010 to the last complete month):** mean D_m > 0 with Newey-West t
  (Bartlett, L = 3, no small-sample correction) >= 2.0. INSUFFICIENT below 120 months.
- **Verdict:** PASS if the primary is met; FAIL otherwise.

## 4. Reported without weight

Mean and t of S_m; the full sample from 2001; by halves; the strategy: hold P_m rebalanced monthly,
10 bp on each month's turnover (the share of weight traded), against U_m: annual return, volatility,
Sharpe over the French RF, maximum drawdown, turnover; the number of stocks per month in P and U.

## 5. Disclosures

1. Survivorship as above; yfinance dividend histories may be incomplete for some names (counts of
   stocks with no dividend history are printed).
2. The analyst knows the paper. The long leg carries only part of the published effect; most
   anomalies' alpha sits in the short leg.
3. A second implementation is written from this file alone and compared.
