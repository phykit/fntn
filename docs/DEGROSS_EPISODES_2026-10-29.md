# Goldman-reported de-gross episodes 2016 to 2026: proxy hit rates and Nasdaq 100 timing, result

Run 29 October 2026, GitHub Actions run id 40898451903 on commit `0436d6b`, branch
`degross-proxy-2026-10-29`. Protocol and tests `tools/degross_episodes/PREREG.md`, committed
(`124d163`) before any episode was collected; episode list frozen before any proxy signal or index
return was computed for it. Non-evidentiary side tests outside the FNTN funnel; not investment
advice.

## Episode list

55 protocol searches (five a year, 2016 to 2026) and 13 confirmation searches produced 103
candidate articles, 71 of them admissible, which merge into **21 episodes: 9 Class D (de-gross) and
12 Class N (record net selling)**, all from January 2021 onwards. No admissible episode was found
for 2016 to 2020: the search engine largely ignored the year term and returned recent coverage, so
the early years are under-sampled rather than quiet. The full candidate log, search log and the
script that applies the rules are committed with the list.

Judgement calls made by the collecting agent before any market data was seen, and kept: "fastest
in six or seven months" read as meeting the six-month rule (admits six episodes); "historic" with
no stated period fails; the superlative must attach to the de-grossing for Class D, which codes
the October 2026 episode as Class N (the analyst's earlier conversation had treated it as
de-grossing).

## Study 2: do the proxies see Goldman's de-gross episodes?

| Proxy | Class D hits | Hit rate | Chance per episode | p | Verdict |
|---|---|---|---|---|---|
| A, momentum deciles | 0 of 9 | 0% | 4.0% | 1.00 | **DOES NOT SEE** |
| B, 13F baskets | 2 of 9 (Jan 2021, Aug 2026) | 22% | 2.9% | 0.026 | **DOES NOT SEE** (below the 50% bar) |

Neither proxy hits any of the 12 Class N episodes. Version B's two hits are about seven times its
chance rate, so the holdings-based proxy carries some information about de-grossing, but it misses
seven episodes in nine.

## Study 3: do the episodes follow Nasdaq 100 falls, or precede them?

| Window | Episodes | Mean | Unconditional mean | Share negative (episodes / all weeks) | p (lower) |
|---|---|---|---|---|---|
| 10 days to the episode week | 9 | **+2.7%** | +0.7% | 33% / 36% | 0.94 |
| 21 days after publication | 9 | +1.1% | +1.8% | 56% / 32% | 0.34 |
| 63 days after publication | 8 | +4.7% | +5.1% | 25% / 23% | 0.45 |

**H-lag: NOT SUPPORTED.** The de-gross episodes did not follow Nasdaq falls: six of nine came after
the index had risen, and the mean pre-window return was about four times the unconditional one
(not tested in that direction, so descriptive only). After publication, returns were close to
normal at both horizons; the 21-day median was slightly negative (-0.5%) and more episodes than
usual were followed by a fall, but on nine episodes this is indistinguishable from chance.

## What the results do and do not license

- Neither public proxy measures Goldman-reported de-grossing reliably; the 13F proxy is better than
  chance but far from adequate. This holds on nine episodes rather than three.
- **Correction to an earlier statement.** The analyst had described the Prime book flow figures as
  moving with the market's falls, on the strength of the October 2026 episode. On the coded record,
  de-grossing episodes more often followed rallies, which is consistent with funds taking risk down
  into strength or rotating, rather than being forced out after a fall. The October 2026 episode is
  Class N under the rules.
- Nothing here shows that a reader of these reports could have avoided a Nasdaq fall.
- Nine episodes is a small sample, drawn from press coverage that is itself selective.

## Disclosures

1. Episodes collected by a language-model agent following the committed protocol; it read no
   market data. The analyst had seen both proxies' figures around the three original reference
   weeks only.
2. Versions A and B were recomputed from their frozen code and hash-verified in the run.
3. No independent second implementation was required by this pre-registration; `score.py` was
   smoke-tested on synthetic inputs.
