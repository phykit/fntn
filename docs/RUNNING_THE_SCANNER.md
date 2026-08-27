# Running the scanner

What a sweep produces today, stated before the instructions so it is not
discovered afterwards.

The design segment does not exist, so **no directive can be measured**. What a
sweep produces is a queue of directive drafts, each blocked on the four things
only you may supply. That is not a degraded output: §3.6.8 step 6 holds that a
pointer is a way to have evidence waiting when the instruments report, and a
directive registered now carries a `registered_at` that precedes the archive's
existence. That is the strongest form of pre-registration available, stronger
than registering before you looked, because the data could not have been looked
at. Nothing about it is a measurement and nothing here pretends otherwise.

## The five markets

| | Venues | Universe | Construction |
|---|---|---|---|
| US | NYSE, Nasdaq | traded | `pre_archive` |
| UK | LSE Main Market, AIM | traded | `pre_archive` |
| AU | ASX | external | `cross_market` |
| EU | Frankfurt, Euronext | external | `cross_market` |
| NZ | NZX Main Board | external | `cross_market` |

**The construction belongs to the corpus, not to the event class.** Insider
dealing read from an ASX corpus is `cross_market`; the same class read from an
EDGAR corpus is `pre_archive`, because NYSE and Nasdaq sit inside §0.7(f) and
the two would share a price path. Declaring an in-universe corpus as
`cross_market` costs nothing, looks like a configuration detail, and voids the
guarantee silently, so the CLI refuses it.

## The key, and why it is not in the environment

**Auth is split.** Claude Code runs on the claude.ai Max subscription. **Only
the scanner's model calls bill the API key.** The key sits at `~/.fntn_key`,
`chmod 600`, **outside the work tree**.

Every scanner invocation that makes model calls takes it at exec time:

```bash
ANTHROPIC_API_KEY="$(cat ~/.fntn_key)" python -m fntn.scanner <cmd>
```

***The reason, stated as a cost rather than a convenience.*** **Putting the key
in the environment makes the harness spend the budget meant for the
measurement.** An exported key is picked up by every process in the session,
including the agent doing the engineering, so the balance intended to pay for a
sweep is drawn down by the work of preparing one — and the draw is invisible,
because nothing in the sweep's own accounting sees it. *The split is what makes
the figure in `docs/CANDIDATE_MECHANISMS.md` a measurement of the sweep and not
of the session.*

**Three rules that follow, and none of them is stylistic:**

- **Never export it.** `ANTHROPIC_API_KEY` must be absent from the session
  environment; the inline form above sets it for one process and no other.
- **Never echo it**, into a terminal, a log or a commit message.
- **Never write it into any file in the repository.** The key is outside the
  tree so that no `git add -A` can reach it.

**What the code does about it, so this is not only a convention.** The client
refuses at construction on an absent key, and separately on a key the API
declines: **a variable that is SET is not thereby USABLE**, and the two are
distinguished because a ten-character stub satisfied a presence check for a
whole day and three sittings. The preflight is a `models.list` call, which
costs no tokens and settles the key and the pinned model together.

**What it does not check, and this is where the money goes.** *The models
endpoint does not consult the balance.* A 200 from it establishes that the key
authenticates and establishes **nothing whatever about credit**; a shortfall
surfaces as a 400 on the first message call. The preflight reports credit as
`not established` for exactly that reason.

## The pin, and the cost guard

**The model is a registered field, `agent_model` (§13 row 39), and there is no
`--model` flag.** An override would let a sweep run under a model the parameter
hash does not name, which is the ledger recording the wrong clerk. Re-pinning
is a re-stamp: a new hash, a row in `docs/REGISTRATION_HISTORY.md`, and the
four register rows that name a hash re-read.

`sweep` takes `--cost-ceiling-usd`, default **4.00**. After the **first** corpus
and before any other, it prints the measured input and output tokens, the cost
at list price, and the projection for all families; **if the projection exceeds
the ceiling it stops.**

***A stop, and deliberately not a truncation.*** The abort is raised inside the
gather loop, **before the control arm is drawn and before a record reaches the
ledger**, so what remains is a measurement of what a sweep costs and no partial
sweep at all. *A book over one family of three, presented as a book, would put
a partial population under §7.1's headline with nothing saying so.*

**Two things the guard does not do.** It does not re-project after every
family, because that pays to re-learn what it already measured. And it does not
treat an unknown price as a small one: a model absent from the rate table makes
the cost **NOT SCORED** and stops the sweep, which is rule 3 applied to the one
quantity the operator is actually spending. **The rates themselves are list
prices read from a reference table stamped `cached: 2026-06-24`, so they are
`named, unread` against a live pricing page** and every figure derived from them
carries that tag. Adequate for *is this about to cost more than the balance*;
not adequate for anything a decision is taken on.

## Install, once

```bash
pip install -e ".[dev]"
```

