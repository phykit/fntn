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
