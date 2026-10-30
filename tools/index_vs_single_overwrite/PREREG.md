# Pre-registration: does overwriting the index improve risk-adjusted return more than overwriting the stocks one by one?

Written 30 October 2026, the third follow-up on the inputs of `tools/single_name_vrp/` (run 3, run
id 41055269824). A non-evidentiary side test outside the FNTN funnel. Not investment advice.

## 1. Question and hypothesis

The correlation risk premium literature (Driessen, Maenhout and Vilkov, 2009, Journal of Finance,
`recollection`) finds index options priced richly relative to their constituents, because the
correlation they imply has tended to exceed realised correlation. If so, a covered call on the
index should improve risk-adjusted return more than covered calls written separately on stocks.
The operator asked for this to be tested on the data in hand.

**H-IX.** The Sharpe improvement from overwriting (Sharpe of the covered position minus Sharpe of
the held position) is larger for the index (SPY with a call priced from the VIX) than for an
equal-weight basket of the five names each carrying its own call.

**Registered sign: positive** (index improvement minus basket improvement). One-sided.

**What the analyst has already seen.** For the five names, run 3 reported the mean single-name
covered-call excess (-0.66% of spot a month) and the pair-risk-adjusted run reported pair Sharpe
figures (held 0.27, covered 0.35 a month on average over ten pairs). Nothing about the index
overwrite and nothing about the five-name basket has been computed. The analyst expects SUPPORTED
on the literature, with low confidence, and expects disclosure 2 below to bias towards it.

## 2. Inputs and quantities

The inputs, trading days, formation days, holding windows and the at-the-money premium function
are those of `tools/single_name_vrp/PREREG.md` sections 2 to 4 (including the section 2
amendment), fetched by its frozen `fetch.py` and loaded by its frozen `run.py`.

`U` is the set of formation days `t0` on or before 2026-09-01 on which all five names are used
under section 3 there (which also requires `VIX(t0)` and all SPY returns in both windows). This is
the month set of `tools/pair_risk_adjusted/`. `n = |U|`; INSUFFICIENT if `n < 120`.

For each month in U:

- names: `G_i = P_i(T1) / P_i(t0)`; `y_i = c(VX_i(t0) / 100) - max(G_i - 1, 0)`, where `c(s)` is the
  at-the-money call premium per unit of spot at volatility `s`, rate 0, time `21 / 252`;
- **basket** (equal weight across the five names, reset monthly): held `h_B = mean_i(G_i) - 1`;
  excess `y_B = mean_i(y_i)`; covered `k_B = h_B + y_B`;
- **index**: `G_I = P_SPY(T1) / P_SPY(t0)`; held `h_I = G_I - 1`; excess
  `y_I = c(VIX(t0) / 100) - max(G_I - 1, 0)`; covered `k_I = h_I + y_I`.

`Sh(x) = mean(x) / sd(x, ddof 1)`, monthly, rate 0.

## 3. Statistic, inference, verdict

`Delta = [Sh(k_I) - Sh(h_I)] - [Sh(k_B) - Sh(h_B)]`.

Moving-block bootstrap over months, as `tools/pair_risk_adjusted/PREREG.md` section 5 except:
`rng = numpy.random.default_rng(20261101)`, `B = 2000`, block length 12; each replication draws
`ceil(n / 12)` starts with `rng.integers(0, n - 11, size=...)`, concatenates the 12-month runs in
draw order, truncates to `n`, and recomputes `Delta*` on the months drawn (duplicates count). A
replication with any zero standard deviation is discarded and counted. `lower` is
`numpy.percentile` of the kept `Delta*` at 5.

Verdict: INSUFFICIENT if `n < 120`; REFUSED if more than 20 replications are discarded; SUPPORTED
if `Delta > 0` and `lower > 0`; NOT SUPPORTED otherwise. Figures are computed and reported in
every case where `n >= 12`.

## 4. Reported without weight

- `Sh` of `h_I`, `k_I`, `h_B`, `k_B`; the two improvements; mean and sd of `y_I` and `y_B` (per cent)
  and their ratio `mean / sd`.
- The monthly difference `y_I - y_B`: mean (per cent) and Newey-West t (3 lags, Bartlett, no
  small-sample correction, constant-only).
- The bootstrap's mean of `Delta*` and its 95th percentile; the count discarded.
- **Skew sensitivity.** `Delta` recomputed with the index call priced at `0.9 * VIX(t0) / 100` and
  each name's call at `0.95 * VX_i(t0) / 100`. The factors are the analyst's round guesses at the
  ratio of at-the-money implied volatility to the VIX-method index (larger skew for the index),
  `recollection`, fitted to nothing; the row exists only to show whether the sign survives a
  plausible correction for disclosure 2.
- Annualised forms (Sharpe times `sqrt(12)`, means times 12) for the four Sharpe ratios.

## 5. Self-test, independent check

1. `selftest.py`, on the implementation's own functions with synthetic monthly arrays over 187
   months: when the index and basket excesses are drawn from the same distribution relative to
   their held returns (null), SUPPORTED in no more than 4 of 40 worlds (`B = 500`); when the index
   excess has mean +0.5% a month and the basket's -0.5% at the same spread, SUPPORTED in 8 of 8;
   `Sh([1, 2, 3]) = 2`; same seed gives identical `Delta*`.
2. `verify.py` is a second implementation by a separate agent from this document and
   `tools/single_name_vrp/PREREG.md` alone. `compare.py` requires `n`, the first and last month,
   the verdict, `Delta` and `lower` (1e-9), the discard count, and the four Sharpe ratios (1e-9) to
   agree.

## 6. Disclosures

1. **Different underlyings.** The index is SPY; the basket is five large caps that rose strongly.
   The Sharpe-improvement statistic compares each overwrite with its own held position, which
   removes the level of each Sharpe but not the dependence of the improvement on how the
   underlying behaved (a strongly rising underlying gives more away to its calls).
2. **Skew bias favours SUPPORTED.** Both premiums are priced from VIX-method indices, which
   include the skew and so exceed at-the-money implied volatility. Index skew is steeper than
   single-stock skew, so the index premium is overstated by more. A NOT SUPPORTED verdict is
   robust to this; a SUPPORTED one is weakened, and the sensitivity row reports whether its sign
   survives one plausible correction.
3. No transaction costs; SPY's call is priced from the VIX, which is computed on SPX options.
4. Five surviving names, one index, 2011 to 2026, one sample path; not blind (section 1).
5. The analyst is a language model with general knowledge of market history to mid-2026.
