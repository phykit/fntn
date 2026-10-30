# Prior-art batch, 29 October 2026: the frame, the ranking and what is being run

Written after `docs/ADJACENT_TESTS_2026-10-29.md` closed without a tradeable result, in answer to
the operator's request for an analysis of the latest prior art and the five best ideas to run. Not
investment advice.

## The frame from the latest prior art

- **Post-publication, out of sample, the average published anomaly earns nothing.** Goncalves,
  Loudis and Ogden (February 2025, "Out-of-Sample Alphas Post-Publication"): across 177 anomaly
  long-short strategies the post-publication out-of-sample CAPM alpha is close to zero (t about
  0.4), although in-sample post-publication alphas stay positive. Chen and Velikov (2023): 204
  anomalies net about 4 bp a month after costs and publication. Siganos (2012): of seven anomalies a
  retail investor could trade after costs, one (earnings yield) survived.
- **This project's own record agrees:** about thirty pre-registered tests since 9 October and one
  replication (the ten-month trend rule, as drawdown insurance), with the recurring finding that the
  market leads the indicators (`claude/strategy_inventory_2026-10-25.md`).
- **What that implies for selection.** Cross-sectional anomalies that need the short leg are out of
  reach for a long-only book and are the ones that decayed most. The candidates with a structural
  reason to persist are calendar and disclosure effects (institutional frictions do not read
  papers), event drifts with low turnover, and anything implementable at near-zero cost at the
  index level.

## The ranking (five), with the evidence and the status

| # | Idea | Evidence | Post-publication | Data and cost | Status |
|---|---|---|---|---|---|
| 1 | **Insider open-market purchases, entry at the next open after the Form 4, 5-session hold** | Cohen, Malloy and Pomorski (JF 2012); Lakonishok and Lee (2001) | Zhao (arXiv 2602.06198, 2026): microcaps 2018 to 2024, mean 30-day CAR 6.3% but median 1.9%, costs heavy; no large-cap result | EDGAR (free) plus survivorship-free prices (EODHD, USD 19.99 a month) | **Built and frozen since 7 October (`killtest-2026-10-07`, 48 tests), never run.** Blocked on the EODHD key; the SEC contact is now authorised |
| 2 | **Pre-FOMC announcement drift, Nasdaq 100** | Lucca and Moench (JF 2015): about 49 bp in the 24 hours before scheduled announcements, 1994 to 2011 | Disputed: Ignatieva and Ohashi (Applied Economics 2025) "short-lived"; practitioner tests show a 2016 to 2019 lull and a return since | Free (FRED, Fed calendars, QQQ); 8 windows a year, 2 bp a trade | **Running** (`tools/fomc_drift`) |
| 3 | **Dividend month premium, long leg** | Hartzmark and Solomon (JFE 2013): 0.3% to 0.5% a month, 1927 to 2009 | No post-2009 replication found: 2010 to 2026 is a genuine out-of-sample test | Free (yfinance), survivorship in the universe; turnover about 100% a month one-way | **Running** (`tools/divmonth`) |
| 4 | **Halloween effect, Nasdaq 100** | Bouman and Jacobsen (AER 2002); Jacobsen and Zhang (2018): 100-plus markets, three centuries of UK data | Persisted in every sub-period to 2009 in the UK series; US evidence after 2002 mixed | Free (FRED); two switches a year | **Running** (`tools/halloween`) |
| 5 | **Buyback announcement drift** | Peyer and Vermaelen (RFS 2009); Manconi, Peyer and Vermaelen (JFQA 2019): 12 to 48 month drift after open-market repurchase announcements | Authors report persistence after publication; no independent post-2015 US test found | EDGAR full-text search (free) plus survivorship-free prices (EODHD) | Not built; needs the same key as 1 |

