"""The discovery layer: agents that locate mechanisms, and the control arm.

This module is under the import fence.  It imports records, fences and the
standard library, and nothing that carries prices, returns, forward outcomes or
gate verdicts.  ``fences.assert_import_fence`` walks the transitive closure and
raises if that ever stops being true, and ``run.py`` calls it at process start,
because a fence checked only in tests is a fence that holds only in tests.

**What the agent is for.**  It reads media and filings the exclusivity
construction permits, and emits *mechanisms*: an event class and a one-sentence
definition, on a stated intended population.  It does not name issuers, does not
name dated episodes, does not score merit, does not set its own evidence tier
and does not propose a stream for a class outside the table.  Everything it
emits is a proposal; nothing it emits is a record.

**Why the control arm exists.**  Blinding the agent at read time does not reach
its weights, which contain the price history this system will be evaluated on,
and nothing can.  The residual is therefore measured rather than asserted: for
every N agent proposals, M mechanisms are drawn uniformly from the reachable
event-class by population grid, registered identically and scored identically.
The difference on the evaluation partition is the selection effect, jointly with
any genuine skill.  If agent-proposed pointers do not separate from drawn ones
at the registered delta, the discovery layer is refuted and switched off.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

from .fences import QueryFence, QueryKind
from .records import Origin, Partition, Proposal, READABLE_BY_DISCOVERY

#: The schema the agent is constrained to.  One schema-enforced call per sweep,
#: temperature zero, cached by content hash -- §3.5.2's conventions, applied to
#: a call that is not on the trading path but is on the search path, which is
#: the thing §6.4's fourth family counts.
#:
#: **This is the SKELETON and not the schema sent.** ``event_class`` carries no
#: ``enum`` here because the permitted vocabulary is a registered field
#: (``discoverable_classes``, §13 row 22) and a constant holding a copy of it
#: would be a second place the vocabulary lives.  ``proposal_schema()`` injects
#: the enum from the registration at call time.  The skeleton is what
#: ``schema_sha()`` hashes, which is what keeps that hash non-circular: the
#: class list is already covered by ``discoverable_classes``.
PROPOSAL_SCHEMA_SKELETON: Dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["proposals"],
    "properties": {
        "proposals": {
            "type": "array",
            "maxItems": 25,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "event_definition",
                    "measured_on_intention",
                    "event_class",
                    "source_ref",
                ],
                "properties": {
                    "event_definition": {
                        "type": "string",
                        "maxLength": 400,
                        "description": (
                            "One sentence. The mechanism at class level. No "
                            "issuer, instrument, ticker or dated episode."
                        ),
                    },
                    "measured_on_intention": {
                        "type": "string",
                        "maxLength": 300,
                        "description": (
                            "Market, capitalisation range and filters the claim "
                            "is intended to hold on."
                        ),
                    },
                    "event_class": {
                        "type": "string",
                        "description": (
                            "Classify against the table supplied in the user "
                            "message under 'event_class_table'. Emit "
                            "'unclassified' where no row fits; do not invent a "
                            "class and do not propose a stream."
                        ),
                    },
                    "source_ref": {"type": "string", "maxLength": 500},
                    "mechanism_note": {"type": "string", "maxLength": 800},
                },
            },
        }
    },
}

#: The literal a clerk emits where no row of the supplied table fits.  It is a
#: **verdict with a route**, not a failure: §3.6.5's unclassified branch sends
#: it to the operator to name a stream by hand, and the table then grows by use
#: rather than by anticipation (P51).  It is deliberately a member of the
#: schema's enum so that the model can reach it *within* the closed vocabulary
#: rather than by escaping it.
UNCLASSIFIED = "unclassified"


def proposal_schema(classes: Sequence[str]) -> Dict[str, object]:
    """The skeleton with ``event_class`` closed over the registered classes.

    **This is P75's repair, one layer up.** The entity fence was refuted as a
    pattern over an open vocabulary and rebuilt as a lookup against a closed
    list, because a regulator's name and an issuer's name are both proper
    nouns.  ``event_class`` was the same defect on the same call: a free string
    described as *the fixed table* against a table the model was never shown.
    *The model classifies; the table decides* cannot hold while the model
    cannot see the table, so the table is now both **supplied** (in the user
    message) and **enforced** (as this enum).

    ``unclassified`` is always admitted, and is appended rather than being left
    to the registration to remember: a registration that forgot it would close
    the escape hatch §3.6.5 requires, and would do so silently.
    """

    permitted = sorted({c for c in classes if c}) + [UNCLASSIFIED]
    schema = copy.deepcopy(PROPOSAL_SCHEMA_SKELETON)
    props = schema["properties"]["proposals"]["items"]["properties"]
    props["event_class"] = dict(props["event_class"], enum=permitted)
    return schema


def schema_sha() -> str:
    """Digest of the schema skeleton, for the parameter object.

    The skeleton and not the composed schema, so that the digest does not move
    when the registered class list moves: that list is ``discoverable_classes``
    and is hashed already.  Two fields, one fact each.
    """

    return hashlib.sha256(
        json.dumps(PROPOSAL_SCHEMA_SKELETON, sort_keys=True).encode()
    ).hexdigest()[:16]


def prompt_sha() -> str:
    """Digest of the system prompt, for the parameter object.

    **Registered because the prompt decides what the layer produces.** §3.7.4
    says the intake ordering is pre-registered and sits in the parameter
    object; the prompt determines the population that ordering is applied to,
    and it sat in a module constant where a change would move every future
    sweep's output while moving no hash and leaving no row.  That is B15's
    defect -- the model pin as a default string -- in a larger field, and it is
    closed here on the same terms: registered rather than edited carefully.
    """

    return hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:16]

SYSTEM_PROMPT = """\
You are a clerk, not an analyst. Your entire job is to read the supplied \
material and emit candidate mechanisms against a fixed schema.

