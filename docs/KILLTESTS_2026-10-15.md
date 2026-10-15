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
