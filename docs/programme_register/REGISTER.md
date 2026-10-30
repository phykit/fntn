# Programme-level test register: result, 30 October 2026

Method fixed before any p-value was collected (`METHOD.md`, commit `0c25160`). Rows in
`rows_manual.csv` (48, read from project-only records by the main session), `rows_repos.csv` (9,
`phykit/act-trigger`) and `rows_local.csv` (49, repository copies of the 9, 15, 29 and 30 October
records); every surviving row's quote was checked against its source. Combined and adjusted by
`bh.py`; full table in `register.csv`. Procedure, not a test; it authorises nothing.

## The family

- **97 included primary hypotheses**, 9 October to 30 October 2026 (106 rows read; 9 excluded:
  the Monte Carlo theory check, superseded pilots, in-test replications, a search with no statistic).
- 10 rows have no recoverable p (bootstrap-percentile rules, gate closures, INSUFFICIENT) and enter
  as p = 1.
- **Known gap:** the Reno (v1 to v4) and Trudie tests in `phykit/fundamental-analysis` are missing;
  this session cannot read that repository. The family is therefore understated by their count,
  which makes the result below slightly too generous, not too strict.

## Result

| Pass | Discoveries |
|---|---|
| Benjamini-Hochberg, q <= 0.05 | 8 |
| Benjamini-Hochberg, q <= 0.10 | 19 |
| Holm, family-wise 0.05 | 3 |

### The eight at q <= 0.05, and what each is

| Row | p | q | What it is | Counts as a tradeable edge? |
|---|---|---|---|---|
| GVIP shortfall is concentration exposure | 1e-13 | 0.000 | An attribution: GVIP's lag behind QQQ is the cap-weight concentration premium | No: an explanation, near-mechanical |
| Futures residual over spot, natural gas | 1e-9 | 0.000 | Futures price predicts the spot, two-sided | No: the future itself shows nothing; recorded as untradable |
| NFCI change, NDX (current vintage) | 0.0005 | 0.016 | Passed on revised data | No: the first-release replication failed with the wrong sign; the "lead" was the revision |
| Credit drift, high-yield issuers | 0.001 | 0.024 | Long-short +1.02% a month | No: WEAK by its own rule; long-only net t 0.99; wrong sign in the only unseen years |
| Project Orange v2 | 0.003 | 0.049 | Post-ruling drift, 8 reacting cases | Not yet: UNSCORABLE (needs 15) |
| Selling 5% OTM puts | 0.0033 | 0.049 | The put premium | No: a risk premium, no risk-adjusted gain; and see the sensitivity below |
| Ten-month trend rule, nine markets | 0.004 | 0.049 | Drawdown timing beats random | As tail insurance only; replicated at q 0.086 |
| Volatility-managed momentum, 2016 to 2026 | 0.004 | 0.049 | Replication of a published effect, long-short | Long-only translation failed |

The three Holm survivors are the first three rows: an attribution, an untradable spot effect and a
revision artefact.

### Sensitivity: the four on the line

The out-of-the-money put row uses a normal-approximation p (t 2.72 gives 0.0033), which that test's
own pre-registration showed to be too generous on skewed data: its bootstrap critical value of 3.01
at 1% means its true p exceeds 0.01. With that one row at 0.01, **four rows drop out together**:
Orange v2, the put premium, the ten-month trend rule and volatility-managed momentum, all of which
sit exactly at q = 0.049. Removing the near-mechanical GVIP attribution has the same effect.

| Variant | Survivors at q <= 0.05 |
|---|---|
| As collected | 8 |
| Put row at its bootstrap bound (0.01) | 4: GVIP attribution, gas futures residual, NFCI current vintage, credit drift |
| Without the GVIP attribution row | 3: gas futures residual, NFCI current vintage, credit drift |

## Reading

1. **No tradeable result survives the programme's own multiple testing robustly.** The rows that
   survive under every variant are an untradable spot effect, a revision artefact already refuted,
   and a long-short effect whose long-only version failed (plus, where included, an attribution).
2. **The two results previously treated as standing, the ten-month trend rule and volatility-managed
   momentum, are borderline at the programme level**: q 0.049, and out under a defensible
   correction to one other row. The analyst predicted, before collection, that these two would be
   the survivors; that prediction was too generous. The trend rule's fresh-market replication (q
   0.086) is the stronger support for it, and is evidence of timing that cuts drawdowns, not of
   extra return.
3. **Moon (p 0.026, q 0.12) and the de-gross study (p 0.017, q 0.087) do not survive at 0.05**, as
   predicted. Moon also rests heavily on one event (`claude/moon_options_prereg_draft_2026-10-30.md`).
4. At q 0.10 the list is longer (19), but it is mostly volatility-targeting variants on one NDX sample
   (strongly dependent), a bitcoin basis effect judged WEAK, and the de-gross footprint, which is
   coincident and not tradeable.

## What this changes

- Report results from now on with their programme-level q beside the test's own p. A p of 0.02 to
  0.03 in this programme is what about two or three of the 97 tests would produce by chance.
- New tests in a well-worked area (index timing, crowding, volatility selling) need to clear a
  stricter bar than a single test would, or come with a forward record.
- The forward tests are the evidence that matters: the court-ruling OT2025/OT2026 register, the
  trend overlay's daily record (restored 30 October), and a forward log for volatility-managed
  momentum.

## Caveats

- BH assumes independence or positive dependence. Many rows share data (vt5 variants on one NDX
  sample; studies 2 and 2c on the same nine weeks), which is positive dependence, so BH remains valid
  but the effective number of independent tests is smaller than 97.
- Converting t to p with the normal distribution (`from_t`, 22 rows) understates p wherever returns
  are skewed or the sample short; the put row shows how much that can matter.
- Two-sided registrations (futures residual, the 15 October kill tests) carry their two-sided p.
- Extraction was by agents for 58 rows; every survivor's quote was checked against its source, the
  rest were not individually re-checked.
