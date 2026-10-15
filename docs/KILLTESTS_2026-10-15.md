# Kill tests of 15 October 2026: follow-ups to the futures-residual result

**Status: outside the FNTN funnel.** Non-evidentiary side tests, no apparatus, no row in
`docs/OPEN_ITEMS.md`, no authorisation. Branch `futures-residual-2026-10-15`; `main` untouched.

The parent test (`docs/FUTURES_RESIDUAL_2026-10-15.md`) found that in US energy the spot converges
to the front future and the future does not move with the residual. The operator asked for every
route to a tradable version to be killed or kept, and these four were pre-registered:

| Test | Question | Tradable leg | Data |
|---|---|---|---|
| A `a_expiry/` | In the last four days before a gas contract's last trading day, does the residual predict the contract's return to expiry? | the expiring futures contract | EIA NYMEX contract 1 (1994 to April 2024), EIA spot via FRED |
| B `b_spread/` | Does the residual predict the front-to-second calendar spread? | the calendar spread | EIA contracts 1 and 2 |
| C `c_vix/` | Does the VIX term-structure slope predict a long-VIX ETF, the documented case where the future converges to the spot? | VIXY | Yahoo ^VIX, ^VIX3M, VIXY |
| D `d_btc/` | Does the CME bitcoin basis predict spot bitcoin, the one liquid pair where the spot is holdable? | spot bitcoin | Yahoo BTC-USD, BTC=F, FRED DTB3 |

Each has its own `PREREG.md`, frozen together in `FROZEN.sha256` before any observation was read,
a frozen `run_*.py`, and an independent `verify_*.py` written from the specification alone by a
separate agent that did not see the run script or the shared estimator library; `compare_all.py`
checks every criterion figure. Sign convention: two-sided throughout, carrying forward the
operator's choice for the parent test. Two structure-only probes preceded the freeze (Yahoo keeps
no expired contracts; EIA's contract 1 switches on the business day after expiry; the CME holiday
calendar is reconstructed in `cal.py`). `selftest_all.py` runs the four scripts on synthetic null
and planted worlds.

The workflow `.github/workflows/killtests-2026-10-15.yml` runs `run_all.sh` on a push to
`DISPATCH` and commits derived statistics only under `results/<run>/`.

## Results (run 4, specification commit 23e23a5, 15 October 2026 10:25 UTC; `results/4/`)

Freeze record verified on the runner; self-test OK; independent implementations agreed on all
114 criterion figures.

| Test | Verdict | Primary figures |
|---|---|---|
| A gas, expiry window | **FAIL** (sign -) | pooled slope -0.02% per pp of M over 1,224 window days, NW t -0.4, p2 0.60; MDE 0.17% per pp |
| A heating oil (replication) | WEAK (sign -) | slope -0.14, t -2.7, p2 0.003; R2_OS -0.022; halves -0.25 / -0.03 (the effect is pre-2005) |
| A gasoline (replication) | FAIL (sign +) | slope +0.04, t 0.8 |
| B gas calendar spread | **FAIL** (sign -) | b_5 -0.006 pp per pp of M, t -0.4, p2 0.29; MDE 0.04 |
| C VIX term structure on VIXY | **FAIL** (sign +) | b_5 +0.018% per pp of slope, t 0.4, p2 0.59; MDE 0.13; contango days -1.17% per 5 days, backwardation days -1.81% |
| D CME bitcoin basis on spot | **WEAK** (sign +) | b_5 +0.57% per pp, t 2.3, p2 0.009; R2_OS -0.002; same-day spot return on M t -3.6 (the stale-futures mechanic); positive in 5 of 9 years |

**Reading.** Nothing here is a tradable strategy. A: the expiring gas contract does not move with
the spot residual in its final days (nor does it away from them: control slope 0.00, t 0.0), so
the last open door on the energy dataset is closed; the heating-oil WEAK is a first-half-of-sample
effect with negative out-of-sample value. B: the calendar spread carries nothing from the residual
beyond its own level. C: on free data the VIX term-structure slope does not time the long-VIX
ETF's decay at 1 to 20 days; the decay is unconditional (both contango and backwardation days are
negative), which is the known short-VIX carry, not a basis-timed signal. D: a positive basis is
followed by slightly higher spot returns at one to five days, but the sign of the same-day
relation shows the eight-hour gap between the futures close and the spot close doing the work,
there is no out-of-sample gain over momentum, and 2018 carries much of the slope.

**Bonus, from B section 8:** the parent result replicates on synchronous 2:30 p.m. NYMEX
settlements: spot 5-day change on M, slope +0.64% per pp, t 6.5, quintiles -4.9% to +3.7%; and the
front contract's own 5-day return on M has a slope of 0.0003 (t 0.01). The spot converges, the
future does not move. That is the finding of the day, stated twice on two data sources.

**Data limits found after the run.** A's switch check is inconclusive (the log-distance detector
fires at k_X+1 on 58% of expiries and at k_X on 41%, so it cannot separate a one-day switch error
from noise); B's incremental sample is 976 days, below the 1,005 the out-of-sample rule needs, so
criterion (e) could not be evaluated (the verdict is FAIL on (a) regardless). Nothing is licensed
and no §13 row is opened.

## C2: the VIX futures basis itself (run 5, specification commit d6650c6, 10:41 UTC; `results/5/`)

Test C's one advance-fixed limit was the proxy. C2 repeats it with the futures: 167 monthly VX
contracts from CBOE's historical files (expiries January 2013 to November 2026), the constant-30-day
price that VIXY's index holds (linear in days across the first two contracts), B30 = its premium
over spot VIX; 3,372 joint days from May 2013; independent reimplementation agreed on 20 of 20
figures; self-test OK.

**Verdict: FAIL (sign +).** b_5 = +0.026% per pp of B30, NW t 0.5, p2 0.38; b_1 -0.001 (t -0.1);
b_20 +0.12 (t 1.0); incremental over VIX level and momentum g = -0.08, t -1.3; R2_OS -0.004. The
front basis and the roll per day (section 8) show the same nothing (t 0.4 and 0.9 at five days).
Quintile means of VIXY's five-day return, lowest B30 to highest: -2.3%, -1.0%, -1.0%, -0.9%,
-0.7%. Contango days -0.90% per five days (n 2,776), backwardation days -2.37% (n 591).

**Reading.** On the futures basis as on the proxy, the long-VIX ETF loses on average in every
state of the curve, and loses most after spikes (backwardation), when the VIX mean-reverts. The
basis carries no timing information at 1 to 20 days beyond the VIX level and its recent moves. The
literature's result (the basis predicts the futures' convergence to spot) is not contradicted by
this: it is absorbed by the baseline, because the basis is mostly a function of the VIX level, and
what is left of it predicts nothing. The tradable content is the unconditional short-VIX carry
with its tail, not a basis-timed signal. Nothing is licensed; no §13 row is opened.
