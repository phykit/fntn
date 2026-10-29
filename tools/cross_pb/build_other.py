"""Build the other-PB (Morgan Stanley + JPMorgan) episode list for cross_pb (PREREG.md section 2).

Shape follows tools/degross_episodes/build_episodes.py: one add() per candidate article (per bank where an
article attributes figures to more than one non-Goldman bank), the same dating rule and the same merge rule,
applied to the combined MS+JPM list. A `bank` field is added.

Usage: python tools/cross_pb/build_other.py tools/cross_pb

Rules applied (PREREG section 2 of tools/degross_episodes, with "Goldman prime data" replaced by "Morgan Stanley
or JPMorgan prime brokerage data"), and the recorded judgement calls:
  * Class D: gross exposure/leverage reduction, "de-grossing", or long sales with short covers, described as the
    largest/fastest/sharpest since a stated time >= 6 months earlier, or a record. The superlative must attach
    to the de-grossing; otherwise at most Class N.
  * Class N: net selling so described, without gross reduction or short covers reported.
  * "historic" with no stated period fails; "fastest in six or seven months" meets the six-month rule.
  * Region: US, North American or global equities, or US/global IT or TMT.
  * Net leverage LEVELS or net leverage CUTS are neither a gross reduction nor net selling, and are excluded.
  * Rankings below first ("10th-biggest", "third-highest", "one of the most") are not "the largest".
  * Goldman-only articles are logged briefly and excluded (bank = GS-only).
query_no: A = annual query (1..5 as in PREREG, bank prefix), M = monthly query.
"""
import csv, datetime as dt, sys
D = sys.argv[1]
def fri(d):
    d = dt.date.fromisoformat(d); y, w, _ = d.isocalendar()
    return dt.date.fromisocalendar(y, w, 5).isoformat()
C = []
def add(year,q,bank,outlet,url,fp,spe,dec,cls,reason,region="",sector="",tier="",phrase="",date_basis=None):
    C.append(dict(year=year,query_no=q,bank=bank,outlet=outlet,url=url,first_public=fp,stated_period_end=spe,decision=dec,
                  **{"class":cls},reason=reason,region=region,sector=sector,tier=tier,phrase=phrase,date_basis=date_basis))

# ---- Morgan Stanley annual queries, 2021
add(2021,"MS-A1","MS","Institutional Investor","https://www.institutionalinvestor.com/article/2bsxb33yosgeb87g2e4g0/premium/hedge-funds-slash-leverage-amid-market-carnage","2020-03-23","n/a","exclude","","outside period (March 2020); 'very large active de-grossing' has no stated-time superlative")
add(2021,"MS-A1","JPM","Bloomberg","https://www.bloomberg.com/news/articles/2023-07-31/hedge-funds-throwing-in-towel-on-stocks-as-rally-forces-unwind","2023-07-31","n/a","include","D",
    "JPM prime: managers cut longs and shorts last week (de-grossing), pushing total client stock flows to highest since the 2021 retail short squeeze (Jan 2021, >6 months); superlative attaches to the de-grossing flows; no region stated, US-framed, read as whole book. Read via hedgefundalpha/advisorperspectives copies",
    region="global (unstated; whole JPM book)",sector="all",tier="T2",phrase="JPM PB de-grossing pushed client flows highest since 2021 squeeze")
add(2021,"MS-A1","MS","Bloomberg","https://www.bloomberg.com/news/articles/2023-07-31/hedge-funds-throwing-in-towel-on-stocks-as-rally-forces-unwind","2023-07-31","n/a","include","D",
    "MS clients: 'de-grossing activity for the week was the largest this year'; 'this year' = since 1 Jan 2023, about 7 months earlier, meets six-month rule; no region stated, read as whole book",
    region="global (unstated; whole MS book)",sector="all",tier="T2",phrase="MS PB weekly de-grossing largest this year")
