"""Fail-fast ingestion.

The rule this module exists for: **as soon as an ingestion point fails, stop and
move to the next idea.**  It is applied on two surfaces with two pre-registered
orderings, and it comes with one obligation that is not optional.

**The obligation.**  An abort that writes nothing shrinks §7.1's denominator
silently.  The headline instrument measures funnel depth against forward return
*across the entire intake*, so an idea that vanishes at ingestion without a
ledger row does not make the funnel look clean, it makes the funnel
unmeasurable.  Every abort here therefore writes a refusal with its reason code,
the set it was measured on, and a rendered §8 summary, and the subject stays in
the ledger with its forward window tracked where one exists.  Fail-fast is a
compute discipline, never a bookkeeping one.

**The censoring, and its antidote.**  Stopping at the first failure censors the
reason-code distribution: a code that only ever fires at position nine is
invisible while position three keeps firing.  §7.2's answer for gates applies
unchanged to ingestion -- a pre-registered audit fraction runs the **full
panel** regardless of early failures, and every attribution statistic computes
there exclusively.  The audit sample is drawn deterministically from a hash of
the subject identity and the parameter hash, so it is replayable and cannot be
redrawn after the answer is known.  §9.4's trace harness runs full-panel always,
for the reason it already gives: batch mode terminates at the first hard kill
and therefore hides every downstream defect.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import summaries
from .codes import INTAKE_ORDER, OBSERVATION_ORDER
from .fences import (
    QueryFence,
    RESERVED_FROM_AGENT,
    assert_agent_authority,
)
from .records import (
    DEFAULT_FENCE,
    Directive,
    EntityFence,
    Item,
    Origin,
    Partition,
    Proposal,
    READABLE_BY_DISCOVERY,
    Refusal,
    entity_mentions,
)

#: A check returns ``None`` to pass, or ``(code, fields)`` to refuse.
CheckResult = Optional[Tuple[str, Dict[str, object]]]


class Mode(str, Enum):
    FAIL_FAST = "fail_fast"
    FULL_PANEL = "full_panel"


@dataclass
class IngestOutcome:
    """What one subject's pass through an ingestion surface produced."""

    subject_id: str
    surface: str
    mode: Mode
    passed: bool
    #: Ordered names of the checks actually applied.  A check not listed was
    #: not reached, and a check never reached is a check never tested.
    checks_reached: List[str] = field(default_factory=list)
    refusals: List[Refusal] = field(default_factory=list)
    #: Position in the pre-registered ordering at which the first failure
    #: occurred, or ``None``.  Reported as a distribution: a surface whose
    #: failures cluster at position one is a surface whose later points have
    #: never been exercised.
    failed_at_position: Optional[int] = None

    @property
    def first_refusal(self) -> Optional[Refusal]:
        return self.refusals[0] if self.refusals else None


class Runner:
    """Applies an ordered check sequence under one of two modes."""

    def __init__(
        self,
        surface: str,
        order: Sequence[str],
        checks: Dict[str, Callable[[object], CheckResult]],
        audit_fraction: float = 0.10,
        parameter_hash: str = "unfrozen",
    ) -> None:
        missing = [c for c in order if c not in checks]
        if missing:
            raise ValueError(
                "ordering names checks that do not exist: " + ", ".join(missing)
            )
        extra = [c for c in checks if c not in order]
        if extra:
            raise ValueError(
                "checks defined outside the pre-registered ordering: "
                + ", ".join(extra)
                + " -- the ordering is part of the parameter object because a "
                "different order produces a different reason-code distribution "
                "for the same corpus"
            )
        self.surface = surface
        self.order = list(order)
        self.checks = checks
        self.audit_fraction = audit_fraction
        self.parameter_hash = parameter_hash

    # -- the audit sample --------------------------------------------------

    def in_audit_stream(self, subject_id: str) -> bool:
        """Deterministic, replayable, and drawn before the answer is known."""

        digest = hashlib.sha256(
            f"{self.parameter_hash}|{self.surface}|{subject_id}".encode()
        ).hexdigest()
        return (int(digest[:8], 16) / 0xFFFFFFFF) < self.audit_fraction

    # -- the run -----------------------------------------------------------

    def run(
        self,
        subject_id: str,
        subject: object,
        mode: Optional[Mode] = None,
    ) -> IngestOutcome:
        if mode is None:
            mode = (
                Mode.FULL_PANEL
                if self.in_audit_stream(subject_id)
                else Mode.FAIL_FAST
            )
        outcome = IngestOutcome(
            subject_id=subject_id, surface=self.surface, mode=mode, passed=True
        )
        for position, name in enumerate(self.order, start=1):
            outcome.checks_reached.append(name)
            result = self.checks[name](subject)
            if result is None:
                continue
            code, fields = result
            fields.setdefault("attempted_at", datetime.now(timezone.utc).isoformat())
            outcome.refusals.append(summaries.render(code, subject_id, fields))
            outcome.passed = False
            if outcome.failed_at_position is None:
                outcome.failed_at_position = position
            if mode is Mode.FAIL_FAST:
                # The whole point: stop here, and start the next idea.
                break
        return outcome


