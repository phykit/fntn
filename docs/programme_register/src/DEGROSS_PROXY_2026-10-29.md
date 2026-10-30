# Price-implied de-grossing proxy (Version A) as a warning of Nasdaq 100 drawdowns: result

Run 29 October 2026, GitHub Actions run 2 (run id 40864917418) on commit `831950c`, branch
`degross-proxy-2026-10-29`. Specification frozen before any input was retrieved:
`tools/degross_proxy/PREREG.md`, SHA-256 `eaae11be...6af17`, frozen 2026-10-29T11:19:17Z. A
non-evidentiary side test outside the FNTN funnel: no apparatus, no row in `docs/OPEN_ITEMS.md`, no
authorisation. An assessment of evidence, not investment advice.

## Verdict

**CLOSED at the gate (FAIL). No outcome was computed.**

| Item | Value |
|---|---|
| Reference weeks available (French data end 2026-09-30) | 2021-01-29, 2026-05-01 (2026-10-16 dropped, after the data end) |
| Reference weeks matched (a de-gross week within 7 days) | **0 of 2** (2 required) |
| De-gross base rate | 1.35% of 4,875 signal-evaluable weeks (cap 5%) |
| Independent implementation | agrees on gate status, matched references and base rate |

The proxy flags about one week in 74, so it is selective; but it flags neither of the two weeks
in which Goldman Sachs Prime Brokerage reported hedge-fund de-grossing.

## What the proxy showed in the reference weeks

Standardised winners-minus-losers pair (z) and the two legs' beta-residual returns, as derived
statistics from `results/2/gate.json`:

| Week ending | z | Winners residual | Losers residual | Reading |
|---|---|---|---|---|
| 2021-01-22 | +1.29 | +2.6% | -4.4% | the opposite of de-grossing |
| 2021-01-29 | -0.46 | -2.1% | +0.3% | right direction, far below the -2.0 threshold |
| 2021-02-05 | +0.05 | +1.5% | +1.2% | none |
| 2026-04-24 | +1.29 | +4.8% | -1.2% | the opposite |
| 2026-05-01 | -0.11 | +1.3% | +1.2% | none |
| 2026-05-08 | +2.58 | +8.2% | -3.3% | strongly the opposite |

In both episodes the momentum pair did not record what Goldman's desk recorded. In late April and
early May 2026, when Goldman reported the largest technology de-grossing in a decade, recent
winners outperformed recent losers by a wide margin.

## What the result does and does not license

- It closes Version A: the Kenneth French momentum deciles do not measure hedge-fund de-grossing
  as Goldman's Prime book sees it, so their behaviour carries no evidence about the mechanism
  either way.
- It does not show that de-grossing fails to precede drawdowns. The outcome was not computed, by
  design, because an outcome read on a proxy that fails to see the mechanism would be read on
  something else.
- The registered decision rule was to build Version B (13F hedge-fund holdings against the most
  shorted shares) only if A passed. A failed, so B is not licensed by this result; whether to
  build it anyway is an operator decision, on the ground that A's failure is evidence about the
  proxy (momentum is broader than hedge-fund crowding) rather than about the mechanism.
- The analyst's reading, not tested: momentum deciles are formed on prior 12-2 month returns
  across the whole market, so they mix hedge-fund positions with every other investor's trend
  exposure; hedge-fund crowding in 2021 sat in heavily shorted small caps and in 2026 in a narrow
  set of mega-cap technology and semiconductor names, neither of which a market-wide decile
  isolates.

## Deviations and disclosures

1. **Run 1** (run id 40864481034) fetched both French files and stopped on a FRED read timeout
   before any outcome step. `fetch.py` gained a retry (the precedent fetcher retries the same
   endpoint), and its hash alone was re-recorded in `FROZEN.sha256`. `PREREG.md`, `run.py` and
   `verify.py` were unchanged; the workflow verified their hashes on run 2.
2. **Amendment before freezing**: the de-gross sign conditions were moved from residual to raw
   returns after the self-test showed a rebound week passing the residual version (PREREG section
   9 item 5). Made before any input was retrieved.
3. The analyst is a language model with general knowledge of market history to mid-2026; the
   sample was not unseen. The reference weeks were chosen from press reports read in the same
   conversation, before any series was retrieved.
4. Self-test (run 2): null worlds passing 3 of 40, planted worlds 8 of 8; hand-built checks all
   passed.
5. **Independent check**: `verify.py` was written by a separate agent from `PREREG.md` alone. It
   agrees with `run.py` on every gate field.

Sources: [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html);
[FRED NASDAQ100](https://fred.stlouisfed.org/series/NASDAQ100).
