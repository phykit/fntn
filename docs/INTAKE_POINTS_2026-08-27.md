# The twelve intake points: which are exercised, and what would exercise the rest

**27 August 2026. Phase 6 of the resumed batch.**

The ladder is `INTAKE_ORDER` in `src/fntn/scanner/codes.py`. **The ordering is
part of the parameter object**, and `IngestRunner.__init__` refuses a check
defined outside it, because a different order produces a different reason-code
distribution over the same corpus.

**Two populations exist and they disagree, so both are reported.** The **live
SQLite ledger** holds 24 proposals under hash `a06400ef28ebb54c`. **§13 row 23's
re-based reading** is taken over `docs/labelled_proposals.json`: 36 drawn
subjects and 6 authored probes. *A point exercised in one and not the other is
not a contradiction; it is two different questions.*

---

## The twelve

| Pos | Point | Live ledger | Drawn arm (row 23) | Reachable at all? |
|---|---|---|---|---|
| 1 | `agent_overreached_schema` | no | no | **no** |
| 2 | `security_master_unavailable` | no | no | yes |
| 3 | `proposal_names_entity` | **yes, 3** *(agent arm)* | **no** *(probes only, 5)* | yes |
| 4 | `discovery_partition_violation` | no | no | **no** |
| 5 | `event_definition_absent` | no | no | yes |
| 6 | `measured_on_absent` | no | no | yes |
| 7 | `duplicate_of_open_pointer` | **yes, 8** *(control arm, all of them)* | no | yes |
| 8 | `registered_at_unstampable` | no | no | **no** |
| 9 | `scoring_mode_unsatisfiable` | **yes, 1** *(agent arm)* | **yes, 8** | yes |
| 10 | `source_inaccessible` | no | no | **no** |
| 11 | `provenance_tag_absent` | no | no | **not as a first failure** |
| 12 | `claim_provenance_recollection` | no | no | yes |

**Three of twelve exercised in the live ledger. One of twelve on drawn
material.** The four marked unreachable are the four §13 row 23 already names as
remediation candidates rather than measurement gaps.

---

## What would exercise each unexercised point

**Position 1, `agent_overreached_schema`.** The authority fence has **no
input**: `raw_payloads()` is called from nowhere, so nothing is ever offered to
it. **What would exercise it:** a discovery-agent response carrying fields
outside the declared schema, delivered through a route that actually calls
`raw_payloads()`. Until that call exists, no material of any kind reaches it.
*This is a wiring defect, and no corpus repairs it.*

**Position 2, `security_master_unavailable`.** **What would exercise it:** a
sweep over a discovery market whose security-master file is absent, or present
below the 0.95 coverage floor. §13 row 25 is PART CLOSED on the US alone, at
10,388 issuers and 100% by construction; **UK, AU, EU and NZ have no master
file at all**, so registering any one of them as a retrieval route exercises
this point on the first subject.

**Position 3, `proposal_names_entity`, exercised but by which arm matters.** In
the live ledger three **agent-origin** proposals trip it. On row 23's drawn
material it never fires and the five position-3 refusals are **authored probes**,
which are built to trip a named route, so their abort position is a property of
the probe and not of the flow. **What would exercise it on drawn material:** an
agent naming a company rather than a mechanism, which the drawn population has
not done in 36 subjects.

**Position 4, `discovery_partition_violation`.** Unreachable: `Corpus.__post_init__`
refuses a contradictory partition **at construction**, so nothing reaches the
intake ladder carrying one. **What would exercise it:** relaxing the
constructor's refusal, which would be a worse system for a better statistic.
*A check behind an earlier and stricter check is a check that reports nothing,
and that is the correct trade here.*

**Positions 5 and 6, `event_definition_absent` and `measured_on_absent`.** The
discovery schema in `discovery.py` requires both fields, so a conforming agent
response always carries them. **What would exercise them:** an agent failure
mode that returns the field empty rather than absent, or **non-agent material
entering the same ladder**, which §3.5's fence forbids for the item pipeline.

**Position 7, `duplicate_of_open_pointer`, and its exercise is an artefact.**
All eight live-ledger firings are on the **random-control arm**, and they are
duplicates of pointers **the agent arm opened first in the same run**. **What
would exercise it on the agent arm:** two agent proposals on one
`(event_class, measured_on)` pair, which the drawn population has not produced.
*See the pooling finding below: this point is the whole reason it matters.*

