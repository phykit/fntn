"""The containment fences.

Three of them, and they are different kinds of object:

* **The query fence** (P59) is a fence over *auditable actions*.  Class-level
  and mechanism-level queries are open before registration; conditional-return
  queries on a directive's own target population are closed until
  ``registered_at`` is stamped.  Enforcement is the research stack's query log,
  because *the operator should be careful* is a fence over nothing.
* **The authority fence** enforces that the agent classifies and the table
  decides.  It is a schema property first -- reserved fields are absent from
  ``Proposal`` -- and a runtime check second, for callers constructing records
  by hand.
* **The import fence** asserts that the discovery path has no read route to
  prices, returns, the forward ledger or the graveyard's outcomes.  Annex A.2
  already uses an import fence to keep model-mediated similarity out of
  peer construction; this is the same instrument pointed at the same class of
  problem.

None of the three reaches the model's weights.  That limit is stated in §10 and
measured, jointly with any genuine skill, by the random-mechanism control arm.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


class QueryKind(str, Enum):
    """Classified *before* the query runs, never after.

    A query classified after it has returned is classified by someone who has
    seen the answer.
    """

    CLASS_LEVEL = "class_level"
    MECHANISM_LEVEL = "mechanism_level"
    #: The closed kind: any query returning returns, performance, or an
    #: outcome conditioned on a population.
    CONDITIONAL_RETURN = "conditional_return"


@dataclass(frozen=True)
class QueryLogEntry:
    at: datetime
    kind: QueryKind
    population_key: str
    text: str
    actor: str


class QueryFence:
    """The query log, and the admissibility rule computed from it."""

    def __init__(self) -> None:
        self._log: List[QueryLogEntry] = []
        self._registered: Dict[str, datetime] = {}

    # -- logging -----------------------------------------------------------

    def record(
        self,
        kind: QueryKind,
        population_key: str,
        text: str,
        actor: str,
        at: Optional[datetime] = None,
    ) -> QueryLogEntry:
        entry = QueryLogEntry(
            at=at or datetime.now(timezone.utc),
            kind=kind,
            population_key=population_key,
            text=text,
            actor=actor,
        )
        self._log.append(entry)
        return entry

    def register_population(self, population_key: str, at: datetime) -> None:
        """Stamp ``registered_at`` for a population.

        After this moment conditional-return queries on that population are
        open, because the pass condition is already committed and cannot be
        moved by what the query returns.
        """

        self._registered.setdefault(population_key, at)

    # -- the rule ----------------------------------------------------------

    def breach(self, population_key: str) -> Optional[QueryLogEntry]:
        """Return the earliest contaminating query, or ``None``.

        A conditional-return query on this population logged before its
        registration makes every directive on it inadmissible.  The rule is
        mechanical: it does not ask whether the operator remembers the answer.
        """

        registered = self._registered.get(population_key)
        for entry in sorted(self._log, key=lambda e: e.at):
            if entry.population_key != population_key:
                continue
            if entry.kind is not QueryKind.CONDITIONAL_RETURN:
                continue
            if registered is None or entry.at < registered:
                return entry
        return None

    def guard(self, kind: QueryKind, population_key: str, actor: str, text: str) -> None:
        """Refuse to *run* a closed query rather than merely recording it.

        Recording a contaminating query and letting it run leaves the operator
        holding the answer and the ledger holding a note about it, which is the
        weaker of the two available designs.
        """

        if kind is QueryKind.CONDITIONAL_RETURN and population_key not in self._registered:
            raise QueryFenceBreach(
                f"conditional-return query on {population_key!r} is closed until "
                "a directive on that population is registered; the query was "
                "refused rather than logged and run"
            )
        self.record(kind, population_key, text, actor)

    @property
    def log(self) -> List[QueryLogEntry]:
        return list(self._log)


class QueryFenceBreach(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Authority fence.
# ---------------------------------------------------------------------------

#: Fields no agent-origin record may carry a value for, with the reason each is
#: reserved.  Kept as data so that §9.5's linter can read the list rather than
#: parsing the code.
RESERVED_FROM_AGENT: Dict[str, str] = {
    "evidence_tier": (
        "computed from field completeness by §3.6.2; an agent that could "
        "declare itself quantified would be choosing its own screen"
    ),
    "delta_min": (
        "the abandonment threshold is the magnitude the operator commits to "
        "before knowing whether it flatters them"
    ),
    "n_min": (
        "the minimum actionable count is registered with the measurement, not "
        "proposed with the idea"
    ),
    "registered_sign": (
        "the operator supplying both the hypothesis and its pass condition is "
        "the endogeneity in one line"
    ),
    "merit": "merit is deterministic checks, not editorial judgement",
    "severity": (
        "a reviewer who can set severity can flatter the denominator, which is "
        "the §0.3 problem in another costume"
    ),
    "priority": (
        "queue admission is by smallest registered span first; a proposed "
        "priority would return ranking to the party that raised the idea"
    ),
    "stream": (
        "for classes outside §3.6.5's table the agent proposes no stream, "
        "having no authority to invent one"
    ),
    "verdict": "the table decides",
}


class AuthorityBreach(RuntimeError):
    pass


def assert_agent_authority(payload: Dict[str, object]) -> Optional[str]:
    """Return the first reserved field the payload populates, or ``None``."""

    for name in RESERVED_FROM_AGENT:
        value = payload.get(name)
        if value not in (None, "", [], {}):
            return name
    return None


# ---------------------------------------------------------------------------
# Import fence.
# ---------------------------------------------------------------------------

#: Modules the discovery path may not reach, directly or transitively.  Names
#: are matched as prefixes so that a submodule cannot slip through.
FORBIDDEN_TO_DISCOVERY: Set[str] = {
    "fntn.data",          # DataSource: delisting-inclusive daily bars
    "fntn.prices",
    "fntn.forward",       # the forward ledger
    "fntn.graveyard",     # kill outcomes
    "fntn.gates",
    "fntn.backtest",
    "fntn.book",
}


class ImportFenceBreach(RuntimeError):
    pass


def discovery_import_closure(
    module_name: str = "fntn.scanner.discovery",
) -> Set[str]:
    """The transitive import closure of ``module_name``, as actually loaded.

    Extracted from ``assert_import_fence`` so a second fence can be built over
    the same closure without a second walk of it. The first fence forbids
    modules that carry prices and outcomes; the second forbids modules that
    **name the trace-filings corpus**, naming being the first step of reading.
    """

    try:
        importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - configuration error
        raise ImportFenceBreach(f"cannot check fence: {exc}") from exc

    seen: Set[str] = set()
    frontier = [module_name]
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        module = sys.modules.get(current)
        if module is None:
            continue
        for attr in vars(module).values():
            candidate = getattr(attr, "__module__", None) or getattr(
                attr, "__name__", None
            )
            if isinstance(candidate, str) and candidate not in seen:
                frontier.append(candidate)
    return seen


def assert_import_fence(module_name: str = "fntn.scanner.discovery") -> None:
    """Assert the discovery module reaches no price or outcome data.

    Raises on the first forbidden prefix in the closure.  Run in the test suite
    and again at process start in ``run.py``: a fence checked only in tests is
    a fence that holds only in tests.
    """

    seen = discovery_import_closure(module_name)
    for name in sorted(seen):
        for forbidden in FORBIDDEN_TO_DISCOVERY:
            if name == forbidden or name.startswith(forbidden + "."):
                raise ImportFenceBreach(
                    f"{module_name} reaches {name}, which carries prices or "
                    "outcomes. Selection and evaluation must share no "
                    "observations, and an import is a read path."
                )


class ReverseImportFenceState(str, Enum):
    """What the reverse fence could establish, and it is three states.

    ``NOT_APPLICABLE`` is not a pass. The item pipeline does not exist in this
    tree yet, so there is nothing to walk, and a check that had nothing to check
    must report that rather than returning clean. §2's rule holds here as
    everywhere: a not-applicable check may never be read as a pass.
    """

    CLEAN = "clean"
    NOT_APPLICABLE = "not_applicable, the item pipeline does not exist here"
    BREACHED = "breached"


def assert_reverse_import_fence() -> ReverseImportFenceState:
    """No item-pipeline module may reach the discovery layer.

    **The fence this codebase already had runs in ONE direction.**
    ``assert_import_fence`` forbids ``discovery.py`` from reaching prices,
    outcomes and gates, so selection cannot see evaluation. **Nothing forbade
    the reverse**, and the reverse is the prohibition ``CLAUDE.md`` states in
    its own words: *agent-origin material may not enter the §3.5 item pipeline,
    because it would re-base §7.1's headline on an agent-selected population.*

    An import is a read path in both directions. A gate module that imported
    ``fntn.scanner.discovery`` for one convenience would put agent-selected
    material one attribute access away from the population §7.1 measures, and
    the existing fence would report clean throughout.

    **Found by phase 8 of the 27 August 2026 batch**, which asked whether the
    import fence covered that direction and established that it did not.

    Returns ``NOT_APPLICABLE`` today, because none of the forbidden modules
    exists yet. *That is the honest answer and it is deliberately not
    ``CLEAN``.* The check is written now so that it is in place before the
    module it guards is, which is the order this project has twice wished it
    had used.
    """

    walked = 0
    for name in sorted(FORBIDDEN_TO_DISCOVERY):
        try:
            importlib.import_module(name)
        except Exception:
            continue
        walked += 1
        closure = discovery_import_closure(name)
        for reached in sorted(closure):
            if reached == DISCOVERY_MODULE or reached.startswith(
                DISCOVERY_MODULE + "."
            ):
                raise ImportFenceBreach(
                    f"{name} reaches {reached}. Agent-origin material may not "
                    "enter the §3.5 item pipeline: it would re-base §7.1's "
                    "headline on an agent-selected population. An import is a "
                    "read path, and this is the direction the original fence "
                    "did not cover."
                )
    return (
        ReverseImportFenceState.CLEAN
        if walked
        else ReverseImportFenceState.NOT_APPLICABLE
    )


#: Named once so both fences agree on what "the discovery layer" is.
DISCOVERY_MODULE = "fntn.scanner.discovery"


@dataclass
class FenceReport:
    """What each fence covers, printed beside every verdict.

    The report exists because the exclusivity claim is a population claim, and
    §Σ.3's second control surface requires a population claim to be stated
    rather than implied.
    """

    #: The registered default construction for this run.
    scoring_mode: str
    #: Directives built per construction.  Displayed rather than summarised to
    #: a single mode, because a run mixing constructions rests on more than one
    #: exclusivity guarantee and a reader must be able to see which.
    scoring_modes: Dict[str, int] = field(default_factory=dict)
    query_log_entries: int = 0
    query_breaches: int = 0
    entity_refusals: int = 0
    partition_refusals: int = 0
    authority_refusals: int = 0
    import_fence_clean: bool = False
    notes: List[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            "Containment (§3.7)",
            f"  default scoring mode         : {self.scoring_mode}",
        ]
        if self.scoring_modes:
            lines.append(
                "  directives by construction   : "
                + ", ".join(f"{k}={v}" for k, v in sorted(self.scoring_modes.items()))
            )
            if "cross_market" in self.scoring_modes:
                lines.append(
                    "    cross_market assumes mechanisms generalise across "
                    "markets whilst episodes do not; §13 row 24 measures it"
                )
            if "pre_archive" in self.scoring_modes:
                lines.append(
                    "    pre_archive assumes mechanisms are stable across the "
                    "regime boundary the archive opens after; §13 row 26 "
                    "measures it, and Brochet is evidence regimes move"
                )
            if "forward_only" in self.scoring_modes:
                lines.append(
                    "    forward_only is disjoint in time by construction and "
                    "assumes nothing; it accumulates slowly, which is its cost"
                )
        lines += [
            f"  import fence                 : {'clean' if self.import_fence_clean else 'BREACHED'}",
            f"  queries logged               : {self.query_log_entries}",
            f"  query-fence refusals         : {self.query_breaches}",
            f"  entity-fence refusals        : {self.entity_refusals}",
            f"  partition-fence refusals     : {self.partition_refusals}",
            f"  authority-fence refusals     : {self.authority_refusals}",
            "  weights                      : not partitionable; residual "
            "measured by the random-mechanism control arm, never removed",
        ]
        lines.extend(f"  note: {n}" for n in self.notes)
        return "\n".join(lines)
