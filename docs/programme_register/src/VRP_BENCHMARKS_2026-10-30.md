# Do Cboe's option-selling benchmarks earn a return beyond their equity exposure?

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, at the operator's request: PUT,
WPUT and CNDR, alpha against SPY on excess returns. The eighth test in this thread. Pre-registration
`tools/vrp_benchmarks/PREREG.md` (first committed `05da477`; a percentile formula that contradicted
its own text was corrected, and measured power added, before any input was fetched). Result to
follow here.

## Result: run 1 (run id 41069810268, commit `9a6ab32`)

Freeze record verified on the runner; self-test passed; the independent implementation agrees on
every required figure. 236 months, February 2007 to September 2026 (the first month with all five
series present at both ends).

### Verdicts: NOT SUPPORTED for all three

| Annualised, excess of bills | Alpha vs SPY (5th to 95th) | Beta | Excess return | Volatility | Excess Sharpe | Max drawdown | Skew |
|---|---|---|---|---|---|---|---|
| SPY | n/a | 1 | 10.0% | 15.4% | 0.65 | -51% | -0.53 |
| PUT (monthly ATM put write) | **0.0%** (-2.1% to +2.0%) | 0.60 | 6.0% | 10.8% | 0.56 | -33% | -1.63 |
| WPUT (weekly ATM put write) | **-2.1%** (-4.3% to 0.0%) | 0.53 | 3.2% | 9.9% | 0.33 | -24% | -1.33 |
| CNDR (monthly iron condor) | **-1.4%** (-3.7% to +0.7%) | 0.10 | -0.5% | 6.8% | -0.07 | -19% | -1.57 |

Alpha t: PUT -0.02, WPUT -1.58, CNDR -0.85; none is positive, so the low power stated in section 4
does not bear on these verdicts: the point estimates are at or below zero.

### What the record shows, all without weight

- **PUT earned exactly its equity exposure.** Beta 0.60, alpha nil: a put-write is, on this
  sample, a 60% equity position with a worse tail (skew -1.6 against SPY's -0.5).
- **Shorter maturity was worse.** WPUT's excess Sharpe was below PUT's by 0.067 a month (bootstrap
  5th to 95th -0.131 to -0.014), before the far heavier trading costs 52 rolls a year would bring.
- **Defined risk removed the premium.** CNDR, nearly market-neutral (beta 0.10), lost 0.5% a year
  over bills; its Sharpe was below PUT's by 0.18 a month (-0.31 to -0.07). The bought wings cost
  about what the sold options earned, consistent with the deep out-of-the-money options being the
  most richly priced.
- PUT's Sharpe of 0.70 in `tools/otm_put_premium` was at rate 0; on excess returns it is 0.56, below
  SPY's 0.65. The bills it holds flattered the earlier figure.

### What this licenses

On Cboe's traded-price benchmarks over 2007 to 2026, none of the three ways of selling S&P 500
volatility earned anything beyond its equity exposure; two earned less. Combined with
`tools/otm_put_premium`, the picture is that the index volatility premium exists but, at the
monthly and weekly horizons and structures tested, is fully accounted for by the equity and crash
risk taken to collect it.