**Excluded, with the reason:** the earnings announcement premium (disappeared in the US after the
2004 8-K rule, Heitz, Narayanamoorthy and Zekhnini 2020); the overnight return effect (two trades
a day; costs); turn-of-month and pre-month-end liquidity (tested 25 October, decayed); long-only
factor tilts (MTUM against SPY: Sharpe 0.84 against 0.85 in this project's own test today);
index additions (the effect has disappeared, Greenwood and Sammon 2024); volatility-managed
momentum (passed long-short today; the long-only form failed).

## What is being run and what it needs

Tests 2, 3 and 4 are pre-registered (`fc34da3`), built with independent second implementations,
and run on GitHub Actions in one job. Tests 1 and 5 need an EODHD key as the repository secret
`EODHD_KEY`; test 1 then runs unchanged under its frozen rule in a day, and test 5 is a two-day build.

## Results (run 40968724411, 29 October 2026, commit `83dcf6e`)

All three FAIL under their pre-registered primary criteria. Every verdict, every primary statistic
and every count agrees between the frozen implementation and the independent second implementation;
the only disagreements are the two definitional ones named before the run (below). Results and both
implementations' outputs are under `tools/halloween/results/1/`. The frozen hashes verified as run.

| Test | OOS sample | Primary | Verdict | Strategy, net | Comparator |
|---|---|---|---|---|---|
| Halloween, NDX | 2003-01 to 2026-09, 285 months | c = −0.27% a month, t = −0.45 (need c > 0, t ≥ 2) | **FAIL** | NDX in winter, bills in summer: 7.6% a year, Sharpe 0.51, drawdown −28% | NDX held: 15.5%, Sharpe 0.80, drawdown −50% |
| Pre-FOMC drift, NDX | 2016-01 to 2026-10, 2,701 days, 85 announcements | d = +11.9 bp, shift p = 0.219 (need p ≤ 0.025) | **FAIL** | QQQ on announcement days only, 2 bp a trade: 3.4% a year, Sharpe 0.27, invested 3.1% of days | QQQ held: 20.1%, Sharpe 0.83 |
| Dividend month, S&P 500 | 2010-01 to 2026-09, 201 months | D = −10.3 bp a month, t = −2.00 (need D > 0, t ≥ 2) | **FAIL** | Predicted payers, 10 bp a leg: 14.1% a year, Sharpe 0.85, turnover 85% a month one-way | Universe: 17.8%, Sharpe 1.05 |

**Halloween.** The sign is wrong out of sample: winter months averaged 1.07% excess and summer
months 1.34%. The replication sample (1986 to 2002, 203 months) gives c = +1.67% a month at t =
1.55, so the effect was not significant on this index even in the period the literature covers.
Winter beat the following summer in 12 of 22 pairs. The full sample (488 months) gives c = +0.54%,
t = 0.94.

**Pre-FOMC drift.** Announcement days averaged 18.6 bp against 6.7 bp on other days, and 55% of
them were positive against 56% of all days. The full sample from 1994 (261 announcements) gives d
= +30 bp at shift p = 0.003, so the Lucca and Moench effect is in the data and is concentrated
before 2016, which is the post-publication decay the prior art describes. The day-before window
is null (d = +2 bp, p = 0.45) and the two-day window is not better (d = +14 bp, p = 0.23). By year,
2022 was the one large positive year (+8.0% summed over eight announcement days in a year the index
lost 36%); 2016, 2018 and 2026 to date were negative. The Newey-West t is 0.72 (coefficient on the
indicator) or 1.15 (the announcement-day mean); neither reaches 2. No announcement day in the list
fell on a non-trading day (`n_dropped` 0); 2020 has seven scheduled meetings because the March
meeting was cancelled.

**Dividend month.** Predicted payers underperformed the universe by 10 bp a month out of sample
and by 14 bp a month (t = −2.58) over 2001 to 2026; both OOS halves are negative. The universe is
the current S&P 500 (502 tickers, 87 with no dividend history), so it is survivor-biased, and the
bias runs *against* the hypothesis: the names that grew into the index without paying dividends sit
permanently in the non-payer group. The FAIL is therefore a failure to find the premium in a
universe tilted away from it, not clean evidence that the premium is absent in the full
cross-section; a CRSP-grade test is the only way to settle that, and the tradeable question for a
long-only book of large caps is answered either way, because this is the universe such a book
would trade. Turnover is 85% a month one-way, so costs alone take about 2% a year.

**The two definitional disagreements, both named before the run.** (i) FOMC `nw_t_oos`: the
frozen rule reports the t of the coefficient on the announcement indicator (0.72); the second
implementation reports the t of the announcement-day mean, intercept plus coefficient (1.15), and
flags that its `nw_t_diff_oos` equals the frozen figure to 1e-6, so the arithmetic agrees and the
reading differs. The statistic is secondary and both readings are below 2. (ii) Dividend month
strategy figures: the frozen rule runs the strategy from 2001 and reads the OOS subset, so the first
OOS month's turnover is measured against December 2009 holdings; the second implementation starts
the strategy in January 2010 from cash. Mean turnover 0.8460 against 0.8441, Sharpe 0.8512 against
0.8515; the second implementation's `mean_turnover_excluding_first_month` (0.8459) reconciles the
two. Neither disagreement touches a verdict or a primary statistic.

**What this leaves of the five.** Three of the five free candidates failed; the two that remain
(insider purchases, buyback drift) are the two whose prior art reports persistence after
publication and the two that need the EODHD key. The insider test has been frozen since 7 October
and runs unchanged once the key exists.
