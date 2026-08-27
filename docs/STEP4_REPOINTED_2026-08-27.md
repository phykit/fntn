# Insider dealing retired, and step 4 RE-POINTED rather than abandoned

**27 August 2026. Phase 2 of the eleven-phase batch.**

---

## 2a. The registration

`insider_dealing` is removed from `discoverable_classes`. **The remaining three
are `major_holdings_change`, `buyback` and `earnings_event`.** The object
re-stamped to **row 10** of `docs/REGISTRATION_HISTORY.md`, caused by that field
and no other. **A `§12.1` rule change: the discoverable population changed.**

## 2b. The cost, and it is substantial

***Retiring the family strands three things, and one of them was the only route
a blocked row has ever had.***

| Stranded | What it was |
|---|---|
| **`corpora/us`** | thirteen Section 16 rule documents from `law.cornell.edu`, with manifest and retained raw. The **entire** discovery corpus this project has ever built |
| **The Form 4 block** | the §9.4 trace corpus, its fetcher, `verify_response`'s byte floor plus structural marker, and the eleven fences written to fail first around it |
| **Position 5 of the item pipeline** | `ingestion_lag_exceeds_window`, **which P115 established was the only route to a §13 row 15 observation that row has ever had** |

***So §13 row 15 returns to having no route, unless 2d finds one.*** *It does;
see below. Had it not, this decision would have closed a blocked row's only
door and the batch would have had to say so in those words.*

**A fourth cost, smaller and worth naming.** The insider family was the one with
**paper-sourced effect sizes** (§0.5's 230 bps raw, 115 after the
post-publication rung). **The three surviving families have no documented effect
in this paper**, so §5.4's decay priors and Gate 1's cost-survival check now run
against claims with no literature behind them. *That is a real narrowing of what
the funnel can check, and it is not repaired by any corpus.*

## 2c. Nothing is deleted

`corpora/us/_RETIRED.md` records the corpus as retired with date and reason, and
`corpora/_trace_filings/.gitkeep` records the same for the Form 4 machinery.

***The machinery is family-agnostic and is reused in phases 4 and 5.***
`scripts_fetch_us_corpus.sh`'s pattern — adoption date per document, refusal
where a document is not datable, raw retained under `_raw` with a re-extraction
test, chrome-free extraction, a manifest carrying URL, adoption date, retrieval
timestamp and both byte counts — **is the pattern every corpus built after it
follows.** `verify_response`'s contract survives the family entirely: **what
changes is the form and the deadline, not the fetcher.**

*One honest weakness recorded:* `corpora/us` is **not** underscore-prefixed, so
it is **not fenced by construction**. What keeps it out of a sweep is that
`discoverable_classes` no longer names its class, **which is a weaker guarantee
than a fence**, and it is stated rather than implied.

---

## 2d. Re-pointing step 4. **8-K Item 2.02, under `earnings_event`.**

**The eleven item-pipeline points, per candidate family.** *Point 11,
`observation_precedes_registration`, is a property of a pairing rather than of
material and needs a registered directive, of which there are zero; it is
unreachable for every candidate and is not counted for any.*

| Pos | Point | **13D/13G** | **8-K Item 2.02** | **Repurchase (Item 703)** |
|---|---|---|---|---|
| 1 | `item_source_inaccessible` | yes | **yes** | yes |
| 2 | `running_document_no_anchor` | no, static | no, static | no, static |
| 3 | `anchor_provenance_absent` | no, regulator-stamped | no | no |
| 4 | `observation_anchor_absent` | no | no | no |
| 5 | `ingestion_lag_exceeds_window` | **yes** | **yes** | **weak, see below** |
| 6 | `extraction_class_suspended` | later | later | later |
| 7 | `extraction_schema_incomplete` | yes, field-delimited | ***yes, and against PROSE*** | yes, inside prose |
| 8 | `issuer_unresolved` | **yes** | **yes** | **yes** |
| 9 | `catalyst_date_corroborated` | no, it IS the corroboration | no | no |
| 10 | `catalyst_duration_below_floor` | some | ***yes, characteristically*** | **no**, a programme is multi-session |
| **Directly exercised** | | **4** *(1, 5, 7, 8)* | ***5*** *(1, 5, 7, 8, 10)* | **3** *(1, 7, 8)* |
| **Restores a route to §13 row 15?** | **yes** | **yes** | **no, see below** |

### Why repurchase disclosure fails on row 15, which is not obvious

