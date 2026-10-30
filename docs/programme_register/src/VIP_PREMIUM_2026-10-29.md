# Hedge-fund VIP basket: six-factor alpha test, result

Run 29 October 2026, GitHub Actions run 1 (run id 40888059070) on commit `55a0a48`, branch
`degross-proxy-2026-10-29`. Specification frozen before any basket return was computed:
`tools/vip_premium/PREREG.md`; the basket is Version B's frozen long basket, rebuilt on the runner
by Version B's frozen scripts (hashes verified in the run). A non-evidentiary side test outside the
FNTN funnel; not investment advice.

## Verdict

**FAIL.** Six-factor alpha **1.35% a year, Newey-West t 1.36**, over 157 months (September 2013 to
September 2026). The registered bar was t >= 2.0 and alpha >= 2.0% a year.

Survivorship bias in the basket (451 of 701 symbols priced; delisted names never entered) inflates
the basket's return, so the true alpha is probably lower than measured. A FAIL is therefore robust.

## Figures (annualised; no weight in the verdict)

| | Basket | SPY | QQQ | RSP (equal-weight S&P) |
|---|---|---|---|---|
| Mean return | 16.7% | 14.6% | 20.0% | 12.1% |
| Volatility | 15.8% | 14.4% | 17.9% | 15.5% |
| Maximum drawdown (monthly) | -25.1% | -23.9% | -32.6% | -26.7% |
| Basket minus benchmark | n/a | +2.1% (t 1.75) | **-3.3% (t -1.62)** | +4.6% (t 2.14) |

| Regression | Alpha a year | t |
|---|---|---|
| Six factors (primary) | 1.35% | 1.36 |
| CAPM | 2.06% | 1.77 |
| On QQQ | **0.20%** | **0.11** |
| Six factors, Sep 2013 to Feb 2020 | -0.30% | -0.22 |
| Six factors, Mar 2020 to Sep 2026 | 2.60% | 1.91 |

Six-factor loadings: market 1.05, size -0.17, value 0.07, profitability -0.20, investment -0.10,
momentum 0.05. The basket beat SPY in 52% of months.

## Reading

- The basket beats the S&P 500 and the equal-weight S&P, but by less than the Nasdaq 100, and once
  its exposure to the Nasdaq 100 is accounted for its alpha is essentially zero (0.2% a year, t
  0.11). Holding QQQ captured the same return with no stock selection.
- Whatever premium appears is concentrated in 2020 to 2026, the period of mega-cap technology
  leadership; in the first half of the sample it is slightly negative.
- Consistent with the analyst's prior: the "smart money" basket is, for practical purposes, a
  large-cap growth and technology exposure.

## What the result does and does not license

- It closes the VIP basket as a source of edge for the operator: no premium beyond factors, and
  none beyond the Nasdaq 100 at all.
- It does not test Goldman's own VIP list (a different fund universe and construction), nor
  periods before 2013.

## Disclosures

1. Basket and returns as registered in Version B; the basket is idealised (daily equal-weight
   rebalancing, no trading costs), which flatters it further.
2. Independent implementation by a separate agent from PREREG.md alone: months, alpha, t, verdict
   and the no-weight comparators agree to at least ten significant figures.
3. Self-test passed (null 3 of 40, planted 8 of 8). The planted alpha in the self-test was raised
   from 6% to 12% a year before freezing, because at 6% the test's power was about 90% and the
   8-of-8 criterion is a check of the machinery, not of power.
4. The analyst is a language model with general knowledge of market history to mid-2026, including
   Goldman's published VIP figures.

Sources: SEC Form 13F data sets; SEC fails-to-deliver data; Kenneth French Data Library (five
factors and momentum, daily); Yahoo Finance via yfinance; Goldman Sachs Research, Hedge Fund Trend
Monitor (20 February 2025).