The package sits at `src/fntn`. Without this it is invisible to `python -m`,
which reports `No module named 'fntn'`. `PYTHONPATH=src` works instead if you
prefer not to install.

## The order, which the CLI enforces

```bash
python -m fntn.scanner markets   # profiles, constructions, master sources
python -m fntn.scanner template  # a form prefilled for all five markets
python -m fntn.scanner init      # or an empty one
python -m fntn.scanner check     # report exactly what is still missing
python -m fntn.scanner trace     # test the machinery; evidentially inert
ANTHROPIC_API_KEY="$(cat ~/.fntn_key)" \
  python -m fntn.scanner sweep   # runs only if the form is complete
```

`trace` and `sweep` are different acts and are kept apart deliberately. A sweep
is the layer running; a trace is the layer being tested, full panel on every
subject regardless of the audit fraction, every row stamped `NON_EVIDENTIARY`,
and the harness refusing to register or admit. It reads the labelled set at
`docs/labelled_proposals.json` rather than proposals from a corpus, because what
it measures is the machinery: §13 row 21's two fence error rates and §13 row 23's
abort-position distribution. Neither is a fact about the market, so neither needs
the archive and neither consumes the first sweep.

`sweep` refuses an incomplete registration and names every gap. That refusal is
why the command exists: a directive raised under a partial registration cannot
be attributed to anything, and registering the missing values afterwards does not
repair it. A kill criterion written once a result is known is not a kill
criterion.

## What you must supply, and why each is yours

| Field | §13/§14 | Why not the machine's |
|---|---|---|
| `control_arm_delta` | row 19 | The separation below which the discovery layer is refuted. Committed before you know whether the answer flatters you |
| `control_arm_n_min` | row 19 | Below it the verdict is `undetermined_at_budget`, never a quiet pass or a quiet kill |
| `control_arm_ratio` | row 20 | Drawn mechanisms per proposed one. Strictly above zero: with no control arm the layer has no instrument that can refute it |
| `control_arm_seed` | row 20 | Recorded with every draw. A control redrawn once the treatment arm's result is known is not a control |
| `corpora` | row 22 | Which material is readable. Only the `discovery` and `external` partitions; anything else is a scored population |
| `discoverable_classes` | row 22 | A class absent from this list is refused with `scoring_mode_unsatisfiable`. The default settles *which* construction applies, never *whether* one exists |
| `security_master_files` | row 25 | The entity fence's binding layer is a lookup. Without a master it refuses to score |
| `theta`, `delta_min_floor` | §14 | Governance. They gate directive admission and registration respectively |

## The security master

CSV with a header. A name column is required; ticker and market columns are used
where present, and column names are matched against common aliases so exchange
listing files can be used as downloaded.

```
Company Name,Ticker,Market
Vodafone Group plc,VOD,LSE
Rio Tinto Limited,RIO,ASX
```

Reference a file as `path`, `path:market`, or `path:market:listed_total`. A
`.json` path loads as an SEC `company_tickers.json`; anything else as CSV.

```bash
mkdir -p master
curl -sA "fntn research <your email>" \
  https://www.sec.gov/files/company_tickers.json -o master/us.json
# UK: londonstockexchange.com/reports?tab=instruments -> master/uk.csv
# AU: asx.com.au/asx/research/ASXListedCompanies.csv  -> master/au.csv
# EU: per-venue lists from Deutsche Boerse and Euronext
# NZ: nzx.com/markets/NZSX                            -> master/nz.csv
```

The SEC file needs no `listed_total`: the regulator's list **is** the
population, so US coverage is complete by construction. Every CSV market needs
one, and EU needs one per venue rather than a combined file, because a combined
file leaves per-venue coverage unknown and unknown is not readable.

**Coverage is measured, not assumed.** An issuer absent from the master is an
episode the fence cannot see, and it will pass silently. A market below
`master_coverage_floor` is not readable for discovery, and a market whose
coverage is *unknown* is also not readable: unknown is not a synonym for
complete. Supply `listed_total` per market, which means one file per market
rather than one combined file.

## Clients

`--transcript path.json` replays a saved payload: deterministic, free, and the
right choice for exercising the machinery. Without it, the sweep calls the model
at temperature zero with the schema forced as a tool call.

**One fence this cannot enforce.** The import fence covers what the discovery
*code* reaches. It says nothing about what the *model* reaches: an agent with web
search or a file reader can look up prices whatever the import graph says. The
production client therefore exposes no tools at all. Wire a tool-using agent into
this interface and the exclusivity construction of §3.7.3 is void.

## Reading the output

- **Drafts blocked on the operator** is the steady state, not a failure.
- **Directives admitted: 0** is expected while `--segment-sessions` is 0, which
  it should remain until the archive exists.
- **Reason-code coverage far below 100%** is expected: one sweep exercises a
  handful of branches. The test suite exercises all of them deliberately.