add(2021,"MS-A2","MS","MarketScreener (Reuters)","https://marketscreener.com/quote/stock/MORGAN-STANLEY-13654/news/Hedge-funds-ditch-shares-as-bullish-bets-hurt-performance-says-Morgan-Stanley-46890537","2024-06-03","2024-05-30","exclude","","MS: net sellers in every region, long cuts; only superlative is performance ('one of the more challenging ... in recent months'); no selling superlative")
add(2021,"MS-A2","MS","Hedgeweek (Reuters)","https://www.hedgeweek.com/hedge-funds-to-offload-45bn-in-equities-says-morgan-stanley/","2024-07-26","n/a","exclude","","macro/systematic strategies; $25bn is a forecast; 'one of the most substantial risk-unwinding events in a decade' is forward-looking and a ranking, not 'the largest'")
add(2021,"MS-A2","GS-only","Hedgeweek","https://www.hedgeweek.com/hedge-funds-sell-global-equities-at-fastest-pace-since-april-goldman-reports/","n/a","n/a","exclude","","Goldman-only (headline); not read further")
add(2021,"MS-A2","GS-only","investingLive","https://investinglive.com/stock-market-update/global-stocks-see-biggest-selling-in-a-year-hedge-funds-ramp-shorts-goldman-sachs-data-20260331","2026-03-31","n/a","exclude","","Goldman-only (headline); not read further")
add(2021,"MS-A2","GS-only","Okonomisk Ugebrev","https://ugebrev.dk/flashnews/finanshus-hedgefonde-og-institutionber-store-aktienettosaelgere-private-og-corporate-nettokoebere/","2021-04-21","n/a","exclude","","hedge-fund data is Goldman prime; BofA figures are institutional/HNW client flows, not MS/JPM PB")
add(2021,"MS-A3","MS","BNN Bloomberg","https://www.bnnbloomberg.ca/hedge-funds-cut-stock-leverage-at-fastest-pace-since-2020-crash-1.1976104","2023-09-25","n/a","exclude","","MS clients 'cut their net leverage at a pace not seen since last October': a NET LEVERAGE cut, neither gross reduction nor net selling (borderline); other figures Goldman")
add(2021,"MS-A3","MS","Investing.com (Bloomberg)","https://uk.investing.com/news/stock-market-news/hedge-funds-cut-highconviction-stock-bets-to-sevenyear-low-2635873","2022-04-28","n/a","exclude","","MS states funds have NOT been trimming gross nor large net sellers; crowding and net leverage levels only")
add(2021,"MS-A3","MS","Bloomberg","https://www.bloomberg.com/news/articles/2022-10-26/hedge-fund-managers-worry-about-another-archegos-blow-up","2022-10-26","n/a","exclude","","MS: US L/S net leverage 41%, a level 'reached on only a small number of occasions over the past decade': net leverage level, not de-grossing or net selling")
add(2021,"MS-A3","MS","WSAU (Reuters)","https://wsau.com/2023/07/10/us-retail-investors-add-equities-while-hedge-funds-trim-exposure/","2023-07-10","n/a","exclude","","MS: US L/S gross leverage fell 2% w/w with no superlative")
add(2021,"MS-A4","GS-only","Bloomberg","https://www.bloomberg.com/news/articles/2021-11-23/hedge-funds-bailing-on-high-beta-stock-picks-at-a-breakneck-clip","2021-11-23","n/a","exclude","","Goldman-only")
add(2021,"MS-A4","GS-only","Seeking Alpha","https://seekingalpha.com/news/4426735-hedge-funds-dump-global-tech-stocks-at-fastest-pace-in-6-months-goldman-sachs","n/a","n/a","exclude","","Goldman-only (headline)")
add(2021,"MS-A4","GS-only","Hedgeweek","https://www.hedgeweek.com/hedge-funds-slash-stocks-risk-amid-tech-sector-rout/","2024-07-23","n/a","exclude","","Goldman-only")
add(2021,"MS-A4","GS-only","Hedgeweek","https://www.hedgeweek.com/hedge-funds-dump-tech-stocks-after-buying-spree/","n/a","n/a","exclude","","Goldman-only (headline; February 2024 Goldman story)")
add(2021,"MS-A4","GS-only","Hedgeweek","https://www.hedgeweek.com/hedge-funds-exit-tech-stocks-ahead-of-us-tariffs/","n/a","n/a","exclude","","Goldman-only (headline)")
add(2021,"MS-A5","JPM","BNN Bloomberg","https://www.bnnbloomberg.ca/hedge-funds-cut-risky-bets-at-fastest-pace-in-two-years-1.1880170","2023-02-06","n/a","exclude","","JPM: '10th-biggest de-grossing session since the start of 2018' is a ranking, not the largest (borderline); MS cited only via trading-desk estimate; largest-since superlatives are Goldman")
add(2021,"MS-A5","JPM","Fortune (Bloomberg)","https://fortune.com/2021/04/20/head-ripped-off-hedge-funds-abandon-shorts-in-droves/","2021-04-20","n/a","exclude","","JPM: long/short ratio high; no selling or de-grossing superlative; MS short covering is Europe")
add(2021,"MS-A5","MS","The Standard HK (Bloomberg)","https://www.thestandard.com.hk/finance/article/164673/Hedge-fund-trades-still-feeling-bruised-from-day-traders-punts","2021-02-01","n/a","exclude","","MS: leverage near all-time highs (level); JPM: de-grossing 'seemed limited'; gross-cut superlative is Goldman")
add(2021,"MS-A5","MS","BloombergQuint","https://www.bloombergquint.com/amp/global-economics/bears-surrendering-again-with-s-p-500-rally-defying-all-bad-news","n/a","n/a","exclude","","MS: 'pointed to a pivot to exit as well', no superlative; superlative is Goldman")
# ---- Morgan Stanley annual queries, 2022
add(2022,"MS-A2","MS","Investing.com","https://investing.com/news/stock-market-news/hedge-funds-were-big-sellers-of-big-tech-stocks-last-week--morgan-stanley-3249615","2023-12-05","n/a","exclude","","MS: megacap tech selling 'third-highest level since May 2022' (ranking, not largest); discretionary 'strongest since early January' is out-of-scope sector")
add(2022,"MS-A4","GS-only","MarketScreener (Reuters)","https://marketscreener.com/news/latest/Hedge-funds-shed-risk-in-tech-megacap-sell-off-Goldman-says-47406331","n/a","n/a","exclude","","Goldman-only (headline)")
add(2022,"MS-A4","GS-only","Opalesque","https://www.opalesque.com/AMW/700/Opalesque_Roundup_Hedge_funds_sold_tech_shares700.html","2022-01-08","n/a","exclude","","Goldman-only")
add(2022,"MS-A4","MS","Hedgeweek (Reuters)","https://www.hedgeweek.com/hedge-funds-cut-us-stock-exposure-amid-tech-mega-cap-sell-off/","2024-07-18","n/a","exclude","","MS: US software exposure at multi-year lows (exposure level, no stated period); selling superlative is Goldman")
# ---- Morgan Stanley annual queries, 2023
add(2023,"MS-A2","GS-only","Bloomberg Law","https://news.bloomberglaw.com/international-trade/hedge-funds-sold-most-global-equities-since-april-goldman-says","n/a","n/a","exclude","","Goldman-only (headline)")
add(2023,"MS-A3","MS","Hedgeweek","https://www.hedgeweek.com/hedge-funds-boost-bearish-equities-bets-and-cut-stock-leverage/","2023-09-26","n/a","exclude","","same story as BNN 2023-09-25: MS net leverage cut 'not seen since last October' is net leverage, not gross or net selling")
add(2023,"MS-A3","MS","Investing.com (Reuters)","https://investing.com/news/stock-market-news/equity-hedge-funds-cut-risk-in-portfolios-less-confidence-in-rallies-3214572","2023-10-31","n/a","exclude","","MS: net leverage cut to near 10-year record low: net leverage level, not gross reduction or net selling (borderline); JPM no superlative")
add(2023,"MS-A4","MS","Investing.com (Reuters)","https://investing.com/news/stock-market-news/hedge-funds-dump-tech-consumer-stocks-at-start-of-year-banks-say-3268967","2024-01-08","2024-01-05","exclude","","MS: no superlative; superlatives are Goldman")
add(2023,"MS-A5","JPM","TradingView (Reuters)","https://in.tradingview.com/news/reuters.com,2023:newsml_L4N34C2B0:0/","n/a","n/a","exclude","","JPM/MS: superlative is European BUYING relative to US; no selling or de-grossing superlative")
# ---- Morgan Stanley annual queries, 2024
add(2024,"MS-A1","MS","Investing.com (Reuters)","https://m.investing.com/news/stock-market-news/hedge-funds-hunt-new-magnificent-tech-stocks-3273852","2024-01-12","n/a","exclude","","MS: non-Mag7 TMT exposure near record low since 2020 (exposure level); funds were adding, not de-grossing")
add(2024,"MS-A3","n/a","Investing.com","https://investing.com/news/stock-market-news/hedge-funds-trim-leverage-anew-in-sign-of-caution-on-us-stocks-1610388","2018-09-14","n/a","exclude","","outside period (2018); MS net leverage level")
add(2024,"MS-A3","GS-only","Bloomberg","https://www.bloomberg.com/news/articles/2024-06-17/hedge-funds-turn-cautious-as-wall-street-strategists-get-bullish","2024-06-17","n/a","exclude","","Goldman-only")
add(2024,"MS-A4","MS","Investing.com (Reuters)","https://investing.com/news/economy/hedge-funds-call-time-on-tech-rally-goldman-sachs-says-3315692","2024-02-26","n/a","exclude","","MS: 'tech was the most net sold sector last week' has no stated-time superlative; others Goldman")
add(2024,"MS-A4","JPM","Opalesque","https://www.opalesque.com/703991/Opalesque_Roundup_Global_hedge_funds_aggressively_selling_tech399.html","2024-07-06","n/a","exclude","","JPM: no selling superlative; 'fastest since 2016' is Goldman")
add(2024,"MS-A4","GS-only","Investing.com","https://investing.com/news/stock-market-news/hedge-funds-shed-risk-in-tech-megacap-selloff-goldman-says-3523914","n/a","n/a","exclude","","Goldman-only (headline)")
add(2024,"MS-A5","MS","Investing.com (Reuters)","https://www.investing.com/news/stock-market-news/hedge-funds-went-on-stockbuying-spree-ahead-of-job-data-morgan-stanley-3254050","n/a","n/a","exclude","","MS: buying, per headline; not read further")
add(2024,"MS-A5","MS","Investing.com","https://au.investing.com/news/stock-market-news/morgan-stanley-hedge-funds-trimmed-us-semis-quality-exposure-in-june-3325462","2024-07-02","2024-06-27","exclude","","MS: global net selling with no magnitude superlative; superlatives are positioning levels (Quality 10-year high)")
# ---- Morgan Stanley annual queries, 2025
add(2025,"MS-A2","GS-only","OnInvest","https://en.oninvest.com/article/hedge-funds-accelerated-the-selloff-to-the-highest-since-april-2025-which-stocks-escaped-the-selloff","2026-02-24","n/a","exclude","","Goldman-only")
add(2025,"MS-A3","MS","Cyprus Mail (Reuters)","https://cyprus-mail.com/2025/04/08/hedge-funds-suffer-heavy-losses-amid-trumps-tariff-driven-market-plunge","2025-04-08","n/a","exclude","","MS: US L/S net leverage 'just shy of historical lows' (net leverage level; 'historical' has no period); JPM net leverage lowest since late 2023 (net leverage, not gross or net selling)")
add(2025,"MS-A3","GS-only","Investing.com","https://ng.investing.com/news/stock-market-news/hedge-funds-cut-us-big-tech-stocks-bought-china-goldman-1930523","n/a","n/a","exclude","","Goldman-only (headline)")
add(2025,"MS-A4","MS","Reuters via d2233 / Fortune","https://d2233.cms.socastsrm.com/?p=2197101","2025-03-31","n/a","exclude","","MS: increasing shorts, no superlative; JPM: sold tech last week, no superlative; superlatives Goldman")
add(2025,"MS-A4","GS-only","Political Wire","https://politicalwire.com/2025/08/01/hedge-funds-dump-u-s-stocks/","2025-08-01","n/a","exclude","","Goldman-only")
add(2025,"MS-A4","GS-only","ROIC.ai","https://www.roic.ai/news/hedge-funds-dump-tech-stocks-at-fastest-pace-in-a-decade-10-19-2026","2026-10-19","n/a","exclude","","Goldman-only (same story as 24/7 Wall St Goldman headline)")
# ---- Morgan Stanley annual queries, 2026
add(2026,"MS-A2","GS-only","ROIC.ai","https://www.roic.ai/news/hedge-funds-sell-global-stocks-at-fastest-pace-since-april-2025-amid-ai-driven-volatility-02-23-2026","2026-02-23","n/a","exclude","","Goldman-only (Goldman story per OnInvest)")
add(2026,"MS-A3","none","Pulse","https://www.pulse.bot/hedge-funds/news/hedge-funds-slash-us-equity-leverage-as-sp-500-hits-record-highs-3736c723-9059-4974-87fa-6f447c2e55c3/","2026-04-29","n/a","exclude","","gross leverage 'fastest since Sep 2023' but NO bank named: attribution to MS/JPM PB cannot be established (borderline)")
add(2026,"MS-A3","MS","Hedgeweek","https://www.hedgeweek.com/hedge-funds-hit-by-sharp-losses-as-net-leverage-plummets-amid-tariff-driven-selloff/","2025-04-09","n/a","exclude","","same story as Cyprus Mail 2025-04-08: MS and JPM net leverage levels only")
add(2026,"MS-A4","GS-only","24/7 Wall St","https://247wallst.com/investing/2026/10/20/hedge-funds-dumped-tech-stocks-at-the-fastest-pace-in-a-decade-goldman-says/","2026-10-20","n/a","exclude","","Goldman-only (headline)")
add(2026,"MS-A4","GS-only","Parameter","https://parameter.io/goldman-sachs-reports-historic-tech-stock-exodus-by-hedge-funds/","n/a","n/a","exclude","","Goldman-only (headline)")
add(2026,"MS-A5","GS-only","Stocktwits","https://stocktwits.com/news-articles/markets/equity/ai-fear-trade-hedge-funds-biggest-bet-against-tech-goldman-sachs/cZbvGiWR4oI","n/a","n/a","exclude","","Goldman-only (headline)")
add(2026,"MS-A5","GS-only","EdgeX","https://pro.edgex.exchange/en-US/news/article/hedge-fund-vip-list-ai-longs-unwind","n/a","n/a","exclude","","Goldman-only (headline)")
# ---- JPMorgan annual queries, 2021
add(2021,"JPM-A1","JPM","Investing.com","https://uk.investing.com/news/stock-market-news/hedge-funds-remained-net-sellers-postfed-says-jpmorgan-3702342","2024-09-23","n/a","exclude","","JPM: net sellers (-1.3z), gross and net leverage unchanged; no stated-time superlative")
add(2021,"JPM-A1","JPM","Tiger Brokers","https://www.itiger.com/news/1183433964","2026-03-12","n/a","exclude","","JPM superlatives are performance (worst drawdown since April 2025), not selling or de-grossing")
add(2021,"JPM-A2","GS-only","Investing.com","https://uk.investing.com/news/stock-market-news/goldman-hedge-funds-sold-global-equities-at-the-fastest-pace-in-two-years-in-june-3572942","n/a","n/a","exclude","","Goldman-only (headline)")
add(2021,"JPM-A2","GS-only","Bloomberg","https://www.bloomberg.com/news/articles/2024-07-22/hedge-funds-aggressively-cut-risks-in-stocks-amid-big-tech-rout","2024-07-22","2024-07-19","exclude","","Goldman-only")
add(2021,"JPM-A2","GS-only","investingLive","https://investinglive.com/news/goldman-sachs-on-the-largest-selling-of-stocks-by-hedge-funds-in-3-months-short-sales-20240409","2024-04-09","n/a","exclude","","Goldman-only (headline)")
add(2021,"JPM-A2","JPM","Bankingnews.gr","https://www.bankingnews.gr/index.php?id=832934","2025-10-20","n/a","exclude","","selling superlatives are Goldman; JPM only on bank-stock positioning moving to neutral")
add(2021,"JPM-A3","JPM","Tickmill","https://www.tickmill.com/blog/institutional-insights-jpmorgan-positioning-intelligence-23925","2025-09-23","n/a","exclude","","JPM: gross leverage at all-time highs (level); 'little evidence of ... de-grossing'; small net sellers, no superlative")
add(2021,"JPM-A3","JPM","HedgeFundAlpha","https://hedgefundalpha.com/?p=238259","n/a","n/a","exclude","","JPM PB: book net short in August; net exposure figures, no superlative")
add(2021,"JPM-A5","JPM","BNN Bloomberg","https://www.bnnbloomberg.ca/jpmorgan-says-hedge-funds-short-covering-may-have-further-to-go-1.1846303","2022-11-11","n/a","exclude","","JPM: covering 'may have room to run', no superlative; MS net leverage JUMP (increase); short-cover superlative is Goldman")
add(2021,"JPM-A5","JPM","Bloomberg Linea","https://www.bloomberglinea.com/mercados/fondos-de-cobertura-sufren-su-mayor-caida-desde-la-crisis-arancelaria-dice-jpmorgan/","2026-03-12","n/a","exclude","","JPM performance superlatives only")
# ---- JPMorgan annual queries, 2022
add(2022,"JPM-A2","GS-only","Tiger Brokers (Bloomberg)","https://itiger.com/news/2524064231","2025-04-03","n/a","exclude","","Goldman-only")
add(2022,"JPM-A2","none","NewsQuantified","https://www.newsquantified.com/jpm/stock-report/jp-morgan-chase-co-hedge-funds-sell-global-stocks-0ftn6o","n/a","n/a","exclude","","not an article: ticker-reaction page with no prime data")
add(2022,"JPM-A2","GS-only","Tiger Brokers","https://www.itiger.com/hans/news/1102480808","2026-03-12","n/a","exclude","","prime data is Goldman; JPM authors performance commentary only")
add(2022,"JPM-A4","none","KuCoin (Kobeissi Letter)","https://www.kucoin.com/news/flash/hedge-funds-sell-tech-stocks-at-highest-rate-since-2016","2026-07-30","2026-07-28","exclude","","no bank named (relayed from The Kobeissi Letter on X): cannot attribute to MS/JPM PB")
add(2022,"JPM-A4","GS-only","Yahoo Finance (Reuters)","https://ca.finance.yahoo.com/news/hedge-funds-dump-tech-stocks-215635404.html","2024-07-01","n/a","exclude","","Goldman-only")
# ---- JPMorgan annual queries, 2023
add(2023,"JPM-A1","JPM","Investing.com (Reuters)","https://au.investing.com/news/stock-market-news/hedge-funds-trim-exposure-to-megacap-tech-stocks-banks-say-3009507","2023-10-24","n/a","exclude","","JPM: megacap exposure near record (level); 'trimmed a bit', no selling superlative")
add(2023,"JPM-A3","GS-only","InvestmentNews","https://www.investmentnews.com/equities/news/hedge-funds-have-cut-back-on-magnificent-seven-holdings-249748","2024-02-21","n/a","exclude","","Goldman-only")
# ---- JPMorgan annual queries, 2024
add(2024,"JPM-A4","GS-only","Bloomberg","https://www.bloomberg.com/news/articles/2024-02-26/hedge-funds-unload-tech-stocks-after-going-all-in-before-nvidia","2024-02-26","n/a","exclude","","Goldman-only")
add(2024,"JPM-A4","GS-only","Benzinga","https://benzinga.com/z/39621477","n/a","n/a","exclude","","Goldman-only")
# ---- JPMorgan annual queries, 2025
add(2025,"JPM-A2","JPM","Stockopedia","https://www.stockopedia.com/share-prices/microsoft-NSQ:MSFT/news/hedge-flow-hedge-funds-sold-broader-tech-ahead-of-space-x-ipo-jp-morgan-data-shows-019ebb7e-10c0-78dc-b688-3ac5f80ad7fd/","n/a","n/a","exclude","","UNREADABLE: page returned empty and web.archive.org blocked; headline carries no superlative; not assessed beyond headline")
add(2025,"JPM-A5","GS-only","Okonomisk Ugebrev","https://ugebrev.dk/?p=4559830","2025-02-24","n/a","exclude","","Goldman-only")
add(2025,"JPM-A5","JPM","Reuters via d2649","https://d2649.cms.socastsrm.com/?p=549831","2025-03-11","2025-03-07","exclude","",
    "JPM: hedge funds 'unwound positions in single stocks on Friday at the largest amount in over two years'; EXCLUDED because region not established (story framed on European managers, region of figure unstated) and the unwind is not described as long sales plus short covers (borderline; most consequential exclusion)")
