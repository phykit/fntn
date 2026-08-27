# Binding-path step 2, attacked. And the archive, scoped rather than purchased

**27 August 2026. Phase 3 of the eleven-phase batch.**

Step 2 is five pre-calibration fixings. **Two of the operator's decisions have
quietly changed what it needs**, and one fixing turns out not to apply at all.

---

## 3a. Borrow snapshot date. ***NOT APPLICABLE, not outstanding.***

§0.7(e) requires a timestamped broker snapshot of borrowability, *erring in both
directions with the anti-conservative direction likely dominant.*

***Two registered decisions between them remove it.***

| Decision | Effect |
|---|---|
| **Account type: CASH** (§14, taken P116) | a cash account **cannot borrow**. There is nothing to snapshot |
| **The grammar is long-only** for every live family (§5.4.1) | **no position requires a locate** |

**Recorded as `n/a` with its reason**, not as outstanding. *§0.7(e) already said
so in a parenthesis — "not currently binding: the insider family is long-only by
grammar" — and it sat in the outstanding column anyway.* **A fixing that has been
non-binding since it was written should have been `n/a` since it was written.**

***What would make it applicable again:*** a **short-side family**, which needs
**margin**, which is a **§0 decision on account type**. **Two decisions deep, and
both are on the record**, so this cannot come back silently.

## 3b. Archive identity and span. ***Scoped for BACKTESTING, per 0a.***

`archive_opens` = **2023-01-01**, set since 26 August and in the parameter object.

**What remains, and 0a narrows it.** The objective is **realistic backtesting**,
not deployment, so **the archive is scoped as an evaluation instrument.**

| Component | State |
|---|---|
| **Opening boundary** | **SET.** 2023-01-01, registered |
| **Closing boundary** | **outstanding.** Under 0a it is the last date at which the archive is complete rather than a date at which trading begins — *a backtest wants a boundary it will not cross, and a live book wants one that moves* |
| **Venue coverage** | **DERIVABLE, and phase 4 does it.** At the registered tolerance the universe is US-listed; §0.7(f) already enumerates NYSE and Nasdaq |
| **Fields** | **DERIVED at P121**: the ten the intake points read, each named by the point that refuses without it. *That was written for the collection protocol and it is the same list* |

**So of four components, one is set, one is derived, one is derivable in phase 4,
and one is outstanding.**

---

## 3c. The price side. **A costed options table, and NOTHING is acquired.**

**The event side is free and already available.** EDGAR supplies filings at no
cost; §3.6.5's collection protocol is registered; the corpora in phase 5 come
from Cornell LII as `corpora/us` did.

***The price side is where the archive is not free, and where the interesting
problem is not cost.***

### THE SURVIVORSHIP PROBLEM, named explicitly

> ***A price source that omits delisted names is not merely incomplete. It
> biases every backtest UPWARD, and it does so silently.***

**The mechanism.** A universe assembled from *names that exist today* and priced
over *2023 to now* contains only companies that **survived** the span. Every
bankruptcy, every deregistration, every acquisition at a discount and every
exchange delisting is **absent from the sample and absent from the returns.**
The strategy is then measured on a population **selected on the outcome it is
being measured for.**

**Why it is worse here than in general.** §0.10 routes microcaps to a shadow
cohort and §5.2.2's least liquid buckets are where the largest documented
effects sit. ***Delisting is concentrated in exactly those buckets***, so the
bias is **largest where this project most wants to look.**

**And why it cannot be patched by care.** A backtest cannot detect its own
survivorship bias from inside: **the missing names leave no trace in the data
that remains.** *It is not a noise term. It is a shift with no error bar.*

### The options, and every provenance is stated

***No source's coverage claim was verified in this session.*** Reachability was
checked by HTTP; **content was not read** except where marked, and **nothing was
acquired.** *Marking this precisely is the point: an options table that asserts
coverage it has not read is the Class I defect in a costed suit.*

| Source | Cost | Delisted names? | Provenance of that claim |
|---|---|---|---|
| **Stooq bulk daily** | **free** | **partial** | ***`named, unread`.*** Reachable, HTTP 200 on 2026-08-27T19:50:23Z, **but the page requires JavaScript and returned only "This site requires JavaScript to verify your browser"** — so nothing about its coverage was read |
| **Yahoo Finance**, unofficial endpoints | free | ***largely NOT*** | `named, unread`. **Also a terms-of-use question that has not been read**, which is a separate reason not to rely on it |
| **Tiingo**, free tier | free tier, registration | partial | `named, unread`. Pricing page reachable and **rendered as an empty shell**; nothing read |
| **Alpha Vantage**, free tier | free, rate-limited | **no** | `named, unread` |
| **EODHD** | **subscription** | yes, claimed | ***`reachable, partially read`***: the pricing page renders and lists an *EOD Historical Data API* and a *Splits and Dividends Data API*. **No delisting claim was read** |
| **Polygon.io** | **subscription** | yes, claimed | `named, unread`. Reachable |
| **Nasdaq Data Link / Sharadar** | **subscription** for the survivorship-free tables | yes | `named, unread`. Reachable |
| **CRSP** | **institutional licence** | ***yes, with delisting returns.*** The reference standard | `named, unread` |
| **Norgate Data** | **subscription** | yes, claimed | `named, unread`. **The URL guessed for its pricing page returned 404**, so not even reachability is established |

