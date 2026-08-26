"""§3.6.3 merit screen (pointer branch), §3.6.5 stream lookup, §3.6.8 registration.

Three deterministic stages between a surviving intake record and a registered
directive.  None of them is a judgement: check 3 is a lookup, the stream table
is a lookup, and registration is a completeness test over fields only the
operator may supply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from . import summaries
from .records import (
    Directive,
    IntakeRecord,
    Origin,
    PreMortem,
    Refusal,
    ScoringMode,
    SegmentSpan,
    StreamProvenance,
    StreamStatus,
)


# ---------------------------------------------------------------------------
# §3.6.5 -- the stream table.  In the parameter object; adding a row is a
# specification version.
# ---------------------------------------------------------------------------

STREAM_TABLE: Dict[str, Tuple[str, StreamStatus]] = {
    "insider_dealing": ("RNS PDMR notifications; EDGAR Form 4", StreamStatus.SUBSCRIBED),
    "major_holdings_change": ("RNS TR-1; EDGAR 13D/G full text", StreamStatus.CATEGORY_FILTER),
    "buyback": ("RNS Transaction in Own Shares", StreamStatus.CATEGORY_FILTER),
    "earnings_event": ("RNS results categories; earnings calendars", StreamStatus.SUBSCRIBED),
    "index_reconstitution": ("FTSE Russell review calendar", StreamStatus.NEW_SUBSCRIPTION),
    "short_interest_disclosure": ("FCA net short positions register", StreamStatus.MANUAL_OBSERVATION),
    "clinical_procurement": ("Subscribed calendars", StreamStatus.SUBSCRIBED),
}

#: §3.6.3's five checks.  Checks 1 and 4 have no input to consume on a pointer
#: and report not-applicable; a not-applicable check may never be read as a
#: pass, which is why it is recorded rather than skipped.
POINTER_CHECKS = {
    1: "cost_survival",
    2: "population_overlap",
    3: "event_observability",
    4: "horizon_admissibility",
    5: "evidence_quality",
}


@dataclass
class ScreenResult:
    intake_id: str
    passed: bool
    check_states: Dict[int, str] = field(default_factory=dict)
    refusals: List[Refusal] = field(default_factory=list)
    #: §3.6.6 rule 4: evidence produced by a machine-raised directive routes
    #: advisory-only under check 5, exactly as ``single_study`` does.
    provenance_route: str = "advisory_only"


def screen_pointer(record: IntakeRecord) -> ScreenResult:
    """The pointer tier's screen.  Check 3 is the whole of it."""

    result = ScreenResult(intake_id=record.intake_id, passed=True)

    result.check_states[1] = "not_applicable_pointer_tier"
    result.check_states[4] = "not_applicable_pointer_tier"
    result.refusals.append(
        summaries.render(
            "check_not_applicable_pointer_tier",
            record.intake_id,
            {"event_class": record.event_class},
        )
    )

    # Check 2: measured_on recorded as an intention, tradable_on as unmeasured.
    record.tradable_on = record.tradable_on or "unmeasured"
    result.check_states[2] = (
        f"recorded: measured_on={record.measured_on}, tradable_on={record.tradable_on}"
    )

    # Check 3: binding.
    known = record.event_class in STREAM_TABLE
    unclassified = record.event_class == "unclassified"
    if not known and not unclassified:
        result.passed = False
        result.check_states[3] = "failed"
        result.refusals.append(
            summaries.render(
                "no_observable_stream",
                record.intake_id,
                {"event_class": record.event_class},
            )
        )
        return result
    result.check_states[3] = "pass" if known else "unclassified_pending_operator"

    # Check 5: provenance routing.
    if record.origin in (Origin.AGENT, Origin.RANDOM_CONTROL):
        result.provenance_route = "advisory_only (agent_generated)"
    elif record.origin is Origin.OPERATOR:
        result.provenance_route = "advisory_only (self_generated)"
    result.check_states[5] = result.provenance_route
    return result


# ---------------------------------------------------------------------------
# §3.6.5 -- directive construction.
# ---------------------------------------------------------------------------


@dataclass
class DirectiveDraft:
    directive: Optional[Directive]
    refusals: List[Refusal] = field(default_factory=list)
    #: Every declined, deferred or displaced directive is logged with the feed
    #: it named.  The distribution of named-but-unsubscribed feeds is reported
    #: at freeze beside the roster decision: persistent mismatch between the
    #: ideas raised and the streams held is evidence the roster is wrong, and
    #: the freeze is where rosters change.
    declined_feed: Optional[str] = None


