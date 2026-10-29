# De-gross proxy, Version B (hedge-fund 13F baskets): result

Run 29 October 2026, GitHub Actions run 4 (run id 40879422472) on commit `7b3cc94`, branch
`degross-proxy-2026-10-29`. Specification frozen before any holding, mapping, price or index
observation was retrieved: `tools/degross_proxy_b/PREREG.md`, SHA-256 `2e6392ab...7b155`, frozen
2026-10-29T13:09:44Z. Run under an **operator override** of Version A's rule that B be built only if
A passed its gate (PREREG section 1). A non-evidentiary side test outside the FNTN funnel; not
investment advice.

## Verdict

**CLOSED at the gate (FAIL): 1 of 3 reference weeks matched (2 required). No outcome was computed.**

| Item | Value |
|---|---|
| 13F inputs | 54 data sets (3.05 GB), periods 2013-03-31 to 2026-06-30, 53 baskets with an effective date |
| Hedge-fund-like filings per period | 453 to 831 in 2025-26 (of 6,800 to 8,700 kept filings) |
| Symbols needed, priced on Yahoo | 701, of which 451 priced (250 return nothing, mostly delisted) |
| Long basket entered at effective date | median 41 of 50 (minimum 27; median 34 before 2019) |
| Short basket entered | median 84% of listed names (listed median 42) |
| First signal-evaluable week; count | 2016-11-18; 520 weeks |
| De-gross base rate | 0.96% (cap 5%) |
| Independent implementation | baskets agree row for row (4,791 rows); gate status, matches and base rate agree |

## The three reference weeks

Derived statistics from `results/4/gate.json`: z of the beta-neutral long-minus-put-crowded pair,
and the raw weekly returns of the two legs.

| Week ending | z | Long basket | Put-crowded basket | De-gross week? |
|---|---|---|---|---|
| 2021-01-29 | **-3.80** | -2.7% | **+7.7%** | **Yes** (matched) |
| 2026-05-01 | +1.95 | +2.0% | -0.6% | No: the opposite |
| 2026-10-16 | -1.60 | -6.0% | -4.4% | No: both legs fell, and z above -2 |

- **January 2021 is a clean hit.** The holdings-based proxy records exactly what Goldman reported:
  hedge funds' favourite longs fell while the shares they held puts on rose sharply. Version A's
  momentum proxy missed this week (z -0.46).
- **Late April to early May 2026 is the opposite of de-grossing** in this proxy, as it was in
  Version A: the long basket outperformed the put-crowded basket.
- **Mid-October 2026** shows a large fall in hedge-fund longs (-6.0% in the week), but the
  put-crowded names fell too. That looks like long selling into a falling market (Goldman reported
  the largest technology selling since 2016) rather than the long-sales-plus-short-covers pattern
  the proxy is built to detect.

## What the result does and does not license

- It closes Version B as registered. The holdings-based pair catches a short-squeeze de-gross
  (2021) but not the two 2026 episodes, so it does not measure de-grossing as Goldman's Prime book
  reports it, in general.
- The analyst's reading, not tested: Goldman's 2026 episodes were concentrated in technology and
  semiconductors and were reported as sector de-grossing; a 50-name market-wide basket and a
  put-holder basket dilute a sector event. A sector-specific version would be a new hypothesis,
  chosen after seeing this result, and would need its own registration and fresh reference weeks.
- No outcome was computed, so nothing here says whether de-grossing precedes Nasdaq 100 falls.
- The register now holds two closed price-based proxies and a closed futures-positioning test
  (25 October 2026). The remaining routes to the original question are live logging of Goldman's
  weekly figures under the event-coding schema, or access to Goldman's own series.

## Deviations and disclosures

1. Metadata probes (runs 1 to 3) read file lists, headers, row counts and date ranges only, before
   PREREG.md was written; run 1 found both repository secrets unset. The SEC User-Agent is the
   operator-authorised contact set in the workflow.
2. Two readings were settled before freezing, after the independent implementation was written and
   before any input was retrieved (PREREG section 6 item 7).
3. **Survivorship.** 250 of 701 symbols returned no Yahoo prices; the long basket entered a median
   41 of 50 names. Delisted names never entered a basket. This biases the legs towards survivors; it
   cannot be quantified here.
4. The analyst is a language model with general knowledge of market history to mid-2026, and had
   seen Version A's figures around the reference weeks before writing this specification.
5. Self-test (run 4): passed, including the hand-built 13F and fails-to-deliver case and 8 of 8
   planted worlds; 3 of 40 null worlds passed the outcome machinery.

Sources: [SEC Form 13F data sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets);
[SEC fails-to-deliver data](https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data);
Yahoo Finance via yfinance; [FRED NASDAQ100](https://fred.stlouisfed.org/series/NASDAQ100).
