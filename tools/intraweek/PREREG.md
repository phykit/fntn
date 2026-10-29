# Pre-registration: intra-week persistence of the crowded-long spread (GVIP against QQQ; MTUM against SPY)

Written 29 October 2026, before any figure below was computed. Origin (disclosed): study 2 found
crowded hedge-fund longs lag QQQ by about 1% in the week Goldman later reports as a de-grossing (E0),
and nothing in the four weeks after; 2d found the full-week spread cannot pick those weeks out from
prices; 2e-ii found no week-to-week persistence; study R found no rebound. The only real-time form
left is inside the week: whether the first two days of a week's spread predict the rest of that
week. If they do not, no public-price detector can act on the E0 lag before it has happened.
Non-evidentiary side test outside the FNTN funnel; not investment advice; authorises nothing.

## 1. Series

- Daily adjusted closes from Yahoo in `bench.csv`: columns `DATE,GVIP,QQQ,MTUM,SPY`, one row per
  SPY trading day in date order, a blank cell where a ticker has no close that day.
- Two pairs, each "first leg against second leg": **P1** GVIP against QQQ (the primary pair);
  **P2** MTUM against SPY (the longer momentum twin, a replication).
- Daily spread of a pair on row t: s_t = (first_t / first_{t-1} - 1) - (second_t / second_{t-1} - 1),
  where t-1 is the preceding row of `bench.csv`; s_t is undefined when any of the four closes is
  blank.
- Trading week: the ISO calendar week (Monday to Sunday); its trading days are the rows of
  `bench.csv` dated in it, numbered 1 .. n in date order. A week is **admissible** for a pair when
  n >= 4 and s is defined on every one of its days. A week is labelled by the date of its last
  trading day.
- Signal variable S_w = s_1 + s_2 (the sum over days 1 and 2). Outcome R_w = s_3 + ... + s_n (the
  sum over the remaining days). Sums, not compounded.

## 2. Signal and eligibility

- **Reference set** of admissible week w: the admissible weeks that precede w, taking the most
  recent 104 of them (fewer if fewer exist).
- **Eligible** week: an admissible week whose reference set holds at least 52 weeks, and whose
  last trading day falls in no ISO week that contains the `week_end` of a frozen Goldman episode in
  `tools/degross_episodes/episodes.csv` (D or N; 21 rows), so the weeks that produced the E0
  finding play no part in the primary. Episode weeks are reported separately (section 4, item 4).
- **Signal week:** an eligible week with S_w at or below the 10th percentile of S over its
  reference set (`numpy.percentile`, default linear interpolation). The reference set is not
  filtered for episodes; only eligibility is.

## 3. Primary test and verdict

- For a pair, over its eligible weeks in date order with indicator I (signal or not):
  d = mean of R over signal weeks minus mean of R over non-signal weeks.
- **H-continue:** d < 0 (a bad first two days continue into the rest of the week).
- **One-sided lower circular-shift p:** for k = 5 .. n_eligible - 5 inclusive, rotate I by k
  positions (`numpy.roll`), recompute d_k, count the rotations with d_k <= d; p = (1 + count) /
  (1 + number of rotations).
- **Verdict:** INSUFFICIENT if P1 has fewer than 40 signal weeks. SUPPORTED if P1 has d < 0 with
  p <= 0.025, and P2 has d < 0 with p <= 0.05 and at least 40 signal weeks (one hypothesis on two
  instruments; the primary at the stricter bar, the replication at the ordinary one). Otherwise
  NOT SUPPORTED; where P1 alone meets its bar, that is reported as `p1_alone`.

## 4. Reported without weight

1. **Daily autocorrelation, all days with the terms defined, no week boundaries:** OLS of s_{t+1} on
   s_t (slope, Newey-West t with Bartlett weights, L = 5, no small-sample correction, n); and OLS of
   (s_{t+1} + s_{t+2} + s_{t+3}) on (s_{t-1} + s_t), the same statistics.
2. **The top decile:** eligible weeks with S_w at or above the 90th percentile of their reference
   set; d as above and the one-sided **upper** shift p (count d_k >= d).
3. **One-day signal:** S'_w = s_1, R'_w = s_2 + ... + s_n, the same 10th-percentile rule, the same
   lower shift p.
4. **The 21 frozen episode weeks** (the admissible ones in the pair's sample): the number; the mean
   of s by day position 1 .. 5 (a four-day week contributes to positions 1 .. 4); the mean S and
   mean R over them; and the **hit rate**, the share whose S_w is at or below the 10th percentile of
   their own reference set (reference set of at least 52 weeks required; episodes without one are
   not counted). The hit rate is what a two-day detector would have caught.
5. **The trade.** Every eligible signal week: at the close of day 2, short the first leg and long
   the second in equal amounts; close at the close of day n. Net return per trade = -R_w - cost -
   borrow, with cost 40 bp for P1 (10 bp per leg per transaction) and 10 bp for P2 (2.5 bp), and
   borrow 0.5% a year times (n - 2) / 252. Reported: trades, share profitable, mean and median net
   return, t of the mean (ordinary; trades do not overlap), worst trade, net sum per year of
   eligible sample (eligible weeks / 52). `trade_passes` is true when the mean is positive with
   t >= 2 over at least 40 trades.

## 5. Output

`results.json` with, for each pair under `pairs.P1` and `pairs.P2`: `legs`, `n_admissible`,
`n_eligible`, `first_eligible`, `last_eligible` (week labels), `n_signal`, `mean_R_signal`,
`mean_R_other`, `d`, `p_shift`, `n_shifts`, `share_R_negative_signal`, `top` {`n_signal`, `d`,
`p_shift`}, `one_day` {`n_signal`, `d`, `p_shift`}, `daily` {`slope1`, `t1`, `n1`, `slope23`, `t23`,
`n23`}, `episodes` {`n`, `mean_by_day` (list of 5), `mean_S`, `mean_R`, `hit_rate`, `n_with_reference`},
`trade` {`n`, `share_profitable`, `mean`, `median`, `t`, `worst`, `net_per_year`, `trade_passes`};
and at the top level `criteria` {`p1`, `p2`}, `p1_alone`, `verdict`. Means and sums in decimals.

## 6. Disclosures

1. GVIP's sample begins in November 2016; its eligible weeks begin about a year later, so P1 has
   roughly 470 eligible weeks and about 45 signals; P2 runs from 2013. The 40-week floor is set
   for power at a 1% effect, not for the number of signals available.
2. The prior odds are poor and are stated: the E0 lag is about 1% over five days, 2d found the
   whole week's spread does not identify the episodes, and the reference-decile cut is on two days'
   noise. A SUPPORTED verdict here would be a general short-horizon autocorrelation finding, not a
   de-grossing finding, and is reported as such.
3. The analyst has seen studies 2, 2a to 2e, R and their per-episode weekly figures; nothing about
   any within-week spread.
4. A second implementation is written from this file alone and compared on every output key.
5. Yahoo adjusted closes; ETF survivorship does not arise (all four funds are live).
