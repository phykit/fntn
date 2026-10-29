# Pre-registration: aggregate short interest as a predictor of Nasdaq 100 returns; the data probe and the power rule

Written 29 October 2026, before any search for the data was run. The idea is Rapach, Ringgenberg
and Zhou, "Short interest and aggregate stock returns", JFE 2016 (the short interest index, SII).
Non-evidentiary side test outside the FNTN funnel; not investment advice.

## 1. The test that would be run

- SII_t: the equal-weighted mean across US listed stocks of (short interest / shares outstanding) at
  the month's last reporting date, in logs, **detrended by a linear trend fitted recursively on data
  to t only** (the published index detrends on the full sample, which uses the future; this test
  does not).
- Forward return: the next calendar month's Nasdaq 100 excess return (FRED NASDAQ100, over the
  one-month Treasury bill from the French RF). Executable: the signal is known at the reporting
  date; the return begins the following month.
- H1 (registered sign): the slope of the forward return on SII_t is **negative**. Primary: one-sided
  circular-shift p <= 0.025 (shifts of 12 to n - 12 months); secondary: out-of-sample R-squared
  against the historical mean from month 120 onwards, positive with the Clark-West t >= 1.65.
- PASS: both; WEAK: primary only; FAIL: primary not met.

## 2. The power rule (fixed before the probe)

With n monthly observations, 80% power at one-sided 5% for a single-regressor slope needs
t about 2.49, that is R-squared about 2.49^2 / (n + 2.49^2): 5.8% at n = 100, 2.5% at n = 240,
1.0% at n = 600. The published one-month R-squared of the SII is about 2%. **The test is run only if
a free series of at least 240 months exists**; otherwise the verdict is NOT TESTABLE AT ADEQUATE
POWER, with the probe log, and no regression is run on a shorter series (a result on 100 months
could neither confirm nor refute an effect of the published size).

## 3. The probe

Sources to check, in order, each logged with what was found: i) the authors' own published series
(Ringgenberg's data page); ii) FINRA's equity short interest files (known from this project to begin
in 2018); iii) NYSE and Nasdaq aggregate short interest histories; iv) FRED and other free
aggregators. Paid sources (Compustat, Bloomberg, S&P) are noted but do not satisfy the rule.

## 4. Disclosures

1. The analyst knows the paper and its figures.
2. A series that exists only to the paper's own end date (about 2014) is in-sample for the paper and
   cannot test persistence; it counts towards the 240 months only together with a consistent
   continuation.
