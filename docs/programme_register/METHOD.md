# Programme-level test register: method

Written 30 October 2026, before any p-value was collected for the register. Procedure, not a test:
it adds no gate, family or input to the FNTN funnel.

## Purpose

About fifty pre-registered side tests have run since 9 October 2026, each judged against its own bar.
None was judged against the family. This register lists every test's primary p-value and applies a
Benjamini-Hochberg (BH) false-discovery-rate pass across the whole programme, and a Holm pass for the
stricter family-wise reading, to show which results survive the count.

## Family

- **In:** every test with a pre-registered primary hypothesis and a fixed decision rule that has
  been run on data and returned a verdict (including FAIL, NOT SUPPORTED, WEAK and UNSCORABLE), from
  9 October 2026 to 30 October 2026, in: the FNTN project's test records; `phykit/act-trigger`
  (results directory); `phykit/fundamental-analysis` (Reno and Trudie verdicts). One row per
  registered primary hypothesis: where a PREREG registered several primaries (for example three
  strategies), each is a row.
- **Out:** Monte Carlo theory checks (no data about the world), descriptive studies registered as
  descriptive, pilots superseded by a wider re-run of the same hypothesis (the wide run is kept),
  runs that failed before computing anything, secondary or no-weight statistics, and tests whose
  verdict was voided for an input defect without a valid re-run.
- Replications of one hypothesis on further markets, registered as part of the same test, are not
  separate rows; the registered primary is.

## The p-value per row

In order of preference, each row records:

1. the one-sided p-value the test itself reported for its primary statistic, in the registered
   direction;
2. if the test reported only a t (or z) for the primary, `p = 1 - Phi(t)` one-sided, flagged
   `from_t` (an approximation: these tests' own critical values were often bootstrap or permutation);
3. if the test reported a two-sided p, half of it when the estimate has the registered sign and
   `1 - p/2` otherwise, flagged `from_two_sided`;
4. if the primary statistic has the wrong sign and no p is reported, `p = 0.5` or above as computed
   from its t, flagged accordingly;
5. if no p and no t can be recovered, the row is kept with `p = NA` and counted, and it enters the
   BH pass as `p = 1` (it cannot be a discovery; omitting it would shrink the family).

Every row carries the source path and a verbatim quote of the line from which the figure was taken.

## Passes

- BH at q = 0.05 and q = 0.10 over all rows (m = row count), standard step-up.
- Holm at family-wise 0.05.
- Reported: m, each row's BH-adjusted p (q-value), and which rows are discoveries.

## Prediction, stated before collection

The analyst expects few or no discoveries at q = 0.05; the most likely survivors are the
volatility-managed momentum replication (bootstrap p 0.004) and the trend overlay's timing effect
(rotation p 0.004 and 0.012), and Project Moon (p 0.026) and the de-gross study (p 0.017) are
expected not to survive.
