# Pre-registration C2: the VIX futures basis (constant 30-day) as a predictor of a tradable long-VIX instrument

Written 15 October 2026, after test C (the VIX3M/VIX proxy slope) failed and before any observation
of the futures series named below was retrieved. A non-evidentiary side test outside the FNTN
funnel: no apparatus, no row in `docs/OPEN_ITEMS.md`, no authorisation. A kill test: the pass and
fail rules below are fixed here and applied mechanically by `run_c2.py`. Data are fetched and read
on the GitHub Actions runner only; derived statistics only are stored.

## 1. Origin and hypothesis

Test C used two spot indices as a proxy for the futures basis and failed. Its one limit fixed in
advance was that proxy. This test uses the VIX futures themselves, from CBOE's historical files,
and the basis of the constant-30-day position that VIXY holds, which is the instrument of the
literature (Simon and Campasano 2014: the basis predicts VIX futures returns, futures converging
to spot, so that contango is followed by negative futures returns).

**Hypothesis H.** B30_t, the constant-30-day VIX futures price over the spot VIX, in pp, is
followed by a return on VIXY in one direction or the other over the next 1, 5 and 20 trading
days, primary 5, beyond the level and momentum of the VIX.

**Registered sign: none (two-sided), carrying forward the operator's choice of 15 October 2026 for
the parent test.** One hypothesis; two-sided level **0.025** (0.0125 in each tail).

**Priors.** `recollection`: as in test C; expected sign negative. Test C's result: on the proxy,
nothing (t 0.4 at five days); VIXY's five-day return averaged -1.2% on contango days and -1.8% on
backwardation days, so the decay is unconditional on the proxy's sign.

## 2. Data

| File | Series | Source | Fields |
|---|---|---|---|
| `data/vx.csv` | VIX futures daily settlement, one row per contract-day, monthly contracts only | CBOE historical data CSVs, one file per expiry at `cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_<expiry>.csv`, column `Settle` | `DATE,EXPIRY,SETTLE` |
| `data/vix.csv` | CBOE Volatility Index, daily close, Yahoo `^VIX` | Yahoo Finance history | `DATE,CLOSE` |
| `data/etp.csv` | ProShares VIX Short-Term Futures ETF, Yahoo `VIXY`: open, close, adjusted close | Yahoo Finance history | `DATE,OPEN,CLOSE,ADJCLOSE` |

ISO dates, oldest first, empty field for missing; a `SETTLE` of zero is treated as missing.

**Monthly expiries, `recollection` of the CBOE rule, with the file list as the check.** The final
settlement date of the VIX futures contract for month m is the Wednesday that is thirty days
before the third Friday of month m+1; if that Friday is an exchange holiday, thirty days before
the business day preceding it; if the resulting Wednesday is itself a holiday, the preceding
business day. `fetch_c2.py` computes that date for every month from January 2013 to the month
after the retrieval date using the holiday list of pre-registration A section 3, requests the
file for it, and on a 404 tries the one and two business days before and the one after; the
expiry recorded in `vx.csv` is the date of the file that answered. The fetch log lists every
month's outcome. Weekly contracts are not requested.

**Timing, `recollection`.** VIX futures daily settlement is at the 4:00 p.m. New York close of
the regular session; the VIX index closes at 4:15 p.m.; VIXY closes at 4:00 p.m. The outcome
starts at VIXY's open on the next trading day, after all three.

## 3. Calendar and definitions

**Futures calendar.** For each DATE in `vx.csv`, the set of contracts with a numeric SETTLE and
EXPIRY strictly after DATE, ordered by EXPIRY. F1 is the SETTLE of the first, F2 of the second;
tau1 and tau2 their EXPIRY minus DATE in calendar days. A DATE with fewer than two such contracts
has F1, F2 undefined.

**Joint calendar.** Dates on which `vix` and `etp` carry numeric values for every field and F1,
F2 are defined. Positions t = 0, ..., N-1. There are no exclusions.

At position t (V = VIX close; O, C, A = VIXY open, close, adjusted close; a_t = A_t / C_t):

- w_t = (tau2_t - 30) / (tau2_t - tau1_t), clipped to [0, 1]; F30_t = w_t x F1_t + (1 - w_t) x
  F2_t (the constant-30-day price, linear in days as in the S&P 500 VIX Short-Term Futures Index).
- **Signal:** B30_t = 100 x (F30_t / V_t - 1), in pp (positive = contango).
- **Baseline:** lv_t = ln(V_t); n1_t = 100 x ln(V_t / V_(t-1)); n5_t, n20_t over 5 and 20
  positions.
