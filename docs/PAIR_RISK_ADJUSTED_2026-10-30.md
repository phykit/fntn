# Covered-call excess per unit of risk, by pair correlation

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, as the operator's follow-up to
`docs/SINGLE_NAME_VRP_2026-10-30.md`: does lower correlation add a risk-adjusted premium? A
non-evidentiary side test outside the FNTN funnel. Pre-registration
`tools/pair_risk_adjusted/PREREG.md` (committed `af98858` before any code), which discloses that
it is not blind. Run channel `.github/workflows/pair-risk-adjusted.yml`. Result to follow here.

## Result: run 1 (run id 41056681788, commit `5511f0e`)

Freeze records verified on the runner (this test's and the single-name files it imports and
fetches with); self-test passed; the independent implementation agrees on every required figure.
187 months, February 2011 to September 2026, run 3's sample (reconciliation: -0.4318% and
-0.8870%, against run 3's -0.4320% and -0.8870%).

### Verdict on H-RA: NOT SUPPORTED

D, the mean over the 10 pairs of IR(low-correlation months) minus IR(high-correlation months), is
**+0.031** (monthly IR units); the bootstrap 5th percentile is **-0.061** (95th +0.165; none of
2,000 replications discarded). The sign is the operator's but the difference is well inside
noise. Six pairs lean his way, four the other.

### What the record shows, all without weight

- **The excess over holding is negative in every pair and every name.** Pair IRs run from -0.10
  (GS-IBM) to -0.23 (AAPL-GOOG) a month; name IRs from -0.06 (IBM) to -0.20 (AAPL).
- **The mechanism is there; the gain is not.** Across pairs, the steadiness of the pair's excess
  tracks correlation almost exactly (Spearman 0.93 between mean correlation and the
  diversification ratio, 0.71 to 0.85). In low-correlation months the excess is both less
  negative (by 0.22% a month on average) and less volatile (by 0.42%), and the two roughly cancel
  in the IR. Across the ten pairs, lower-correlation pairs have slightly better IRs (Spearman
  -0.32 on 10 non-independent pairs, not a test).
- **On a Sharpe basis, covering beat holding in all ten pairs.** Monthly Sharpe at rate 0: held
  pair 0.27, covered pair 0.35 on average (annualised roughly 0.95 and 1.20), an improvement in
  every pair from +0.045 (AAPL-GS) to +0.115 (AAPL-AMZN). The calls gave up 0.4% to 1.0% a month
  of return but removed more volatility than that in proportion. The largest improvements are
  in two of the more correlated pairs, so it is not a low-correlation effect. Sharpe counts
  upside volatility as risk, which is exactly what a call gives away, so this flatters the
  strategy for an investor who does not mind large gains; and the proxy overstates the premium
  (single_name_vrp disclosure 2).

### What this licenses

Lower correlation makes the covered-call excess steadier, as arithmetic requires, but on these
five names it did not make it better per unit of risk in any way distinguishable from noise. The
one risk-adjusted improvement in the record, covered over held on a Sharpe basis, comes from
writing calls at all, not from the pair's correlation.
