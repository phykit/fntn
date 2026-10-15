# Pre-registration A: the spot residual in the last days of a futures contract as a predictor of that contract's return to expiry

Written 15 October 2026, before any observation of the series named below was retrieved for this
test. A non-evidentiary side test outside the FNTN funnel: no apparatus, no row in
`docs/OPEN_ITEMS.md`, no authorisation. A kill test: the pass and fail rules below are fixed here
and applied mechanically by `run_a.py`. Data are fetched and read on the GitHub Actions runner
only; derived statistics only are stored.

## 1. Origin and hypothesis

The parent test of this morning excluded the five trading days up to each expiry and found that,
away from expiry, the spot converges to the front future and the future shows nothing. In the
excluded window the front contract stops being a monthly strip and settles into delivery, and a
spot dislocation is most likely to bleed into it. That window is the one futures expression not
yet tested.

**Hypothesis H.** On the last days of the expiring contract's life, M_t, the expiring contract's
premium over spot net of financing, is followed by a return on that contract to its last trading
day in one direction or the other, beyond the contract's own momentum.

**Registered sign: none (two-sided), carrying forward the operator's choice of 15 October 2026 for
the parent test.** One hypothesis; two-sided level **0.025** (0.0125 in each tail).

**Primary asset:** Henry Hub natural gas. **Replication assets, no weight in any verdict:** NY
Harbor heating oil and RBOB gasoline.

**Priors.** The parent test (same morning): away from expiry, spot converges to the future,
coefficient positive, and the future does not move with M. `recollection`, not verified: delivery
dynamics at expiry (physical players covering) push the expiring gas contract towards the physical
price in the final days, which would give a negative coefficient (spot above the contract, M < 0,
is followed by the contract rising). The two-sided test carries both.

## 2. Data

| File | Series | Source | Fields |
|---|---|---|---|
| `data/ng_spot.csv` | Henry Hub spot, USD/MMBtu, daily | EIA via FRED `DHHNGSP` | `DATE,VALUE` |
| `data/ng_c1.csv` | NYMEX natural gas futures contract 1, official daily closing price at 2:30 p.m., USD/MMBtu | EIA `RNGC1d.xls` (sheet "Data 1") | `DATE,CLOSE` |
| `data/ng_c2.csv` | Contract 2, likewise | EIA `RNGC2d.xls` | `DATE,CLOSE` |
| `data/ho_spot.csv` | No. 2 heating oil NY Harbor spot | FRED `DHOILNYH` | `DATE,VALUE` |
| `data/ho_c1.csv` | NY Harbor No. 2 heating oil future contract 1 | EIA `EER_EPD2F_PE1_Y35NY_DPGd.xls` | `DATE,CLOSE` |
| `data/rb_spot.csv` | Conventional gasoline NY Harbor spot | FRED `DGASNYH` | `DATE,VALUE` |
| `data/rb_c1.csv` | NY Harbor RBOB gasoline future contract 1 | EIA `EER_EPMRR_PE1_Y35NY_DPGd.xls` | `DATE,CLOSE` |
| `data/tbill.csv` | 3-month Treasury bill, discount basis, per cent | FRED `DTB3` | `DATE,RATE` |

ISO dates, oldest first, empty field for missing. The EIA futures series end on 5 April 2024
(structure probe, 15 October 2026); the sample ends there.

**Contract 1, `verified_secondary` (EIA table definitions, read 15 October 2026):** "a futures
contract specifying the earliest delivery date", from NYMEX official closing prices at 2:30 p.m.;
natural gas contracts expire three business days prior to the first calendar day of the delivery
month. Heating oil and RBOB: last business day of the month preceding delivery (CME rulebook
chapter 829, read 15 October 2026; RBOB assumed the same). The day on which EIA's contract 1
switches to the next contract was checked by the structure probe of 15 October 2026 (probe 3) and
is recorded in section 9.

**Timing.** The EIA spot assessment and the 2:30 p.m. NYMEX close are on the same trading day; the
spot assessment is a day's trading on the physical market, published after it. The outcome starts
at the same 2:30 p.m. close as the signal's futures component and ends at the expiring contract's
last 2:30 p.m. close.

## 3. Calendar and definitions (per asset)

**Joint calendar.** Dates on which the spot file and the contract 1 file both carry numeric
values. Positions t = 0, ..., N-1.

**Rate.** r_t = (latest `tbill` RATE on or before date t) / 100.