- **Outcome:** R_h(t) = 100 x ln( (C_(t+h) x a_(t+h)) / (O_(t+1) x a_(t+1)) ), h in {1, 5, 20}.
- **Front basis (section 8 only):** Bf_t = 100 x (F1_t / V_t - 1); and the roll per day
  RY_t = Bf_t / tau1_t.

**Test sample.** All joint days. Each statistic uses exactly the days on which every quantity it
needs is defined (its aligned sample, in date order, length m).

## 4. Estimators

- **Slope:** OLS with an intercept. **Newey-West t:** (X'X)^-1 S (X'X)^-1, Bartlett weights
  w_l = 1 - l/(L+1), L = h + 5 unless stated, no degrees-of-freedom correction.
- **Rotation p-value:** shifts k = 21, ..., m-21 of x against y, K = m - 41; p+ = (1 + #{rotated
  slope >= observed}) / (1 + K); p- likewise with <=; p2 = min(1, 2 x min(p+, p-)).
- **Percentile:** numpy linear. **Standard deviation:** population. **Halves:** first floor(m/2)
  days and the rest. **sign(b):** +1, -1 or 0.

## 5. Statistics

- Each h: slope b_h of R_h on B30, Newey-West t, p+, p-, p2, minimum detectable slope 2.80 x s.e.
  **Primary: b_5; s = sign(b_5).**
- **Incremental:** R_5 on a constant, B30, lv, n1, n5, n20; coefficient g with Newey-West t
  (L = 10).
- **Out of sample:** on the aligned sample of {B30, lv, n1, n5, n20, R_5}, with positions counted
  within that aligned sample, for t >= 750, fit the baseline (lv, n1, n5, n20) and the augmented
  model (plus B30) by OLS on positions 0..t-5 inclusive; R2_OS = 1 - SSE_aug / SSE_base;
  Clark-West mean and Newey-West t (L = 10).
- **Size:** Q = 80th percentile of s x B30 on the h = 5 aligned sample; Dq = mean R_5 on days
  with s x B30 >= Q minus mean R_5 over all days. If s = 0, Dq = 0.

## 6. Units

B30 in pp; returns in per cent. Slopes per 1 pp and per one standard deviation.

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
**UNSCORABLE:** fewer than 100 rotation shifts at h = 5. The direction s is reported with every
verdict.

**What a verdict licenses.** As in test C: a PASS would justify one frozen test of an executed
version on an instrument the operator can hold, with costs, borrow and the path risk of a short
volatility position stated. It authorises no capital. A FAIL is no support at the detectable
size. A PASS here would be a replication of a known result, not a discovery.

## 8. Reported without weight in the verdict

1. Baseline alone: slopes of R_h on lv, n1, n5, n20, each h, with Newey-West t and p+, p-; R2_OS
   of the baseline against the historical mean from position 750.
2. Front basis and roll per day: slopes of R_h on Bf and on RY, each h, with Newey-West t and p2.
3. Contango against backwardation: mean R_h and counts on days with B30 > 0 and B30 <= 0.
4. The level of B30: mean, median, 5th and 95th percentiles, standard deviation, share positive;
   the same for Bf; mean tau1.
5. Regimes: per calendar year with 20 or more days; VIX above and below 20; high and low 20-day
   VIX volatility at its median.
6. Fixed hold-out: b_5 on the last 30% of the h = 5 aligned sample.
7. Influence: b_5 after dropping the 1% most extreme |B30 - median|; leave-one-year-out range.
8. Quintiles of B30: mean and count of R_5.
9. Path: 5th percentile and minimum of R_5 on the days in the size group.
10. Data coverage: number of monthly contracts found, first and last expiry, number of joint
    days, and the number of trading days of VIXY with no futures pair (dropped).

## 9. What was known before this file was frozen

1. The structure probe of 15 October 2026 (probe 2) fetched two CBOE VX files (expiries 16
   September 2026 and 22 January 2025) and read their headers and line counts (about 185 lines
   each); no settlement value was read. Test C's full results are known, including the VIX3M/VIX
   slope's level and its null on VIXY.
2. The analyst is a language model with general knowledge of volatility markets to mid-2026.
   The window cannot be treated as unseen.
3. Whether CBOE serves files for expiries before 2013 at this path is unknown; the sample starts
   where the files start.

## 10. Limits fixed in advance

- Monthly contracts only; VIXY's index rolls daily across the first two monthly contracts, so
  F30 is the right object, but VIXY's own holdings, fees and tracking differ from the index.
- No cost, borrow or margin model beyond the 15.7 bp size threshold; item 9 reports the tail.
- Sample at most January 2013 to October 2026; one hypothesis; two-sided.
- CBOE and Yahoo data for internal analysis only; no observation committed or published.

## 11. Independent check

`verify_c2.py` is written from this file and the data headers alone, without sight of
`run_c2.py` or `kt.py`, and every criterion figure is compared on the runner.
