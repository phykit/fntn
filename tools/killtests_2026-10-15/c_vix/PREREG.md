# Pre-registration C: the VIX term-structure basis as a predictor of a tradable long-VIX instrument

Written 15 October 2026, before any observation of the series named below was retrieved. A
non-evidentiary side test outside the FNTN funnel: no apparatus, no row in `docs/OPEN_ITEMS.md`,
no authorisation. A kill test: the pass and fail rules below are fixed here and applied
mechanically by `run_c.py`. Data are fetched and read on the GitHub Actions runner only; derived
statistics only are stored.

## 1. Origin and hypothesis

Follow-up to the energy futures-residual test of the same morning. In energy the spot converges to
the future, so the future is not tradable on the basis. Volatility is the documented mirror case:
spot VIX is not tradable, VIX futures and the exchange-traded products built on them are, and the
futures converge to the spot. The question is whether the term-structure basis predicts the return
of a tradable long-VIX instrument.

**Hypothesis H.** B_t, the slope of the VIX term structure (the three-month VIX index over the
one-month VIX index), is followed by a return on a long-VIX exchange-traded product in one
direction or the other over the next 1, 5 and 20 trading days, primary 5, beyond the level and
momentum of the VIX.

**Registered sign: none (two-sided), carrying forward the operator's choice of 15 October 2026 for
the parent test.** One hypothesis; two-sided level **0.025** (0.0125 in each tail).

**Priors.** `recollection`, not verified: Simon and Campasano (2014, Journal of Alternative
Investments) find that the VIX futures basis predicts VIX futures returns with the futures
converging to the spot, so that contango (futures above spot) is followed by negative futures
returns; the long-VIX ETNs have lost most of their value over their lives for that reason. The
expected sign under that prior is negative. B here is a proxy built from two spot indices, not the
futures basis itself.

## 2. Data

| File | Series | Source | Fields |
|---|---|---|---|
| `data/vix.csv` | CBOE Volatility Index, daily close, Yahoo `^VIX` | Yahoo Finance history | `DATE,CLOSE` |
| `data/vix3m.csv` | CBOE 3-Month Volatility Index, daily close, Yahoo `^VIX3M` | Yahoo Finance history | `DATE,CLOSE` |
| `data/etp.csv` | ProShares VIX Short-Term Futures ETF, Yahoo `VIXY`: open, close, adjusted close | Yahoo Finance history | `DATE,OPEN,CLOSE,ADJCLOSE` |

ISO dates, oldest first, empty field for missing. Retrieval window: everything available. VIXY is
the instrument because its history (from January 2011) is continuous under one ticker; it holds a
daily-rolled position in the first two VIX futures. Its adjusted close carries its reverse splits.

**Timing, `recollection` on exchange conventions.** VIX and VIX3M closes are 16:15 New York; VIXY
closes at 16:00. The outcome starts at VIXY's open on the next trading day, after both.

## 3. Calendar and definitions

**Joint calendar.** Dates on which `vix`, `vix3m` and `etp` all carry numeric values for every
field named above. Positions t = 0, ..., N-1. There are no exclusions.

At position t (V = VIX close, V3 = VIX3M close; O, C, A = VIXY open, close, adjusted close;
a_t = A_t / C_t):

- **Signal:** B_t = 100 x (V3_t / V_t - 1), in pp (positive = contango in the term structure).
- **Baseline:** lv_t = ln(V_t); n1_t = 100 x ln(V_t / V_(t-1)); n5_t, n20_t over 5 and 20
  positions.
- **Outcome:** R_h(t) = 100 x ln( (C_(t+h) x a_(t+h)) / (O_(t+1) x a_(t+1)) ), h in {1, 5, 20}:
  VIXY from the next open to the close h days after t, adjusted.

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

- Each h: slope b_h of R_h on B, Newey-West t, p+, p-, p2, minimum detectable slope 2.80 x s.e.
  **Primary: b_5; s = sign(b_5).**
- **Incremental:** R_5 on a constant, B, lv, n1, n5, n20; coefficient g with Newey-West t (L = 10).
- **Out of sample:** on the aligned sample of {B, lv, n1, n5, n20, R_5}, for t >= 750, fit the
  baseline (lv, n1, n5, n20) and the augmented model (plus B) by OLS on positions 0..t-5;
  R2_OS = 1 - SSE_aug / SSE_base; Clark-West mean and Newey-West t (L = 10).
- **Size:** Q = 80th percentile of s x B on the h = 5 aligned sample; Dq = mean R_5 on days with
  s x B >= Q minus mean R_5 over all days. If s = 0, Dq = 0.

## 6. Units

B in pp; returns in per cent. Slopes per 1 pp of B and per one standard deviation.

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

**What a verdict licenses.** A PASS would justify one frozen test of an executed version on an
instrument the operator can hold (VIXY is a US-domiciled ETF a UK retail account cannot buy; VIX
futures on IBKR need permissions that are unverified; UCITS long- and short-VIX ETPs exist), with
costs, borrow and the path risk of a short volatility position stated. It authorises no capital.
A FAIL is no support at the detectable size. The prior says this is a replication of a known
result, not a discovery; a PASS here is expected and would be the test working, not an edge found.

## 8. Reported without weight in the verdict

1. Baseline alone: slopes of R_h on lv, n1, n5, n20 separately, each h, with Newey-West t and
   p+, p-; R2_OS of the baseline model against the historical mean from position 750.
2. Contango against backwardation: mean R_h and counts on days with B > 0 and B <= 0.
3. The level of B: mean, median, 5th and 95th percentiles, standard deviation, share positive.
4. Regimes: per calendar year with 20 or more days; VIX above and below 20 (its level, not its
   change); high and low 20-day VIX volatility at its median.
5. Fixed hold-out: b_5 on the last 30% of the h = 5 aligned sample.
6. Influence: b_5 after dropping the 1% most extreme |B - median|; leave-one-year-out range.
7. Quintiles of B: mean and count of R_5.
8. Path: for the 5-day outcome, the 5th percentile and the minimum of R_5 on the days in the
   strongest-signal fifth (the size group), so that a PASS carries its tail with it.

## 9. What was known before this file was frozen

1. No observation of `^VIX`, `^VIX3M` or `VIXY` was retrieved for this test. A structure-only
   probe of the same morning reported row counts and date ranges.
2. The analyst is a language model with general knowledge of volatility markets to mid-2026,
   including the February 2018 and March 2020 spikes, the August 2024 spike and the April 2025
   spike, and the long decline of the long-VIX ETNs. The window cannot be treated as unseen.
3. Prior art: section 1.

## 10. Limits fixed in advance

- B is a proxy from two spot indices, not the VIX futures basis the literature uses; the two are
  close but not identical, and VIXY holds futures, not either index.
- No cost, borrow or margin model in the verdict except the 15.7 bp size threshold. The known
  trade here is short VIXY (or long an inverse product), whose losses in a spike are large and
  fast; section 8 item 8 reports the tail, the verdict does not price it.
- About 3,900 joint days from January 2011; one hypothesis; two-sided.
- Yahoo data for internal analysis only; no observation committed or published.

## 11. Independent check

`verify_c.py` is written from this file and the data headers alone, without sight of `run_c.py`
or `kt.py`, and every criterion figure is compared on the runner.