# ---- JPMorgan annual queries, 2026
add(2026,"JPM-A2","JPM","Bloomberg","https://www.bloomberg.com/news/articles/2026-03-11/jpmorgan-says-hedge-funds-hit-by-worst-drawdown-since-april","2026-03-11","n/a","exclude","","JPM performance superlative only (same story as Tiger Brokers / Bloomberg Linea)")
add(2026,"JPM-A3","JPM","Kitco (Reuters)","https://www.kitco.com/news/off-the-wire/2026-08-04/hedge-funds-2026-gains-dented-tech-trades-july-jpmorgan-says","2026-08-04","2026-07-31","exclude","",
    "JPM: July de-grossing 'more pronounced than in any year apart from 2020 and 2022' is a SEASONAL ranking of Julys, not the largest de-grossing since a stated time (borderline)")
add(2026,"JPM-A4","JPM","Hedgeweek","https://www.hedgeweek.com/tech-unwind-trims-hedge-fund-gains-but-industry-remains-up-8-for-2026/","2026-08-05","2026-07-31","exclude","",
    "same JPM July note: 'deleveraging most pronounced since 2022' compares Julys only (seasonal), monthly figure (borderline)")
add(2026,"JPM-A5","GS-only","TheStreet Pro","https://pro.thestreet.com/market-commentary/big-funds-are-degrossing-to-manage-this-ugly-market-what-that-means-for-you","2026-03-19","n/a","exclude","","Goldman-only; author's own de-grossing observation is unattributed")
add(2026,"JPM-A5","GS-only","Mammoth Times","https://business.mammothtimes.com/mammothtimes/article/marketminute-2026-3-16-the-great-financial-de-leveraging-hedge-funds-pivot-aggressively-against-banks-and-fintech","n/a","n/a","exclude","","Goldman-only (financials sector)")
# ---- monthly queries (Morgan Stanley January 2021 to March 2024 run; remainder not run, see search_log.txt)
add(2022,"MS-M Jan","MS","Yahoo Finance (Reuters)","https://finance.yahoo.com/news/early-data-show-january-losses-145558884.html","2022-01-27","n/a","exclude","","MS: performance figures only")
add(2023,"MS-M Sep","MS","Investing.com","https://uk.investing.com/news/economy/banks-stocks-back-in-vogue-for-hedge-funds-in-september-morgan-stanley-3176758","n/a","n/a","exclude","","MS: buying, per headline; not read further")
add(2023,"MS-M Sep","MS","Investing.com","https://uk.investing.com/news/stock-market-news/hedge-funds-increase-bullish-positions-in-financial-sector-morgan-stanley-reports-93CH-3177276","n/a","n/a","exclude","","MS: bullish positioning, per headline; not read further")

