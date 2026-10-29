# Pre-registration: the Halloween effect on the Nasdaq 100, after publication

Written 29 October 2026, before any observation was retrieved for this test. Idea: Bouman and
Jacobsen, "The Halloween indicator, 'Sell in May and go away'", AER 2002; Jacobsen and Zhang (2018)
report it in 100-plus markets and across three centuries of UK data. Published December 2002, so
2003 onwards is out of sample. Non-evidentiary side test outside the FNTN funnel; not investment
advice; authorises nothing.

## 1. Data and definitions

- NDX: FRED `NASDAQ100` daily closes (from 1986); monthly return = last close of the month over the
  last close of the prior month; RF: French daily, compounded within the month. Monthly excess
  return e_m. A month is complete if the file holds a later month's date or the last date is the
  final weekday of the month.
- Winter W_m = 1 for November to April, 0 for May to October.

## 2. Test

- **Primary (OOS, January 2003 to the last complete month):** in e_m = a + c W_m + u_m, c > 0 with
  Newey-West t (Bartlett, L = 3, no small-sample correction) >= 2.0. INSUFFICIENT below 120 months.
- **Verdict:** PASS if the primary is met; FAIL otherwise.

## 3. Reported without weight

The same on the full sample from 1986; mean excess return in winter and summer months; the share of
winters beating the following summer; the strategy, NDX in winter and cash (RF) in summer, no costs
(two switches a year), against NDX held: annual return, volatility, Sharpe, maximum drawdown, OOS;
the published-sample (1986 to 2002) figures as the replication.

## 4. Disclosures

1. Twenty-four OOS years is a small sample for a seasonal; the test detects an effect of the
   published size (about half a per cent a month) and not a smaller one.
2. The analyst knows the papers and the sample.
3. A second implementation is written from this file alone and compared.
