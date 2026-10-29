# Pre-registration: study 2e, does crowded-long weakness lead de-grossing?

Written 29 October 2026, before any figure below was computed and before the outstanding searches of
studies 1 and 3 were resumed. Extends `tools/crowd_degross/PREREG_2.md`; series, weekly compounding,
permutation method (10,000 draws, `default_rng(20261029)`) carry over. Non-evidentiary side test
outside the FNTN funnel; not investment advice.

**Origin of the hypothesis (disclosed).** Study 2d reported, without weight, that in the week before
the 9 frozen Class D episodes (E-1) GVIP lagged QQQ by 0.69% against 0.09% (p lower 0.064). A
hypothesis found on those 9 weeks cannot be tested on them; both tests below exclude them.

## 1. 2e-i: the lead on new episodes (confirmatory)

- **Episodes:** Class D episodes **not** in the frozen list: (a) those of
  `tools/degross_ext/episodes_ext.csv` (Goldman, 2016 to 2020), and (b) those of
  `tools/cross_pb/episodes_other.csv` (Morgan Stanley, JPMorgan) whose week-end is more than 14 days
  from every frozen Goldman episode (D or N), each list as frozen when its search completes under its
  own PREREG.
- **Measure:** GVIP minus QQQ in E-1, the ISO week before the episode week.
- **Test:** mean against the unconditional mean of all defined weeks, one-sided lower permutation p.
- **Reported without weight:** E-1 on the reconstructed basket minus QQQ; E-1 GVIP minus QQQ on the
  12 frozen Class N episodes (not yet computed); E0 on the new episodes (an out-of-sample replication
  of study 2).

## 2. 2e-ii: persistence of crowded-long weakness (the tradeable form)

- x_t = weekly GVIP minus QQQ. **Signal week t:** x_t at or below the 10th percentile of the 104
  weeks t-104 .. t-1 (all defined; else no signal).
- **Eligible t:** x_t and x_{t+1} defined and the 104-week window complete; **excluded** when the
  week-end of t or of t+1 is within 14 days of any frozen Goldman episode (D or N), so the hint's
  weeks and the episode weeks themselves play no part.
- **Statistic:** mean x_{t+1} over eligible signal weeks. **Null:** the same number of eligible weeks
  drawn without replacement; one-sided lower p.
- **Reported without weight:** the same on the reconstructed basket W minus QQQ (available from
  2013); x_{t+1} regressed on x_t over eligible weeks (Newey-West, L = 3); the two-week horizon
  x_{t+1} + x_{t+2}; the mean next-week excess in percentage points, as the economic size.

## 3. Verdicts and multiplicity

Holm across the two primary p-values (2e-i, 2e-ii) at 0.05. 2e-i: SUPPORTED if Holm p <= 0.05 with
at least 8 new episodes having E-1 defined, else INSUFFICIENT below 8, else NOT SUPPORTED. 2e-ii:
SUPPORTED if Holm p <= 0.05 with at least 20 eligible signal weeks, else INSUFFICIENT below 20,
else NOT SUPPORTED. If 2e-i is INSUFFICIENT it drops out and 2e-ii is judged on its unadjusted p
against 0.05.

## 4. Disclosures

1. 2e-ii is related to the published evidence that crowded positions unwind in clusters; it is a
   check of that evidence on this basket, not a novel claim.
2. A SUPPORTED 2e-ii shows predictability in a spread; it says nothing yet about returns after costs
   or about a strategy, which would need its own pre-registration.
3. The analyst is a language model with general knowledge of market history to mid-2026.
