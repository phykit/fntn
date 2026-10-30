# Pre-registration: does low correlation between two stocks raise the expected profit of monthly covered-call writing on the pair? A Monte Carlo theory check

Written 30 October 2026, before any simulated figure was produced. A non-evidentiary side test
outside the FNTN funnel; it produces no number about the world. Not investment advice.

## 1. Question, thesis and what this run can and cannot settle

The operator's thesis (stated in chat, 30 October 2026): selling call options every month on a
two-stock portfolio earns an excess profit when the two stocks are not perfectly correlated.

**H-CC.** The expected monthly overlay excess of the pair's covered calls (the premium received
less the call payoff surrendered, averaged across the two legs; section 3) is strictly decreasing
in the correlation of the two stocks' returns.

**Registered sign: negative** (the slope of mean overlay excess on correlation). One-sided. The
sign is the operator's, taken from the thesis as he stated it.

**The analyst's prior, stated before the run.** Under the model in section 2 the expectation of a
sum is the sum of expectations, each leg's marginal distribution is fixed by construction, and each
leg's overlay excess depends only on that leg's own return and on the premium it was paid.
Therefore, i) wherever the implied volatility charged for a leg does not itself depend on the
correlation (the control arm and Arm A), the mean overlay excess is exactly independent of the
correlation and only its variance moves; and ii) where the premium attaches to the systematic
share of variance only (Arm B), the mean overlay excess rises with the correlation, which is the
opposite of the registered sign. Under the model as written, SUPPORTED is unreachable. The run
exists to verify that claim numerically against closed forms, to size the variance effect that
does exist, and to record the direction of the Arm B effect, so that the empirical question the
simulation cannot answer (does idiosyncratic variance carry a risk premium in the option market?)
is the one left standing.

For the avoidance of doubt, a simulation reproduces the expected return it is given. Any excess
return in this run comes from the volatility premium assumed in section 4 and from nothing else.

## 2. Model

Two stocks, indexed i = 1, 2, with identical marginal distributions.

- Annualised volatility `SIGMA = 0.30`; annualised drift `MU = 0.06` such that the expected gross
  monthly return is `exp(MU * DT)`; risk-free rate `R = 0.04`; one month `DT = 1 / 12`.
- Monthly log return of leg i: `x_i = (MU - SIGMA^2 / 2) * DT + SIGMA * sqrt(DT) * eps_i`. Gross
  return `G_i = exp(x_i)`.
- `(eps_1, eps_2)` standard normal with correlation `rho`, built from common random numbers:
  `eps_1 = Z1`, `eps_2 = rho * Z1 + sqrt(1 - rho^2) * Z2`, the same `(Z1, Z2)` at every `rho`.
  Marginals are therefore identical across the grid and only the dependence moves. Leg 1's
  returns are identical across the grid; this is intended.
- Correlation grid: `RHO_GRID = [-0.3, 0.0, 0.3, 0.6, 0.9, 1.0]`.
- Factor reading, used only by Arm B: in a symmetric one-factor model with equal betas, the
  systematic share of each leg's variance equals the pairwise correlation, so `s = abs(rho)`
  (a negative correlation is two legs of opposite beta).
- Months are independent and identically distributed; there is no stochastic volatility and no
  path dependence in the dynamics.

## 3. Option and strategy

At the start of each month each leg holds one unit of its stock with value normalised to 1, and
sells one European call on that unit with strike `m` (moneyness, as a multiple of the start price)
expiring at the month end.

- Premium, as a fraction of the start price, by Black-Scholes at rate `R`, time `DT` and implied
  volatility `v`:
  `c(m, v) = N(d1) - m * exp(-R * DT) * N(d2)`,
  `d1 = (ln(1 / m) + (R + v^2 / 2) * DT) / (v * sqrt(DT))`, `d2 = d1 - v * sqrt(DT)`,
  with `N` the standard normal distribution function, `N(x) = 0.5 * erfc(-x / sqrt(2))`.