Rules, all binding:

1. Emit MECHANISMS, never EPISODES. Write "clusters of same-day open-market \
purchases by multiple directors of one issuer" and never "what happened to a \
named company in a named month". Any issuer name, ticker, instrument \
identifier, corporate designator, named month with a year, quarter label or \
bare four-digit year causes the whole proposal to be discarded.
2. Classify the event class against the table supplied in the user message \
under "event_class_table". That table is the whole of the permitted \
vocabulary and the schema rejects anything outside it. Where no row fits, \
emit exactly "unclassified": that is a real verdict which routes to the \
operator to map a stream, and it is not a way of declining to choose between \
rows that do fit. You have no authority to invent a class or to name a feed.
3. Do not score merit, promise, strength, confidence, priority or severity. Do \
not state an expected effect size, a horizon, or a threshold. Those are \
decided elsewhere and a proposal that carries them is discarded whole.
4. State the intended population plainly: market, capitalisation range, \
filters. An intention, not a measurement.
5. You have no access to prices, returns or outcomes, and you must not reason \
from any you happen to recall. If a candidate mechanism is interesting to you \
only because you remember that it worked, that is the failure mode this \
instruction exists to prevent; emit it only if the mechanism stands on its own.

Return only the schema. Anything else is discarded."""


class AgentClient(Protocol):
    """Injectable so the layer is testable and the fence is enforceable.

    A production implementation calls the model at temperature zero with the
    schema attached.  It is a ``Protocol`` rather than a concrete class so that
    the test suite can exercise every branch without a network call, and so that
    the module carries no client dependency the import fence would have to
    reason about.
    """

    def complete(
        self, system: str, user: str, schema: Dict[str, object]
    ) -> Dict[str, object]:  # pragma: no cover - interface
        ...


@dataclass
class Corpus:
    """Material a discovery sweep may read.

    ``partition`` is asserted here rather than inferred later.  A corpus in a
    scored partition is refused at construction, so an agent is never handed
    material it should not see and then relied upon to ignore it.
    """

    corpus_id: str
    partition: Partition
    documents: Sequence[str]

    def __post_init__(self) -> None:
        if self.partition not in READABLE_BY_DISCOVERY:
            raise PermissionError(
                f"corpus {self.corpus_id!r} sits in the "
                f"{self.partition.value} partition, which a discovery agent may "
                "not read. Selection and evaluation must share no observations."
            )


class ProposalCache:
    """Content-hash cache, mirroring §3.5.2.

    A sweep over unchanged material returns the same proposals, so a rerun does
    not inflate the family-4 proposal count with duplicates of a search that was
    already counted.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, object]] = {}

    @staticmethod
    def key(system: str, user: str) -> str:
        return hashlib.sha256(f"{system}\x00{user}".encode()).hexdigest()

    def get(self, k: str) -> Optional[Dict[str, object]]:
        return self._store.get(k)

    def put(self, k: str, value: Dict[str, object]) -> None:
        self._store[k] = value


