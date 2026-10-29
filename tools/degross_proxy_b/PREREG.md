# Pre-registration: Version B of the de-gross proxy, from hedge-fund 13F holdings

Written 29 October 2026, after Version A closed at its gate (`docs/DEGROSS_PROXY_2026-10-29.md`)
and after a metadata-only probe (`results/1` to `results/3` of this directory: file lists, column
headers, row counts and date ranges; no holding, price or other observation value). Before any
holding, mapping, price or index observation used below was retrieved for this test. A
non-evidentiary side test outside the FNTN funnel: no apparatus, no row in `docs/OPEN_ITEMS.md`,
no authorisation. A kill test: the rules below are applied mechanically by `build.py` and `run.py`.
All data are fetched and read on the GitHub Actions runner only; derived statistics only are
committed.

## 1. Origin, decision and hypothesis

Version A's registered rule was to build B only if A passed its gate. A failed; **the operator
overrode that rule on 29 October 2026** ("Build and run version B"), on the ground that A's
failure is evidence about a market-wide momentum proxy rather than about the mechanism. This test
is therefore run under an explicit override and is reported as such.

**Mechanism** (as for A). When hedge funds de-gross, the shares they are crowded long fall and the
shares they are crowded short rise in the same week, beyond market beta. B builds both legs from
the holdings hedge funds themselves report to the SEC.

**Hypothesis H3-B.** When a de-gross week occurs while the long-minus-short trade is crowded, the
Nasdaq 100 suffers a drawdown of 10% or more within the following 63 trading days more often than
after comparable ordinary weeks. **Registered sign: positive.** One-sided.

**Gate first**, exactly as for A: the proxy must flag weeks Goldman Sachs Prime Brokerage reported
as de-grossing, or the outcome is not computed.

**Expected power, stated before the run.** Machine-readable 13F data start in 2013, and the signal
needs about three years of history, so the signal-evaluable sample is about late 2016 to 2026. The
analyst expects fewer than 8 episodes, so the outcome verdict will most probably be INSUFFICIENT.
The gate is the part of this test that can decide something.

## 2. Inputs

All retrieved by `fetch_raw.py` and `fetch_prices.py` on the runner; nothing in `data/` is
committed.

| Input | Source | Use |
|---|---|---|
| Form 13F data sets, all 54 files (`2013q2` to `2023q4`, then the date-range files to `01jun2026-31aug2026`) | SEC, `https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets` | `SUBMISSION.tsv`, `COVERPAGE.tsv`, `INFOTABLE.tsv` |
| Fails-to-deliver files, every file from January 2012 | SEC, `https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data` | point-in-time CUSIP to symbol mapping (`SETTLEMENT DATE`, `CUSIP`, `SYMBOL`) |
| Daily adjusted closes for every basket symbol and for SPY | Yahoo Finance via `yfinance` (`auto_adjust=True`) | basket and market returns |
| Nasdaq 100 daily close | FRED `NASDAQ100` | outcome |

SEC requests carry the User-Agent `Simon Kittson skittson@gmail.com`, authorised by the operator on
29 October 2026.

## 3. Basket construction (`build.py`)

**Filings.** From every file: rows of `SUBMISSION.tsv` with `SUBMISSIONTYPE` exactly `13F-HR`
(amendments `13F-HR/A` and notices `13F-NT` excluded). Period q = `PERIODOFREPORT`; filing date f =
`FILING_DATE`. Keep a filing only if f is no more than 45 calendar days after q. If a CIK has more
than one kept filing for one period, keep the latest f (ties: the lexically last accession number).
Filings are pooled across all files and de-duplicated by accession number.

**Rows.** From `INFOTABLE.tsv`, for kept filings only. `CUSIP` upper-cased and stripped. A row is a
**long row** when `PUTCALL` is empty and `SSHPRNAMTTYPE` is `SH`; a **put row** when `PUTCALL` is
`Put` (case-insensitive); a **call row** when it is `Call`.

**Funds excluded.** A row is a fund row, and is dropped from everything below except the options
test in the next paragraph, when the upper-cased `NAMEOFISSUER` or `TITLEOFCLASS` contains any of:
`ETF`, `ETN`, `FUND`, `SPDR`, `ISHARES`, `PROSHARES`, `POWERSHARES`, `INVESCO QQQ`,
`SELECT SECTOR`, `VANGUARD`, `DIREXION`, `VANECK`, `WISDOMTREE`, `GLOBAL X`.

**Hedge-fund-like filer**, per filing: (i) between 10 and 200 inclusive distinct CUSIPs among its
non-fund long rows, as Goldman's own VIP list uses to isolate fundamental funds; and (ii) at least
one put row or call row of any kind (fund rows included), to separate funds that use options from
long-only managers. The criterion is a heuristic: some advisers that are not hedge funds will pass
and some hedge funds will not.

**Top 10.** For each hedge-fund-like filing, sum `VALUE` over its non-fund long rows by CUSIP; rank
by summed value, descending (ties: CUSIP ascending); its top 10 are the first ten. `VALUE` units
changed from thousands to dollars in 2023, but values are compared only within one filing.

**Long basket for period q:** the 50 CUSIPs that appear in the most top-10 lists across that
period's hedge-fund-like filings. Ties broken by the number of those filings holding the CUSIP in
any non-fund long row (descending), then CUSIP ascending.