def build_directive(
    record: IntakeRecord,
    directive_id: str,
    span: SegmentSpan,
    n_min: int,
    scoring_mode: ScoringMode,
    manual_capacity_remaining: int = 0,
) -> DirectiveDraft:
    if record.event_class == "unclassified":
        return DirectiveDraft(
            directive=None,
            refusals=[
                summaries.render(
                    "stream_unmapped_pending_operator",
                    record.intake_id,
                    {"event_class": record.event_class},
                )
            ],
            declined_feed=None,
        )

    stream, status = STREAM_TABLE[record.event_class]

    if status is StreamStatus.NEW_SUBSCRIPTION:
        return DirectiveDraft(
            directive=None,
            refusals=[
                summaries.render(
                    "stream_requires_new_subscription",
                    record.intake_id,
                    {"stream": stream, "event_class": record.event_class},
                )
            ],
            declined_feed=stream,
        )

    if status is StreamStatus.MANUAL_OBSERVATION and manual_capacity_remaining <= 0:
        return DirectiveDraft(
            directive=None,
            refusals=[
                summaries.render(
                    "manual_observation_capacity_exhausted",
                    record.intake_id,
                    {"stream": stream, "capacity": manual_capacity_remaining},
                )
            ],
            declined_feed=stream,
        )

    return DirectiveDraft(
        directive=Directive(
            directive_id=directive_id,
            intake_id=record.intake_id,
            origin=record.origin,
            event_class=record.event_class,
            measured_on=record.measured_on,
            stream=stream,
            stream_status=status,
            stream_provenance=StreamProvenance.TABLE,
            scoring_mode=scoring_mode,
            span=span,
            n_min=n_min,
        )
    )


# ---------------------------------------------------------------------------
# §3.6.8 step 4 -- registration, in four parts.
# ---------------------------------------------------------------------------


@dataclass
class RegistrationInputs:
    """What only the operator may supply.

    Every field here is absent from ``Proposal`` by design.  The scanner's
    honest output is a queue of drafts blocked on exactly these, and that is not
    a defect in the scanner: widening the search must not shorten the fence.
    """

    delta_min: Optional[float] = None
    registered_sign: Optional[int] = None
    pre_mortem: Optional[PreMortem] = None
    literature_search_ref: Optional[str] = None


def register(
    directive: Directive,
    inputs: RegistrationInputs,
    delta_min_floor: float,
    now: datetime,
) -> List[Refusal]:
    """Attempt registration.  Returns the refusals blocking it, empty on success.

    Note this is *not* fail-fast: registration reports every missing part at
    once.  The fail-fast rule exists to stop spending compute on an idea that
    has already died; registration spends no compute and its output is a
    worklist for a person, and handing someone one blocker at a time when four
    are known is a worse deliverable, not a purer one.
    """

    blocking: List[Refusal] = []
    fields = {"directive_id": directive.directive_id}

    if inputs.delta_min is None:
        blocking.append(
            summaries.render("delta_min_absent", directive.directive_id, fields)
        )
    elif inputs.delta_min < delta_min_floor:
        blocking.append(
            summaries.render(
                "delta_min_below_floor",
                directive.directive_id,
                {
                    **fields,
                    "delta_min": inputs.delta_min,
                    "delta_min_floor": delta_min_floor,
                },
            )
        )

    pm = inputs.pre_mortem
    if pm is None:
        blocking.append(
            summaries.render(
                "premortem_unratified", directive.directive_id, fields
            )
        )
    else:
        if not pm.measurable_on_available_data:
            blocking.append(
                summaries.render(
                    "confound_unmeasurable",
                    directive.directive_id,
                    {**fields, "confound": pm.confound},
                )
            )
        if not pm.ratified_by_operator:
            blocking.append(
                summaries.render(
                    "premortem_unratified", directive.directive_id, fields
                )
            )

    if not inputs.literature_search_ref:
        blocking.append(
            summaries.render(
                "literature_search_absent", directive.directive_id, fields
            )
        )

    if blocking:
        return blocking

    directive.delta_min = inputs.delta_min
    directive.registered_sign = inputs.registered_sign
    directive.pre_mortem = inputs.pre_mortem
    directive.literature_search_ref = inputs.literature_search_ref
    directive.registered_at = now
    return []