**Position 8, `registered_at_unstampable`.** Unreachable: **the query log is
written and never read back**, and each scan builds a fresh fence, so no scan
can know that a prior scan queried the same population key. **What would
exercise it:** reading the query log back across scans, which is a change to
what the fence knows and not merely to what it is shown.

**Position 10, `source_inaccessible`.** Unreachable: the resolver defaults to
`bool(ref)`, so **retrieval is never attempted** and a citation is treated as
resolved because it is non-empty. **What would exercise it:** a resolver that
attempts retrieval. *The machinery to do it exists in this tree*:
`trace_filings.verify_response` checks that a response **is** the document, by
byte floor and structural marker. It is on the wrong side of a fence, by design.

**Position 11, `provenance_tag_absent`.** It can emit and **can never be a first
failure**: a proposal with no source has no provenance tag either, so position
10 fires first on the same trigger. **What would exercise it as a first
failure:** material with a **present, resolvable** `source_ref` and **no §0.5
provenance tag**. No configured path produces that combination today.

**Position 12, `claim_provenance_recollection`.** **What would exercise it:**
a proposal whose claim provenance is tagged `recollection` under §0.5. The
discovery agent has never emitted one, and §0.5 ranks it as blocking, so it is
a code waiting for a source class the corpus does not contain.

---

## Would the Form 4 block exercise any of them? **No. Not one.**

**And the reason is the fence, not the material.** `corpora/_trace_filings` is
underscore-prefixed; `Corpus.__post_init__` refuses **any** underscore-prefixed
path component, so no registration route can resolve there; `corpusio.corpus_documents`
returns nothing for such a route; and `discovery.py`'s import closure may not so
much as name the path. **A Form 4 cannot reach the intake ladder by any route.**

**What it would exercise if the fence were removed, and this is why it is not.**
A Form 4 names **an issuer, a reporting owner and a transaction date**. That is
precisely the material **position 3's entity fence exists to keep out of a
proposal**. `corpora/us` is rule text and names no company; this corpus names
little else. **So the one point the block would light up is the one whose firing
would mean the fence had failed.**

*Two points it would exercise incidentally and only through the fetcher, which
is outside the intake pipeline:* position 10's retrieval, which
`verify_response` performs properly, and position 2's master lookup, which the
US master would satisfy rather than fail. **Neither reaches the ladder.**

---

## The third pooling site, and it is in code rather than in a published reading

**P77 and P79 found row 21 pooling a drawn arm with an authored one. P95 found
row 23 doing the same. This is the third, on a third axis.**

**`RunReport._abort_positions` in `src/fntn/scanner/report.py` selects every
intake refusal with no filter on `origin`.** It therefore pools:

- the **agent arm**, which is the thing under test, and
- the **random-mechanism control arm**, which §Σ.4 provides in order to be
  compared *against* the agent arm.

**Pooling the control arm into the treatment arm's distribution destroys the
comparison the control arm exists to enable.** It is the same error as the
previous two and it is worse in one respect: **those were readings published in
a document; this one is rendered into every run report, from the ledger, on
every run.**

**What the pooling hides, on the live ledger:**

| | n | intake kill rate | Where the failures fall |
|---|---|---|---|
| **Agent arm** | 12 | **4/12 = 33.3%** | position 3 (×3), position 9 (×1) |
| **Random-control arm** | 12 | **8/12 = 66.7%** | **position 7 (×8), and nowhere else** |
| *Pooled, as published* | 24 | *12/24 = 50.0%* | *positions 3, 7 and 9* |

**The two arms do not share a single failure position.** The pooled 50% is a
number describing no arm, and position 7's eight firings are an **artefact of
the control arm running second**: those are duplicates of pointers the agent arm
opened in the same run. **Pooling therefore imports a scheduling property of the
control design into a figure that claims to describe the intake flow**, and it
makes position 7 look like the dominant intake kill.

**Corrected in the same commit as this finding**, following the precedent P79
and P95 set: the report splits the distribution by `origin`, and the pooled
figure is retained beside it and labelled as not a reading. `§12.1` row P105.
