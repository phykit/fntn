"""The design-segment reuse ledger and the admission arithmetic.

v1.11 capped concurrency at six directives, a number defended by nothing.  The
real constraint was never tidiness: the design segment is short -- a three-way
split of a two-to-three-year archive leaves perhaps twelve to eighteen design
months -- directives measuring on it overlap, and an over-reused segment quietly
stops being out of sample for anything.

An agent scanner makes that constraint bind immediately rather than eventually,
because a machine can raise registrable pointers faster than a segment can
absorb them.  Two rules follow, and both are new in v1.14:

* **Admission is by smallest registered span first**, ties broken by
  registration time.  This maximises directives per unit of segment and, more
  importantly, neither the agent nor the operator scores merit at admission --
  a proposed priority would return ranking to the party that raised the idea.
* **Agent-origin drafts queue and may not displace.**  Only operator-origin
  pointers keep the displacement right v1.11 gave them.  Without this the
  machine evicts the operator's own directives simply by out-producing them,
  which converts a capacity rule into a takeover.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import summaries
from .records import Directive, Origin, Refusal, SegmentSpan


@dataclass
class SegmentPolicy:
    """§14 governance decisions.  Both are open, and both are stated ranges."""

    #: Pairwise overlap tolerance.  Open §14 decision.
    theta: float = 0.25
    #: Sessions the pending §13 calibrations hold first claim on.  Directives
    #: take the residual: the calibrations complete the freeze and the
    #: directives do not.
    calibration_reserve_sessions: int = 0
    #: Total sessions in the design segment.
    segment_sessions: int = 0
    #: Floor below which a directive is not worth a session of the segment.
    #: Open §14 decision.
    delta_min_floor: float = 25.0


@dataclass
class ReuseLedger:
    """Per-directive span consumed and pairwise overlap with every other.

    Displayed with the funnel, in the same spirit as the manual and explore
    shares: the reader sees how much of the segment the search has eaten.
    """

    policy: SegmentPolicy
    open_directives: Dict[str, Directive] = field(default_factory=dict)
    closed_directives: Dict[str, Directive] = field(default_factory=dict)
    queue: List[Directive] = field(default_factory=list)

    # -- accounting --------------------------------------------------------

    def consumed_sessions(self) -> int:
        return sum(d.span.sessions for d in self.open_directives.values())

    def available_sessions(self) -> int:
        return max(
            0,
            self.policy.segment_sessions
            - self.policy.calibration_reserve_sessions
            - self.consumed_sessions(),
        )

    def worst_overlap(self, span: SegmentSpan) -> Tuple[Optional[str], float]:
        worst_id, worst = None, 0.0
        for did, d in self.open_directives.items():
            ov = span.overlap_fraction(d.span)
            if ov > worst:
                worst_id, worst = did, ov
        return worst_id, worst

    def overlap_matrix(self) -> Dict[Tuple[str, str], float]:
        ids = sorted(self.open_directives)
        out: Dict[Tuple[str, str], float] = {}
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                out[(a, b)] = self.open_directives[a].span.overlap_fraction(
                    self.open_directives[b].span
                )
        return out

    # -- admission ---------------------------------------------------------

    def admit(self, directive: Directive) -> Optional[Refusal]:
        """Admit, or return the refusal that blocks admission.

        Order of the three tests matters and is pre-registered: the segment
        reserve is checked before overlap, because a directive that cannot fit
        at all should not be reported as an overlap problem it could fix by
        re-registering a narrower span.
        """

        if not directive.is_registered:
            raise ValueError(
                f"{directive.directive_id} is not registered; admission is the "
                "step after registration, never a substitute for it"
            )

        if directive.span.sessions > self.available_sessions():
            return summaries.render(
                "segment_reserved_for_calibration",
                directive.directive_id,
                {
                    "available": self.available_sessions(),
                    "reserve": self.policy.calibration_reserve_sessions,
                },
            )

        worst_id, worst = self.worst_overlap(directive.span)
        if worst > self.policy.theta:
            return summaries.render(
                "segment_overlap_exceeds_theta",
                directive.directive_id,
                {
                    "worst_pair": worst_id,
                    "overlap": worst,
                    "theta": self.policy.theta,
                },
            )

        self.open_directives[directive.directive_id] = directive
        return None

    def enqueue(self, directive: Directive) -> Refusal:
        """Queue a registration-ready draft that admission refused."""

        self.queue.append(directive)
        self._sort_queue()
        position = self.queue.index(directive) + 1
        return summaries.render(
            "queued_behind_capacity",
            directive.directive_id,
            {"queue_position": position, "queue_length": len(self.queue)},
        )

    def _sort_queue(self) -> None:
        self.queue.sort(
            key=lambda d: (
                d.span.sessions,
                d.registered_at.isoformat() if d.registered_at else "",
                d.directive_id,
            )
        )

    def drain_queue(self) -> List[Directive]:
        """Admit whatever the arithmetic now clears, head of queue first."""

        admitted: List[Directive] = []
        progress = True
        while progress:
            progress = False
            for d in list(self.queue):
                if self.admit(d) is None:
                    self.queue.remove(d)
                    admitted.append(d)
                    progress = True
                    break
        return admitted

    def close(self, directive_id: str) -> None:
        d = self.open_directives.pop(directive_id, None)
        if d is not None:
            self.closed_directives[directive_id] = d
            self.drain_queue()

    # -- displacement ------------------------------------------------------

    def displace(
        self, incoming: Directive, target_id: str, operator_summary: Refusal
    ) -> None:
        """Only operator-origin pointers may displace, and the swap is recorded."""

        if not incoming.may_displace:
            raise PermissionError(
                f"{incoming.directive_id} is {incoming.origin.value}-origin and "
                "may not displace an open directive; machine-raised drafts "
                "queue, so that volume cannot evict the operator's own ideas"
            )
        if operator_summary.author == "template":
            raise ValueError(
                "a displacement is a human decision and §8 requires the "
                "operator's own two to three sentences, not a rendered template"
            )
        self.close(target_id)
        self.admit(incoming)

    # -- display -----------------------------------------------------------

    def render(self) -> str:
        lines = [
            "Design-segment reuse ledger (§3.6.8)",
            f"  segment sessions             : {self.policy.segment_sessions}",
            f"  calibration reserve          : {self.policy.calibration_reserve_sessions}",
            f"  consumed by open directives  : {self.consumed_sessions()}",
            f"  unconsumed and available     : {self.available_sessions()}",
            f"  overlap tolerance theta      : {self.policy.theta:.2f}",
            f"  open directives              : {len(self.open_directives)}",
            f"  queued, registration-ready   : {len(self.queue)}",
        ]
        matrix = self.overlap_matrix()
        if matrix:
            lines.append("  pairwise overlap:")
            for (a, b), ov in sorted(matrix.items(), key=lambda kv: -kv[1]):
                flag = "  <-- at tolerance" if ov > self.policy.theta else ""
                lines.append(f"    {a} x {b}: {ov:.2f}{flag}")
        by_origin: Dict[str, int] = {}
        for d in self.open_directives.values():
            by_origin[d.origin.value] = by_origin.get(d.origin.value, 0) + 1
        if by_origin:
            lines.append(
                "  open by origin               : "
                + ", ".join(f"{k}={v}" for k, v in sorted(by_origin.items()))
            )
        return "\n".join(lines)


def counting_family_four(
    proposed: int, registered: int, promoted: int
) -> str:
    """§6.4's fourth family, with the three-tier counter v1.14 adds.

    A scanner makes the proposal count and the registration count differ by
    orders of magnitude, so reporting one number would mislead in whichever
    direction the author preferred.  All three are disclosed, and none divides
    anything: a pointer killed or left undetermined on the design segment never
    touches the evaluation sample, so its cost is design-segment power, tracked
    by the reuse ledger, and not false-discovery budget.  Only a candidate that
    survives into an evaluation-scored cohort crosses into the cross-candidate
    family and enters the Benjamini-Hochberg step, with its provenance displayed
    beside its percentile.
    """

    return "\n".join(
        [
            "Multiplicity family 4 -- design-segment search (§6.4)",
            f"  proposals raised             : {proposed}",
            f"  pointers registered          : {registered}",
            f"  promoted to evaluation       : {promoted}",
            "  divides                      : nothing",
            "  crosses into family 2        : promoted only",
        ]
    )
