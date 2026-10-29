# High-yield credit (HYG against IEF) as a lead for the Nasdaq 100, 2007 to 2026: result

Run 29 October 2026, GitHub Actions run id 40949983099 on commit `bc4fcee`, branch
`degross-proxy-2026-10-29`. Pre-registration `tools/credit_hyg/PREREG.md`, committed at `7956d0b`
before any price was retrieved. Third test of the credit-spread idea in this project (after 9 and 11
October 2026). Non-evidentiary side test outside the FNTN funnel; not investment advice.

## Verdict

**FAIL (wrong sign).** 4,880 days, May 2007 to September 2026. The 20-day credit excess return of
HYG over IEF has no relationship with the Nasdaq 100's next 20 days.

| Criterion | Requirement | Result |
|---|---|---|
| (a) primary | slope > 0, shift p <= 0.025 | **-0.010, p 0.54** |
| (b) incremental, controlling for QQQ's own 20 days | slope > 0, t >= 2 | +0.005, t 0.05 |
| (c) both halves | slope > 0 in each | +0.064 (2007 to 2016), **-0.243** (2017 to 2026) |
| (d) 5 and 10 days | slope > 0 at both | -0.010, -0.013 |

Reported without weight: credit and the Nasdaq move together on the same day (correlation **+0.61**);
without the one-day delay the slope is still negative (-0.024, p 0.62); the Nasdaq's past 20 days do
not predict the next 20 days of credit either (t 0.32) at this horizon.

## The warning rule, as an indicator would be used (no verdict weight)

Out of QQQ when 20-day credit weakness reaches the worst 10% of history to date, back in above the
median, one-day delay, 10 bp per switch. Evaluation from May 2009 (the first two years are burn-in for
the percentiles, **so the 2008 crisis is inside the regression but outside the rule's evaluation**).

| May 2009 to Oct 2026 | Annual return | Max drawdown | Invested | Exits | False alarms | 10% falls missed |
|---|---|---|---|---|---|---|
| Buy and hold QQQ | **20.0%** | -35.1% | 100% | n/a | n/a | n/a |
| Credit warning rule | 15.0% | **-40.7%** | 91% | 22 | **14 of 22** | **12 of 18** |
| QQQ's own 20-day momentum rule (benchmark) | 13.8% | -32.2% | 86% | 34 | 21 of 34 | 5 of 18 |

The credit rule gave up five points a year, had a **deeper** drawdown than simply holding, raised false
alarms on two exits in three, and was still invested at the low of two thirds of the 10% falls.

## Independent implementation

Written from the PREREG alone. Every headline figure agrees (n, verdict, all slopes to 1e-9 relative,
p and t exactly). The rule figures agree exactly on exits, false alarms and missed declines and differ
in the fifth decimal on return, drawdown and invested share (for example 15.044% against 15.043%),
from two choices the PREREG left open: whether the 10 bp cost is subtracted or applied to wealth, and
one day's difference in where the evaluation window starts. No conclusion depends on either.

## Reading

Three tests, three data sets and forty years now agree: credit spreads move with the equity market,
not ahead of it. This test adds the high-yield market, the Nasdaq 100 specifically and a strategy view:
a credit warning rule would have cost money and failed to avoid the falls. The proposal's AI-financing
framing describes a possible future channel with no history to test; it can be monitored, not
backtested.

## Disclosures

1. HYG minus IEF is a proxy with a duration mismatch (about 3 to 4 years against 7 to 8).
2. The analyst knew the two earlier credit results and the market history of the sample.
3. Prices from Yahoo via yfinance; QQQ is total return; no tax.
