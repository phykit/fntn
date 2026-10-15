# Pre-registration D: the CME bitcoin futures basis as a predictor of spot bitcoin

Written 15 October 2026, before any observation of the series named below was retrieved. A
non-evidentiary side test outside the FNTN funnel: no apparatus, no row in `docs/OPEN_ITEMS.md`,
no authorisation. A kill test: the pass and fail rules below are fixed here and applied
mechanically by `run_d.py`. Data are fetched and read on the GitHub Actions runner only; derived
statistics only are stored.

## 1. Origin and hypothesis

Follow-up to the energy futures-residual test of the same morning, which found that the spot
converges to the front future and that the future is therefore not tradable on the residual. This
test takes the one liquid pair in which the spot leg is an instrument the operator can hold: spot
bitcoin against the CME bitcoin future. The question is whether the financing-adjusted basis
predicts the subsequent spot return, which is here the tradable return.

**Hypothesis H.** M_t, the front CME bitcoin future's premium over spot net of bill financing, is
followed by a spot bitcoin return in one direction or the other over the next 1, 5 and 20 joint
days, primary 5, beyond spot momentum.

**Registered sign: none (two-sided), carrying forward the operator's choice of 15 October 2026 for
the parent test.** One hypothesis; two-sided level **0.025** (0.0125 in each tail).

**Priors.** `recollection`, not verified: the cash-and-carry basis on CME bitcoin futures has been
large and positive in bull markets and near zero or negative in sell-offs; studies of perpetual
funding rates and the futures basis report that a high basis is followed by lower spot returns
(crowded longs), which is the negative sign. The parent test's mechanism (spot converges to the
future) would give the positive sign. The two-sided test carries both.

## 2. Data

| File | Series | Source | Fields |
|---|---|---|---|
| `data/btc_spot.csv` | Bitcoin in USD, daily close, Yahoo symbol `BTC-USD` | Yahoo Finance history | `DATE,CLOSE` |
| `data/btc_fut.csv` | CME bitcoin futures, continuous front contract, Yahoo symbol `BTC=F` | Yahoo Finance history | `DATE,CLOSE` |
| `data/tbill.csv` | 3-month Treasury bill, secondary market, discount basis, per cent | FRED `DTB3` | `DATE,RATE` |

ISO dates, oldest first, empty field for missing. Retrieval window: everything available.

**Timing, `recollection` on Yahoo's conventions.** Yahoo's `BTC-USD` daily bar for date d closes
at 23:59:59 UTC of d (CoinMarketCap-sourced). The CME bitcoin future closes at 16:00 London on
date d, so the futures close precedes the spot close by six to eight hours. M_t therefore contains
up to eight hours of spot movement after the futures close, measured against a stale future. The
outcome starts at the spot close of date t, the later of the two timestamps, so nothing in the
outcome precedes any component of the signal. The stale hours add noise to M and, if the spot
reverses intraday, could add a mechanical component; section 8 item 3 reports the relation of M to
the same-day spot return as the check.

**Expiry, `verified_secondary` (CME rule filing 17-417S, chapter 350 rule 35002.F, read 15
October 2026).** Trading in expiring bitcoin futures terminates at 4 p.m. London time on the last
Friday of the contract month; if that day is not a business day in both the UK and the US, on the
preceding day that is. Here: the last Friday of each calendar month, by weekday arithmetic.

**Roll.** `BTC=F` is an unadjusted front-contract splice with an undocumented roll date.

## 3. Calendar, exclusions and definitions

**Joint calendar.** Dates on which `btc_spot` and `btc_fut` both carry a numeric value (weekdays,
in practice). Positions t = 0, ..., N-1. All differences, look-backs and horizons count positions.

**Rate.** r_t = (latest `tbill` RATE on or before date t) / 100.

**Expiries.** For each calendar month from the first joint date's month to the month after the
last joint date's month, X = the last Friday of that month. k_X = position of the last joint date
on or before X (undefined if none). Positions k_X - 4 to k_X + 1 inclusive are **excluded** as
signal days; others are **kept**. For a kept day t, X(t) = the first expiry strictly after date_t
with k_X defined or X after the last joint date; tau_t = (X(t) - date_t in calendar days) / 365.
Two kept days are in the same contract if they share X(t).

At position t (S = spot CLOSE, F = futures CLOSE):

- F*_t = S_t x exp(r_t x tau_t). **M_t = 100 x (F_t / F*_t - 1)**, in pp, kept days only.
- **Baseline (spot momentum):** n1_t = 100 x ln(S_t / S_(t-1)); n5_t, n20_t over 5 and 20 positions.
- **Outcome:** R_h(t) = 100 x ln(S_(t+h) / S_t), h in {1, 5, 20}; the spot return, which is the
  tradable return. Outcome positions may be excluded days.
- **Futures expression (section 8 only):** Q_h(t) = 100 x ln(F_(t+h) / F_t), defined only if t and
  t+h are both kept and in the same contract.

**Test sample.** All kept days. Each statistic uses exactly the days on which every quantity it
needs is defined (its aligned sample, in date order, length m).

