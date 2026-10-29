# Pre-registration: what hedge funds' crowded longs do in Goldman-reported de-gross weeks

Written 29 October 2026, before any return below was computed. Follow-up study 2, joining
`docs/GVIP_LIVE_2026-10-29.md` (the VIP basket is a costly Nasdaq tracker) and
`docs/DEGROSS_EPISODES_2026-10-29.md` (de-gross episodes tend to follow rallies). The analyst has
seen GVIP's and the reconstructed basket's monthly aggregate statistics only, and no weekly figure
around any episode. Non-evidentiary side test outside the FNTN funnel; not investment advice.

## 1. Hypothesis

**H-crowd:** in the week of a Goldman-reported de-gross episode, hedge funds' most crowded longs
underperform the Nasdaq 100. If true, the VIP basket is not merely a tracker but one that gives
ground precisely in the stress weeks the Prime book reports.

## 2. Series

- **Primary:** GVIP minus QQQ, total-return (Yahoo adjusted closes), from GVIP's first full week.
- **Secondary:** the reconstructed VIP basket (Version B's long leg W, by B's frozen `daily_legs`)
  minus QQQ; GVIP minus SPY; GVIP's residual against QQQ (GVIP minus beta x QQQ, beta estimated on
  the 52 weeks ending 4 weeks before each week, at least 40 available).
- Weekly returns compound daily returns over the ISO week; a week with any missing day is undefined.

## 3. Episodes and windows

- **Primary episodes:** the 9 Class D episodes of the frozen `tools/degross_episodes/episodes.csv`.
- **Secondary episodes:** its Class N episodes; and, when follow-up study 1 has frozen
  `tools/degross_ext/episodes_all.csv`, the combined Class D list (declared here, run then).
- **Windows:** E0, the episode's ISO week (week-end as coded); E+1..4, the four ISO weeks after it,
  compounded.

## 4. Test

- **Primary:** the mean E0 excess return of the primary series over the primary episodes, against
  the unconditional mean over all defined weeks; one-sided (lower) permutation p, 10,000 draws of
  the same number of distinct defined weeks without replacement, `default_rng(20261029)`.
- **Verdict:** SUPPORTED when p <= 0.05 with at least 8 episodes having E0 defined; INSUFFICIENT
  below 8; otherwise NOT SUPPORTED.
- **Reported without verdict weight:** E+1..4 (lower test: does the underperformance persist; upper
  test: does it reverse), every secondary series and episode set, the share of episodes with a
  negative E0 excess, and each episode's E0 excess.

## 5. Disclosures

1. Nine episodes is a small sample; a single large week can dominate the mean, so the per-episode
   figures are printed.
2. Prices from Yahoo via yfinance; the reconstructed basket carries Version B's survivorship
   disclosure (451 of 701 symbols priced).