@dataclass
class SweepResult:
    proposals: List[Proposal]
    cache_hit: bool
    cache_key: str
    #: Elements of the returned payload the schema does not describe, as
    #: ``(index, type name)``. **Counted, never repaired.** See `sweep`.
    off_schema: List[tuple] = field(default_factory=list)
    #: Set when the ``proposals`` value was not an array at all, as
    #: ``(type name, length)``. **One refusal for the whole call**, and the
    #: distinction from ``off_schema`` is not tidiness: see `sweep`.
    payload_not_a_list: Optional[tuple] = None


def sweep(
    client: AgentClient,
    corpus: Corpus,
    fence: QueryFence,
    cache: ProposalCache,
    actor: str = "discovery_agent",
    now: Optional[datetime] = None,
    classes: Optional[Sequence[str]] = None,
) -> SweepResult:
    """One discovery sweep over one corpus.

    Every read is logged to the query fence as a mechanism-level query.  A
    sweep cannot log a conditional-return query, because it has no path to
    returns; the fence entry exists so that the query log is a complete record
    of the search rather than a record of the operator's half of it.

    ``classes`` is the registered discoverable vocabulary (§13 row 22).  It is
    supplied to the model in the user message and enforced as the schema's
    enum.  Defaulting it to empty is deliberate: a caller that does not pass it
    gets a sweep whose only reachable class is ``unclassified``, which is the
    pre-repair behaviour and is now visible as such rather than looking like a
    fact about the corpus.
    """

    now = now or datetime.now(timezone.utc)
    # **The table the prompt has always referred to, now actually supplied.**
    # Rule 2 said *classify against the fixed table* and the table was never in
    # the call: the user message carried the corpus and nothing else, and
    # `event_class` was a free string. `unclassified` was therefore not the
    # fallback branch but the only branch reachable on the instructions given,
    # and the run of record's six-of-six intake kill followed by construction
    # rather than from anything about the corpus, the model or the layer.
    permitted = sorted({c for c in (classes or ()) if c})
    schema = proposal_schema(permitted)
    user = json.dumps(
        {
            "corpus_id": corpus.corpus_id,
            "event_class_table": permitted + [UNCLASSIFIED],
            "documents": list(corpus.documents),
        },
        sort_keys=True,
    )
    # The key covers the schema too, because two sweeps run under different
    # permitted vocabularies are different calls and a cache that conflated
    # them would replay the narrower one's answer at the wider one.
    key = ProposalCache.key(SYSTEM_PROMPT, user + json.dumps(schema, sort_keys=True))

    fence.record(
        kind=QueryKind.MECHANISM_LEVEL,
        population_key=f"corpus:{corpus.corpus_id}",
        text=f"discovery sweep over {len(corpus.documents)} documents",
        actor=actor,
        at=now,
    )

    cached = cache.get(key)
    if cached is not None:
        payload, hit = cached, True
    else:
        payload = client.complete(SYSTEM_PROMPT, user, schema)
        cache.put(key, payload)
        hit = False

    proposals: List[Proposal] = []
    off_schema: List[tuple] = []
    not_a_list: Optional[tuple] = None

    raw_proposals = payload.get("proposals", [])
    # **A string is iterable, and that is the whole reason this branch exists
    # separately from the one below.** On the first live sweep, two of three
    # families returned `proposals` as a JSON *string*. Iterating it walked its
    # characters, so a single malformed reply produced 5,607 and 2,869
    # refusals, the funnel reported 8,484 proposals raised, and **a search that
    # located four mechanisms looked like a search that located eight
    # thousand**. Rule 5 says counting is mechanical because intent flatters
    # the denominator; nothing intended that denominator, and it was flattered
    # anyway.
    #
    # So a non-array `proposals` is ONE refusal for the whole call. The call
    # yielded no mechanism, which is one fact about one call.
    if not isinstance(raw_proposals, list):
        not_a_list = (type(raw_proposals).__name__, len(raw_proposals)
                      if hasattr(raw_proposals, "__len__") else -1)
        raw_proposals = []

    for index, raw in enumerate(raw_proposals):
        # **A forced tool call is not a validated tool call.** `tool_choice`
        # makes the model call the tool; it does not make the arguments
        # conform, and `strict` is not set (that is a registered decision, see
        # `docs/DECISION_structured_outputs_2026-08-27.md`). The first live
        # sweep returned a bare string here and this loader raised
        # `AttributeError` part-way through the second family, losing both the
        # remaining families and the money already spent on them.
        #
        # **Discarded whole and never repaired.** A bare string could be coaxed
        # into `event_definition`, and that would be the loader guessing which
        # field the clerk meant, which is the loader doing the clerk's work on
        # material the clerk did not put in a field.
        if not isinstance(raw, dict):
            off_schema.append((index, type(raw).__name__))
            continue
        proposals.append(
            Proposal(
                event_definition=str(raw.get("event_definition", "")),
                measured_on_intention=str(raw.get("measured_on_intention", "")),
                event_class=str(raw.get("event_class", "")),
                source_ref=str(raw.get("source_ref", "")),
                source_partition=corpus.partition,
                corpus_id=corpus.corpus_id,
                mechanism_note=str(raw.get("mechanism_note", "")),
                origin=Origin.AGENT,
                raised_at=now,
            )
        )
    return SweepResult(
        proposals=proposals, cache_hit=hit, cache_key=key,
        off_schema=off_schema, payload_not_a_list=not_a_list,
    )


