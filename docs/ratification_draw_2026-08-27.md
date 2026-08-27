# Ratification draw, 2026-08-27

Registration `701adbd9d48015ed`. Registered seed `20260826`, salt `ratification-draw-v1`. Draw digest `65e688a67fc0054e`.

**The clerk's labels on the drawn arm are withheld from this file.** An operator shown the answer beside the question is being asked to agree rather than to label, and agreement obtained that way measures deference and not accuracy. Write your own label in each box, then run `python -m fntn.scanner ratify-reveal`.

**Stated before any result exists: one disagreement in twelve refutes the clerk's labels for the whole drawn arm.** Not reduces confidence in them. Row 21a's reading compares the fence's verdict against a clerk label on every one of the thirty-six; if the clerk and you part company on any subject here, those labels are not your classifications and the arm has no denominator anyone has checked. Twelve is a third of the arm, so one disagreement implies about three across it.

The question on each is the taxonomy's own: **is this a class-level mechanism, naming no issuer, no instrument and no dated episode?**

## Drawn arm: 12 of the 36, labels withheld

### 1. `sweep-023`

- **event_class**: index_reconstitution
- **corpus**: tsx
- **event_definition**: A TSX-listed issuer files its Form 1 report of changes in issued and outstanding securities within ten days after the end of a month in which the share count changed, or files a nil report where no change occurred.
- **measured_on_intention**: Intended to hold on TSX-listed issuers whose share count feeds public float determinations, across mid and large capitalisation, restricted to listed equity classes and excluding structured products and non-corporate issuers.
- **mechanism_note**: Issued and outstanding share counts are the input that float-weighted index maintenance consumes, and the TSX supplies that input on a fixed monthly cadence through Form 1 filed via TMX LINX, with quarterly nil reports when nothing changed. Related capital events arrive through their own channels on their own clocks.

```
operator_label (class_level / not_class_level):
reason:
```

### 2. `sweep-035`

- **event_class**: short_interest_disclosure
- **corpus**: eu_mar
- **event_definition**: First appearance of a net short position in a national public register, and the symmetric disappearance when a position falls back below the public disclosure threshold while remaining reportable to the regulator.
- **measured_on_intention**: Shares admitted to trading on Euronext Amsterdam and German regulated markets, mid- and small-cap bands where individual position holders are few, excluding sovereign debt positions and excluding positions held under market-making or primary-dealer exemptions.
- **mechanism_note**: Under the Short Selling Regulation as applied by the AFM, a net short position must be notified privately to the competent authority at a first threshold and at each further increment, while public disclosure in the national register begins only at a higher threshold and continues at each increment above it.

```
operator_label (class_level / not_class_level):
reason:
```

### 3. `sweep-026`

- **event_class**: insider_dealing
- **corpus**: eu_mar
- **event_definition**: Managers' transactions executed inside a closed period under an issuer-granted permission, typically the exercise of options or warrants expiring within the window or a pre-committed employee scheme instruction.
- **measured_on_intention**: Continental European regulated markets under BaFin and AFM supervision, large-cap through small-cap bands, restricted to issuers operating share-based remuneration schemes and excluding funds and investment vehicles.
- **mechanism_note**: Articles 7 to 9 of Delegated Regulation 2016/522 set out when an issuer may allow a manager to trade during a closed period: exceptional circumstances that are urgent, unforeseen, compelling and external, or an enumerated category of transaction such as employee share schemes with no timing discretion, options or warrants expiring in the window, savings schemes entered into beforehand, transfers between the manager's own accounts, and statutorily required acquisitions.

```
operator_label (class_level / not_class_level):
reason:
```

### 4. `sweep-003`

- **event_class**: insider_dealing
- **corpus**: asx
- **event_definition**: A director's transition from a nil registered holding to a non-nil direct holding acquired on market, identifiable from the 'no. of securities held prior to change' field reading nil against a non-zero number acquired.
- **measured_on_intention**: Intended to hold on ASX-listed entities across small, mid and large capitalisation bands, filtered to directors whose first non-nil holding is acquired rather than issued, and excluding initial holdings arising from admission, IPO subscription or contractual appointment arrangements.
- **mechanism_note**: Guidance Note 22 requires notification of securities registered in the director's name and of securities in which the director holds a relevant interest, with the notice due within five business days of the change and the director expected to inform the entity within three. Because the form demands the holding both before and after, the boundary case of a first acquisition is directly readable from the disclosure without inference.

```
operator_label (class_level / not_class_level):
reason:
```

### 5. `sweep-036`

