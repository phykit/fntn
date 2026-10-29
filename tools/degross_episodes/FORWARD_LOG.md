# Forward log of Goldman-reported de-gross episodes (from November 2026)

Opened 29 October 2026. Purpose: to accumulate episodes that no test has seen, so that study 2
(`tools/crowd_degross/PREREG.md`: crowded longs lag QQQ in the de-gross week) can be confirmed or
refuted on fresh data. Non-evidentiary; not investment advice.

## Rules (fixed; do not alter)

- Coding: exactly `tools/degross_episodes/PREREG.md` section 2 (sources, tiers, Class D and Class N,
  the 6-month superlative rule, dating, merging), with the recorded judgement calls: "fastest in six or
  seven months" meets the six-month rule; "historic" with no stated period fails; for Class D the
  superlative must attach to the gross reduction (or long sales with short covers); attribution must
  name Goldman's prime brokerage, Prime Services, the Prime book or the Prime desk.
- Coverage: one search pass a month for the previous calendar month, using the five queries of that
  section with the month and year substituted. Every candidate is logged in `forward_candidates.csv`
  with its decision and reason, included or not.
- `forward_log.csv`: one row per included article; rows are appended, never edited or deleted.
- The coder reads no price or return data when coding.

## The confirmatory test (pre-registered now, run later)

When **8 new Class D episodes** (after merging, week-ends from 1 November 2026) are in the log, run
study 2's primary statistic (GVIP minus QQQ in the episode week, against all defined weeks, one-sided
lower permutation p, 10,000 draws, `default_rng(20261029)`) by the frozen `tools/crowd_degross/run.py`
on those episodes only. SUPPORTED at p <= 0.05; otherwise NOT SUPPORTED. At the past rate of about two
de-gross episodes a year this may take three to four years.