## 4. Estimators

- **Slope:** OLS with an intercept. **Newey-West t:** (X'X)^-1 S (X'X)^-1, Bartlett weights
  w_l = 1 - l/(L+1), L = h + 5 unless stated, no degrees-of-freedom correction.
- **Rotation p-value:** shifts k = 21, ..., m-21 of x against y, K = m - 41; p+ = (1 + #{rotated
  slope >= observed}) / (1 + K); p- likewise with <=; p2 = min(1, 2 x min(p+, p-)).
- **Percentile:** numpy linear. **Standard deviation:** population. **Halves:** first floor(m/2)
  days and the rest. **sign(b):** +1, -1 or 0.

## 5. Statistics

- Each h: slope b_h of R_h on M, Newey-West t, p+, p-, p2, minimum detectable slope 2.80 x s.e.
  **Primary: b_5; s = sign(b_5).**
- **Incremental:** R_5 on a constant, M, n1, n5, n20; coefficient g with Newey-West t (L = 10).
- **Out of sample:** on the aligned sample of {M, n1, n5, n20, R_5}, for t >= 750, fit baseline
  (n1, n5, n20) and augmented (plus M) by OLS on positions 0..t-5; R2_OS = 1 - SSE_aug / SSE_base;
  Clark-West mean and Newey-West t (L = 10).
- **Size:** Q = 80th percentile of s x M on the h = 5 aligned sample; Dq = mean R_5 on days with
  s x M >= Q minus mean R_5 over all days. If s = 0, Dq = 0.

## 6. Units

M in pp; returns in per cent. Slopes per 1 pp of M and per one standard deviation.

## 7. Verdict rule (applied mechanically)

| Criterion | Requirement |
|---|---|
| (a) primary | b_5 != 0 and p2 <= 0.025 |
| (b) horizons | sign(b_1) = s and sign(b_20) = s |
| (c) halves | sign of b_5 = s in each half |
| (d) incremental | sign(g) = s and \|Newey-West t\| >= 2.0 |
| (e) out of sample | R2_OS > 0 |
| (f) size | Dq >= 0.157 |

**PASS:** all of (a) to (f). **WEAK:** (a) met, another not. **FAIL:** (a) not met.
**UNSCORABLE:** fewer than 100 rotation shifts (fewer than 141 aligned days) at h = 5; no criterion
is met. The direction s is reported with every verdict.

**What a verdict licenses.** A PASS would justify one frozen test of the executed version:
spot bitcoin bought and sold on a venue the operator can use, with that venue's fees and the
signal taken from a real-time futures feed rather than Yahoo's day-end splice. It authorises no
capital. A FAIL is no support at the detectable size.

## 8. Reported without weight in the verdict

1. Momentum alone: slopes of R_h on n1, n5, n20, each h, with Newey-West t and p+, p-; R2_OS of
   the momentum-only model against the historical mean from position 750.
2. Futures expression: slopes of Q_h on M with Newey-West t and p2; Dq on Q_5.
3. Same-day check: slope and Newey-West t (L = 5) of n1_t (the spot return into the signal's own
   close) on M_t; this measures the stale-futures mechanics.
4. The level of M: mean, median, 5th and 95th percentiles, standard deviation, share positive,
   mean tau in days, implied annualised carry 100 x ln(F/F*) / tau in bp, mean and median.
5. Roll check: on kept days, the maximum and 99th percentile of |M_t - M_(t-1)| within a
   contract; across each exclusion window, the step in M and the count above 5 pp.
6. Regimes: per calendar year with 20 or more days; high and low 20-day spot volatility at its
   median; days with M > 0 against M <= 0 (mean R_5 and counts).
7. Fixed hold-out: b_5 on the last 30% of the h = 5 aligned sample.
8. Influence: b_5 after dropping the 1% most extreme |M - median|; leave-one-year-out range.
9. Quintiles of M: mean and count of R_5.

## 9. What was known before this file was frozen

1. No observation of `BTC-USD`, `BTC=F` or `DTB3` was retrieved for this test. The structure-only
   probe of the same morning reported row counts and date ranges for the two Yahoo series.
2. The analyst is a language model with general knowledge of bitcoin's history to mid-2026,
   including the 2018 and 2022 drawdowns, the 2021 and 2024 to 2025 rises, and the spot ETF
   launch of January 2024. The window cannot be treated as unseen.
3. The probe also showed whether individual CME contracts exist on Yahoo; they are not used here.

## 10. Limits fixed in advance

- The futures close precedes the spot close by six to eight hours (section 2). The free spot
  series is a composite exchange price, not a venue price the operator would trade at.
- Financing only; no venue fees in the verdict except the 15.7 bp size threshold, which is below
  typical retail crypto spreads and fees, so a PASS at the threshold would still be a FAIL at
  realistic cost.
- About 2,200 joint days since December 2017; one hypothesis; two-sided.
- Yahoo data for internal analysis only; no observation committed or published.

## 11. Independent check

`verify_d.py` is written from this file and the data headers alone, without sight of `run_d.py`
or `kt.py`, and every criterion figure is compared on the runner.
