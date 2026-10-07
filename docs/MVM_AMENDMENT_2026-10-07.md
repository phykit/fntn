# The minimum viable measurement, amended before it was run

**7 October 2026.** Amends the protocol fixed in `tools/mvm.py` on 19 September
2026 (`claude/mvm_preregistration_2026-09-19.md`). **Fixed before any price was
fetched and before any result existed.** The amended harness is `tools/mvm2.py`;
`tools/mvm.py` is untouched, per rule 4, and its `PROTOCOL` is imported by the
new file so that every constant the two share has one copy.

**Protocol hash: `4d9455c43fb49ffb`**, taken over the 19 September protocol and
this amendment's constants together, and printed on every output. A run whose
output carries another hash was not run under this document. *The hash covers
the two parameter objects and not the code; every output also carries a SHA-256
of `tools/mvm2.py`, and the commit that lands this file is the record of both.*

**NON-EVIDENTIARY, exactly as before.** Nothing here registers a parameter, no
§13 row may take a reading from its output, and it authorises no capital. It is
**procedure** under armed §0.6: it adds no gate, family, cost tier or feed to
the system. The cost table it charges is one the register already holds.

**Authority.** The operator's instruction of 7 October 2026 to carry out the
review of that date, whose recommendation was to run this measurement as a kill
test with two changes: results by liquidity bucket, and the hurdle fixed first.
Reading the harness to do that turned up four further defects, each of which
would have decided the result, so the amendment is wider than the instruction
asked for. **That widening is the thing the operator should check first.**

**Reviewed before it was fixed.** A second reader with no part in writing the
harness read it against this document and ran it against synthetic inputs. It
found no error on the core path (entry and exit indices, the trailing window,
total-return opens across dividends and both kinds of split, the clustered
interval) and twelve points off it. Each is repaired in the code or written
into this document as a stated cost. Three changed the rule itself and are marked *(review)* below.

---

## 0. Reconciliation, and what was known when this was fixed

| Item | State |
|---|---|
| Branch | `killtest-2026-10-07`, cut from `main` at `4d104cc` |
| Tests on `main` before any change | 292: 288 pass, 4 fail (`test_registration_history_recomputes`, `test_control_arm_values_unchanged_across_restamps`, and the two `ANTHROPIC_API_KEY` preflight tests). All four need something this clone does not have, a full history or a key, and none touches `tools/` |
| Unmerged branches | `mothball-2026-09-27` (one commit, the mothball entry in `OPEN_ITEMS.md`) and `review-repairs` (stale since 28 August). Neither is touched here |
| Workflow runs to date | **None.** The Actions API reports a total of nought, so `runbook.yml` has never been dispatched and whether the `SEC_CONTACT` secret is set is UNCHECKED: the secrets endpoint is not readable from this session |
| Project status | Mothballed 27 September 2026. This is the "revival condition" the closing register named, run once |

**Prior knowledge, declared.** One outside result was known when this was
written: Makeev, *SEC Form 4 Insider Purchases in Python* (QuantInsti, 25 August
2026), which reports a five-session abnormal return against SPY of **+1.009%**
(*n* = 7,404, *t* = 5.05) for chief-officer purchases, 1 January 2022 to 30 June
2026, entered at the first session after the filing date, on Yahoo prices and
**before any cost**. Provenance `verified_secondary`: the article and its code
were read; no figure was recomputed. **Its tables by capacity and tail
concentration were deliberately not read before this document was committed**,
because they answer on an overlapping sample the question amendment A3 asks.

*Read after the rule was committed at `c2b11a6`, and recorded so that the order
is on the record; the rule has not moved since.* From that repository's result
files, same provenance: the five-session figure has a median of +0.20% and is
positive in 51.6% of events, so the mean is carried by its right tail; **against
matched placebo dates the difference is +0.60 points and not significant
(*t* = 1.08)**; and entry on the transaction date instead of the filing date
earns +2.57% against +1.05%, so **about three fifths of the move has gone
before the filing is public**. Its capacity table is by the insider's own
footprint and not by liquidity, and carries no five-session row, so it does not
answer A3.

**Dependency contracts this batch writes or first runs against:**

