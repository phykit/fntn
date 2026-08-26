# `fntn/scanner`: the agent discovery layer

Reference implementation of §3.7 (proposed v1.14). Drop the `scanner/` package into `fntn/` and the `tests/` file into your existing test tree.

## What it does

Uses agents to locate candidate **mechanisms**, runs each fail-fast through intake ingestion, screens it, maps it to a stream, and produces an observation directive that runs at **zero capital** once the operator supplies the two things only they may supply.

```
corpus (readable partition only)
  → sweep          agent emits mechanisms, never episodes
  → intake         FAIL-FAST: first failed point ends the idea
  → screen         §3.6.3, check 3 binding
  → directive      §3.6.5 lookup; new_subscription logged and deferred
  → registration   blocked on δ_min and a ratified pre-mortem
  → admission      segment arithmetic; machine drafts queue, never displace
```

## What it structurally cannot do

Emit a trading signal, size a position, amend a family, supply a parameter, create a grammar row, or enter the §3.5 item pipeline. A pointer's only reachable output is a directive, and that has not changed because a machine raised it.

## Files

| File | Contents |
|---|---|
| `codes.py` | Reason-code registry. The **only** place a code may be introduced; carries the §8 summary template and resurrection predicate for each, plus the two pre-registered fail-fast orderings |
| `records.py` | `Proposal` (the whole of what an agent may emit), `IntakeRecord`, `Directive`, `Item`, the enums, and the entity detector |
| `fences.py` | Query fence (P59), authority fence, import fence, and the containment report |
| `ingest.py` | The fail-fast runner, both surfaces, plus the deterministic audit-stream sampler |
| `screen.py` | §3.6.3 pointer screen, §3.6.5 stream table, §3.6.8 registration |
| `segment.py` | Design-segment reuse ledger, θ arithmetic, the queue, family-4 counter |
| `discovery.py` | Agent protocol, schema, system prompt, content-hash cache, random-mechanism control arm. **Under the import fence** |
| `ledger.py` | SQLite. Nothing deleted, nothing overwritten |
| `summaries.py` | §8 rejection summaries: rendered from fields, never model-written |
| `run.py` | One scan cycle, and the report |

## Wiring it in

One thing is required from you: an `AgentClient` with `complete(system, user, schema) -> dict`, calling the model at **temperature zero** with `PROPOSAL_SCHEMA` attached. Everything else is deterministic and offline.

```python
from datetime import date
from fntn.scanner import Ledger, Partition, ScanConfig, ScoringMode, scan
from fntn.scanner.discovery import Corpus, GridCell
from fntn.scanner.segment import SegmentPolicy

ledger = Ledger("fntn.db", parameter_hash=PARAM_HASH)
config = ScanConfig(
    parameter_hash=PARAM_HASH,
    default_scoring_mode=ScoringMode.CROSS_MARKET,   # registered default, P74
    exclusivity={                                    # §13 row 22
        "insider_dealing": None,                     # None = use the default
        "buyback": ScoringMode.DISJOINT_PARTITION,   # per-class override
    },
    control_arm_ratio=0.25,           # must exceed zero; §3.7.5
    policy=SegmentPolicy(
        theta=0.25,                       # §14 open decision
        delta_min_floor=25.0,             # §14 open decision
        segment_sessions=378,             # from the archive partition
        calibration_reserve_sessions=189, # §13 holds first claim
    ),
    span_start=date(2024, 1, 1),
)
result = scan(client, [Corpus("tsx", Partition.EXTERNAL, docs)], grid, config, ledger)
print(result.render(ledger))
```

A class **absent** from `exclusivity` is not discoverable and is refused with `scoring_mode_unsatisfiable`. The default settles *which* construction applies, never *whether* one exists.

## Three things that will look like bugs and are not

**Nothing is ever admitted on the first run.** Every draft blocks on `delta_min_absent`, `premortem_unratified` and `literature_search_absent`. That is §3.6.8 working: widening the search must not shorten the fence, so the scanner's steady-state output is a queue of registration-ready drafts waiting on a person.

**`control_arm_ratio=0` raises instead of running.** A sweep with no control arm produces directives whose selection effect nothing can attribute, which makes the layer unfalsifiable; running one is worse than running none. It is refused rather than quietly floored to a working value.

**The coverage report is far below 100% on any single run.** A live sweep exercises a handful of branches; the test suite exercises all 35 deliberately. A code defined and never emitted is an untested branch (§9.4), which is why `test_every_defined_code_is_emitted` is the headline test rather than a completeness nicety.

## Before the first sweep

Four things must be registered, and the layer is not falsifiable without them: **δ**, ***n*ₘᵢₙ**, the **control-arm ratio** and the **seed** (§13 rows 19–20). A kill criterion written after the first result is not a kill criterion.

## Tests

```
python -m pytest fntn/tests/test_scanner.py -q      # 77 tests
```
