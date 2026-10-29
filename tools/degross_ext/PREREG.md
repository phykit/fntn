# Pre-registration: Goldman-reported de-gross episodes 2016 to 2020, the extension

Written 29 October 2026, before any search below was run. Follow-up study 1 to
`docs/DEGROSS_EPISODES_2026-10-29.md`, whose search found no admissible episode before 2021 because
the search engine largely ignored the year term. Non-evidentiary side test outside the FNTN funnel;
not investment advice.

## 1. What is fixed and what is new

**Fixed, unchanged:** the sources, tiers, inclusion classes (D and N), the 6-month superlative rule,
dating, merging, fields and judgement calls of `tools/degross_episodes/PREREG.md` section 2 and
`docs/DEGROSS_EPISODES_2026-10-29.md` ("fastest in six or seven months" meets the six-month rule;
"historic" with no stated period fails; for Class D the superlative must attach to the de-grossing).
The 21 frozen episodes of `tools/degross_episodes/episodes.csv` are not re-opened.

**New: the search protocol for 2016 to 2020**, chosen to be calendar-driven and blind to market
events, so that the search cannot preferentially find episodes after falls (which would bias the
timing test):
1. For every calendar month M of 2016 to 2020 (60 months): `Goldman Sachs prime brokerage hedge
   funds <Month> <Year>`.
2. For every year Y of 2016 to 2020 and each of the five original queries, the query restricted to
   each of `zerohedge.com`, `businessinsider.com`, `cnbc.com` and `bloomberg.com` (`site:` operator).
3. Any article found may be read through the Internet Archive (web.archive.org) if the live page is
   paywalled or gone.
Queries naming a market event, crash, sell-off or index level are **not** permitted. Every query
run and every candidate found is logged, with the inclusion decision and reason.

The collecting agent reads no price, index or return data, and does not consult the proxies' signals.

## 2. Combined list

New episodes are merged with the 21 frozen ones under the original merge rules (same-class within
14 days into the earliest; a Class N episode within 14 days of a Class D episode dropped). IDs of the
21 are kept; new episodes are numbered X01, X02, ... in date order. Output `episodes_all.csv`.

## 3. Tests (the original studies 2 and 3, rerun, no retuning)

- **Primary:** study 2 (proxy hit rates, both proxies) and study 3 (H-lag pre-window test, H-lead
  post-publication windows) on the combined Class D list, by the frozen functions of
  `tools/degross_episodes/score.py`, with every threshold unchanged (SEES: hit rate >= 50%, p <=
  0.05, >= 8 scored; H-lag: one-sided permutation p <= 0.05 with >= 8 episodes).
- **Secondary (out-of-sample for the earlier statement):** the same on the new 2016 to 2020 Class D
  episodes alone, verdicts reported and marked INSUFFICIENT below 8.
- **Count reported:** episodes per year 2016 to 2026, as the measure of whether the press record is
  patchy (which governs whether study 3 of this follow-up, cross-bank corroboration, is weighted).

## 4. Disclosures

1. The collecting agent is a language model with general knowledge of market history to mid-2026;
   it is told not to use it and the protocol is calendar-driven, but it cannot unknow it.
2. Search intensity differs between 2016 to 2020 (this protocol) and 2021 to 2026 (the original);
   per-year counts are therefore not comparable as frequencies.
