# Pre-registration: Goldman-reported de-gross episodes, 2016 to 2026; proxy hit rates and Nasdaq 100 timing

Written 29 October 2026, before any episode below was searched for or coded, and before any proxy
signal or index return was computed for these episodes. Studies 2 and 3 of the follow-up plan to
`docs/DEGROSS_PROXY_2026-10-29.md`, `docs/DEGROSS_PROXY_B_2026-10-29.md` and
`docs/VIP_PREMIUM_2026-10-29.md`. Non-evidentiary side tests outside the FNTN funnel; not
investment advice.

## 1. Purpose

The gate tests of Versions A and B rested on three reference weeks. Study 2 builds a fuller list of
Goldman Sachs Prime Brokerage de-gross episodes from the press, under rules fixed here, and scores
both proxies against it without retuning either. Study 3 measures whether Nasdaq 100 moves precede
or follow those episodes.

## 2. Episode collection (fixed before searching)

**Sources.** Any publicly reachable article that attributes the figures to Goldman Sachs prime
brokerage, Prime Services, the Prime book or the Prime desk: Bloomberg, Reuters, CNBC, Business
Insider, Financial Times, Wall Street Journal, MarketWatch, Barron's, Yahoo Finance, Investing.com,
HedgeWeek, ZeroHedge and similar. Tiers as in the event-coding schema (T2 major wires and papers,
T3 aggregators); T4 social media is excluded.

**Search protocol.** For each year Y from 2016 to 2026, run these five web searches, and follow
links found in their results:
1. `Goldman Sachs prime brokerage hedge funds de-grossing Y`
2. `Goldman prime book hedge funds largest net selling since Y`
3. `hedge funds cut gross leverage Goldman Sachs Y`
4. `Goldman Sachs prime hedge funds dumped tech stocks fastest pace Y`
5. `hedge funds degross Goldman long sales short covers Y`
Every candidate article found is logged with its inclusion decision and reason, included or not.

**Inclusion.** An article yields an episode when it reports, from Goldman prime data, for US, North
American or global equities, or for US or global information technology (or TMT):
- **Class D (de-gross):** a reduction in gross exposure or gross leverage, "de-grossing", or
  selling led by long sales together with short covers, described as the largest, fastest or
  sharpest since a stated time at least 6 months earlier, or as a record; or
- **Class N (net selling):** net selling described as the largest or fastest since a stated time at
  least 6 months earlier, or as a record, without a gross reduction or short covers being reported.
An article reporting both is Class D.

**Dating.** The episode week is the ISO week of the data period end the article states; if it
states none, the ISO week of the article's publication date minus one week. The publication date
(first public) is recorded separately.

**Merging.** Episodes of the same class whose week-end dates are within 14 days of each other merge
into the earliest. A Class N episode within 14 days of a Class D episode is dropped.

**Fields** (`episodes.csv`): `episode_id, class, week_end, first_public, region, sector, outlet,
tier, url, phrase` (`phrase` at most 12 words, identifying the claim, not reproducing text).

The three reference weeks of the gate tests are coded under the same rules, with no special
treatment; if the rules do not admit one of them, it is not added.

## 3. Study 2: proxy hit rates

- **Proxies:** Version A (momentum deciles) and Version B (13F baskets), each exactly as frozen,
  recomputed on the runner by importing their frozen `run.py` (and B's frozen `build.py` inputs).
- **Hit:** an episode is hit by a proxy when some signal-evaluable week of that proxy with D_t
  true has its week-end within 7 calendar days of the episode's week-end.
- **Scored episodes:** Class D episodes whose week-end lies inside the proxy's signal-evaluable
  range (A: to its last French week; B: from its first signal-evaluable week).
- **Chance rate:** q = 1 - (1 - b)^3, b the proxy's de-gross base rate. p = binomial probability of
  at least the observed hits out of the scored episodes at rate q.
- **Verdict per proxy:** SEES when the hit rate is at least 50% **and** p <= 0.05 **and** at least 8
  episodes are scored; INSUFFICIENT below 8 scored episodes; otherwise DOES NOT SEE.
- Reported without weight: the same for Class N episodes, and for Class D and N together.

## 4. Study 3: timing against the Nasdaq 100

For each Class D episode, using FRED `NASDAQ100` closes and k counting NDX trading days from the
last NDX day on or before the episode week-end (k = 0):

- Pre-window return R_pre = N(0) / N(-10) - 1; post-windows R_21 = N(21) / N(0) - 1 and
  R_63 = N(63) / N(0) - 1. The same from the first-public date (k = 0 at the first NDX close on or
  after the publication date), for R_21 and R_63, as what a reader of the report could have earned.
- Unconditional comparison: all weeks from 2016-01-01 with the windows available.
- **H-lag (primary):** the mean pre-window return of episodes is below the unconditional mean.
  One-sided permutation p (10,000 draws of the same number of weeks, `default_rng(20261029)`); the
  claim "de-grossing is reported after the market has fallen" is supported at p <= 0.05.
- **H-lead (reported, no verdict weight):** mean R_21 and R_63 from the first-public date below the
  unconditional mean, same permutation.
- Fewer than 8 Class D episodes with the windows available: INSUFFICIENT.

## 5. Disclosures

1. Episodes come from press coverage, which over-represents dramatic weeks; the list is a sample of
   Goldman-reported episodes, not the population.
2. The episode search is done by a language-model agent following section 2; its full log of
   candidates and decisions is committed with `episodes.csv`.
3. The analyst has seen both proxies' z and leg returns within 10 days of the three original
   reference weeks; nothing else of either proxy's weekly series.