- **event_class**: clinical_procurement
- **corpus**: eu_mar
- **event_definition**: Ad hoc disclosure of inside information released at the end of a delay period whose stated legitimate interest was a pending public authority approval or an authorisation affecting a product, invention or supply arrangement.
- **measured_on_intention**: Life-science, medical-technology and diagnostics issuers on Frankfurt Prime Standard and Euronext Amsterdam/Brussels/Paris, mid- and small-cap bands, restricted to issuers whose revenue depends on regulated health-sector authorisations, reimbursement decisions or public tender awards, and excluding diversified industrial conglomerates.
- **mechanism_note**: Article 17(1) MAR requires disclosure as soon as possible, and Article 17(4) permits delay where legitimate interests are prejudiced, the delay is not likely to mislead the public and confidentiality is maintained, with the competent authority notified afterwards. ESMA's guidelines enumerate legitimate interests that include the issuer having developed a product or invention whose immediate disclosure would jeopardise intellectual property rights.

```
operator_label (class_level / not_class_level):
reason:
```

### 6. `sweep-031`

- **event_class**: buyback
- **corpus**: eu_mar
- **event_definition**: Aggregated public disclosure of buy-back programme executions made at the far end of the permitted reporting window rather than promptly after execution.
- **measured_on_intention**: Euronext and Deutsche Boerse regulated-market listings running an announced buy-back under the MAR safe harbour, large- and mid-cap bands, restricted to open-market repurchases and excluding tender offers, reverse auctions and stabilisation.
- **mechanism_note**: Article 2 of Delegated Regulation 2016/1052 requires disclosure of the programme's purpose, monetary allocation, maximum number of shares and duration before trading begins, then reporting of transactions to the competent authority and public disclosure in aggregated form by the end of the seventh daily market session after execution.

```
operator_label (class_level / not_class_level):
reason:
```

### 7. `sweep-018`

- **event_class**: major_holdings_change
- **corpus**: tsx
- **event_definition**: An eligible institutional investor without a control intention crosses one of the alternative monthly reporting thresholds and files a report within ten days of the end of the month in which the crossing occurred, in place of the immediate news release and early warning report.
- **measured_on_intention**: Intended to hold on TSX-listed Canadian reporting issuers across mid and large capitalisation, restricted to filings by financial institutions, pension funds and registered investment managers electing the alternative monthly reporting exemption.
- **mechanism_note**: NI 62-103 gives eligible institutional investors a separate reporting lane keyed to month end, with reports due within ten days of the end of the month at the ten, twelve and a half, fifteen and seventeen and a half percent thresholds, available only to holders that do not have the intention to make a take-over bid or to change control.

```
operator_label (class_level / not_class_level):
reason:
```

### 8. `sweep-007`

- **event_class**: buyback
- **corpus**: asx
- **event_definition**: Announcement of a new on-market buy-back by a listed entity via an Appendix 3C notification, including whether the programme sits within the 10/12 limit and therefore proceeds without a security holder resolution.
- **measured_on_intention**: Intended to hold on ASX-listed entities across the full capitalisation range, restricted to buy-backs of quoted ordinary securities and excluding minimum-holding buy-backs, employee share scheme buy-backs and selective buy-backs from identified holders.
- **mechanism_note**: The Appendix 3C separates on-market, equal access, selective, employee scheme and other buy-backs on the face of the form, records the total securities on issue in the class and the maximum number proposed to be bought back, and caps the programme's end date at twelve months.

```
operator_label (class_level / not_class_level):
reason:
```

### 9. `sweep-015`

- **event_class**: insider_dealing
- **corpus**: tsx
- **event_definition**: A reporting insider files a SEDI report for an equity monetization transaction such as a prepaid forward, a costless collar or a total return swap, which alters the insider's economic exposure to the issuer's shares while leaving registered ownership of those shares unchanged.
- **measured_on_intention**: Intended to hold on TSX-listed issuers where control-block or founder holders are present, across mid and large capitalisation, restricted to common equity and to insiders who are significant shareholders or executive officers.
- **mechanism_note**: CSA Staff Notice 55-312 sets out that derivative-based arrangements letting an investor receive a cash amount similar to proceeds of disposition while retaining legal ownership are reportable, with forwards filed as acquisitions of third-party derivatives under nature-of-transaction code 70, collars filed as separate put and call legs, and total return swaps filed as equity swaps.

```
operator_label (class_level / not_class_level):
reason:
```

### 10. `sweep-013`

