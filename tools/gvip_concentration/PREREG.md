# Pre-registration: is GVIP's shortfall against QQQ a concentration exposure?

Written 29 October 2026, before any QQQE observation was retrieved. Motivated by
`docs/GVIP_LIVE_2026-10-29.md` (known to the analyst): GVIP returned 4.9% a year less than QQQ
(t -2.04), 0.9% more than SPY and 4.2% more than RSP, December 2016 to September 2026. The question
is whether "long QQQ, short GVIP" is a trade or a bet on index concentration. Non-evidentiary side
test outside the FNTN funnel; not investment advice.

## 1. Data

Yahoo adjusted closes via yfinance: GVIP, QQQ, QQQE (Direxion Nasdaq-100 Equal Weighted, listed
March 2012), RSP, SPY, on SPY trading days. Monthly compounded returns over calendar months with
every day present; December 2016 (GVIP's first full month) to the last complete month (complete:
the file holds a later month's date, or the last date is the final weekday of the month).

## 2. Test

y_m = GVIP_m - QQQ_m regressed on x_m = QQQE_m - QQQ_m with intercept; Newey-West (Bartlett,
L = 3, no small-sample correction).

- **CONCENTRATION EXPLAINS:** b >= 0.5 with t(b) >= 2.0, and t(a) > -2.0 (no significant residual
  shortfall).
- **RESIDUAL SHORTFALL:** t(a) <= -2.0 (a shortfall remains after the concentration exposure).
- **INDETERMINATE:** otherwise. INSUFFICIENT with fewer than 96 months.

The implication for the reframed trade: its alpha after the concentration exposure is -a.

## 3. Reported without weight

GVIP minus QQQE annual excess with t; the regression R-squared; the same regression with
x = RSP - SPY (broad-market concentration); a, b and t by halves.

## 4. Disclosures

1. Expense ratios are inside every return (QQQE's is the highest of the five).
2. The analyst has seen GVIP's figures against QQQ, SPY and RSP; not against QQQE.
3. A second implementation is written from this file alone and compared.
