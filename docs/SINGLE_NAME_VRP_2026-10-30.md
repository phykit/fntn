# Single-stock option premium, systematic and idiosyncratic parts

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, as the empirical follow-up to
`docs/COVERED_CALL_PAIR_MC_2026-10-30.md`. A non-evidentiary side test outside the FNTN funnel.
Pre-registration `tools/single_name_vrp/PREREG.md` (committed `a41ab08` before any input was
fetched); run channel `.github/workflows/single-name-vrp.yml`. Result write-up to follow here.

Run 1 (run id 41053140387) failed in the fetch step: FRED timed out on the runner before any
series was read, so no input and no figure exist from it. The fetcher gained a five-attempt retry
(the precedent fetcher's), `FROZEN.sha256` was re-stamped for `fetch.py` only, and the test was
re-dispatched. The analysis code and the pre-registration are unchanged.

Run 2 (run id 41053396172) failed the same way: FRED gave no response to five attempts. The input
source was then changed, before any input was read, to CBOE's own histories of the same indices;
the change is annotated in PREREG section 2 and `PREREG.md` and `fetch.py` were re-stamped.

## Result: run 3 (run id 41055269824, commit `9adefa5`)

Freeze record verified on the runner; self-test passed; the independent implementation agrees on
every required and no-weight figure (`results/3/compare.log`). 187 months, February 2011 to
September 2026, all five names in every month.

### Verdict on H-IV: NOT SUPPORTED (as predicted)

| Monthly series, annualised variance | Mean | Newey-West t |
|---|---|---|
| Total premium, implied less realised variance | +0.0108 | 2.14 |
| Systematic part, beta squared times the market's | +0.0099 | 1.73 |
| **Idiosyncratic part (primary)** | **+0.0010** | **0.39** |
| Idiosyncratic part, ex-post beta (no weight) | -0.0048 | -1.81 |

The idiosyncratic part is 9% of the total premium and 2.2% of implied idiosyncratic variance
(0.0457, about 21% volatility): implied idiosyncratic volatility exceeded realised by roughly a
quarter of a volatility point. Halves: +0.0038 (t 1.53) to October 2018, -0.0018 (t -0.42) after.

| Name | Total (t) | Systematic (t) | Idiosyncratic (t) |
|---|---|---|---|
| AAPL | +0.0146 (2.55) | +0.0071 (0.82) | +0.0075 (1.39) |
| AMZN | +0.0158 (2.65) | +0.0123 (2.33) | +0.0035 (0.59) |
| GOOG | +0.0082 (1.73) | +0.0094 (1.75) | -0.0012 (-0.31) |
| GS | +0.0141 (1.68) | +0.0147 (2.35) | -0.0006 (-0.15) |
| IBM | +0.0014 (0.21) | +0.0057 (1.51) | -0.0042 (-0.74) |

### Covered-call proxy (no weight)

Selling a one-month at-the-money call each month returned **0.66% of spot a month less than
holding the stock** (t -3.25, 187 months). The proxy prices the call at the CBOE index level,
which includes the skew and overstates the at-the-money premium, so the true shortfall is if
anything larger (PREREG disclosure 2). The options were rich in variance terms and the strategy
still lost, because these five stocks rose strongly and the calls gave the rises away.

### Pair split (descriptive, no standard error)

Over 1,870 pair-months, pairs whose trailing correlation was below the median (0.42) lost 0.43%
a month against holding; pairs above it lost 0.89%. The direction is the operator's, but this row
has no standard error, rests on ten overlapping pairs of five names, and neither sign was
registered; it is not evidence and is not cited as such.

### What this licenses and what it does not

- The premium in these single-stock options sits on the systematic part. Correlation between two
  such stocks therefore cannot add a premium of its own, as the Monte Carlo had shown would follow.
- On these five names a covered call returned less than holding. That is a fact about five
  surviving, strongly rising large caps from 2011 to 2026, not about covered calls in general.
- It does not test a broad cross-section of stocks, which needs a paid options feed.
