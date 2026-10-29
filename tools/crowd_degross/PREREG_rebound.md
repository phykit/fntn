# Pre-registration: study R, do crowded longs rebound after a bad week? (GVIP against QQQ)

Written 29 October 2026, before any figure below was computed. Origin (disclosed): in studies 2 and
2e the four weeks after Goldman-reported de-gross weeks showed crowded longs beating QQQ (+0.63%
against -0.37%, p 0.09, reported without weight); 2e-ii found, without weight, a faint reversal at one
and two weeks outside the episode weeks (slopes -0.08). This test asks whether a general four-week
rebound exists, without Goldman's reports. Non-evidentiary side test outside the FNTN funnel; not
investment advice; authorises nothing.

## 1. Series and signal

- Daily adjusted closes: GVIP, QQQ (as fetched by `tools/gvip_live/fetch.py`); the reconstructed
  basket W (Version B's long leg, by B's frozen `daily_legs`).
- Weekly excess x_t = compounded GVIP return minus compounded QQQ return over ISO week t (a week with
  any missing day is undefined), as in `tools/crowd_degross/run.py`.
- **Signal week t:** x_t at or below the 10th percentile (numpy linear) of x over weeks t-104 .. t-1,
  all defined.
- **Eligible t:** the window complete, x_t and the forward window defined, and t's week-end more than
  14 days from every frozen Goldman episode (D or N) of `tools/degross_episodes/episodes.csv`, so the
  weeks that suggested the idea play no part. Forward windows may overlap an episode week.

## 2. Forward window (executable)

Entry at the close of the first trading day after week t's last trading day (a reader of Friday's
close acts on Monday); exit at the close 20 trading days after entry. Forward excess
R_t = (GVIP close at exit / close at entry) - (QQQ close at exit / close at entry).

## 3. Test

- **H-rebound (primary):** the mean R_t over eligible signal weeks is **above** the mean over all
  eligible weeks. One-sided upper permutation p: 10,000 draws of the same number of eligible weeks
  without replacement, `default_rng(20261029)`.
- **Verdict:** SUPPORTED if p <= 0.05 with at least 20 eligible signal weeks; INSUFFICIENT below 20;
  otherwise NOT SUPPORTED.

## 4. Reported without weight

1. The same on the reconstructed basket W minus QQQ (from 2013; survivorship as disclosed for
   Version B), entry and exit as above using W's daily returns compounded.
2. Forward windows of 5 and 10 trading days.
3. **De-clustered:** only signal weeks with no other signal in the 4 preceding weeks.
4. **The trade.** Each eligible signal (in date order, skipping signals while a trade is open): long
   GVIP and short QQQ in equal amounts from entry to exit. Costs: 10 bp per leg per transaction
   (40 bp a round trip) and QQQ borrow at 0.5% a year for the days held. Reported: trades, share
   profitable, mean and median net return per trade, t of the mean, worst trade, the sum of net
   returns per year of sample, and the same for the basket.

## 5. Disclosures

1. GVIP's sample begins in November 2016, so the primary uses at most about 9 years after the
   104-week window; the basket gives a longer, survivorship-affected check.
2. The analyst has seen studies 2, 2a to 2e and their per-episode figures; nothing about R_t outside
   the episode windows.
3. A second implementation is written from this file alone and compared on the headline figures.