def raw_payloads(payload: Dict[str, object]) -> List[Dict[str, object]]:
    """The agent's untouched output, for the authority fence to inspect.

    The fence must see what the model actually returned, including any field it
    invented outside the schema, rather than the tidied ``Proposal`` the loader
    built.  A proposal that set its own threshold and had the field silently
    dropped on the way in would pass a fence designed to catch exactly that.
    """

    raw = payload.get("proposals", [])
    if not isinstance(raw, list):
        return []
    return [dict(p) for p in raw if isinstance(p, dict)]


# ---------------------------------------------------------------------------
# The random-mechanism control arm.
# ---------------------------------------------------------------------------


@dataclass
class GridCell:
    event_class: str
    population: str
    definition: str


def draw_control_mechanisms(
    grid: Sequence[GridCell],
    count: int,
    seed: int,
    corpus_partition: Partition = Partition.EXTERNAL,
    now: Optional[datetime] = None,
    corpus_id: str = "",
) -> List[Proposal]:
    """Draw mechanisms uniformly from the reachable grid.

    The seed is pre-registered and recorded with the draw, so the control arm is
    replayable and cannot be redrawn after the agent arm's result is known --
    the same discipline §7.5 applies to the placebo, for the same reason.
    """

    now = now or datetime.now(timezone.utc)
    rng = random.Random(seed)
    chosen = [rng.choice(list(grid)) for _ in range(count)]
    return [
        Proposal(
            event_definition=cell.definition,
            measured_on_intention=cell.population,
            event_class=cell.event_class,
            source_ref=f"grid:{cell.event_class}",
            source_partition=corpus_partition,
            corpus_id=corpus_id,
            mechanism_note="drawn uniformly from the reachable grid",
            drawn_from_grid_cell=f"{cell.event_class}|{cell.population}",
            origin=Origin.RANDOM_CONTROL,
            raised_at=now,
        )
        for cell in chosen
    ]


@dataclass
class ControlArmVerdict:
    """The scanner's own falsification instrument.

    Pre-registered before the first sweep: if agent-proposed pointers do not
    separate from drawn ones by at least ``delta`` at ``n_min``, the discovery
    layer is refuted.  Reported in the same three-verdict idiom as §3.6.8, so
    that failing for want of power says so rather than passing by it.
    """

    agent_n: int
    control_n: int
    n_min: int
    delta: float
    separation: Optional[float] = None

    def verdict(self) -> str:
        if self.agent_n < self.n_min or self.control_n < self.n_min:
            return "undetermined_at_budget"
        if self.separation is None:
            return "undetermined_at_budget"
        if self.separation >= self.delta:
            return "agent_selection_carries_information"
        if abs(self.separation) < self.delta:
            return "killed_negligible: discovery layer refuted, switch it off"
        return "agent_selection_anti_informative: switch it off"
