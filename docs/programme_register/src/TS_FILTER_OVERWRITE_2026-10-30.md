# Term-structure filter on the index overwrite

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, at the operator's request for a
calendar element in the index covered call; he chose the term-structure filter. The fifth test in
this thread, with a one-sided 1% hurdle. Pre-registration `tools/ts_filter_overwrite/PREREG.md`
(first committed `6761ac1`; random-skip benchmark added before any input was fetched, annotated
in section 4). Result to follow here.

## Result: run 1 (run id 41061882560, commit `aa8679b`)

Freeze record verified on the runner; self-test passed; the independent implementation agrees on
every required figure. 204 months, October 2009 to September 2026; 18 began in backwardation
(VIX above VIX3M), among them August 2011, September 2015, March 2018, March and April 2020 and
March 2022.

### Verdict on H-TS: NOT SUPPORTED

| Monthly Sharpe (annualised) | |
|---|---|
| SPY held | 0.29 (0.99) |
| Overwrite every month | 0.42 (1.45) |
| Overwrite only in contango | 0.37 (1.29) |

`Delta` = -0.045 (wrong sign); bootstrap 1st percentile -0.119. Against random skipping of 18
months, the filter did worse than 85.5% of random draws (random mean -0.027, 99th percentile
+0.009). All three conditions fail. Both sensitivity rows keep the wrong sign (steeper
threshold -0.066; skew-corrected pricing -0.019).

### What the record shows, all without weight

- **Backwardation months were bad months to have written a call.** The overwrite's excess over
  holding averaged -1.58% a month in them (sd 4.15%), against -0.08% in contango months (sd
  2.16%). That is the rebound the PREREG named: a large premium collected, then a sharp rally
  given away.
- **So the filter raised return and lowered the Sharpe ratio.** Annualised return: held 14.6%,
  overwrite every month 12.1%, filtered 13.8% (filtered minus always 0.14% a month, Newey-West t
  1.80). But the skipped months are the most volatile ones, and leaving them uncovered put back
  more volatility than return, so the risk-adjusted figure fell.
- The filtered overwrite still beat holding SPY on a Sharpe basis (+0.087 a month), which is the
  index overwrite's own effect and not the filter's.

### What this licenses

On this sample the term-structure filter does not improve the index overwrite's risk-adjusted
return; it does slightly worse than skipping months at random. It does lift raw return by about
1.7% a year, at the cost of more volatility, by not capping the post-stress rebounds. That trade
was not the registered question, its t is 1.80 on 18 skipped months, and it rests on a handful of
episodes (2020 above all); it is recorded as an observation, not a finding.
