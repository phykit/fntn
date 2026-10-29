# Pre-registration: a price-implied de-grossing proxy as a warning of Nasdaq 100 drawdowns

Written 29 October 2026, before any observation of any series named below was retrieved for this
test. A non-evidentiary side test outside the FNTN funnel: no apparatus, no row in
`docs/OPEN_ITEMS.md`, no authorisation. A kill test: the pass, fail and gate rules below are fixed
here and are applied mechanically by `run.py`. The data are fetched and read on the GitHub Actions
runner only; no observation of any input is committed, printed or stored. Derived statistics only.

## 1. Origin and hypothesis

Idea as received (S. Kittson, 29 October 2026): Goldman Sachs Prime Brokerage weekly positioning
data as a leading indicator of a fall in the Nasdaq 100. Those data are client-only and reach the
public through selective press reports, so a direct test needs four to eight years of live logging.
This test uses a free, long proxy for the same mechanism instead.

**Mechanism.** When hedge funds de-gross (long sales together with short covers), the shares they
are crowded long fall and the shares they are crowded short rise, in the same week and beyond what
market beta explains. Goldman's own desk describes de-grossing episodes in these terms. The proxy
uses the Kenneth French momentum deciles: the top decile (recent winners) stands in for crowded
longs, the bottom decile (recent losers) for crowded shorts.

**Hypothesis H3-A.** When a de-gross week occurs while the winners-minus-losers trade is crowded,
the Nasdaq 100 suffers a drawdown of 10% or more within the following 63 trading days more often
than after comparable ordinary weeks.

**Registered sign: positive** (triggered weeks have the higher event rate). One-sided.

**Gate (read before any outcome).** The proxy must flag weeks that Goldman itself reported as
de-grossing. If it does not, it is not measuring the mechanism, the outcome is not computed, and the
idea is closed on that ground.

**Priors, with provenance.**
- `verified_secondary` (search results read 29 October 2026): Brown, Howard and Lundblad, "Crowded
  Trades and Tail Risk", Review of Financial Studies 2022: crowded hedge-fund holdings earn a
  premium and suffer larger drawdowns in industry distress, notably 2008.
- `recollection`, not verified: Daniel and Moskowitz (2016) find that momentum crashes concentrate
  in market rebounds after bear markets, when losers rally. That is the reason the de-gross
  condition in section 3 requires winners to fall as well as losers to rise: a rebound squeeze
  without long selling is excluded.
- `verified_secondary`: the operator's CFTC test of 25 October 2026 found futures positioning
  uncorrelated with the NDX's own moves and closed it; its record concluded that de-grossing lives
  in single-stock books that no public weekly position report shows. Hence a price-based proxy.

## 2. Data

All series are retrieved by `fetch.py` on the runner at run time and written to `data/`. Nothing in
`data/` is committed, uploaded or cached.

| File | Series | Source |
|---|---|---|
| `data/mom10_daily.csv` | 10 Portfolios Formed on Momentum (Prior 12-2), daily, **value-weighted** section only | Kenneth French Data Library, `10_Portfolios_Prior_12_2_Daily_CSV.zip` |
| `data/ff3_daily.csv` | Fama/French 3 Factors, daily (`Mkt-RF`, `SMB`, `HML`, `RF`) | Kenneth French Data Library, `F-F_Research_Data_Factors_daily_CSV.zip` |
| `data/ndx.csv` | Nasdaq 100 index, daily close | FRED series `NASDAQ100` |

`fetch.py` writes each file as `DATE,<columns>` with ISO dates, oldest first. French values are
kept in per cent as published; a value of -99.99 or -999 is written as empty. FRED's "." is written
as empty. Retrieval window: everything available on the retrieval date.

Definitions of the inputs:
- L_d = the first momentum column (`Lo PRIOR`) on day d, divided by 100.
- W_d = the last momentum column (`Hi PRIOR`) on day d, divided by 100.
- M_d = (`Mkt-RF` + `RF`) on day d, divided by 100.
- A French day is used only if L, W and M are all present.
- N_d = the Nasdaq 100 close; NDX days with an empty value are dropped.

## 3. Definitions

**Weeks.** French days are grouped by ISO calendar week (ISO year and ISO week number). Weekly
returns are compounded: X_t = product over the week's days of (1 + X_d), minus 1, for X in W, L, M.
The week-end date e_t is the last French day in the week. Weeks are indexed t = 0, 1, 2, ... in date
order.

**Betas.** For each week t with at least 52 earlier weeks, bW_t is the slope of an ordinary least
squares regression, with intercept, of W on M over weeks t-52 to t-1; bL_t likewise for L.

**Residuals and pair.** rW_t = W_t - bW_t·M_t; rL_t = L_t - bL_t·M_t; P_t = rW_t - rL_t.

**Standardised pair.** z_t = (P_t - mean) / sd, where mean and sd (ddof = 1) are taken over P for
weeks t-156 to t-1. Defined only when all 156 earlier P values exist.

**De-gross week.** D_t is true when z_t <= -2.0 **and** W_t < 0 **and** L_t > 0, where W_t and
L_t are the **raw** weekly returns (not the residuals): the winners fell outright and the losers
rose outright. The condition is on raw returns because a rebound week in which winners rise but lag
their beta has a negative residual, and a residual condition would let exactly the rebound squeezes
through that the condition exists to exclude.

**Crowding.** S_t = the sum of P over weeks t-26 to t-1 (defined when all 26 exist). C_t is true
when S_t >= the 90th percentile (numpy `percentile`, default linear interpolation) of S over weeks
t-260 to t-1 (defined when all 260 exist).