# ---------------------------------------------------------------------------
# Surface A -- intake ingestion of a discovery proposal.
# ---------------------------------------------------------------------------


@dataclass
class IntakeContext:
    """Everything the intake checks read.  Deliberately small."""

    proposal: Proposal
    raw_payload: Dict[str, object]
    fence: QueryFence
    #: Whether ``source_ref`` resolved.  Retrieval happens before the checks
    #: run, so that no check performs network I/O at decision time.
    source_resolved: bool
    #: (event_class, measured_on) pairs already carrying an open pointer.
    open_pairs: Dict[Tuple[str, str], Dict[str, object]]
    #: Event classes for which some readable exclusivity construction exists.
    exclusivity_available: Dict[str, str]
    claim_provenance: Dict[str, Optional[str]] = field(default_factory=dict)
    #: The configured entity fence.  Its binding layer is a lookup against the
    #: security master; without one the check refuses to score.
    entity_fence: EntityFence = DEFAULT_FENCE


def _population_key(p: Proposal) -> str:
    return f"{p.event_class}|{p.measured_on_intention}"


def build_intake_checks() -> Dict[str, Callable[[object], CheckResult]]:
    """The ordered intake points, one callable per reason code.

    The ordering is by kill rate per unit of compute, subject to one override:
    the three fences run before anything expensive, because a proposal that
    breaches a fence must not have its document opened, its duplicates
    searched, or its exclusivity construction computed.  A cheap refusal that
    has already read the thing it refuses is not cheap.
    """

    def source_inaccessible(ctx: IntakeContext) -> CheckResult:
        if ctx.source_resolved:
            return None
        return (
            "source_inaccessible",
            {"source_ref": ctx.proposal.source_ref, "detail": "no response at cited location"},
        )

    def event_definition_absent(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.event_definition and ctx.proposal.event_definition.strip():
            return None
        return ("event_definition_absent", {})

    def measured_on_absent(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.measured_on_intention and ctx.proposal.measured_on_intention.strip():
            return None
        return ("measured_on_absent", {})

    def provenance_tag_absent(ctx: IntakeContext) -> CheckResult:
        for name, tag in ctx.claim_provenance.items():
            if tag is None:
                return ("provenance_tag_absent", {"failed_field": name})
        return None

    def claim_provenance_recollection(ctx: IntakeContext) -> CheckResult:
        for name, tag in ctx.claim_provenance.items():
            if tag == "recollection":
                return ("claim_provenance_recollection", {"failed_field": name})
        return None

    def registered_at_unstampable(ctx: IntakeContext) -> CheckResult:
        breach = ctx.fence.breach(_population_key(ctx.proposal))
        if breach is None:
            return None
        return (
            "registered_at_unstampable",
            {
                "measured_on": ctx.proposal.measured_on_intention,
                "fence_breach_at": breach.at.isoformat(),
            },
        )

    def agent_overreached_schema(ctx: IntakeContext) -> CheckResult:
        breached = assert_agent_authority(ctx.raw_payload)
        if breached is None:
            return None
        return (
            "agent_overreached_schema",
            {"failed_field": breached, "reason": RESERVED_FROM_AGENT[breached]},
        )

    def security_master_unavailable(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.origin not in (Origin.AGENT, Origin.RANDOM_CONTROL):
            return None
        if ctx.entity_fence.security_master:
            return None
        return ("security_master_unavailable", {})

    def proposal_names_entity(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.origin not in (Origin.AGENT, Origin.RANDOM_CONTROL):
            return None
        text = ctx.proposal.fenced_text()
        hits = entity_mentions(text, ctx.entity_fence)
        if not hits:
            return None
        dates = ctx.entity_fence.dates(text)
        return (
            "proposal_names_entity",
            {
                "failed_field": ", ".join(hits[:5])
                + (f" (bound to {', '.join(dates[:2])})" if dates else "")
            },
        )

    def discovery_partition_violation(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.origin not in (Origin.AGENT, Origin.RANDOM_CONTROL):
            return None
        if ctx.proposal.source_partition in READABLE_BY_DISCOVERY:
            return None
        return (
            "discovery_partition_violation",
            {
                "source_ref": ctx.proposal.source_ref,
                "failed_field": ctx.proposal.source_partition.value,
            },
        )

    def scoring_mode_unsatisfiable(ctx: IntakeContext) -> CheckResult:
        if ctx.proposal.event_class in ctx.exclusivity_available:
            return None
        return (
            "scoring_mode_unsatisfiable",
            {
                "event_class": ctx.proposal.event_class,
                "measured_on": ctx.proposal.measured_on_intention,
            },
        )

    def duplicate_of_open_pointer(ctx: IntakeContext) -> CheckResult:
        key = (ctx.proposal.event_class, ctx.proposal.measured_on_intention)
        existing = ctx.open_pairs.get(key)
        if existing is None:
            return None
        return (
            "duplicate_of_open_pointer",
            {
                "event_class": key[0],
                "measured_on": key[1],
                "duplicate_ref": existing.get("directive_id", "an open pointer"),
                "duplicate_registered_at": existing.get("registered_at", "an earlier time"),
            },
        )

    return {
        "source_inaccessible": source_inaccessible,
        "event_definition_absent": event_definition_absent,
        "measured_on_absent": measured_on_absent,
        "provenance_tag_absent": provenance_tag_absent,
        "claim_provenance_recollection": claim_provenance_recollection,
        "registered_at_unstampable": registered_at_unstampable,
        "agent_overreached_schema": agent_overreached_schema,
        "security_master_unavailable": security_master_unavailable,
        "proposal_names_entity": proposal_names_entity,
        "discovery_partition_violation": discovery_partition_violation,
        "scoring_mode_unsatisfiable": scoring_mode_unsatisfiable,
        "duplicate_of_open_pointer": duplicate_of_open_pointer,
    }


def intake_runner(parameter_hash: str = "unfrozen", audit_fraction: float = 0.10) -> Runner:
    return Runner(
        surface="intake",
        order=INTAKE_ORDER,
        checks=build_intake_checks(),
        audit_fraction=audit_fraction,
        parameter_hash=parameter_hash,
    )


# ---------------------------------------------------------------------------
# Surface B -- observation ingestion of items from a named stream.
# ---------------------------------------------------------------------------


@dataclass
class ObservationContext:
    item: Item
    directive: Directive
    source_resolved: bool
    suspended_classes: frozenset
    lag_ceiling_sessions: int
    admissible_horizon: int
    mandatory_fields: Sequence[str] = ("direction", "direction_basis", "issuer")
    issuer_resolves: bool = True


def build_observation_checks() -> Dict[str, Callable[[object], CheckResult]]:
    def item_source_inaccessible(ctx: ObservationContext) -> CheckResult:
        if ctx.source_resolved:
            return None
        return (
            "item_source_inaccessible",
            {
                "item_id": ctx.item.item_id,
                "source_ref": ctx.item.source_ref,
                "detail": "no response at cited location",
            },
        )

    def running_document_no_anchor(ctx: ObservationContext) -> CheckResult:
        if ctx.item.document_type != "running":
            return None
        return ("running_document_no_anchor", {"item_id": ctx.item.item_id})

    def anchor_provenance_absent(ctx: ObservationContext) -> CheckResult:
        if ctx.item.t_pub_earliest is None:
            return (
                "anchor_provenance_absent",
                {"item_id": ctx.item.item_id, "failed_field": "t_pub_earliest"},
            )
        if not ctx.item.t_pub_earliest_provenance:
            return (
                "anchor_provenance_absent",
                {"item_id": ctx.item.item_id, "failed_field": "t_pub_earliest"},
            )
        return None

    def observation_anchor_absent(ctx: ObservationContext) -> CheckResult:
        if ctx.item.t_pub_observed is not None:
            return None
        return ("observation_anchor_absent", {"item_id": ctx.item.item_id})

    def ingestion_lag_exceeds_window(ctx: ObservationContext) -> CheckResult:
        lag = ctx.item.ingestion_lag_sessions
        if lag is None or lag <= ctx.lag_ceiling_sessions:
            return None
        return (
            "ingestion_lag_exceeds_window",
            {
                "item_id": ctx.item.item_id,
                "lag": lag,
                "lag_ceiling": ctx.lag_ceiling_sessions,
                "horizon": ctx.admissible_horizon,
            },
        )

    def extraction_class_suspended(ctx: ObservationContext) -> CheckResult:
        if ctx.item.extraction_class not in ctx.suspended_classes:
            return None
        return (
            "extraction_class_suspended",
            {
                "item_id": ctx.item.item_id,
                "extraction_class": ctx.item.extraction_class,
            },
        )

    def extraction_schema_incomplete(ctx: ObservationContext) -> CheckResult:
        for name in ctx.mandatory_fields:
            if ctx.item.extracted.get(name) in (None, ""):
                return (
                    "extraction_schema_incomplete",
                    {"item_id": ctx.item.item_id, "failed_field": name},
                )
        return None

    def issuer_unresolved(ctx: ObservationContext) -> CheckResult:
        if ctx.issuer_resolves and ctx.item.issuer:
            return None
        return (
            "issuer_unresolved",
            {
                "item_id": ctx.item.item_id,
                "detail": "no primary listing for the referenced issuer",
            },
        )

    def catalyst_date_corroborated(ctx: ObservationContext) -> CheckResult:
        if ctx.item.t_cat_claimed is None or ctx.item.t_cat_confirmed is not None:
            return None
        return ("catalyst_date_corroborated", {"item_id": ctx.item.item_id})

    def catalyst_duration_below_floor(ctx: ObservationContext) -> CheckResult:
        duration = ctx.item.catalyst_duration_sessions
        if duration is None or duration >= 1:
            return None
        return ("catalyst_duration_below_floor", {"item_id": ctx.item.item_id})

    def observation_precedes_registration(ctx: ObservationContext) -> CheckResult:
        registered = ctx.directive.registered_at
        observed = ctx.item.t_pub_observed
        if registered is None or observed is None or observed >= registered:
            return None
        return (
            "observation_precedes_registration",
            {
                "item_id": ctx.item.item_id,
                "item_date": observed.isoformat(),
                "registered_at": registered.isoformat(),
            },
        )

    return {
        "item_source_inaccessible": item_source_inaccessible,
        "running_document_no_anchor": running_document_no_anchor,
        "anchor_provenance_absent": anchor_provenance_absent,
        "observation_anchor_absent": observation_anchor_absent,
        "ingestion_lag_exceeds_window": ingestion_lag_exceeds_window,
        "extraction_class_suspended": extraction_class_suspended,
        "extraction_schema_incomplete": extraction_schema_incomplete,
        "issuer_unresolved": issuer_unresolved,
        "catalyst_date_corroborated": catalyst_date_corroborated,
        "catalyst_duration_below_floor": catalyst_duration_below_floor,
        "observation_precedes_registration": observation_precedes_registration,
    }


def observation_runner(
    parameter_hash: str = "unfrozen", audit_fraction: float = 0.10
) -> Runner:
    return Runner(
        surface="observation",
        order=OBSERVATION_ORDER,
        checks=build_observation_checks(),
        audit_fraction=audit_fraction,
        parameter_hash=parameter_hash,
    )