for c in C:
    if c["decision"]=="include":
        spe = c["stated_period_end"]
        if spe=="n/a":
            p = dt.date.fromisoformat(c["first_public"][:10]) - dt.timedelta(days=7)
            c["week_end"] = fri(p.isoformat()); c["date_basis"]="pub-7"
        else:
            c["week_end"] = fri(spe); c["date_basis"]="stated"
with open(f"{D}/candidates_log.csv","w",newline="") as f:
    w = csv.writer(f); cols=["year","query_no","bank","outlet","url","first_public","stated_period_end","decision","class","reason"]
    w.writerow(cols)
    for c in C: w.writerow([c[k] for k in cols])
inc = [c for c in C if c["decision"]=="include"]
def wk(c): return dt.date.fromisoformat(c["week_end"])
def fp(c): return c["first_public"][:10]
# merge same class within 14 days into earliest (chain from earliest), on the COMBINED MS+JPM list
def merge(rows):
    rows = sorted(rows, key=lambda c:(wk(c), fp(c)))
    eps=[]
    for c in rows:
        if eps and (wk(c)-wk(eps[-1]["head"])).days<=14:
            eps[-1]["members"].append(c)
        else:
            eps.append({"head":c,"members":[c]})
    return eps
Dd = merge([c for c in inc if c["class"]=="D"])
Nn = merge([c for c in inc if c["class"]=="N"])
Dweeks=[wk(e["head"]) for e in Dd]
keptN=[]; droppedN=[]
for e in Nn:
    if any(abs((wk(m)-dw).days)<=14 for m in e["members"] for dw in Dweeks): droppedN.append(e)
    else: keptN.append(e)
eps = sorted(Dd+keptN, key=lambda e: wk(e["head"]))
with open(f"{D}/episodes_other.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["episode_id","class","week_end","first_public","bank","region","sector","outlet","tier","url","phrase"])
    for i,e in enumerate(eps,1):
        h=e["head"]; w.writerow([f"O{i:02d}",h["class"],h["week_end"],fp(h),h["bank"],h["region"],h["sector"],h["outlet"],h["tier"],h["url"],h["phrase"]])
print("candidates",len(C),"included",len(inc),"D articles",sum(c['class']=='D' for c in inc),"N articles",sum(c['class']=='N' for c in inc))
print("included by bank", {b:sum(c['bank']==b for c in inc) for b in ("MS","JPM")})
print("excluded GS-only",sum(c['bank']=='GS-only' for c in C))
print("D eps",len(Dd),"N eps after N-merge",len(Nn),"N kept",len(keptN),"N dropped",[e['head']['week_end'] for e in droppedN])
for e in Dd: print("D", e["head"]["week_end"], [(m["bank"],m["week_end"]) for m in e["members"]])
for e in Nn: print("N", e["head"]["week_end"], [(m["bank"],m["week_end"]) for m in e["members"]])