- The premium is held in cash for the month at `R`: it is worth `c * exp(R * DT)` at expiry.
- The call is settled in cash at expiry and the unit of stock is kept (identical to assignment
  and repurchase at the expiry price, with no transaction costs). No transaction costs anywhere.
- **Overlay excess** of leg i for the month: `y_i = c * exp(R * DT) - max(G_i - m, 0)`.
- **Total return** of leg i for the month: `g_i = (G_i - 1) + y_i`.
- Pair figures are equal-weighted averages of the two legs: `y = (y_1 + y_2) / 2`,
  `g = (g_1 + g_2) / 2`. Weights are reset to one half each month.
- Moneyness grid: `M_GRID = [1.00, 1.05]`.

**Closed forms** (used by the self-test and by the compare step). For a leg with the dynamics of
section 2, `E[max(G - m, 0)] = exp(MU * DT) * N(d1s) - m * N(d2s)` with
`d1s = (ln(1 / m) + (MU + SIGMA^2 / 2) * DT) / (SIGMA * sqrt(DT))`, `d2s = d1s - SIGMA * sqrt(DT)`;
hence `E[y_i] = c * exp(R * DT) - E[max(G - m, 0)]`, and this does not involve `rho`. When
`MU = R` and `v = SIGMA`, `E[y_i] = 0` exactly.

## 4. Arms (what the market is assumed to charge)

Three arms set the implied volatility `v` used to price the call. The realised dynamics are those
of section 2 in every arm.

- **Control**: `v = SIGMA`. No volatility premium.
- **Arm A** (premium on total variance): `v = SIGMA * sqrt(1 + KAPPA)`, `KAPPA = 0.21`, so
  `v = 0.33`, a 10% vol-point premium on single-name implied volatility.
- **Arm B** (premium on systematic variance only): `v = SIGMA * sqrt(1 + KAPPA * abs(rho))`. At
  `rho = 1` this equals Arm A; at `rho = 0` it equals the control.

## 5. Rule variants

- **V1, separable**: both calls are written every month.
- **V2, drawdown governor** (a portfolio-level rule, included to test that a rule reading the
  joint history cannot let `rho` into the mean): let the strategy equity be `E_0 = 1` and
  `E_t = E_(t-1) * (1 + q_t)`, where `q_t = g_t` in a month in which the calls are written and
  `q_t = (G_1 + G_2) / 2 - 1` in a month in which they are not. Let `P_(t-1)` be the running
  maximum of `E_0 ... E_(t-1)`. The calls are written in month t if and only if
  `E_(t-1) >= 0.9 * P_(t-1)`; month 1 is always written. Reported for V2: the fraction of months
  written, and the mean overlay excess over written months only.

V2 is run on the control arm and Arm A only. The jump arm (section 6) is run under V1 only.

## 6. Robustness arm: jumps with correlated arrival

The same two legs with a jump component, to show what correlation asymmetry does to the
variance and drawdown of the pair strategy. Priced under Arm A (`v = 0.33`), both moneyness
values, rule V1 only.

- Jump probability per leg per month `P_J = 1 / 12`; jump size in log terms
  `J ~ Normal(MU_J = -0.10, S_J = 0.05)`.
- Jump variance per month `VJ = P_J * (S_J^2 + MU_J^2) - P_J^2 * MU_J^2`; diffusive variance
  `VD = SIGMA^2 * DT - VJ`; diffusive scale `SD = sqrt(VD)`. Total monthly variance of the log
  return is `SIGMA^2 * DT`, as in section 2.
- Log return of leg i: `x_i = A + SD * eps_i + B_i * J_i`, where `B_i` is 1 with probability
  `P_J` and 0 otherwise, and `A = MU * DT - VD / 2 - ln(1 - P_J + P_J * exp(MU_J + S_J^2 / 2))`,
  so that `E[exp(x_i)] = exp(MU * DT)`.
