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
python -m fntn.scanner sweep     # runs only if the form is complete
```

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