| Contract | Reference read | Status |
|---|---|---|
| SEC Insider Transactions Data Sets: file names, columns, `DOCUMENT_TYPE` = `4`, dates as `DD-MON-YYYY` | The SEC's own readme, and the working parser in `github.com/makeev/form4-event-study` (`code/build_events2.py`) | **CHECKED**, against two sources that agree |
| Download paths | The same repository's `code/download_data.sh`: `/files/structureddata/data/...` to 2026 Q1 and `/files/datastandardsinnovation/data/...` for 2026 Q2. Both are tried for every quarter and the one that answered is logged | **CHECKED** to 2026 Q2. 2026 Q3 is UNCHECKED and may not be published |
| Yahoo chart endpoint: `timestamp`, `quote.open/close/volume`, `adjclose`, `events.splits`, `meta.gmtoffset` | None. Written from recollection | **UNCHECKED, and now moot on hosted runners:** the provider probe of 7 October (run 37608613720) was answered HTTP 429 on its first two questions. Yahoo does not serve GitHub's runners, and impersonating a browser to get round that is not something this project does |
| EODHD end-of-day endpoint | The vendor's own field definitions, read 7 October 2026 after the review raised it: OHLC raw, `adjusted_close` adjusted for splits and dividends, **`volume` adjusted for splits only**, delisted tickers kept under their own symbol | **CHECKED on the page, UNTESTED live** (no key exists). The review's suspicion was right and the provider as first written was wrong: notional is now `adjusted_close × volume` *(review)* |

---

## 1. Six defects in the registered protocol, found by reading it

Each row is a property of `tools/mvm.py` as registered. None was found by
running it, and each would have moved the result.

| # | Defect | Direction of the error |
|---|---|---|
| **A1** | **The statistic is a raw return and the hurdle is an excess return.** 13.9 bp is what a book must add to beat a tracker; the harness compares it with a return that includes the market. Over 2023 to 2026 the market alone supplied roughly 40 bp per five sessions, so a random long book clears branch (c) | **Flatters, decisively** |
| **A2** | **Every purchase is counted at least twice.** `form.idx` carries one row per filer, issuer and reporting owner alike, and the harness appends a purchase for each. Half the rows also carry the *owner's* CIK, so the delisting match fails on them. The interval is naive over five-session windows that overlap | **Flatters**: inflated *n*, an interval too narrow |
| **A3** | **A flat 15.7 bp is the cost of the most liquid bucket only.** The registered table charges 28.7, 78.7 and 208.7 bp below it, and the liquidity floor of USD 40,312 a day admits names the table does not reach at all | **Flatters** the illiquid tail, which is where §0.5 says every anomaly lives |
| **A4** | **It could never have finished.** It fetches every Form 4 in the span, roughly half a million distinct filings, at SEC's fair-access rate: more than a day, against a job limit of 330 minutes | No result at all |
| **A5** | **Liquidity is the median over the whole span**, which looks ahead. The EODHD provider prices from unadjusted opens, so a split inside the window is a 50% loss. Nothing checks that a symbol's series is the security the insider bought | Mixed, and unbounded in the split case |
| **A6** | **`--register` defaults to a path that does not exist**, and `load_delisted` returns an empty set for it. The workflow passes the path explicitly, so no run was affected | A silent default, which rule 3 forbids |

---

## 2. The amendment

**Unchanged:** the span (2023-01-01 to 2026-08-27), the family and the event
(Form 4, code P, acquired, non-derivative, officer or director), entry at the
open of the first session strictly after the filing date, exit at the open five
sessions later, the two universe floors (USD 10.42 a share and USD 40,312 of
median daily notional), the flat 15.7 bp, and no gates.

