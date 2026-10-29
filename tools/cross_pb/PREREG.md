# Pre-registration: do other prime brokers report de-grossing in Goldman's episode weeks?

Written 29 October 2026, before any search below was run. Follow-up study 3 to
`docs/DEGROSS_EPISODES_2026-10-29.md`. Non-evidentiary side test outside the FNTN funnel; not
investment advice.

## 1. Purpose

An indicator built on one bank's client book is only as general as that book. This study builds an
independent episode list from Morgan Stanley and JPMorgan prime brokerage commentary and measures
agreement with the frozen Goldman list, both ways.

## 2. Collection (fixed before searching)

- **Banks:** Morgan Stanley (Prime Brokerage, MS PB, "Morgan Stanley prime brokerage data") and
  JPMorgan (Prime Brokerage, "JPMorgan prime book", "JPM PB"). Combined as one list ("other PB").
- **Period:** 1 January 2021 to 23 October 2026, the period the frozen Goldman list covers.
- **Searches:** for each bank B in {Morgan Stanley, JPMorgan} and each year Y of 2021 to 2026, the
  five queries of `tools/degross_episodes/PREREG.md` section 2 with `Goldman Sachs` / `Goldman`
  replaced by B (60 searches), plus for each bank and calendar month M of the period
  `<B> prime brokerage hedge funds <Month> <Year>` (140 searches). No query may name a market
  event, crash, sell-off, index level, or a Goldman episode or its dates.
- **Inclusion, classes, dating, merging, fields:** exactly as `tools/degross_episodes/PREREG.md`
  section 2 and the judgement calls recorded in `docs/DEGROSS_EPISODES_2026-10-29.md`, with "Goldman
  prime data" replaced by "Morgan Stanley or JPMorgan prime brokerage data". An article attributing
  figures to more than one bank counts for each non-Goldman bank it attributes. Merging is applied
  to the combined other-PB list. A field `bank` is added.
- The collecting agent does **not** see the Goldman episode list or its dates, reads no market data,
  and logs every query and candidate with its decision and reason.

## 3. Tests

Weeks are ISO weeks ending Friday; the comparison period is the ISO weeks with week-end from
2021-01-01 to 2026-10-23 (T weeks).

- **Agreement G->O (primary):** of the 9 frozen Goldman Class D episodes, the share with an
  other-PB episode (Class D or N) whose week-end is within 7 days. Chance per episode
  q = 1 - (1 - b)^3, b = (number of other-PB episodes) / T. One-sided binomial p.
  **CORROBORATED** when the share is >= 50% and p <= 0.05; **NOT CORROBORATED** otherwise;
  INSUFFICIENT when the other-PB list has fewer than 5 episodes (the record is then too thin to
  corroborate or contradict).
- **Agreement O->G (reported, verdict as above, no further weight):** of the other-PB Class D
  episodes, the share with a Goldman episode (D or N, frozen list) within 7 days, chance from the
  Goldman list's density.
- **Timing replication (secondary):** study 3's H-lag and H-lead windows, by the frozen
  `timing()` function of `tools/degross_episodes/score.py`, on the other-PB Class D episodes. This
  asks whether de-grossing reported by other banks also follows rallies.

## 4. Disclosures

1. Press stories often cite several banks in the same week, and journalists write positioning
   stories when markets move; agreement may partly measure press attention, not independent data.
   The O->G direction and the per-article bank attribution are recorded so this can be inspected.
2. Coverage of Morgan Stanley and JPMorgan prime data is thinner than Goldman's; silence is not
   contradiction, which is why INSUFFICIENT exists.
3. The collecting agent is a language model with general knowledge to mid-2026.
