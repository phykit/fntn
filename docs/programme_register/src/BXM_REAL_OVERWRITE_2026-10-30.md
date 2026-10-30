# Index overwrite at real option prices: BXM against SPY

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`: the index overwrite of
`docs/INDEX_VS_SINGLE_OVERWRITE_2026-10-30.md` re-tested at traded option prices. The sixth test in
this thread, one-sided 1% hurdle. Pre-registration `tools/bxm_real_overwrite/PREREG.md` (committed
`04969c8`). Result to follow here.

## Result: run 1 (run id 41063396563, commit `dcb31f4`)

Freeze record verified on the runner; self-test passed; the independent implementation agrees on
every required figure. 294 months, April 2002 to September 2026.

### Verdict on H-BXM: NOT SUPPORTED

| Annualised, 2002-04 to 2026-09 | BXM (real-price overwrite) | SPY (held) |
|---|---|---|
| Mean return | 6.6% | 10.7% |
| Volatility | 10.7% | 14.8% |
| Sharpe (rate 0) | 0.62 | 0.72 |
| Maximum drawdown (monthly) | -35.8% | -50.8% |
| Downside ratio (monthly) | 0.25 | 0.32 |

`Delta` = -0.029 a month (wrong sign); bootstrap 1st percentile -0.106, 95th +0.015.

### What the record shows, all without weight

- **Before 2011 the overwrite helped a little; after, it hurt.** `Delta` +0.028 to December 2010,
  -0.060 from January 2011. BXM lagged SPY by 0.34% a month over the whole sample (Newey-West t
  -2.79) and by 0.54% a month from 2011 (t -3.88).
- **It cut volatility and drawdown, but cut return by more.** BXM's volatility was about 28% lower
  and its worst drawdown 15 points shallower; its return was about 38% lower. Even on the downside
  ratio, which does not count upside swings as risk, BXM was worse.
- **The VIX proxy overstated the premium badly.** Over 2011-02 to 2026-09 the real overwrite lagged
  holding by 0.536% a month; the VIX-priced proxy in `tools/index_vs_single_overwrite` put the same
  shortfall at 0.221% a month. The proxy overstated the index call's net premium by about 0.31% a
  month, roughly 3.8% a year (different monthly cycles, so a comparison of levels only). That is
  the skew bias PREREG disclosures in the earlier tests named, and it is larger than the margin by
  which the index-against-single-stock test passed.

### What this licenses

At traded prices, overwriting the S&P 500 with monthly at-the-money calls did not improve
risk-adjusted return over 2002 to 2026, and lowered it after 2011. The index overwrite's
improvement in `tools/index_vs_single_overwrite` came from a proxy that overpriced the index call
by more than the effect it found; that earlier SUPPORTED verdict should be read as an artefact of
the proxy. BXM bears no bid-ask spread on its calls, so a real overwriter would fare slightly worse
still; SPY bears its 0.09% fee, which favours BXM slightly.
