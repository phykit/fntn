# Pre-registration: the pre-FOMC announcement drift on the Nasdaq 100, after publication

Written 29 October 2026, before any price observation was retrieved for this test and before the
FOMC date list was collected. Idea: Lucca and Moench, "The Pre-FOMC Announcement Drift", JF 2015
(the 24 hours before scheduled FOMC announcements earned about 49 bp on the S&P 500, 1994 to 2011,
most of the equity premium). Persistence is disputed (Ignatieva and Ohashi, Applied Economics 2025,
"short-lived"; practitioner tests report a lull in 2016 to 2019 and a return since). Non-evidentiary
side test outside the FNTN funnel; not investment advice; authorises nothing.

## 1. Dates

Scheduled FOMC meetings from February 1994 (the first meeting after which decisions were announced
the same day) to the latest meeting before the run, from federalreserve.gov only (the historical
year pages and the current calendar page). The **announcement day** is the last day of each scheduled
meeting. Unscheduled and conference-call meetings are excluded. The list is collected by an agent
that reads no price data, committed as `fomc_dates.csv` and frozen before any price is retrieved.

## 2. Data and definitions

- NDX: FRED `NASDAQ100` daily closes (from 1986); RF: French daily (`ff5_daily.csv`), in decimals.
- Trading days are NDX days with a close. Daily excess return x_t = NDX_t / NDX_(t-1) - 1 - RF_t.
- **Announcement-day return:** x on the announcement day t (close t-1 to close t; the 2 pm statement
  falls inside it, so this is Lucca and Moench's window moved to close-to-close). If the announcement
  day is not an NDX trading day, the meeting is dropped (and counted).
- Samples: **OOS (primary): 1 January 2016 to the last NDX close** (after publication); full sample
  from February 1994 reported.

## 3. Test

- **Primary:** mean x on announcement days minus mean x on all other trading days, OOS, > 0, with a
  one-sided circular-shift p <= 0.025: the announcement-day indicator is rotated by k trading days,
  k = 5 .. n - 5, and p = (1 + number of rotations whose difference is at or above the observed) /
  (1 + number of rotations). INSUFFICIENT with fewer than 60 OOS announcement days.
- **Verdict:** PASS if the primary is met; FAIL otherwise.

## 4. Reported without weight

The same for the day before (t-1) and the two-day window (close t-2 to close t); the full sample;
the OOS mean announcement-day return in bp with a Newey-West t (L = 5); the share of announcement
days positive against all days; by calendar year, the sum of announcement-day excess returns against
the year's total; a strategy, long QQQ (Yahoo adjusted closes, from 1999) from the close of t-1 to the
close of t and cash otherwise, 2 bp a trade, annual return, Sharpe and share of days invested against
QQQ held, OOS.

## 5. Disclosures

1. The analyst knows the papers and the market history of the sample. Eight meetings a year give
   about 86 OOS announcement days; the test can detect a drift of the published size (about half a
   per cent a day) and not a much smaller one.
2. Close-to-close is a coarser window than the paper's 2 pm to 2 pm; the post-announcement move is
   inside it, which the paper excluded.
3. A second implementation is written from this file alone and compared.