- Diffusive dependence `rho_d` on `(eps_1, eps_2)` exactly as in section 2 (same `Z1, Z2`).
- Jump dependence `rho_j`: in each path-month a mixing indicator `Mix` is 1 with probability
  `rho_j`. If `Mix = 1` both legs share one arrival indicator and one size, `(B_c, J_c)`; if
  `Mix = 0` leg i uses its own independent `(B_i, J_i)`. Each leg's marginal is identical for
  every `rho_j`.
- Grid: `RHO_D_GRID = [0.0, 0.3, 0.6, 0.9]` by `RHO_J_GRID = [0.0, 1.0]`.

## 7. Simulation size and random numbers

- `N_PATHS = 2000` paths of `T = 120` months, giving 240,000 path-months per cell.
- `rng = numpy.random.default_rng(20261030)`. Draws, in this order and these shapes, all
  `(N_PATHS, T)`, made once and reused by every cell:
  1. `Z1 = rng.standard_normal((N_PATHS, T))`
  2. `Z2 = rng.standard_normal((N_PATHS, T))`
  3. `U_MIX = rng.random((N_PATHS, T))`
  4. `U_C = rng.random((N_PATHS, T))`; `J_C = rng.normal(MU_J, S_J, (N_PATHS, T))`
  5. `U_1 = rng.random((N_PATHS, T))`; `J_1 = rng.normal(MU_J, S_J, (N_PATHS, T))`
  6. `U_2 = rng.random((N_PATHS, T))`; `J_2 = rng.normal(MU_J, S_J, (N_PATHS, T))`
  Indicators: `B_c = U_C < P_J`, `B_1 = U_1 < P_J`, `B_2 = U_2 < P_J`, `Mix = U_MIX < rho_j`.
  Draws 3 to 6 are used by the jump arm only; they are made regardless so that the stream is
  fixed.

## 8. Statistics per cell

A cell is one `(arm, m, variant, rho)` in the base design, or one `(m, rho_d, rho_j)` in the jump
arm. For each cell, over all path-months (for V2, see the two written-only figures):

- `mean_y`, `sd_y` (ddof 1), `se_y = sd_y / sqrt(n)`, `sharpe_y = mean_y / sd_y` (monthly, not
  annualised) for the pair overlay excess `y`;
- `mean_y1`, `mean_y2` for the two legs;
- `mean_g`, `sd_g` for the pair total return `g`; `worst_g`, the minimum pair total return over
  all path-months;
- `assign_1`, `assign_2`: the fraction of path-months in which `G_i > m`; `assign_both`: the
  fraction in which both legs end above `m`;
- `mdd_median`, `mdd_p05`: maximum drawdown of the pair total-return equity (the compounded `g`
  series from 1, drawdown measured against its running maximum, the most negative value taken)
  per path, then the median and the 5th percentile across paths (`numpy.percentile`, default
  linear interpolation);
- V2 only: `frac_written`, and `mean_y_written`, `sd_y_written`, `se_y_written` with
  `n_written`, over the written path-months only (`se_y_written = sd_y_written /
  sqrt(n_written)`);
- jump arm only: `frac_both_jump`, the fraction of path-months in which both legs jump.

## 9. Checks and verdict, fixed before the run

Paired difference across the grid, exploiting the common random numbers: for each path k, let
`ybar_k(rho)` be the path's mean pair overlay excess over its 120 months (over written months
only under V2), and `d_k = ybar_k(1.0) - ybar_k(-0.3)`. Then `D = mean(d_k)`,
`SE_D = sd(d_k, ddof 1) / sqrt(N_PATHS)`, `z_D = D / SE_D`. The thesis predicts `z_D <= -3`
somewhere. A no-weight slope, `slope_y`, is the ordinary least-squares slope of `mean_y` on
`rho` across the six grid points.

1. **Analytic check** (every base cell): `abs(mean_y1 - E[y]) <= 3 * se_leg` and the same for
   leg 2, with `E[y]` the closed form of section 3 at that cell's `m` and `v`, and
   `se_leg = sd_leg / sqrt(n)` for that leg's pooled path-months. Failure in any cell HALTS the
   run: a code defect, not a result. For V2 the check is applied over written path-months.
