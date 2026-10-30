# Intra-week persistence of the crowded-long spread: the last real-time door, tested

Run 30 October 2026 (UTC), GitHub Actions run 40977451544 on commit `54fbb3b`. Pre-registration
`tools/intraweek/PREREG.md`, committed at `47988ad` before any figure; frozen implementation and
an independent second implementation written from the PREREG alone; 88 of 88 output items agree on
two synthetic worlds and on the real data. Results under `tools/intraweek/results/1/`. Non-evidentiary
side test outside the FNTN funnel; authorises nothing.

## The question

Study 2 found crowded hedge-fund longs lag QQQ by about 1% in the week Goldman later reports as a
de-grossing, and nothing afterwards. Every public-price route to that week in advance has failed
(proxies A and B, 2d, 2e-ii, R). The one form left is inside the week: do the first two days of a
week's spread predict the remaining days? If they do not, no public-price detector can act on the
lag before it has happened.

## Verdict: NOT SUPPORTED

| Pair | Eligible weeks | Signals | Rest-of-week spread, signal weeks | Other weeks | d | Shift p (lower) | Bar |
|---|---|---|---|---|---|---|---|
| P1 GVIP against QQQ (primary) | 446, Nov 2017 to Oct 2026 | 66 | −0.26% | +0.04% | **−0.30%** | **0.014** | met (p ≤ 0.025) |
| P2 MTUM against SPY (replication) | 632, Apr 2014 to Oct 2026 | 72 | +0.24% | −0.02% | **+0.26%** | 0.971 | not met (wrong sign) |

The pre-registered rule required both instruments. The primary meets its bar and the replication
reverses, so the verdict is NOT SUPPORTED with `p1_alone` recorded. The reading is that one
instrument out of two, at p 0.014 on 66 signals, with the longer momentum twin pointing the other
way, is the pattern of a chance result rather than a property of crowded longs.

**What else the record shows, all without weight.**

- **The trade loses on both pairs.** Short GVIP, long QQQ from the close of day 2 to the close of
  the week, 40 bp a round trip: 66 trades, 38% profitable, mean **−0.15%** (t −1.14), −1.1% a year.
  Gross of costs the mean is +0.26% a trade, so even at a quarter of the registered cost the edge
  would be about +0.1% a trade, below one standard error. The MTUM trade loses 0.35% a trade
  (t −2.87).
- **Daily autocorrelation points the other way.** GVIP−QQQ's day-to-day slope is −0.04 (t −1.3)
  and the two-day-on-three-day slope −0.03 (t −0.7): a faint reversal, as 2e-ii found at weekly
  frequency. MTUM−SPY: +0.02 (t 0.9) and **−0.07 (t −2.2)**, reversal at the three-day horizon.
- **The top decile does not continue** on either pair (P1 d −0.07%, p 0.74; P2 d −0.29%, p 0.99,
  which is reversal).
- **A one-day signal is weaker:** P1 d −0.29%, p 0.039; P2 d +0.40%, p 0.998.
- **The 21 frozen episode weeks.** A two-day detector would have caught 6 of 21 (29%) on GVIP and
  4 of 21 (19%) on MTUM, against a base rate of about 15% of eligible weeks flagged. By day, the
  GVIP lag in episode weeks sits almost entirely on **day 2** (−0.34%; days 1, 3, 4 and 5 are
  within ±0.11%), and the rest of the week after a two-day read is flat (+0.08%). On MTUM the
  lag is spread across days 2 and 3 (−0.38%, −0.50%) with the rest of the week at −0.66%; that is
  21 weeks of mixed D and N class and is reported as a description, not a result.

## What this closes

The passage under review said the surviving result "could conceivably support a same-week
implementation if one could observe the underlying flows in real time". In public prices the only
real-time observation is the spread itself, and its first two days do not predict its last three
on the pre-registered rule, do not do so on the momentum twin at all, and do not pay for a round
trip on the one pair where they lean the right way. With this, every public-data route to the E0
lag has been tested and closed: the French-factor proxies (A, B), the full-week nowcast (2d), the
week-before hint (2e), week-to-week persistence (2e-ii), the rebound (R) and now the intra-week
read. What remains is prime-broker flow data, which only a prime broker has.

## Disclosures

1. The signal count on GVIP (66 of 446, 14.8%) is above the nominal 10% because the reference
   window is the prior 104 weeks and GVIP's spread volatility rose over the sample; the rule was
   fixed before the data and is kept.
2. Episode weeks are excluded from the primary and reported separately; eligibility, not the
   reference set, is filtered.
3. No definitional disagreement between the implementations arose on this test.
