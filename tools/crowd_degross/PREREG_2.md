# Pre-registration: studies 2a to 2d, the crowding footprint of Goldman-reported de-gross weeks

Written 29 October 2026, after study 2 (`docs/FOLLOWUP2_2026-10-29.md`) and before any figure below
was computed. Extends `tools/crowd_degross/PREREG.md`; its series, weekly compounding, episode list
(the 9 frozen Class D episodes of `tools/degross_episodes/episodes.csv`), windows and permutation
method (10,000 draws, `default_rng(20261029)`) carry over unless stated. Non-evidentiary side tests
outside the FNTN funnel; not investment advice.

**What the analyst has seen:** study 2's results, including each episode's GVIP minus QQQ excess in
its episode week. No short-leg, factor or matched-control figure. 2d's threshold is the z <= -2 used
by Versions A and B, fixed by them, not chosen here.

## 1. The four studies (one primary hypothesis each)

**2a, short side.** Hedge funds' crowded shorts (Version B's short basket L, by B's frozen
`daily_legs`) minus QQQ, in the episode week E0. H-short: the mean is **above** the unconditional
mean (short covering lifts crowded shorts). One-sided upper permutation p.
Reported without weight: E+1..4; the long-short spread W minus L in E0 (lower).

**2b, momentum.** The French daily momentum factor (`Mom`), compounded over E0. H-mom: the mean is
**below** the unconditional mean. One-sided lower permutation p. Reported without weight: SMB, HML,
RMW, CMA in E0, two-sided p.

**2c, rally-matched control.** Study 2 found de-gross episodes tend to follow Nasdaq 100 rallies;
crowded high-beta names might lag after any rally, de-grossing or not. Each week is assigned to a
quintile of its pre-window Nasdaq 100 return (`NASDAQ100`, the 10 trading days to the last NDX close
of the week, quintiles over all defined weeks). The null draws, for each episode, one week from the
episode's own quintile (without replacement within a draw), 10,000 times. H-crowd-matched: GVIP
minus QQQ E0 mean below the matched null. One-sided lower p.

**2d, real-time nowcast.** x_t = weekly GVIP minus QQQ; z_t = (x_t - mean) / sd over the 104 weeks
t-104 .. t-1 (all defined; else z undefined). Signal week: z_t <= -2. A Class D episode is **hit**
when a signal week lies within 7 days of its week-end. Chance per episode q = 1 - (1 - b)^3, b the
signal rate over defined weeks; one-sided binomial p. H-nowcast is the hit test, with study 2's rule:
**SEES** when hit rate >= 50% and p <= 0.05 with >= 8 episodes scored. Reported without weight:
precision (share of signal weeks within 7 days of any frozen episode, D or N), and the week before
the episode, E-1, GVIP minus QQQ (lower p), as a lead.

## 2. Multiplicity

The four primary p-values (2a upper, 2b lower, 2c lower, 2d binomial) are adjusted by **Holm** at
family-wise 0.05. Each study's verdict is SUPPORTED (2d: SEES) only if its Holm-adjusted p <= 0.05
and its other conditions hold; INSUFFICIENT with fewer than 8 episodes defined. Unadjusted p-values
are printed alongside.

## 3. Disclosures

1. Nine episodes, all from 2021 onwards; the four studies reuse them, so they are not independent
   evidence of crowding, they are tests of its shape.
2. Version B's short basket is a put-holder proxy for crowded shorts, not borrow or short-interest
   data; a null on 2a may reflect the proxy.
3. The analyst is a language model with general knowledge of market history to mid-2026.