2. **Theorem check** (control and Arm A, both m). Under V1: `abs(z_D) <= 3`. Under V2: the
   pooled difference `D2 = mean_y_written(1.0) - mean_y_written(-0.3)` with
   `z2 = D2 / sqrt(se_w(1.0)^2 + se_w(-0.3)^2)`, where `se_w = sd_written / sqrt(n_written)` over
   the cell's written path-months, must satisfy `abs(z2) <= 3` (the common random numbers make
   this standard error an overstatement, so the check is conservative). Failure HALTS: a code
   defect, because `E[y | written] = E[y]` exactly under the model.

   *Annotation, 30 October 2026, before the freeze.* As first committed (`dc63086`) this check
   applied the per-path paired `z_D` to V2 as well, on the claim that `E[d_k] = 0` exactly. That
   claim is true for V1 and false for V2: the per-path written-month mean is a ratio
   `sum(W_t y_t) / sum(W_t)` whose denominator counts later months' writing decisions, which
   depend on this month's return through the equity path, so numerator and denominator are
   correlated within a path and the ratio's expectation is not `E[y]` at finite `T`. The
   discrepancy is upward (a month in which the stock falls has a high `y` and a low total
   return, which triggers the governor and shrinks the denominator) and grows with how often
   the governor fires, which grows with `rho`; it would have produced a halt on V2 cells that
   was not a code defect. It was found on a 50-path smoke run made to confirm the code executes,
   whose figures are not the registered ones and are not carried anywhere; the pooled
   written-month means in that smoke run were flat in `rho`, as the theorem requires, which is
   what located the error in the estimator rather than the code. The per-path `z_D` under V2 is
   still computed and reported, without weight, as a worked instance of the bias: a per-pair
   backtest statistic of this shape would show a higher written-month mean for more volatile
   pairs for no economic reason.
3. **Arm B direction** (both m, V1): `z_D >= 3`. Predicted. Failure is recorded as an
   unexpected result and the run does not halt.
4. **Variance effect** (control, A and B, both m, V1): `sd_y` strictly increasing along
   `RHO_GRID`. Predicted. Failure is recorded.
5. **Jump arm** (both m). The jump arm's `E[y]` is not the base arm's (the payoff distribution
   differs) and has no closed form here, but it is the same in every jump cell because the
   marginals are fixed. Theorem check: with `d_k = ybar_k(rho_d = 0.9, rho_j = 1.0) -
   ybar_k(rho_d = 0.0, rho_j = 0.0)` and `z_J = mean(d_k) / (sd(d_k, ddof 1) / sqrt(N_PATHS))`,
   `abs(z_J) <= 3`; failure HALTS, as in check 2. Then `mdd_p05` and `worst_g` at `rho_j = 1`
   no better than at `rho_j = 0` for the same `rho_d`. Predicted. Failure of this second part is
   recorded.

**Verdict on H-CC.** A thesis hit is `z_D <= -3` in any V1 base cell or `z2 <= -3` in any V2
cell. NOT SUPPORTED when checks 1 and 2 pass and there is no thesis hit. SUPPORTED when checks 1
and 2 pass and there is a thesis hit; under the
model this cannot occur in the control arm or Arm A (check 2 would halt first) and cannot occur
in Arm B (its premium rises with `abs(rho)`), so a SUPPORTED verdict would mean the model
written here is not the model that ran, and would be treated as a defect to diagnose. HALTED
when check 1 or 2 fails. The predicted verdict is NOT SUPPORTED, and it is predicted here so that
it cannot be presented afterwards as a finding.

## 10. Output files and comparison

