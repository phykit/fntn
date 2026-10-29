# Pre-registration: is GVIP's result general to 13F-copycat ETFs?

Written 29 October 2026, before any return of the funds below was retrieved. Follow-up study 4 to
`docs/GVIP_LIVE_2026-10-29.md`. Non-evidentiary side test outside the FNTN funnel; not investment
advice.

## 1. Candidate funds (fixed now)

US-listed ETFs whose stated strategy is to hold stocks selected from hedge-fund or "guru" 13F
filings: **GURU** (Global X Guru Index), **ACTX** (Global X Guru Activist), **GURI** (Global X Guru
International), **ALFA** (AlphaClone Alternative Alpha), **ALFI** (AlphaClone International),
**IBLN** (Direxion iBillionaire). GVIP is the reference already tested and is excluded from the
composite. No fund is added after retrieval.

## 2. Data and admission

- Daily adjusted closes from Yahoo via yfinance; if Yahoo returns no history for a ticker, the
  Stooq daily CSV (`<ticker>.us`) is tried. The source used is recorded per fund.
- A fund is **admitted** with at least 36 complete months inside the French factor range. The
  number of candidates admitted, and which, is a result in itself (feasibility), reported first.
- **Survivorship:** funds that closed and are absent from both sources are lost. Closed funds are
  more likely to have done badly, so the admitted set is biased **upward**; a FAIL is therefore
  conservative, a PASS is not.

## 3. Test

For each admitted fund, by the frozen `analyse()` and `ols()` of `tools/vip_premium/run.py`
(Newey-West, L = 3): six-factor alpha (FF5 plus momentum), CAPM alpha, alpha on QQQ, and excess over
SPY and QQQ.

- **Primary:** the **composite**, the equal-weighted monthly average of the admitted funds' excess
  returns in each month at least one is live (funds enter and leave as they list and close).
  **PASS** when six-factor alpha t >= 2.0 and alpha >= 2.0% a year over at least 60 months;
  INSUFFICIENT with fewer than 2 funds admitted or fewer than 60 composite months; otherwise FAIL.
- **Reported without weight:** each fund's figures; the composite including GVIP.

## 4. Disclosures

1. The analyst is a language model with general knowledge of market history to mid-2026, including
   commentary on some of these funds; the sample is not unseen.
2. Expense ratios are inside the returns; the test is of the investable product, not the idea gross
   of fees.
