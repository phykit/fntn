# Premium in selling 5% out-of-the-money S&P 500 puts, at traded prices

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, at the operator's request
after the BXM result. The seventh test in this thread, one-sided 1% hurdle. Pre-registration
`tools/otm_put_premium/PREREG.md` (first committed `ff4991c`; critical value changed to a
block-bootstrap t before any input was fetched, annotated in section 4). Result to follow here.

## Result: run 1 (run id 41065397245, commit `718adb2`)

Freeze record verified on the runner; self-test passed; the independent implementation agrees on
every required figure. 404 months, February 1993 to September 2026.

### Verdict on H-OTM: NOT SUPPORTED, narrowly

The seller of 5% out-of-the-money puts earned **+0.26% of index notional a month** (3.2% a year),
Newey-West t **2.72**. The registered critical value, the block-bootstrap t, is **3.01**, so the
verdict is NOT SUPPORTED. Under the normal critical value (2.326) it would have been SUPPORTED: this
is exactly the case the pre-freeze amendment was made for, the data's own skew (below) inflating
the t statistic.

| Sub-period | Months | Mean a month | t |
|---|---|---|---|
| 1993-02 to 2016-05 (summarised before the test) | 280 | +0.27% | 2.21 |
| 2016-06 to 2026-09 (not seen before the test) | 124 | +0.26% | 1.61 |

The premium is the same size in the unseen decade as before it; it is the uncertainty, not the
level, that keeps it below the bar.

### What the record shows, all without weight

- **Shape.** Skewness -4.3; worst month -16.3% of notional; negative in 22% of months. The five
  worst months alone gave back 24% of everything earned in all positive months.
- **Added to held stock** (S&P 500 plus one short 5% out-of-the-money put per unit): return 14.6% a
  year against 11.4%, but volatility 19.4% against 14.7%, Sharpe 0.75 against 0.77, maximum
  drawdown -63% against -51%, and a worse downside ratio. The extra return is paid for with more
  crash exposure, one for one; `Delta_k` -0.006 a month (bootstrap 5th to 95th percentile -0.033
  to +0.025).
- **At-the-money comparators at traded prices** (236 common months): PUT (cash-secured
  at-the-money put writing) return 7.5%, volatility 10.7%, Sharpe 0.70, drawdown -33%; BXM 6.4%,
  11.0%, 0.59, -36%; SPY 11.6%, 15.4%, 0.75, -51%. At-the-money put writing did better than
  at-the-money call writing on every measure, as the skew implies, but neither beat holding SPY on
  a Sharpe basis.

### What this licenses

The out-of-the-money put does carry a positive premium, about 3% a year, and at the same level
before and after 2016. It is not distinguishable from zero once the t statistic is judged against
its own skewed distribution, and in risk-adjusted terms it does not improve on holding the index:
the premium is close to fair payment for the crash exposure it brings. Selling these puts raises
return by taking more of the same risk the stock already carries.