| # | Change | What it costs |
|---|---|---|
| **A1** | The decision statistic is the **abnormal** return: the trade's open-to-open total return less the benchmark's over the same two opens. Two benchmarks, **SPY** for what the operator would otherwise hold and **IWM** because insider purchases sit in smaller names. **The reading is the lower of the two lower bounds** | Beta is assumed to be one. A book of high-beta small names is under-adjusted in a rising market and the lower-of-two rule only partly repairs that |
| **A2** | **One event per issuer per filing date**, from the SEC's own accession-level tables. **One open position per issuer**: an event whose entry would fall on or before the exit date of the issuer's running position is skipped and counted. The interval is two-sided 95%, **clustered by calendar month of entry**, on Student *t* with clusters less one; fewer than ten clusters is refused | Fewer events and a wider interval than the registered harness would have printed. Month clusters do not absorb dependence across a month end, and with clusters of unequal size the interval under-covers: the review's simulation put the miss rate near 8% against a nominal 5%. **A bound that clears a threshold narrowly has not cleared it** |
| **A3** | Gross abnormal returns are reported **by liquidity bucket**, and the tiered reading charges each trade its bucket's **registered midpoint cost** from `docs/ROW29_REDERIVED_2026-08-27.md`: 15.7 / 28.7 / 78.7 / 208.7 bp for trailing median daily notional above USD 1bn / 100m / 10m / 1m. **Below USD 1m the table has no row**, so those trades take the flat cost only and every tiered statistic refuses them | The table's spread terms are themselves unmeasured (§13 row 36), and for US names they may be too high. A verdict that turns on them is reported as turning on them, which is what the COST-DETERMINED branch is for |
| **A4** | Events come from the **SEC Insider Transactions Data Sets**, about fifteen quarterly archives, each logged with its SHA-256. A quarter missing at the end of the span shortens the span and says so; one missing inside it refuses | The filing date is a date and not a timestamp, so nothing here can measure §13 row 13's capture rate. Entry at the next open is conservative by up to a session |
| **A5** | The **price floor is read from the filing's own volume-weighted purchase price**, which is row 12's precedent. **Liquidity is the median of the 63 sessions before entry**, 21 at least. **Opens are adjusted for splits and dividends.** **Identity:** the filing price over the provider's nominal close on the last transaction date (or the last session in the five days before it, where that date has no bar) must lie in 0.5 to 2.0, the band Makeev uses, or the event is dropped and counted. A transaction dated after its own filing anchors nothing and is dropped as unscorable | Events with under 21 sessions of history are lost, which removes recent listings. The identity band is borrowed and not derived, and it is wide enough that a recycled symbol will sometimes pass it, which adds noise and pulls a mean towards zero |
| **A6** | The register path has no default: a missing or empty register refuses. **A provider that omits delisted names cannot pass anything**: any branch above KILL on it is PROVISIONAL and buys one thing, a re-run on an archive that keeps them. ***And it cannot kill unconditionally either (review).*** The names it is missing over this span are largely acquisitions, whose omission pulls the mean down, so **a KILL on such a provider is final only if the unpriced events would have needed to average more than 230 bp to bring L(G) to zero**, 230 bp being the largest US effect this project has ever documented for the family (§0.5); otherwise the KILL is PROVISIONAL too. **On any provider**, a branch above KILL is PROVISIONAL unless its bound survives charging every event lost on a delisted issuer a total loss, so the flag is a measurement and not a property of the vendor's name | The free route cannot confirm an edge, by construction, and may not be able to deny one. Both tests are bounds, deliberately loose |

---

## 3. The decision rule, fixed before the result

Abnormal returns throughout. Every bound is the lower 95% bound, and the lower
of the SPY and IWM readings.

- **G** is every trade at the flat 15.7 bp: the most generous reading available.
  *It admits names trading USD 40,000 a day at opening prints, where bid-ask
  bounce inflates an open-to-open mean. That is why it can only kill.*
- **T** is tiered midpoint cost on **two pre-declared populations**: buckets B1
  to B4, and buckets B1 to B2 alone *(review)*. Pooled to B4, three quarters of
  the cost table is charged at 78.7 and 208.7 bp, so an edge living only where
  costs are real would be reported and could not decide. **Clearing on either
  population counts and the verdict names which.** *The cost: two looks, so the
  nominal 5% is nearer 10% at worst.*

| Verdict | Condition | What follows |
|---|---|---|
| **KILL** | L(G) ≤ 0 | No edge over a tracker at the cheapest cost this project has ever registered. The equity book is finished and no register row rescues it |
| **COST-DETERMINED** | L(G) > 0 and L(T) ≤ 0 on both populations | A gross effect exists and whether it pays turns on spreads nobody has measured. **Not a pass and no capital.** The one act it buys is measuring quoted spreads on the buckets that carry the effect |
| **BEATS A TRACKER** | L(T) > 0 on a population, under that population's time hurdle | Real, and does not pay for the time |
| **PAYS FOR ITSELF** | L(T) ≥ the time hurdle on a population | Only here is the programme worth its own cost |
| **UNSCORABLE** | An interval cannot be formed | Reported with the reason, never as a pass |