**Short basket for period q:** among non-fund CUSIPs not in the long basket, the 50 on which the
most hedge-fund-like filings report a put row, counting each filing once per CUSIP. A CUSIP needs at
least 2 such filings. Ties: CUSIP ascending. Fewer than 50 qualifying CUSIPs: the basket is the
qualifying set.

**Effective date.** The basket for period q has effective date E_q, the first SPY trading day
strictly after q + 45 calendar days. It is entered at the close of E_q and earns the daily returns
of every SPY day d with E_q < d <= E_next, where E_next is the next basket's effective date (the
last basket earns through the end of the data). Days before the first basket earns are undefined.

**Symbols.** For a CUSIP and an effective date E, the symbol is the `SYMBOL` of its most recent
fails-to-deliver record with settlement date on or before E and no more than 365 days before it.
No record: the CUSIP is unmapped and dropped from that basket. For Yahoo, `.` and `/` in a symbol
become `-`.

`build.py` writes `data/baskets.csv` (`period,effective,leg,rank,cusip,symbol`) and reports, per
period: kept filings, hedge-fund-like filings, basket sizes before and after mapping.

## 4. Returns (`run.py`)

- Market M_d: SPY daily return from adjusted closes. Trading days are SPY's.
- A constituent's daily return on day d is its adjusted close on d over that on the previous SPY
  day, minus 1, when both exist.
- A constituent enters its basket only if it has an adjusted close on the effective date E_q.
  On each day d the basket earns (section 3), the basket return is the equal-weighted mean of the
  daily returns of its entered constituents that have a return that day. A constituent whose data stop
  leaves the mean (it is not set to zero).
- A basket day with no constituent return: the week containing it is not used (its weekly returns
  are undefined).
- Long-leg daily return W_d, short-leg daily return L_d.

## 5. Signals, gate and test

Identical to Version A's `PREREG.md` sections 3 to 5 except as stated here; every rule not
restated below is carried over word for word from that document, with W and L now the long and
short baskets:

- Weeks are ISO calendar weeks of SPY trading days, compounded; week-end e_t the last such day.
- Betas over weeks t-52 to t-1 (52 weeks), as in A.
- **z window 104 weeks** (A: 156). **Crowding sum S over 13 weeks** (A: 26). **Crowding
  percentile over 104 weeks** (A: 260). Shortened because the 13F sample is 13 years long; with
  A's windows the first signal-evaluable week would fall in 2020.
- De-gross week D_t: z_t <= -2.0 and raw W_t < 0 and raw L_t > 0 (the long basket fell outright and
  the put-crowded basket rose outright).
- Crowded C_t: S_t >= the 90th percentile of S over the previous 104 weeks.
- Trigger T_t = D_t and C_t.
- A week whose W, L or M is undefined is not signal-evaluable, and any window containing it leaves
  the dependent quantities undefined.
- **Gate:** reference weeks 2021-01-29, 2026-05-01, 2026-10-16; a reference is available if it is
  on or before the last week-end date; matched within 7 calendar days by a de-gross week; PASS when
  at least 2 are matched and the base rate is no more than 5%; UNTESTABLE when fewer than 2 are
  available; FAIL otherwise. Outcome computed only on PASS.
- **Outcome, episodes, strata, permutation, verdict:** as A sections 3 and 5 (NDX close, 63 trading
  days, -10%, episodes merged within 63 NDX trading days of the episode's first trigger, R21
  terciles, 10,000 placebo sets with `default_rng(20261029)`, INSUFFICIENT below 8 episodes, PASS on
  p <= 0.05 and Delta >= 0.10).
- **Reported without weight:** the 21-day, -5% variant; the variant without the sign conditions;
  and, for the gate, z, raw W and raw L for every week within 10 days of each reference.

## 6. Self-test, independent check, disclosures

1. `selftest.py` runs `build.py` on small synthetic TSV and FTD files with a known answer, and
   runs the outcome machinery on 40 null and 8 planted worlds; acceptable at no more than 4 null
   passes and 8 planted passes.
2. `verify.py` is written by a separate agent from this document, Version A's `PREREG.md` and the
   input formats alone. It rebuilds the baskets from the raw files and recomputes the gate and the
   test. `compare.py` requires its baskets to agree with `build.py`'s, and its gate and primary
   results to agree as in Version A.
3. **Survivorship.** Yahoo returns nothing for many delisted symbols, so those constituents never
   enter a basket. `run.py` reports, per period, the share of each basket priced at its effective
   date. A symbol reused by a later company would carry the later company's prices; this cannot
   be detected here.
4. The analyst is a language model with general knowledge of market history to mid-2026, and has
   seen Version A's derived statistics around the reference weeks (momentum winners outperformed
   in late April and early May 2026). Version B's baskets are different securities, but the sample
   is not unseen.
5. Hedge-fund identification is a heuristic (section 3). The short basket measures where hedge-fund
   -like filers hold puts, which includes hedges of long positions and long-volatility trades as
   well as bearish views; it is a proxy for crowded short exposure, not a measure of it.
6. Non-evidentiary, outside the FNTN funnel; not investment advice.
7. **Readings settled before freezing**, after the independent implementation was written and
   before any input was retrieved: (i) a long row whose `VALUE` cannot be parsed counts as a held
   CUSIP with value 0; (ii) the crowding sum S_t is undefined in a week whose W, L or M is
   undefined. Both implementations apply both readings.
