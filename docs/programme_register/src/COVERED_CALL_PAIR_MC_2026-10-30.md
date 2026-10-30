# Covered calls on a two-stock pair: does low correlation raise expected profit? Monte Carlo theory check, result

Run 30 October 2026, GitHub Actions run 1 (run id 41051347692) on commit `3aa0707`, branch
`covered-call-pair-mc-2026-10-30`. Pre-registration `tools/covered_call_pair_mc/PREREG.md`, first
committed at `dc63086` before any figure; three pre-freeze corrections annotated in place; frozen
2026-10-30T11:53:40Z (`FROZEN.sha256`, verified on the runner). Independent second implementation
(`verify.py`) written by a separate agent from the PREREG alone: 984 cell statistics agree to 1e-9,
every z, check and the verdict agree. Results under `tools/covered_call_pair_mc/results/1/`.
A non-evidentiary theory check outside the FNTN funnel: it is given its expected return by
construction and produces no number about the world.

## Verdict on H-CC: NOT SUPPORTED (as predicted)

All five checks passed. No cell in any arm showed the registered sign.

| Arm (what the market charges) | m | Overlay excess, rho -0.3 | rho 1.0 | Paired z (rho 1.0 less -0.3) |
|---|---|---|---|---|
| Control, no vol premium | 1.00 | -9.2 bp/month | -8.5 bp | +0.75 (flat) |
| Control | 1.05 | -5.4 bp | -5.1 bp | +0.51 (flat) |
| A, 10% premium on total vol | 1.00 | +25.4 bp | +26.0 bp | +0.75 (flat) |
| A | 1.05 | +25.8 bp | +26.1 bp | +0.51 (flat) |
| B, premium on systematic vol only | 1.00 | +1.5 bp | +26.0 bp | **+28.8** (rises with rho) |
| B | 1.05 | +4.2 bp | +26.1 bp | **+38.3** (rises with rho) |

The control and Arm A differences of +0.75 and +0.51 are identical because the paired difference
does not depend on the premium, which is a constant; this is the common random numbers working,
not a coincidence.

## Reading

1. **Correlation does not change the expected premium captured.** Where the option price does not
   itself depend on correlation, the mean overlay is flat across rho from -0.3 to 1.0 to within
   noise (check 2), and every leg matches its closed form (check 1, 120 legs, all within 1 SE).
2. **It changes the risk, as diversification always does.** Pair overlay volatility at m = 1.00
   rises from 3.49% a month at rho -0.3 to 5.51% at rho 1.0; under Arm A the overlay's monthly
   Sharpe falls from 0.073 to 0.047, and median maximum drawdown of the covered pair over ten
   years deepens from -16% to -32%. The same result follows from holding two uncorrelated stocks
   without options.
3. **If the market prices only systematic variance (Arm B), the thesis has the wrong sign.** The
   premium is largest where correlation is highest, and an uncorrelated pair writes calls at
   roughly fair value. This is the reading most consistent with the published single-stock
   variance risk premium literature (`recollection`; not relied on by any check).
4. **Correlated jumps make it worse at the tail without moving the mean** (check 5): at m = 1.00,
   rho_d 0, the 5th-percentile drawdown moves from -34% to -41% when the two legs' jumps arrive
   together; the mean is unmoved (z_J +1.14).

## One result that contradicts what the analyst said in advance

Before the run the analyst told the operator that a portfolio-level rule would probably not let
correlation into the mean. That was right for the overlay per written month and **wrong for the
strategy's total return.** Under the drawdown governor (V2, Arm A, m = 1.00) the strategy's mean
monthly total return is 0.712% at rho -0.3 and 0.628% at rho 1.0: lower correlation does produce
a higher expected profit. The mechanism is not pricing. A less volatile pair breaches the 10%
drawdown trigger less often (calls written in 81% of months at rho -0.3, 51% at rho 1.0), so it
spends more months collecting a premium that Arm A makes positive by assumption. In the control
arm, where the premium is slightly negative, the sign reverses (0.439% against 0.456%). So
correlation enters expected profit only through how often a risk rule lets the position run,
and the direction depends entirely on whether the premium was positive to begin with. The
governor also deepened drawdowns in every cell, because it switches the overlay off after a fall
and so gives up the premium's cushion into the rebound.

A second finding of method: the per-path written-month mean, the statistic a per-pair backtest
would naturally report, is biased upward under the governor and the bias grows with rho
(per-path z of +4.6 to +6.3 where the true difference is zero). It is recorded in the PREREG's
check 2 annotation and was caught on a smoke run before the freeze.

## What this licenses and what it does not

- It closes the thesis as a statement about option pricing: correlation between two stocks does
  not by itself create excess profit from writing calls on them.
- It does not answer the empirical question on which any profit turns: whether single-name
  implied volatility is rich, and whether that richness sits on idiosyncratic or systematic
  variance. That needs historical single-stock option prices (CBOE single-name vol indices for a
  first pass, or a paid feed).
- It does not test transaction costs, early assignment, dividends, skew or stochastic volatility.

## Disclosures

1. Three corrections were made to the PREREG between first commit and freeze, each annotated in
   place: a wrong asserted self-test figure; the V2 theorem check, whose original estimator was
   biased (found on a 50-path smoke run); and an ambiguity in the V2 total-return definition on
   which the two implementations diverged (settled by a dry comparison on seed 99, 300 paths, a
   non-registered seed). No figure at the registered seed and size existed before the freeze.
2. Parameters (vol 30%, drift 6%, rate 4%, 10% vol premium, jump settings) are round values
   chosen before the run and fitted to nothing; they set magnitudes, not signs.
3. The analyst is a language model; the design was proposed by it and accepted by the operator.
