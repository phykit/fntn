# Index overwrite against single-stock overwrite

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, at the operator's request
after the correlation-risk-premium discussion. A non-evidentiary side test outside the FNTN
funnel. Pre-registration `tools/index_vs_single_overwrite/PREREG.md` (committed `0bb1870`).
Result to follow here.

## Result: run 1 (run id 41059715815, commit `74335f0`)

Freeze records verified on the runner; self-test passed; the independent implementation agrees on
every required figure. 187 months, February 2011 to September 2026 (the month set of the two
preceding tests).

### Verdict on H-IX: SUPPORTED

| | Held, Sharpe (annualised) | Covered, Sharpe (annualised) | Improvement (monthly) |
|---|---|---|---|
| Index (SPY, call priced at the VIX) | 1.03 | 1.53 | +0.143 |
| Basket (five names, each its own call) | 1.13 | 1.40 | +0.079 |

`Delta` = +0.064 (monthly Sharpe units); bootstrap 5th percentile **+0.011**, 95th +0.143; no
replications discarded. The registered bar (`Delta > 0` and 5th percentile `> 0`) is met, but
only just.

### What the record shows, all without weight

- **The index overwrite gave up less.** Covered-call excess over holding: index -0.22% of spot a
  month (sd 2.40%), basket -0.66% (sd 3.30%). The index was better by 0.44% a month, Newey-West
  t 3.21. Both are still negative: neither overwrite beat its own held position on return.
- **Skew sensitivity.** With the index call priced at 0.9 of the VIX and each name's at 0.95 of
  its index, `Delta` falls from +0.064 to +0.035. The sign survives this one plausible correction;
  its significance was not tested.

### How much weight this can bear

1. **Not blind**, though no index or basket figure had been computed before the run.
2. **The skew bias favours this result** (PREREG disclosure 2), and the margin over the bar is
   small: a 5th percentile of +0.011 on a bootstrap of one 15-year path.
3. **Different underlyings.** The five names rose much more than SPY, and a short call on a
   strongly rising stock gives more away, so part of the gap may be the stocks and not the
   options. The Sharpe-improvement statistic does not remove that.
4. It is consistent with the literature's correlation risk premium but does not isolate it: the
   test cannot separate a richer index premium from a calmer index path.

### What this licenses

On this sample, writing calls on the index improved risk-adjusted return by about twice as much
as writing them on the five stocks separately, in the direction the correlation risk premium
predicts. It is the one result in this series that favours a correlation-based route to better
risk-adjusted returns from call writing, and it points to the index, not to picking an
uncorrelated pair. It is weak evidence for the reasons above and is not a basis for capital.