**The time hurdle is 29.8 bp at a full book**, being `(22,000 − 7,000) / 504`:
the tracker-plus-time rung of `claude/programme_hurdle_2026-09-19.md` less its
tracker rung. The tracker is now removed by subtracting it trade by trade, so
what is left of the hurdle is the time. **£504 a basis point assumes 806 trades
a year**, which is what sixteen slots turning every five sessions consume. A
population supplying fewer cannot keep the book invested, its idle slots earn
the tracker and nothing more, and its hurdle is `15,000 / (trades a year ×
0.625)`, which is higher. *The registered 19 September rule held the hurdle
constant whatever the breadth; this does not.* **The rung itself remains an unratified proposal for a §13 row; this
document uses the arithmetic and ratifies nothing.**

**The tail rule.** The branch is computed twice, with and without trades whose
gross five-session return exceeds 100% in absolute value. If the two differ,
**the lower branch is the verdict** and it is marked TAIL-DEPENDENT. A verdict
that twelve trades carry is a verdict about twelve trades.

**The statistic registered on 19 September is still computed and still read by
its own four branches**, and is printed beside the amended one under a label
saying what it is.

**What would falsify the premise, stated now:** L(G) ≤ 0 on a five-session
window, on a population of several thousand events, against both benchmarks.

---

## 4. What this does not decide

- **§0 decision 0c.** The family stays retired. Measuring it is not reinstating it.
- **The programme hurdle.** Still a proposal awaiting a §0 decision.
- **Market impact.** In no cost figure here, as §13 row 37 has never had a column.
- **Capture.** Entry is a daily open after a dated filing; the intraday question is untouched.

---

## 5. Running it

`runbook.yml` gains three steps and one input. All are manual, as every step in
that file is.

```
gh workflow run runbook.yml --ref killtest-2026-10-07 -f step=provider-probe   # no SEC host, no event
gh workflow run runbook.yml --ref killtest-2026-10-07 -f step=killtest-smoke   # 150 seeded tickers, COVERAGE ONLY
gh workflow run runbook.yml --ref killtest-2026-10-07 -f step=killtest         # the measurement
gh workflow run runbook.yml --ref killtest-2026-10-07 -f step=killtest -f killtest_provider=eodhd
```

**The provider probe is first contact with the price source**, added because
the first dispatch of 7 October stopped at the reachability check: the
`SEC_CONTACT` secret is not set, and setting it is the operator's act. The probe
needs no secret. It asks the provider for seven well-known live names and eight
that were acquired or failed inside the span, checks that a known ten-for-one
split is un-adjusted in the right direction, and counts how many of the eight
the provider still holds. It prices no insider event, so it is not a look.

**The smoke run computes no return into any output.** It exists to learn
whether the SEC archives parse and what share of tickers the provider answers
for, and it draws its tickers by a registered seed so that it is not the head of
the alphabet, which is the error row 12's first reading made.

**The run refuses rather than reports** if more than 2% of tickers go
unanswered: a verdict over whatever a rate-limited provider chose to return is
not a verdict. The cache is saved on failure, so a re-run resumes.

---

## 6. State at the end of 7 October 2026: nothing measured, two inputs missing

**No event has been priced and no return exists.** Three dispatches were made
and each is recorded here because each is a fact about the world and not about
the harness.

| Run | Step | Outcome |
|---|---|---|
| 37606610225 | `killtest-smoke` | Stopped at the reachability check. **The `SEC_CONTACT` secret is not set**, so no SEC host was contacted |
| 37606930326 | `provider-probe`, yahoo | Cancelled after fourteen minutes without an answer |
| 37608613720 | `provider-probe`, yahoo | **HTTP 429 on SPY and on IWM.** The free price route is closed on hosted runners |

**What the measurement now needs, and both are the operator's to supply:**

1. **`SEC_CONTACT`** as a repository secret: a real name and address, per
   `claude/github_runbook_setup_2026-09-19.md` §3. It costs nothing.
2. **`EODHD_KEY`** as a repository secret. This is the purchase the closing
   register of 27 September already named as the revival condition, and the
   one-month plan covers a single run. It is also the only route here that
   keeps delisted names, so it is the only one whose answer A6 lets stand.

**Then, in order:** `provider-probe` with `killtest_provider=eodhd`,
`killtest-smoke`, `killtest`.

*NON-EVIDENTIARY throughout. §13 row 31 is unaffected and remains BLOCKED BY
DECISION.*