### ***The free route that changes the shape of the problem***

**You cannot get survivorship-free prices for nothing. You CAN get, for nothing,
a complete list of what is missing.**

**SEC Form 25 and 25-NSE are the notifications of removal from listing, they are
filed on EDGAR, and EDGAR is free.** *So is Form 15, deregistration.*

> ***A backtest that knows which names it is missing can BOUND its own
> survivorship bias instead of ignoring it.***

**What that buys, concretely.** For any span, the Form 25 population gives the
**denominator of the missing set**. A run can then report: *"this backtest
covers N names; M names were delisted in the span and are absent; the result is
computed on N/(N+M) of the population that existed."* **A stated coverage
fraction is not a repair, and it is the difference between a biased number and a
biased number that says so.**

***And a stronger use.*** Under a worst-case assumption — every missing name
returned −100% over its final window — the reported expectancy can be **bounded
below**. *If the strategy survives the worst case, survivorship is no longer a
live objection; if it does not, the size of the gap is the size of the purchase
that would settle it.*

**Provenance: `named, unread`.** Form 25 was **not** retrieved in this session,
because **EDGAR access is fenced behind `SEC_CONTACT` and it is unset**, and this
project does not fetch from a regulator without identifying itself. *The route is
named, not verified, and it is on the register as such.*

### The recommendation. ***And it is deliberately NOT a purchase recommendation.***

**Take the free path first, and take it in this order:**

1. **Set `SEC_CONTACT`.** It unblocks step 4 **and** the Form 25 route in one act.
2. **Build the delisting population from Form 25 and Form 15**, free, and make
   the archive's coverage fraction a **reported field on every run**.
3. **Then, and only then, decide whether a purchase is warranted**, because
   *the coverage fraction is the number that tells you how much a purchase would
   buy*, and **nobody currently knows it**.

***The cost of this recommendation, stated: it delays any priced data and it
does not remove the bias.*** What it removes is **the ignorance of the bias's
size**, which is the thing that makes an unpriced purchase decision impossible.

---

## 3d. Universe constituents. **Deferred to phase 4, with the dependency named.**

The constituent list is **derivable from the achievability screen**: US-listed,
above the minimum share price, above the liquidity floor §6.7's participation cap
implies. **Phase 4 states those numbers, and this fixing is revisited there.**

## 3e. Partition boundaries and source roster

**Partition boundaries. Obtainable now, and part of it is done here.** §0.7(a)
requires boundaries at **observable structural breaks in the corpus**, with
proportional points only where **a documented search finds none** — *"we looked
and found no break" and "we did not look" are different claims.* **The
deliverable is the search, not the boundary**, and **the search cannot run until
the archive exists**, because the breaks are breaks *in the corpus*.

***What IS obtainable now and is recorded: the search's specification.*** It runs
over source composition, platform volume and disclosure timing, and **a
documented null result is a valid outcome and must be recorded as one.** *Naming
that in advance is what stops a null being read later as "we did not look".*

**Source roster: §13 row 32's numerator, BLOCKED, and unchanged from P121.** Its
denominator cannot come from inside the corpus, and the two external routes are a
purchase or hand enumeration. **Nothing in this phase moves it.**

---

## 3f. Step 2's five fixings, counted

| Fixing | State after this phase |
|---|---|
| Archive identity and span | **PART.** Opening set, fields derived, venue derivable in phase 4; **closing boundary outstanding** |
| Partition boundaries | **OUTSTANDING**, and its search specification is now recorded |
| Universe constituents | **DEFERRED to phase 4**, dependency named |
| **Source roster** | **OUTSTANDING**, §13 row 32 |
| **Borrow snapshot date** | ***n/a***, and it should have been for some time |

***One of five is settled, and it is settled as NOT APPLICABLE rather than
done.*** **Step 2 is NOT closed and is not marked closed.**

*The honest summary: this phase removed one fixing, scoped a second, deferred a
third to a phase that will answer it, and left two outstanding. The archive
itself did not move, because the archive needs data nobody has authorised buying
and the free path needs one environment variable.*
