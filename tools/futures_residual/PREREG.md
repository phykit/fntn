# Pre-registration: the futures residual over spot as a predictor of the spot price, US energy

Written 15 October 2026, before any observation of any spot, futures or rate series named below was
retrieved. A non-evidentiary side test outside the FNTN funnel: no apparatus, no row in
`docs/OPEN_ITEMS.md`, no authorisation. A kill test: the pass and fail rules below are fixed here and
are applied mechanically by `run.py`. The data are fetched and read on the GitHub Actions runner only;
no observation of any input is committed, printed or stored. Derived statistics only.

## 1. Origin and hypotheses

Idea as received (S. Kittson, 15 October 2026, from a research proposal he described as "a really
simple idea"): does the difference between a futures price and its cost-of-carry fair value contain
information about subsequent changes in the spot price, beyond the spot price's own momentum? The
proposal refuses to state a direction ("Do not impose a directional relationship in advance").

The version tested here is the one with the best chance on free data: a physical commodity whose spot
price is a different instrument from the front futures contract, so that the residual carries storage
cost, convenience yield and term structure rather than basis noise. The equity-index version of the
same idea (Nasdaq-100) and the copper-via-miners version were tested on 12 October 2026 and failed
on every hypothesis; they are not repeated.

**Primary asset:** Henry Hub natural gas. **Replication assets, reported without weight in any
verdict:** NY Harbor heating oil and NY Harbor gasoline.

Two hypotheses on the primary asset, each with its own verdict.

| Id | Signal | Hypothesis |
|---|---|---|
| HL | M, the front-contract premium over spot net of financing (section 3) | M is followed by a change in the spot price in one direction or the other |
| HC | dM, the daily change in M | dM is followed by a change in the spot price in one direction or the other |

**Registered sign: none (two-sided), chosen by the operator on 15 October 2026 from three options
offered (negative, positive, two-sided).** Family-wise two-sided level 2.5%, split equally over the two
hypotheses (Bonferroni): each primary test is judged at two-sided **0.0125**, that is 0.00625 in each
tail. The sign of the primary slope is reported and the supporting criteria are judged in that sign.

**Priors, with provenance.**
- `verified_secondary` (NBER working paper 15830, fetched and read 15 October 2026): Chinn and
  Coibion, "The Predictive Content of Commodity Futures", monthly data 1990 to 2009, horizons 3, 6
  and 12 months. For natural gas the basis explains about 13% of subsequent spot changes at 3 months
  and about 24% at 12 months, with a slope of 0.63 (s.e. 0.09) at 3 months; energy futures are
  broadly unbiased predictors of spot. Direction: a futures premium over spot is followed by a spot
  rise. That prior is at horizons of 3 months and more, with the seasonal term structure of gas doing
  much of the work; nothing in it speaks to 1 to 20 trading days.
- `recollection`, not verified: Fama and French (1987) find that the basis forecasts spot changes for
  commodities whose basis is volatile, and risk premia for the others; Gorton, Hayashi and
  Rouwenhorst (2013) associate low inventories and backwardation with higher subsequent futures
  returns. These point in opposite directions for a spot outcome and are the reason the proposal
  declines a sign.
- The operator's earlier tests (9 to 12 October 2026) found equity moves preceding the candidate
  signal rather than following it, and no futures-premium effect on the Nasdaq-100 or on copper
  miners.

## 2. Data

All series are retrieved by `fetch.py` on the runner at run time and written to `data/`. Nothing in
`data/` is committed, uploaded or cached.

| File | Series | Source | Fields |
|---|---|---|---|
| `data/ng_spot.csv` | Henry Hub natural gas spot price, USD per MMBtu, daily | EIA, as republished by FRED, series `DHHNGSP` | `DATE,VALUE` |
| `data/ng_fut.csv` | Henry Hub natural gas futures, continuous front contract, Yahoo symbol `NG=F` | Yahoo Finance history | `DATE,CLOSE` |
| `data/ho_spot.csv` | No. 2 heating oil, New York Harbor spot, USD per gallon, daily | EIA via FRED, `DHOILNYH` | `DATE,VALUE` |
| `data/ho_fut.csv` | NY Harbor ULSD (heating oil) futures, continuous front contract, `HO=F` | Yahoo Finance history | `DATE,CLOSE` |
| `data/rb_spot.csv` | Conventional gasoline, regular, New York Harbor spot, USD per gallon, daily | EIA via FRED, `DGASNYH` | `DATE,VALUE` |
| `data/rb_fut.csv` | RBOB gasoline futures, continuous front contract, `RB=F` | Yahoo Finance history | `DATE,CLOSE` |
| `data/tbill.csv` | 3-month Treasury bill, secondary market, discount basis, per cent, daily | FRED, `DTB3` | `DATE,RATE` |

ISO dates, oldest first, an empty field for a missing value (FRED's "." is written as empty). Retrieval
window: every observation available on the retrieval date. The sample is whatever the joint calendar
(section 3) yields; no start date is imposed beyond the look-backs.

**Timing, `verified_secondary` and inference.** The EIA daily spot price for date d is the day's
assessment of physical, next-day delivery at the hub or harbour. Yahoo's futures close for date d is
the last Globex trade near 17:00 New York, not the CME settlement, as found on 12 October 2026 for
`NQ=F`; the CME energy settlement is at 14:30 New York. The spot and the futures value for one date
are therefore a few hours apart, both on the same trading day. The outcome starts from the spot value
of date t itself (section 3); the signal at t cannot contain information from after date t. FRED
republishes EIA spot prices with a lag of up to a week; a market participant observes the same spot
assessments on the day, so the signal exists in real time, but this free vintage does not.

**Expiry, `verified_secondary` (CME rulebook chapters 508 and 829, read 15 October 2026).** Henry
Hub natural gas futures: trading ceases on the 3rd business day prior to the first calendar day of
the contract month. NY Harbor ULSD and RBOB gasoline futures: trading ceases on the last business day
of the month preceding the contract month. Business days are counted as weekdays; a US holiday
falling in the count moves the true expiry one day earlier than computed. The exclusion window of
section 3 absorbs that.

**Roll.** Each `=F` series is an unadjusted front-contract splice with an undocumented roll date.
Days near each expiry are excluded as signal days (section 3) and the roll check (section 8 item 5)
measures what remains.

## 3. Calendar, exclusions and definitions

Everything below is defined per asset. The primary asset is natural gas; the same definitions are
applied verbatim to heating oil and gasoline.

**Joint calendar.** A date is on the joint calendar if and only if the spot file and the futures file
both carry a numeric value for it. Positions t = 0, 1, ..., N-1. All differences, look-backs and
horizons count positions on this calendar.

**Rate on date t.** The `tbill` RATE on the latest date on or before date t; r_t = RATE / 100. (A
discount-basis bill rate stands in for a financing rate; this is the proposal's "financing only"
specification. Storage, insurance and convenience yield are not estimated and are, by design, what
M contains.)

**Expiries.** For each calendar month Y-m from the first joint date's month to the month after the
last joint date's month, the expiry X of the contract for delivery in month Y-m is: for natural gas,
the third weekday counting backwards from the last day of the preceding month inclusive (that is,
with the last three weekdays of the preceding month numbered 1, 2, 3 from the end, the one numbered
3); for heating oil and gasoline, the last weekday of the preceding month. For each expiry X, let k_X
be the position of the last joint date on or before X (undefined if there is none). Positions k_X - 4
to k_X + 1 inclusive are **excluded** as signal days (five trading days up to and including expiry,
and the day after). Any other position is **kept**. For a kept day t, X(t) is the first expiry date
strictly after date_t for which position k_X exists or X is after the last joint date, and tau_t =
(X(t) - date_t in calendar days) / 365. Two kept days are "in the same contract" if they have the
same X(t).

At position t (S = spot VALUE, F = futures CLOSE):

- Fair value F*_t = S_t x exp(r_t x tau_t). **M_t = 100 x (F_t / F*_t - 1)**, in percentage points
  (pp), kept days only.
- P_t = 100 x (F_t / S_t - 1), the raw premium in pp (section 8 only).
- dM_t = M_t - M_(t-1), defined only if t and t-1 are both kept and in the same contract.
- **Baseline regressors (spot momentum):** n1_t = 100 x ln(S_t / S_(t-1)); n5_t and n20_t likewise
  over 5 and 20 positions.
- **Outcome:** R_h(t) = 100 x ln(S_(t+h) / S_t), h in {1, 5, 20}: the change in the spot price from
  date t to h positions later, in per cent. Outcome positions may fall on excluded days; only signal
  days are excluded.
- **Tradable expression (section 8 only):** Q_h(t) = 100 x ln(F_(t+h) / F_t), defined only if t and
  t+h are both kept and in the same contract (so that no roll lies between them).

**Test sample.** All kept days. A quantity is undefined where any position it needs is out of range
or excluded as stated. Each test uses exactly the days on which every quantity it needs is defined
(its "aligned sample", in date order, length m).

## 4. Estimators

Stated so that a second implementation can reproduce them.

- **Slope.** OLS with an intercept; "slope of y on x" is the coefficient on x.
- **Newey-West t.** Covariance (X'X)^-1 S (X'X)^-1, S = sum_t e_t^2 x_t x_t' + sum_(l=1..L) w_l
  sum_(t=l..m-1) e_t e_(t-l) (x_t x_(t-l)' + x_(t-l) x_t'), w_l = 1 - l/(L+1), no degrees-of-freedom
  correction; x_t is the regressor row including the constant. L = h + 5 unless stated.
- **Rotation p-value.** For aligned arrays x and y of length m and each shift k = 21, ..., m-21, form
  x_k[i] = x[(i + k) mod m] and recompute the simple slope on (x_k, y). K = m - 41 shifts.
  p+ = (1 + #{rotated >= observed}) / (1 + K); p- = (1 + #{rotated <= observed}) / (1 + K);
  **p2 = min(1, 2 x min(p+, p-))**.
- **Percentile:** numpy default (linear). **Standard deviation:** population (ddof = 0).
- **Halves:** first floor(m/2) days of the aligned sample, and the rest.
- **sign(b):** +1 if b > 0, -1 if b < 0, 0 if b = 0.

## 5. Statistics, for each hypothesis, signal x in {M (HL), dM (HC)}

- For each h: slope b_h of R_h on x, Pearson correlation, Newey-West t, rotation p+, p- and p2, and the
  minimum detectable slope 2.80 x the Newey-West standard error. **Primary statistic: b_5; its sign
  s = sign(b_5) is the reported direction.**
- **Incremental regression:** R_5 on a constant, x, n1, n5, n20; coefficient g on x with Newey-West t
  (L = 10). In-sample R-squared of the baseline (n1, n5, n20) and augmented models.
- **Out of sample:** on the aligned sample of {x, n1, n5, n20, R_5}, positions 0..m-1: baseline model
  R_5 on a constant, n1, n5, n20; augmented model the same plus x. For each t >= 1000, fit both by OLS
  on positions 0 to t-5 and forecast R_5 at t. R2_OS = 1 - SSE(augmented) / SSE(baseline) over
  t >= 1000. Clark-West f_t = (y - fb)^2 - [(y - fa)^2 - (fb - fa)^2]; mean and Newey-West t (L = 10).
- **Size:** on the h = 5 aligned sample, with s = sign(b_5): Q = 80th percentile of s x x;
  Dq = mean R_5 on days with s x x >= Q minus mean R_5 over all days, in per cent (the mean outcome
  on the fifth of days where the signal is strongest in its own direction, relative to all days).
  If s = 0, Dq = 0.

## 6. Units

M, P and dM in pp; returns in per cent. Slopes reported per 1 pp of the signal and per one standard
deviation of the signal on its aligned sample.

## 7. Verdict rule, for each hypothesis separately (applied mechanically)

With s = sign(b_5):

| Criterion | Requirement |
|---|---|
| (a) primary | b_5 != 0 and rotation p2 <= 0.0125 |
| (b) horizons | sign(b_1) = s and sign(b_20) = s |
| (c) halves | sign(b_5) = s in each half of the h = 5 aligned sample |
| (d) incremental | sign(g) = s and \|Newey-West t\| >= 2.0 |
| (e) out of sample | R2_OS > 0 against the momentum baseline |
| (f) size | Dq >= 0.157 (15.7 bp, the registered cost floor, used here as a size threshold because the spot price is not itself traded; Dq is already taken in the direction s, section 5) |

- **PASS:** (a) to (f) all met, in the direction s. **WEAK:** (a) met and at least one of (b) to (f)
  not met; not actionable.
- **FAIL:** (a) not met. The direction s is reported with the verdict.

There is no "reversed" outcome: the test is two-sided and either direction can pass.

**What each verdict licenses.** A PASS authorises nothing. It would justify one separate frozen test
of a tradable expression (the front futures contract, section 8 item 2, with a roll-aware outcome,
costs and the operator's futures permissions, which are unverified) under its own pre-registration.
A FAIL is no support at the detectable size, reported as the minimum detectable slope. A WEAK is a
FAIL for any practical purpose. Results on heating oil and gasoline carry no weight in any verdict
and are reported as replications only.

## 8. Reported without weight in the verdict

For the primary asset, and for each replication asset in full (including the verdict rule applied to
it, labelled "replication, no weight"):

1. **Momentum alone:** slopes of R_h on each of n1, n5, n20, each h, with Newey-West t and rotation
   p+, p-; R2_OS of the momentum-only model against the historical mean, from position 1000.
2. **Tradable expression:** slopes of Q_h on x for each h and each signal, with Newey-West t and
   rotation p+, p-, p2; the count; and Dq computed on Q_5 as in section 5. This is the front futures
   contract held within one contract, before costs.
3. **Raw premium:** slopes of R_h on P, each h, with Newey-West t and rotation p+, p-, p2.
4. **The level of M:** mean, median, 5th and 95th percentiles of M; share of kept days with M > 0;
   mean tau in days; the implied annualised carry 100 x ln(F/F*) / tau, mean and median.
5. **Roll check:** on the dM aligned sample, the maximum |dM|, the 99th percentile of |dM|, and the
   count of days with |dM| > 5 pp. Across each exclusion window: the step M on the first kept day
   after the window minus M on the last kept day before it (both defined), its median absolute
   value, and the count of steps with |step| > 5 pp (the roll itself; expected to be large for gas,
   whose curve is seasonal).
6. **Regimes:** b_5 in each calendar year with at least 20 days; in high and low spot volatility
   (20-day standard deviation of n1 ending at t, split at its full-sample median); for natural gas
   only, in heating season (signal dates in November to March) and outside it.
7. **Fixed hold-out:** b_5 on the last 30% of the h = 5 aligned sample.
8. **Influence:** b_5 after dropping days with |x - median(x)| at or above its 99th percentile; and
   leaving out each calendar year in turn (minimum and maximum and the years that produce them).
9. **Quintiles:** mean and count of R_5 in each quintile of x (full-sample breakpoints).

Anything computed beyond sections 5 to 8 is labelled "not pre-registered" and carries no weight.

## 9. What was known before this file was frozen

1. No observation of any series in section 2 was retrieved. FRED and Yahoo are not reachable from
   the analyst's workspace; only the runner reaches them. The column layout of a FRED CSV and of the
   Yahoo chart JSON are known from documentation and earlier work.
2. The analyst is a language model with general knowledge of market history to about mid-2026,
   including, as recalled: the Henry Hub spot spikes of February 2021 (winter storm Uri) and of the
   2022 export boom, the collapse to about USD 2 in 2023 and 2024, the heating-oil spike of 2022, and
   the gasoline crack spread of mid-2022. The window cannot be treated as unseen; the influence and
   per-year items of section 8 are mechanical for that reason.
3. Prior art: section 1.
4. The structure of the gas term curve is seasonal (winter premium), so M for the front contract
   carries a predictable seasonal component. Section 8 item 6 reports the heating-season split; the
   verdict does not condition on it.
5. The Yahoo roll date for `NG=F`, `HO=F` and `RB=F` is not documented; the five-day exclusion is a
   guess, and the roll check is the measurement of whether it was enough.

## 10. Limits fixed in advance

- Spot and futures closes a few hours apart on the same day; no intraday data; no CME settlements.
- Financing only: a Treasury bill discount rate, no storage, insurance or convenience-yield
  estimates, no transaction-cost band. M is the residual the proposal calls specification 1 and
  nothing more.
- The free spot vintage lags; the test measures whether the information exists, not whether the
  operator could act on it from free data.
- About 6,000 joint days for natural gas; Bonferroni over two hypotheses; two-sided throughout.
- No cost model in the verdict except the size threshold. The spot price is not traded; the futures
  expression is reported without weight and without costs.
- EIA and Yahoo data are used for internal analysis only; no observation is committed or published.

## 11. Independent check

A second implementation, `verify.py`, is written from this file and the data file headers alone,
without sight of `run.py` or its output, and every criterion figure is compared on the runner.