**Business days.** A business day is a weekday that is not a US exchange holiday. The holidays
are, with Saturday observed on the preceding Friday and Sunday on the following Monday, except
that New Year's Day falling on a Saturday is not observed (the exchanges trade on that 31
December): New Year's Day (1 January); Martin Luther King Day (third Monday of January, from 1998);
Presidents' Day (third Monday of February); Good Friday (two days before Easter Sunday, Gregorian
computus); Memorial Day (last Monday of May); Juneteenth (19 June, from 2022); Independence Day
(4 July); Labor Day (first Monday of September); Thanksgiving (fourth Thursday of November);
Christmas Day (25 December). This list is the operator-side reconstruction of the CME holiday
calendar and is checked by section 8 item 9.

**Expiries.** For each calendar month from the first joint date's month to the month after the
last joint date's month, the expiry X of the contract delivering in that month: natural gas, the
third business day counting back from the last day of the preceding month inclusive; heating oil
and gasoline, the last business day of the preceding month. **Only expiries X on or before the
last joint date are used in this test** (a contract whose expiry lies beyond the data has no
return to expiry). k_X = position of the last joint date on or before X (undefined if none). The
**window** of expiry X is positions k_X - 4 to k_X inclusive, and its **last day** is k_X. Windows of successive expiries do not overlap (they are
about 17 trading days apart).

**Switch convention (fixed from probe 3, section 9).** On every window day the contract 1 series
is the expiring contract; on k_X + 1 it is the next one.

At a window position t with e = k_X - t days remaining (e in {0, 1, 2, 3, 4}), S = spot, F =
contract 1:

- tau_t = (X - date_t in calendar days) / 365. F*_t = S_t x exp(r_t x tau_t).
  **M_t = 100 x (F_t / F*_t - 1)**, in pp.
- **Outcome:** Y(t) = 100 x ln(F_(k_X) / F_t), the expiring contract's log return from t to its
  last day. Defined for e in {1, 2, 3, 4}; a day with e = 0 has no outcome and is not a signal day.
- **Baseline (contract momentum):** m1_t = 100 x ln(F_t / F_(t-1)), m5_t = 100 x ln(F_t / F_(t-5)),
  defined only if every position used lies after the previous expiry's last day (so that no roll
  lies inside the look-back).
- **Spot momentum (section 8 only):** n1_t, n5_t as 100 x ln(S_t / S_(t-k)).

**Test sample.** All window days with e in {1, 2, 3, 4}; "signal days" below means these. Each
statistic uses exactly the days on which every quantity it needs is defined (its aligned sample,
in date order, length m).

## 4. Estimators

- **Slope:** OLS with an intercept. **Newey-West t:** (X'X)^-1 S (X'X)^-1, Bartlett weights
  w_l = 1 - l/(L+1), no degrees-of-freedom correction; **L = 5** throughout (the four outcomes of a
  window share an end point).
- **Rotation p-value:** shifts k = 21, ..., m-21 of x against y, K = m - 41; p+ = (1 + #{rotated
  slope >= observed}) / (1 + K); p- likewise with <=; p2 = min(1, 2 x min(p+, p-)).
- **Percentile:** numpy linear. **Standard deviation:** population. **Halves:** first floor(m/2)
  days and the rest. **sign(b):** +1, -1 or 0.

## 5. Statistics

- **Primary:** slope b of Y on M over all signal days pooled, Newey-West t, p+, p-, p2, minimum
  detectable slope 2.80 x s.e. **s = sign(b).**
- **By days remaining:** slope b_e of Y on M for each e in {1, 2, 3, 4}, Newey-West t (L = 5) and
  p2; and the pooled slopes for e in {1, 2} and for e in {3, 4}.
- **Incremental:** Y on a constant, M, m1, m5; coefficient g with Newey-West t (L = 5).
- **Out of sample:** on the aligned sample of {M, m1, m5, Y}, with positions counted within that
  aligned sample, for t >= 400, fit the baseline (m1, m5) and the augmented model (plus M) by OLS
  on positions 0..t-5 inclusive; R2_OS = 1 - SSE_aug / SSE_base; Clark-West mean and Newey-West t
  (L = 5).
- **Size:** Q = 80th percentile of s x M on the pooled aligned sample; Dq = mean Y on days with
  s x M >= Q minus mean Y over all days. If s = 0, Dq = 0.

## 6. Units

M in pp; returns in per cent. Slopes per 1 pp of M and per one standard deviation.

## 7. Verdict rule (applied mechanically)