`run.py` writes `results.json` with: `params` (every constant above); `cells`, a list of objects
each carrying the cell's keys and the statistics of section 8; `paired`, a list of objects with
`arm`, `m`, `variant`, `D`, `SE_D`, `z_D`, `slope_y` for the base design (V2 objects also carry
`D2`, `SE2`, `z2` as defined in check 2) and one object per `m`
with `arm = "jump"`, `variant = "V1"`, `D`, `SE_D`, `z_D` (the `z_J` of check 5) for the jump arm;
`checks`, an object with keys `check1_analytic`, `check2_theorem`, `check3_armB`,
`check4_variance`, `check5_jump`, each an object with a boolean `pass` and a free-text `detail`;
`verdict`, one of `"NOT SUPPORTED"`, `"SUPPORTED"`, `"HALTED"`. `verify.py` is a second implementation written by a separate agent from
this document alone and writes `verify.json` in the same shape. `compare.py` requires every
`mean_y`, `sd_y`, `mean_y1`, `mean_y2`, `mean_g`, `sd_g`, `assign_*`, `mdd_*`, `frac_written`,
`mean_y_written`, `sd_y_written` and `worst_g` to agree to 1e-9 absolute, every `z_D` and `z2`
to 1e-6 absolute, and the verdict and every check's `pass` to agree exactly. The `(arm, m, variant, rho)` and
`(m, rho_d, rho_j)` cells must match one for one.

## 11. Self-test

`selftest.py`, on the implementation's own functions: i) the Black-Scholes premium at
`m = 1, v = 0.2, DT = 1, R = 0` equals `N(0.1) - N(-0.1)` to 1e-12; ii) the closed-form `E[y]`
with `MU = R` and `v = SIGMA` is zero to 1e-12 at both moneyness values; iii) a small simulation
(`N_PATHS = 400, T = 120`, seed 7) under the control arm at `rho = 0.5` and `m = 1.05` has a
leg mean within 3 SE of the closed form; iv) in that simulation leg 1's returns are identical
at `rho = 0.0` and `rho = 0.9`; v) the jump-arm log return has sample variance within 3% of
`SIGMA^2 * DT` and sample mean of the gross return within 3 SE of `exp(MU * DT)` at
`rho_d = 0, rho_j = 0`; vi) maximum drawdown of the sequence of total returns
`[+0.10, -0.20, +0.05, -0.10]` is `-0.244` to 1e-12.

*Annotation, 30 October 2026, before the freeze.* Item vi) as first committed (`dc63086`) read
`-0.28`, an asserted figure that was wrong: the equity path is 1.10, 0.88, 0.924, 0.8316 against a
running peak of 1.10, so the deepest drawdown is `0.8316 / 1.10 - 1 = -0.244`. The figure now
stands computed from the constants. No simulated figure had been produced when this was
corrected; the correction is recorded here rather than rewritten silently.

## 12. Disclosures

1. This is a theory check. It cannot find excess profit in markets because it is given its
   expected return by construction. Its result licenses a statement about the model only.
2. Parameters (`SIGMA`, `MU`, `R`, `KAPPA`, the jump settings) are round numbers chosen by the
   analyst before the run and have not been fitted to anything. The sign of every check is set
   by the structure of the model, not by the values; the values set magnitudes only.
3. The empirical fact on which H-CC turns, whether single-name implied volatility carries a
   premium on idiosyncratic variance, is not in this run. The analyst's reading of Driessen,
   Maenhout and Vilkov (2009, Journal of Finance), that the individual-stock variance risk
   premium is small and usually insignificant while the index premium is large, is
   `recollection` and is not relied on by any check here.
4. The analyst is a language model; the operator's thesis was stated to it in chat on
   30 October 2026 and the design in sections 2 to 6 was proposed by the analyst and accepted by
   the operator ("register it. and run it") without amendment.
5. Two corrections were made to this document between its first commit (`dc63086`) and the
   freeze, each annotated where it stands: the self-test drawdown figure (section 11, an
   asserted number that was wrong) and the V2 theorem check (section 9, an estimator that does
   not estimate what the check assumed). The second was located by a 50-path smoke run of the
   code, whose output was inspected for that purpose and for no other; the registered figures
   come from the run of record at the registered size and seed, and none of them had been
   produced when the corrections were made.