- **event_class**: insider_dealing
- **corpus**: tsx
- **event_definition**: An insider files a SEDI insider report disclosing an open-market acquisition of the issuer's equity made at the insider's own discretion, as distinguished from an acquisition reported under the automatic securities purchase plan alternative reporting route.
- **measured_on_intention**: Intended to hold on TSX-listed non-investment-fund operating issuers across the full capitalisation range from small through large cap, restricted to common equity classes with continuous SEDI coverage, and excluding issuers listed only on TSX Venture.
- **mechanism_note**: NI 55-104 splits insider acquisitions into two reporting channels. Discretionary changes in beneficial ownership must be filed within five days of the change, while acquisitions under an automatic securities purchase plan qualify for alternative reporting, disclosable annually by March 31 or in acceptable summary form with a December 31 deemed transaction date.

```
operator_label (class_level / not_class_level):
reason:
```

### 11. `sweep-032`

- **event_class**: buyback
- **corpus**: eu_mar
- **event_definition**: Interruption of an announced buy-back programme across a closed period or a period of delayed disclosure of inside information, where the programme has not been structured as time-scheduled or delegated to an independent lead manager.
- **measured_on_intention**: German and Dutch regulated-market issuers with a live repurchase authorisation, large- through small-cap bands, restricted to programmes disclosed under the MAR safe harbour and excluding programmes conducted solely to meet employee scheme or convertible obligations.
- **mechanism_note**: Article 3 of Delegated Regulation 2016/1052 bars the issuer from trading in own shares during a closed period or while it is delaying disclosure of inside information, unless the programme is time-scheduled or is managed by an investment firm taking trading decisions independently of the issuer.

```
operator_label (class_level / not_class_level):
reason:
```

### 12. `sweep-019`

- **event_class**: buyback
- **corpus**: tsx
- **event_definition**: A TSX-listed issuer files a Form 12 Notice of Intention to Make a Normal Course Issuer Bid together with the accompanying press release, establishing an authorised repurchase capacity and a bid period before any purchases occur.
- **measured_on_intention**: Intended to hold on TSX-listed non-investment-fund issuers across small through large capitalisation, restricted to bids in listed common equity classes and excluding substantial issuer bids and formal issuer bids made by circular.
- **mechanism_note**: The TSX requires acceptance of a Form 12 notice and a press release before an NCIB begins, and the notice states the class, the number of securities sought and the bid duration. The authorised capacity is bounded by the greater of ten percent of the public float on the acceptance date and five percent of the outstanding securities of the class.

```
operator_label (class_level / not_class_level):
reason:
```

## Authored probes: all 6, shown in full (§13 row 21b)

Not withheld and not sampled. Row 21b asks whether each probe exercises the route it claims and whether these are the routes that matter, and both are answered by reading all six. This arm reports coverage and never a rate: a proportion over a chosen set estimates nothing, and doubling the set to twelve routes would halve any percentage whilst leaving the fence untouched.

### 1. `plant-01`: issuer name with a legal-form designator

- **event_definition**: Purchases disclosed by Apple Inc. in a Form 4 cluster during March 2024, following the results release.
- **measured_on_intention**: US large-capitalisation issuers with ordinary common stock.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

### 2. `plant-02`: bare ticker in capitals

- **event_definition**: A run of open-market purchases by directors of AAPL reported within two business days of the January 2025 close.
- **measured_on_intention**: US issuers on Nasdaq across the full capitalisation range.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

### 3. `plant-03`: title-case bare ticker

- **event_definition**: A run of open-market purchases reported under the symbol Aapl during the November 2024 window.
- **measured_on_intention**: US issuers on Nasdaq across the full capitalisation range.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

### 4. `plant-04`: exchange-prefixed identifier, symbol too short for the ticker rule

- **event_definition**: Repurchases executed by NYSE:BA under an announced programme in Q3 2025.
- **measured_on_intention**: US issuers with a live open-market repurchase authorisation.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

### 5. `plant-05`: ISIN

- **event_definition**: Holdings crossing five per cent in US0378331005 notified in the same week.
- **measured_on_intention**: US issuers with registered voting classes.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

### 6. `plant-06`: one-word issuer name equal to its own ticker

- **event_definition**: A buy-back notice filed by Ball in February 2025 under an existing authorisation.
- **measured_on_intention**: US issuers with a live open-market repurchase authorisation.
- **clerk label**: not_class_level

```
route exercised as claimed (yes / no):
route belongs in the set (yes / no):
reason:
```

## What ratifying this does and does not do

Ratification makes the labels the operator's. It does **not** close row 21a, which is blocked on the design segment: the tolerance the rate must be known to is set by how much funnel depth §7.1 can lose before it loses power, and §7.1 has not run. It does **not** turn row 21b's coverage into a rate; only a drawn episode-level sample could.

The reading it would ratify is an **upper bound**, not a rate: 0 events in 36 trials, 95% upper bound approximately 8.3% by the rule of three. Zero events does not estimate zero.

