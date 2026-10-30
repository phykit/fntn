# Prior art for the de-gross and VIP findings

Written 29 October 2026 from eleven web searches and the sources read below; not an exhaustive
literature review (SSRN and journal databases were not searched systematically). Its purpose is to
fix what the article may claim as its own.

## Finding by finding

| Finding (ours) | Closest prior art found | Assessment |
|---|---|---|
| The hedge-fund VIP basket is a Nasdaq tracker that lags it (GVIP: six-factor alpha -0.5% a year, -4.9% a year against QQQ, 2016 to 2026) | Nugent, *Market Rebellion*, 23 May 2023: the VIP list is "basically QQQ but worse" (six of ten top names shared; QQQ about twice the basket's return that year). Klement, CFA Institute *Enterprising Investor*, 22 Sep 2021: GVIP beat the S&P 500 by about 2.6% a year from 2016, with deeper drawdowns | **Anticipated qualitatively.** The point has been made in commentary over a single year; our contribution is the formal test: live fund, ten years, six factors, QQQ benchmark, independent implementation. Klement's early outperformance against the S&P 500 is consistent with ours over the full period (+0.9% a year, t 0.36): the early lead did not persist |
| Consensus 13F stock picks earn no alpha after factors and fees | Iqbal, Jivraj and Angelini, "Systematic 13F Hedge Fund Alpha" (2019): a conviction-consensus portfolio of long-term hedge fund holders returned about 14.1% a year gross against 10.3% for the S&P 500, 2004 to 2019, drawdown about 54% | **In tension with prior work; must be addressed.** Their result is gross, before factor adjustment and against the S&P 500, on a different selection rule and an earlier period. Ours is net of fees, factor-adjusted and against QQQ. The article should state the difference, not claim a contradiction |
| Copycat ETFs: four of six no longer trade; the survivor (GURU) lags (alpha -1.7% a year; -7.1% a year against QQQ) | Klement 2021: GURU and ALFA trailed the S&P 500 by 1.3% and 1.6% a year from mid-2012 ("fair weather investments"); Frank, Poterba, Shackelford and Shoven (2004), *Journal of Law and Economics*, on copycat mutual funds | **Partly anticipated.** The underperformance is known; the closures and the survivorship point (four of six gone from both free price sources, ALFA among them) appear to be new as a stated observation |
| Crowded longs lag, crowded shorts rise and momentum falls in de-gross weeks | Brown, Howard and Lundblad, "Crowded Trades and Tail Risk", *Review of Financial Studies* 35(7), 2022: crowded stocks suffer larger drawdowns in market distress, from position-level hedge fund holdings | **Mechanism established.** Ours is a measurement of that mechanism on Goldman's own reported de-gross weeks, with a rally-matched control. No prior event study of press-reported prime-brokerage episodes was found |
| No free proxy (momentum deciles, 13F baskets, GVIP's weekly gap) reproduces Goldman's de-gross weeks | None found | **Apparently new.** |
| De-gross episodes follow rallies, not falls, and carry no forward signal | Journalistic framing only: e.g. Bloomberg, 31 Jul 2023, "Hedge Funds 'Throwing In Towel' on Stocks as Rally Forces Unwind" | **Apparently new as a measured result**; anecdotally noticed in coverage |
| The press record of "hedge-fund de-grossing" is almost entirely Goldman's book (21 episodes against 2 for Morgan Stanley and JPMorgan, 2021 to 2026) | None found | **Apparently new**, and a caveat for anyone building an indicator from coverage |

Academic work on prime brokerage itself (e.g. Dahlquist, Rottke, Sokolovski and Sverdrup, "Hedge
Funds and Financial Intermediary Risk", 2022; Ongena, Karagiorgis, Anastasiou and Drakos, Swiss
Finance Institute RP 25-57, 2025) studies broker-to-fund risk transmission, not the published flow
figures as a market signal.

## What the article may claim

1. The first systematic test, to our knowledge, of Goldman Prime Book de-gross episodes as reported
   in the press: what they coincide with, what follows, and whether free data can reproduce them.
2. A formal, net-of-fees confirmation of a point made informally since 2023: the hedge-fund VIP
   basket has been a lagging Nasdaq 100 tracker.
3. The methodological point: pre-registered, hash-frozen tests with independent implementations,
   including the failures, run by an AI system under audit.

It should not claim the crowding mechanism or the VIP-equals-QQQ observation as discoveries.

## Sources

- [Nugent, Market Rebellion, 2023](https://marketrebellion.com/news/goldmans-hedge-fund-vip-basket-is-basically-qqq-but-worse)
- [Klement, CFA Institute Enterprising Investor, 2021](https://rpc.cfainstitute.org/blogs/enterprising-investor/2021/does-guru-investing-work)
- [Iqbal, Jivraj and Angelini 2019, summarised by CXO Advisory](https://www.cxoadvisory.com/investing-expertise/exploiting-consensus-hedge-fund-conviction-stock-picks/)
- [Frank, Poterba, Shackelford and Shoven 2004 (NBER w8653)](https://nber.org/papers/w8653)
- [Brown, Howard and Lundblad 2022 (RePEc)](https://econpapers.repec.org/RePEc:oup:rfinst:v:35:y:2022:i:7:p:3231-3271.)
- [Dahlquist, Rottke, Sokolovski and Sverdrup 2022](https://www.ualberta.ca/finance-and-statistical-analysis/events/dahlquistrottkesokolovskisverdrup_hedgefunds_2022wp.pdf)
- [Ongena et al., SFI RP 25-57](https://www.sfi.ch/en/publications/n-25-57-the-leverage-of-hedge-funds-and-the-risk-of-their-prime-brokers)
- [Bloomberg, 31 July 2023](https://www.bloomberg.com/news/articles/2023-07-31/hedge-funds-throwing-in-towel-on-stocks-as-rally-forces-unwind)
- [Schroeder and Posch 2024, summarised by CXO Advisory (findings paywalled)](https://www.cxoadvisory.com/miscellaneous/form-13f-clone-portfolio-performance/)