**Trigger.** T_t = D_t and C_t.

**Signal-evaluable week.** A week for which z_t and C_t are both defined.

**Model date and NDX close.** For week t, the model date is e_t. Its NDX index position i_t is the
last NDX day on or before e_t, and the entry close is N at i_t.

**Outcome.** With P now denoting the NDX close and k counting NDX trading days after i_t:

DD_t = min over k = 1..63 of [ N(i_t + k) / max over j = 0..k of N(i_t + j) ] - 1

E_t is true when DD_t <= -0.10. **Outcome-evaluable week:** a signal-evaluable week whose e_t is on
or after the first NDX date and for which N(i_t + 63) exists.

**Prior return.** R21_t = N(i_t) / N(i_t - 21) - 1, defined when i_t >= 21. Outcome-evaluable weeks
without R21 are dropped from the outcome test.

**Episodes.** Walking forward through outcome-evaluable trigger weeks in date order, a trigger
starts a new episode unless its i_t is within 63 NDX trading days after (i_t - i_start <= 63) the
start of the current episode; otherwise it is merged into that episode. Chaining is not used: the
comparison is always with the episode's first trigger. Each episode is represented by its first
trigger week.

## 4. Gate

Reference weeks, from Goldman Prime Brokerage de-grossing as reported in the press (week-end
dates): **2021-01-29**, **2026-05-01**, **2026-10-16**.

1. A reference is **available** if its date is on or before the last French date in the data.
2. A reference is **matched** if some signal-evaluable week with D_t true has e_t within 7 calendar
   days of the reference date (inclusive). Crowding is not required for the gate.
3. Base rate b = share of signal-evaluable weeks with D_t true.
4. **Gate PASS** when at least 2 references are matched **and** b <= 0.05.
5. **Gate UNTESTABLE** when fewer than 2 references are available.
6. Otherwise **Gate FAIL**.

The outcome in section 5 is computed **only on Gate PASS**. On FAIL or UNTESTABLE, `run.py` writes
the gate result and stops, and the verdict is CLOSED (gate). For information only, the gate report
includes the chance of matching at least the observed number of available references if D weeks
fell at random at rate b, taking each reference window as 3 weeks.

## 5. Test

- E_bar_T = mean of E over episodes (their first trigger weeks). E_bar_O = mean of E over
  outcome-evaluable weeks with T_t false. Delta = E_bar_T - E_bar_O.
- **Strata.** Tercile cut points of R21 over all outcome-evaluable weeks (numpy `percentile` at
  100/3 and 200/3). Stratum 0 below the first cut, 2 at or above the second, 1 otherwise.
- **Permutation.** 10,000 placebo sets, numpy `default_rng(20261029)`. Each set takes, for each
  episode in date order, one week drawn uniformly from the untriggered outcome-evaluable weeks in
  the episode's stratum, without replacement within the set (a stratum that runs out is a coding
  error and the run stops). Placebo Delta_b = mean of E over the set - E_bar_O.
  p = (1 + count of Delta_b >= Delta) / (1 + 10,000).
- **Verdict.** n = number of episodes.
  - INSUFFICIENT when n < 8.
  - PASS when n >= 8 **and** p <= 0.05 **and** Delta >= 0.10.
  - FAIL otherwise.

## 6. Reported without weight in the verdict

1. The same test with a 21-day window and a -5% threshold.
2. The same test with D_t defined by z_t <= -2.0 alone (the sign conditions removed), to show what
   the rebound filter does.
3. The same test on the French market: an index built by compounding M over French days, the
   outcome window counted in French days, the prior return over 21 French days, and the 1927 onwards
   sample (all signal-evaluable weeks with 63 later French days).
4. Episode dates, each with its E value and DD.

## 7. Self-test before freezing

`selftest.py` runs before any input is fetched: (a) the signal construction on a small hand-built
series with a known answer; (b) 40 null worlds (random triggers, NDX a random walk independent of
them) and 8 planted worlds (a fall of 15% over the 30 days after each trigger), reporting how many
of each reach PASS. The test machinery is acceptable if no more than 4 of 40 null worlds and all 8
planted worlds pass.

## 8. Independent check

`verify.py` is a second implementation written by a separate agent from this document and the
file formats in section 2 alone, without sight of `run.py` or of any output. `compare.py` requires
the gate result, the episode count, E_bar_T, E_bar_O, Delta and the verdict to agree, and p to agree
within 0.01 (the two use the same seed, but draw order may differ).

## 9. Disclosures

1. The analyst is a language model with general knowledge of market history to mid-2026, so the
   sample is not unseen. The reference weeks were chosen from press reports read in the same
   conversation, before any series here was retrieved.
2. The French portfolios are a historical construction published with a lag of a month or more;
   the October 2026 reference will probably fall outside the data and be dropped. A live version
   of the signal would need baskets built from current prices.
3. The momentum deciles are a broad proxy for hedge-fund crowding, not a measure of it. A pass here
   licenses building Version B (13F holdings and most-shorted baskets); it does not license a
   trade.
4. Everything is a non-evidentiary side test outside the FNTN funnel; nothing here is investment
   advice.
5. **Amendment before freezing.** The first draft put the de-gross sign conditions on the residual
   returns rW and rL. The self-test's hand-built rebound week (winners +10%, losers +25%, market
   +12%) passed that condition because the winners' residual was negative. The conditions were moved
   to raw returns (section 3) before freezing and before any input was retrieved.
