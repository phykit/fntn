# Pre-registration B: the spot residual as a predictor of the front-to-second calendar spread, natural gas

Written 15 October 2026, before any observation of the series named below was retrieved for this
test. A non-evidentiary side test outside the FNTN funnel: no apparatus, no row in
`docs/OPEN_ITEMS.md`, no authorisation. A kill test: the pass and fail rules below are fixed here
and applied mechanically by `run_b.py`. Data are fetched and read on the GitHub Actions runner
only; derived statistics only are stored.

## 1. Origin and hypothesis

The parent test of this morning found that the spot converges to the front future and that the
front future's own return does not move with the residual. If a spot dislocation contaminates the
front contract slightly and the second contract not at all, the residual would predict the
front-to-second spread even though it does not predict the front's total return. The spread is a
tradable instrument (a calendar spread).

**Hypothesis H.** On kept days, M_t (the front contract's premium over spot net of financing) is
followed by a change in the front-to-second spread in one direction or the other over the next 1,
3 and 5 trading days, primary 5, beyond the spread's own level and recent change and beyond spot
momentum.

**Registered sign: none (two-sided), carrying forward the operator's choice of 15 October 2026 for
the parent test.** One hypothesis; two-sided level **0.025** (0.0125 in each tail).

**Asset:** Henry Hub natural gas only (EIA publishes contracts 1 to 4 for gas; for the oil
products only contract 1).

**Priors.** The parent test: the front's return shows nothing (NW t 1.2 at five days). The
mechanism stated above gives a negative coefficient (M low, meaning spot above the front, is
followed by the spread widening as the front falls back relative to the second). The spread's
own mean reversion is a known feature and is in the baseline. The two-sided test carries both.

## 2. Data

| File | Series | Source | Fields |
|---|---|---|---|
| `data/ng_spot.csv` | Henry Hub spot, USD/MMBtu, daily | EIA via FRED `DHHNGSP` | `DATE,VALUE` |
| `data/ng_c1.csv` | NYMEX natural gas futures contract 1, official 2:30 p.m. close | EIA `RNGC1d.xls` | `DATE,CLOSE` |
| `data/ng_c2.csv` | Contract 2, likewise | EIA `RNGC2d.xls` | `DATE,CLOSE` |
| `data/tbill.csv` | 3-month Treasury bill, discount basis, per cent | FRED `DTB3` | `DATE,RATE` |

ISO dates, oldest first, empty field for missing. The EIA series end on 5 April 2024.

**Contract definitions, expiries, timing and switch convention:** as in pre-registration A,
sections 2 and 3, including the PROBE 3 RESULT recorded there.

## 3. Calendar, exclusions and definitions

**Joint calendar.** Dates on which spot, contract 1 and contract 2 all carry numeric values.
Positions t = 0, ..., N-1.

**Rate.** r_t = (latest `tbill` RATE on or before date t) / 100.

**Expiries and exclusions, as in the parent test but with A's business-day expiries.** X for
each delivery month as in A section 3 (business days, holiday list as there). k_X =
position of the last joint date on or before X. Positions k_X - 4 to k_X + 1 are **excluded**;
others **kept**. For a kept day t, X(t) = the first expiry strictly after date_t with k_X defined
or X after the last joint date; tau_t = (X(t) - date_t in calendar days) / 365. Two kept days are
in the same contract if they share X(t).

At position t (S = spot, F1 = contract 1, F2 = contract 2):

- F*_t = S_t x exp(r_t x tau_t). **M_t = 100 x (F1_t / F*_t - 1)**, in pp, kept days only.
- **Spread:** Sp_t = 100 x ln(F2_t / F1_t), in pp (positive = contango between the first two
  months).
- **Outcome:** D_h(t) = Sp_(t+h) - Sp_t, h in {1, 3, 5}, defined only if t and t+h are both kept
  and in the same contract (so that the spread is the same pair of contracts at both ends).
- **Baseline:** Sp_t; dSp1_t = Sp_t - Sp_(t-1) and dSp5_t = Sp_t - Sp_(t-5), each defined only if
  both ends are kept and in the same contract; n1_t = 100 x ln(S_t / S_(t-1)) and n5_t likewise.
- **Parent replication (section 8 only):** R_5(t) = 100 x ln(S_(t+5) / S_t), the spot change.

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

- Each h in {1, 3, 5}: slope b_h of D_h on M, Newey-West t, p+, p-, p2, minimum detectable slope
  2.80 x s.e. **Primary: b_5; s = sign(b_5).**
- **Incremental:** D_5 on a constant, M, Sp, dSp1, dSp5, n1, n5; coefficient g with Newey-West t
  (L = 10).
- **Out of sample:** on the aligned sample of {M, Sp, dSp1, dSp5, n1, n5, D_5}, with positions
  counted within that aligned sample, for t >= 1000, fit the baseline (Sp, dSp1, dSp5, n1, n5)
  and the augmented model (plus M) by OLS on positions 0..t-5 inclusive; R2_OS = 1 - SSE_aug /
  SSE_base; Clark-West mean and Newey-West t (L = 10).
- **Size:** Q = 80th percentile of s x M on the h = 5 aligned sample; Dq = mean D_5 on days with
  s x M >= Q minus mean D_5 over all days, in pp. If s = 0, Dq = 0.

## 6. Units

M and Sp in pp; D_h in pp (a 1 pp move in the spread is 1% of one leg's notional). Slopes per
1 pp of M and per one standard deviation.

## 7. Verdict rule (applied mechanically)

| Criterion | Requirement |
|---|---|
| (a) primary | b_5 != 0 and p2 <= 0.025 |
| (b) horizons | sign(b_1) = s and sign(b_3) = s |
| (c) halves | sign of b_5 = s in each half |
| (d) incremental | sign(g) = s and \|Newey-West t\| >= 2.0 |
| (e) out of sample | R2_OS > 0 |
| (f) size | Dq >= 0.157 (pp of the spread) |

**PASS:** all of (a) to (f). **WEAK:** (a) met, another not. **FAIL:** (a) not met.
**UNSCORABLE:** fewer than 100 rotation shifts at h = 5. The direction s is reported.

**What a verdict licenses.** A PASS would justify one frozen test of the executed calendar
spread with its two-leg costs, margin and the operator's futures permissions (unverified). It
authorises no capital. A FAIL is no support at the detectable size.

## 8. Reported without weight in the verdict

1. Baseline alone: slopes of D_h on Sp, dSp1, dSp5, n1, n5 separately, each h, with Newey-West t
   and p+, p-; R2_OS of the baseline model against the historical mean from position 1000.
2. **Parent replication on settlement data:** on kept days, slopes of R_5 (the spot change) on M
   with Newey-West t and p2, and the quintile means of R_5 by M; and the slope of the contract 1
   log return over 5 positions (both ends kept, same contract) on M. This repeats the parent
   test's headline with the 2:30 p.m. NYMEX close in place of Yahoo's 5 p.m. close.
3. The level of Sp and of M: mean, median, 5th and 95th percentiles, standard deviation, share
   positive.
4. Regimes: per calendar year with 20 or more days; heating season (signal dates in November to
   March) against the rest; high and low spot volatility at the median; Sp > 0 against Sp <= 0.
5. Fixed hold-out: b_5 on the last 30% of the h = 5 aligned sample.
6. Influence: b_5 after dropping the 1% most extreme |M - median|; leave-one-year-out range.
7. Quintiles of M: mean and count of D_5.

## 9. What was known before this file was frozen

As in pre-registration A, section 9, including the PROBE 3 RESULT recorded there. No value of
any series was read beyond those structure statistics. The parent test's result is known.

## 10. Limits fixed in advance

- The EIA spot vintage lags; no cost in the verdict except the size threshold; two legs' costs
  apply in practice.
- Sample 1997 to 5 April 2024 (spot from 1997, EIA series to 2024). Kept days only, so about
  4,500 signal days.
- One hypothesis; two-sided.

## 11. Independent check

`verify_b.py` is written from this file (and A's sections 2 and 3 for the shared definitions)
and the data headers alone, without sight of `run_b.py` or `kt.py`, and every criterion figure
is compared on the runner.