Under **Item 703 of Regulation S-K** repurchases are disclosed in **periodic
reports**, so the catalyst precedes its disclosure by up to a quarter. **Position
5 would fire constantly**, and the reading would be **about the disclosure
regime rather than about this system's ingestion**, which is precisely the
distinction §3.5 draws: *ingestion lag is a property of this system, distinct
from §3.1.1's diffusion half-life, which is a property of the market.* **A row 15
populated from Item 703 would be measuring the wrong thing.**

*The 2023 buyback disclosure modernisation, which would have supplied a timely
filing, **postdates `archive_opens` and must be refused** (phase 5b).*

### Why 8-K Item 2.02 wins, and the decisive reason is not the count

***It exercises point 7 against PROSE, and every other candidate exercises it
against a field-delimited form.***

`CLAUDE.md`: *"Where a regulatory form is field-delimited, **even the clerk is
replaced by a parser**."* **Form 4 and Schedule 13D are field-delimited, so
their extraction path is a parser and carries no probabilistic dependency.**
**An 8-K Item 2.02 furnishes a press release**, and its numbers are extracted by
**a schema-enforced model call**.

> ***So the 8-K flow is the only candidate that exercises the model-mediated
> extraction path at all, and that is the path rule 1 is written against.***

**A trace should be pointed where the machinery is weakest**, and the weakest
part of this machinery is the one place a model still touches a number.

**It also wins on the count (5 of 11), on point 10** — an earnings announcement
is the archetypal single-session catalyst, so `catalyst_duration_below_floor`
fires characteristically rather than incidentally — **and on row 15**, Item 2.02
carrying a **four-business-day** furnishing deadline against which ingestion lag
is a clean reading.

### ***TAKEN: step 4 is re-pointed at 8-K Item 2.02.*** Delegated authority, 27 August 2026.

**The cost, stated.** Item 2.02 is **furnished, not filed**, so its legal status
differs; the release is free-form, so **the refusal rate at point 7 will be
higher than a field-delimited form's and must not be read as a machinery
defect**; and **Regulation G and Item 10(e)'s non-GAAP reconciliation** make the
extraction genuinely hard. *That difficulty is the reason for choosing it and
will look like a fault in the results.*

**Step 4's description is rewritten against the chosen family** in
`docs/OPEN_ITEMS.md`.

### And it remains unbegun

***All three candidates are EDGAR. `SEC_CONTACT` is required whatever the
family, and it is UNSET.***

```
>>> from fntn.scanner.trace_filings import user_agent
>>> user_agent()
TraceCorpusRefused: SEC_CONTACT is not set, so this fetch will not run.
```

**Everything up to the fetch is built. The fetch refuses.** ***Binding-path step
4 remains unbegun, for want of one environment variable.***

---

## 2e. The three-part repair holds, and the sweep found TWO MORE

**The fail-first tests pass:** `test_no_ledger_read_path_hands_out_a_directive_without_its_origin`,
`test_the_import_fence_now_runs_in_both_directions`,
`test_a_sweep_refuses_over_a_corpus_that_is_not_committed`.

***Every `SELECT` in the package was swept for markers the fences rely on, and
two more queries project one away.***

| Query | Verdict |
|---|---|
| `report.py` `_unexercised`: `SELECT DISTINCT code FROM refusal WHERE surface='intake'` | ***DEFECT. Repaired.*** It projects `origin` away, so **a point exercised only by the control arm was reported as exercised**, and for the agent arm it was not |
| `report.py` `_surfaces`: `SELECT surface, code, COUNT(*) FROM refusal GROUP BY surface, code` | **Pooled by design, and now says so.** It counts every refusal on a surface including points that fired behind an earlier failure, so it is a **code census** and not an arm reading |
| `ledger.py` `emitted_codes` / `code_distribution` | **Pooled by design.** They feed `codes.coverage` and the headline test, which is a coverage measure over the whole ledger and is deliberately not per-arm |
| everything else | counts, hashes and display-only summaries; no marker to project away |

***The repaired one is the FOURTH instance of Class III, and its invariant was
already installed.*** P105 split the abort-position distribution by `origin`
**and the method beside it kept the pooled query.**

> **The invariant was applied to a METHOD when the class was about a QUERY.**

*That is the same shape as P114's finding about retrievability: three instances
were each closed where they occurred, and the class stayed open.* **Phase 9b
must decide whether Class III's invariant needs the same widening Class I's
does.**