| Criterion | Requirement |
|---|---|
| (a) primary | b != 0 and p2 <= 0.025 |
| (b) horizons | the pooled slopes for e in {1, 2} and for e in {3, 4} both have sign s |
| (c) halves | sign of b = s in each half |
| (d) incremental | sign(g) = s and \|Newey-West t\| >= 2.0 |
| (e) out of sample | R2_OS > 0 |
| (f) size | Dq >= 0.157 |

**PASS:** all of (a) to (f). **WEAK:** (a) met, another not. **FAIL:** (a) not met.
**UNSCORABLE:** fewer than 100 rotation shifts. The direction s is reported with every verdict.
Replication assets receive the same labels, marked "replication, no weight".

**What a verdict licenses.** A PASS would justify one frozen test of the executed version: a
position in the expiring contract opened at the 2:30 p.m. close with e days remaining and closed
at expiry, with the roll-period spread and the operator's futures permissions (unverified)
stated, and with a real-time spot assessment in place of the FRED vintage. It authorises no
capital. A FAIL is no support at the detectable size.

## 8. Reported without weight in the verdict

1. Baseline alone: slopes of Y on m1 and on m5, with Newey-West t and p+, p-.
2. Spot momentum: the incremental regression with n1 and n5 added; coefficient on M and its t.
3. Away from the window, as the control: on kept days of the parent test's definition (positions
   not in k_X - 4 to k_X + 1 of any expiry), the slope of the contract 1 log return over 4
   positions (t to t+4, both kept and in the same contract) on M_t, Newey-West t (L = 9) and p2.
   This is the parent's null restated on settlement data, for comparison with the window.
4. The level of M in the window: mean, median, 5th and 95th percentiles, standard deviation,
   share positive, by e.
5. Regimes: per calendar year with 20 or more signal days; heating season (windows whose expiry
   falls in October to February, that is, delivery November to March) against the rest; high and
   low spot volatility (20-day standard deviation of n1 at its full-sample median).
6. Fixed hold-out: b on the last 30% of the pooled aligned sample.
7. Influence: b after dropping the 1% most extreme |M - median|; leave-one-year-out range.
8. Quintiles of M: mean and count of Y.
9. Switch check, from the data as read: for each expiry, the indicator that contract 1 on
   k_X + 1 is nearer (in log distance) to contract 2 on k_X than to contract 1 on k_X; the share
   of expiries for which that holds, and the same for k_X and for k_X + 2. This is the probe-3
   convention re-measured on the whole sample; a share below 0.9 at k_X + 1 is recorded as a
   data limit.

## 9. What was known before this file was frozen

1. The structure probe of 15 October 2026 (probe 2): EIA contracts 1 to 4 for natural gas run
   from January 1994 to 5 April 2024 with about 7,500 rows each; heating oil contract 1 from
   1980 and RBOB contract 1 from October 2005 to the same end date; the spot series as in the
   parent test. Probe 3 (same morning) measured on which trading day around the computed expiry
   EIA's contract 1 switches to the next month. Its result is recorded here: **[filled before
   the freeze: see the line "PROBE 3 RESULT" below]**.
2. No value of any series was read beyond those structure statistics.
3. The analyst is a language model with general knowledge of gas market history to mid-2026
   (February 2021, 2022, the 2023 to 2024 collapse). The window cannot be treated as unseen.
4. The parent test's result (spot converges to the future; future unmoved by M away from expiry)
   is known.

PROBE 3 RESULT (read 15 October 2026, before this file was frozen): for 17 of the last 18 natural
gas expiries to April 2024, EIA's contract 1 on the trading day after the computed weekday expiry
is nearer (in log distance) to the previous day's contract 2 than to the previous day's contract
1, and for the remaining one (delivery April 2024) that holds on the computed expiry day itself,
which is Good Friday 2024 moving the true expiry one business day earlier. The detector also
fires on other days in volatile months, where the spread is small against daily moves, so it is
a confirmation of the convention, not a per-expiry roll detector. Conclusion: contract 1 switches
on the business day after expiry, and expiries must be computed on business days, not weekdays;
section 3 now does so.

## 10. Limits fixed in advance

- The EIA spot vintage lags; a real-time assessment would be needed to act.
- No cost in the verdict except the 15.7 bp size threshold; the expiring gas contract's spread in
  its last days is wider than at other times, and liquidity moves to the next month.
- The sample ends 5 April 2024 with the EIA series.
- About 1,300 signal days for gas (four per expiry); overlapping outcomes within a window are
  handled by L = 5 and by the rotation test, which shifts whole blocks.
- One hypothesis; two-sided.

## 11. Independent check

`verify_a.py` is written from this file and the data headers alone, without sight of `run_a.py`
or `kt.py`, and every criterion figure is compared on the runner.
